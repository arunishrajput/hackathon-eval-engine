from app.config import settings
import structlog

logger = structlog.get_logger()


async def enqueue_evaluation(submission_id: str) -> None:
    """Enqueue an evaluation job via arq.

    Failure to enqueue is logged but not raised so that the submission
    creation API call still succeeds even when Redis is temporarily unavailable.
    """
    try:
        from arq import create_pool
        from arq.connections import RedisSettings

        redis = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
        await redis.enqueue_job("run_evaluation", submission_id)
        await redis.close()
        logger.info("Evaluation job enqueued", submission_id=submission_id)
    except Exception as e:
        logger.error(
            "Failed to enqueue evaluation job",
            error=str(e),
            submission_id=submission_id,
        )


async def run_evaluation(ctx: dict, submission_id: str) -> None:  # noqa: C901
    """arq worker task: run the full evaluation pipeline for a submission.

    Steps:
    1. Load submission from DB.
    2. Load criteria for the hackathon from DB.
    3. Create / update the Evaluation record.
    4. Run the LangGraph pipeline (evaluation_graph.ainvoke).
    5. Save AgentResult rows to DB.
    6. Update submission status to completed (or failed).
    7. Trigger embed_repository job.
    8. Trigger recompute_rankings for the hackathon.
    9. Handle all errors: mark status=failed.
    """
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
    from datetime import datetime, timezone
    from uuid import UUID

    from app.database import AsyncSessionLocal
    from app.models.submission import Submission, SubmissionStatus
    from app.models.evaluation import Evaluation, EvaluationStatus
    from app.models.hackathon import Hackathon
    from app.models.criterion import Criterion
    from app.models.agent_result import AgentResult
    from app.orchestration.graph import evaluation_graph
    from app.embedding.embedder import embed_repository
    from app.scoring.aggregator import recompute_rankings

    logger.info("Starting evaluation job", submission_id=submission_id)

    async with AsyncSessionLocal() as db:
        # ------------------------------------------------------------------ #
        # Step 1 – Load submission
        # ------------------------------------------------------------------ #
        try:
            result = await db.execute(
                select(Submission).where(Submission.id == UUID(submission_id))
            )
            submission = result.scalar_one_or_none()
            if not submission:
                logger.error("Submission not found", submission_id=submission_id)
                return
        except Exception as e:
            logger.error("DB error loading submission", error=str(e), submission_id=submission_id)
            return

        # ------------------------------------------------------------------ #
        # Step 2 – Load hackathon + criteria
        # ------------------------------------------------------------------ #
        try:
            hack_result = await db.execute(
                select(Hackathon).where(Hackathon.id == submission.hackathon_id)
            )
            hackathon = hack_result.scalar_one_or_none()

            criteria_result = await db.execute(
                select(Criterion)
                .where(Criterion.hackathon_id == submission.hackathon_id)
                .order_by(Criterion.display_order)
            )
            criteria_rows = criteria_result.scalars().all()
            criteria = [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "description": c.description or "",
                    "weight": float(c.weight),
                    "agent_id": c.agent_id,
                }
                for c in criteria_rows
            ]
        except Exception as e:
            logger.error("DB error loading hackathon/criteria", error=str(e), submission_id=submission_id)
            criteria = []
            hackathon = None

        # ------------------------------------------------------------------ #
        # Step 3 – Create / upsert Evaluation record
        # ------------------------------------------------------------------ #
        try:
            existing_eval = await db.execute(
                select(Evaluation).where(Evaluation.submission_id == submission.id)
            )
            evaluation = existing_eval.scalar_one_or_none()

            if evaluation is None:
                evaluation = Evaluation(
                    submission_id=submission.id,
                    hackathon_id=submission.hackathon_id,
                    status=EvaluationStatus.running,
                    started_at=datetime.now(timezone.utc),
                )
                db.add(evaluation)
            else:
                evaluation.status = EvaluationStatus.running
                evaluation.started_at = datetime.now(timezone.utc)

            submission.status = SubmissionStatus.cloning
            await db.flush()
        except Exception as e:
            logger.error("DB error creating evaluation record", error=str(e), submission_id=submission_id)
            await db.rollback()
            return

        # ------------------------------------------------------------------ #
        # Step 4 – Run LangGraph pipeline
        # ------------------------------------------------------------------ #
        initial_state = {
            "submission_id": submission_id,
            "hackathon_id": str(submission.hackathon_id),
            "repo_url": submission.repo_url,
            "repo_path": None,
            "files": None,
            "static_analysis": None,
            "context": None,
            "agent_outputs": None,
            "final_score": None,
            "report": None,
            "error": None,
            "status": "cloning",
            "hackathon_description": hackathon.description if hackathon else "",
            "criteria": criteria,
        }

        try:
            final_state = await evaluation_graph.ainvoke(initial_state)
        except Exception as e:
            logger.error("evaluation_graph.ainvoke raised", error=str(e), submission_id=submission_id)
            final_state = {**initial_state, "status": "failed", "error": str(e)}

        # ------------------------------------------------------------------ #
        # Step 5 / 6 – Persist results or mark failed
        # ------------------------------------------------------------------ #
        try:
            if final_state.get("status") == "completed":
                # Save agent results
                for output in (final_state.get("agent_outputs") or []):
                    agent_result = AgentResult(
                        evaluation_id=evaluation.id,
                        agent_id=output["agent_id"],
                        score_raw=output.get("score"),
                        confidence=output.get("confidence"),
                        evidence=output.get("evidence", []),
                        strengths=output.get("strengths", []),
                        weaknesses=output.get("weaknesses", []),
                        reasoning=output.get("reasoning"),
                        abstained=output.get("abstained", False),
                        abstain_reason=output.get("abstain_reason"),
                        processing_time_ms=output.get("processing_time_ms"),
                        prompt_version=output.get("prompt_version", "1.0"),
                    )
                    db.add(agent_result)

                evaluation.status = EvaluationStatus.completed
                evaluation.final_score = final_state.get("final_score")
                evaluation.report = final_state.get("report")
                evaluation.completed_at = datetime.now(timezone.utc)

                submission.status = SubmissionStatus.completed
                submission.evaluation_completed_at = datetime.now(timezone.utc)

            else:
                evaluation.status = EvaluationStatus.failed
                submission.status = SubmissionStatus.failed
                submission.error_message = final_state.get("error") or "Unknown error"

            await db.commit()
            logger.info(
                "Evaluation job persisted",
                submission_id=submission_id,
                pipeline_status=final_state.get("status"),
            )
        except Exception as e:
            logger.error("DB error saving evaluation results", error=str(e), submission_id=submission_id)
            await db.rollback()
            raise

        # ------------------------------------------------------------------ #
        # Step 7 – Trigger embed_repository (best-effort, non-blocking)
        # ------------------------------------------------------------------ #
        if final_state.get("status") == "completed" and final_state.get("files"):
            try:
                async with AsyncSessionLocal() as embed_db:
                    await embed_repository(embed_db, submission_id, final_state["files"])
                    logger.info("Repository embeddings created", submission_id=submission_id)
            except Exception as e:
                logger.warning(
                    "embed_repository failed (non-fatal)",
                    error=str(e),
                    submission_id=submission_id,
                )

        # ------------------------------------------------------------------ #
        # Step 8 – Trigger recompute_rankings (best-effort, non-blocking)
        # ------------------------------------------------------------------ #
        if final_state.get("status") == "completed":
            try:
                async with AsyncSessionLocal() as rank_db:
                    rankings = await recompute_rankings(rank_db, submission.hackathon_id)
                    await rank_db.commit()
                    logger.info(
                        "Rankings recomputed",
                        hackathon_id=str(submission.hackathon_id),
                        count=len(rankings),
                    )
            except Exception as e:
                logger.warning(
                    "recompute_rankings failed (non-fatal)",
                    error=str(e),
                    submission_id=submission_id,
                )
