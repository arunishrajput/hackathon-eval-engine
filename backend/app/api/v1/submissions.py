from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from datetime import datetime, timezone
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.submission import Submission, SubmissionStatus
from app.schemas.submission import SubmissionCreate, SubmissionRead
from app.core.exceptions import NotFoundError, ForbiddenError, BadRequestError
from app.jobs.tasks import enqueue_evaluation
import json
import asyncio
import re

router = APIRouter()

GITHUB_URL_RE = re.compile(
    r"^https?://github\.com/[\w\-\.]+/[\w\-\.]+(/.*)?$"
)


def _validate_github_url(url: str) -> None:
    if not GITHUB_URL_RE.match(url):
        raise BadRequestError("Only public GitHub repository URLs are accepted.")


@router.post("/", response_model=SubmissionRead, status_code=status.HTTP_201_CREATED)
async def create_submission(
    data: SubmissionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _validate_github_url(data.repo_url)

    # Check for duplicate submission
    existing = await db.execute(
        select(Submission).where(
            Submission.hackathon_id == data.hackathon_id,
            Submission.user_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise BadRequestError("You have already submitted to this hackathon.")

    submission = Submission(
        hackathon_id=data.hackathon_id,
        user_id=current_user.id,
        repo_url=str(data.repo_url).rstrip("/"),
    )
    db.add(submission)
    await db.flush()
    await db.refresh(submission)

    await enqueue_evaluation(str(submission.id))

    return submission


@router.get("/", response_model=List[SubmissionRead])
async def list_my_submissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Submission)
        .where(Submission.user_id == current_user.id)
        .order_by(Submission.submitted_at.desc())
    )
    return result.scalars().all()


@router.get("/{submission_id}", response_model=SubmissionRead)
async def get_submission(
    submission_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Submission).where(Submission.id == submission_id))
    submission = result.scalar_one_or_none()
    if not submission:
        raise NotFoundError("Submission not found")
    if submission.user_id != current_user.id and current_user.role.value != "admin":
        raise ForbiddenError()
    return submission


@router.get("/{submission_id}/status")
async def stream_submission_status(
    submission_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """SSE stream for real-time evaluation progress.

    Events:
      progress — stage update with percentage
      completed — final score ready
      error — pipeline failure
    """
    result = await db.execute(select(Submission).where(Submission.id == submission_id))
    submission = result.scalar_one_or_none()
    if not submission:
        raise NotFoundError("Submission not found")
    if submission.user_id != current_user.id and current_user.role.value != "admin":
        raise ForbiddenError()

    STAGE_PROGRESS = {
        SubmissionStatus.pending: ("pending", 0),
        SubmissionStatus.cloning: ("cloning", 10),
        SubmissionStatus.analyzing: ("analyzing", 30),
        SubmissionStatus.evaluating: ("evaluating", 60),
        SubmissionStatus.completed: ("completed", 100),
        SubmissionStatus.failed: ("failed", 0),
    }

    async def event_generator():
        last_status = None
        for _ in range(180):  # Poll up to 3 minutes
            # Re-query to get fresh status
            fresh_result = await db.execute(
                select(Submission).where(Submission.id == submission_id)
            )
            sub = fresh_result.scalar_one_or_none()
            if not sub:
                break

            stage, pct = STAGE_PROGRESS.get(sub.status, ("unknown", 0))

            if sub.status != last_status:
                last_status = sub.status
                event_data = {
                    "event": "progress",
                    "data": {
                        "stage": stage,
                        "message": f"Pipeline stage: {stage}",
                        "progress_pct": pct,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                }
                yield f"data: {json.dumps(event_data)}\n\n"

            if sub.status == SubmissionStatus.completed:
                from sqlalchemy.orm import selectinload
                from app.models.evaluation import Evaluation
                eval_result = await db.execute(
                    select(Evaluation).where(Evaluation.submission_id == submission_id)
                )
                evaluation = eval_result.scalar_one_or_none()
                final_score = float(evaluation.final_score) if evaluation and evaluation.final_score else None
                complete_data = {
                    "event": "completed",
                    "data": {
                        "evaluation_id": str(evaluation.id) if evaluation else None,
                        "final_score": final_score,
                    },
                }
                yield f"data: {json.dumps(complete_data)}\n\n"
                break

            if sub.status == SubmissionStatus.failed:
                error_data = {
                    "event": "error",
                    "data": {
                        "message": sub.error_message or "Evaluation pipeline failed",
                        "stage": stage,
                    },
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                break

            await asyncio.sleep(2)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def withdraw_submission(
    submission_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Submission).where(Submission.id == submission_id))
    submission = result.scalar_one_or_none()
    if not submission:
        raise NotFoundError("Submission not found")
    if submission.user_id != current_user.id:
        raise ForbiddenError()
    if submission.status not in (SubmissionStatus.pending, SubmissionStatus.failed):
        raise BadRequestError("Cannot withdraw a submission that is already being evaluated.")
    await db.delete(submission)


@router.post("/{submission_id}/retry", response_model=SubmissionRead)
async def retry_submission(
    submission_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Allow the submission owner to retry a failed evaluation."""
    result = await db.execute(select(Submission).where(Submission.id == submission_id))
    submission = result.scalar_one_or_none()
    if not submission:
        raise NotFoundError("Submission not found")
    if submission.user_id != current_user.id:
        raise ForbiddenError()
    if submission.status != SubmissionStatus.failed:
        raise BadRequestError("Only failed submissions can be retried.")

    submission.status = SubmissionStatus.pending
    submission.error_message = None
    await db.flush()
    await db.refresh(submission)

    await enqueue_evaluation(str(submission_id))
    return submission
