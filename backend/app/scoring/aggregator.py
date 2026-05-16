from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.ranking import Ranking
from app.models.evaluation import Evaluation, EvaluationStatus
import structlog

logger = structlog.get_logger()

DEFAULT_WEIGHTS = {
    "repo_understanding": 0.30,
    "code_quality": 0.40,
    "innovation": 0.30,
}


def aggregate_scores(
    agent_outputs: List[Dict[str, Any]],
    criteria: List[Dict[str, Any]] = None,
) -> float:
    """
    Compute weighted average of agent scores.
    Falls back to DEFAULT_WEIGHTS if no criteria are specified.
    Abstained agents are excluded from the weighted sum.
    """
    weights = {}
    if criteria:
        for c in criteria:
            agent_id = c.get("agent_id")
            weight = c.get("weight", 0)
            if agent_id:
                weights[agent_id] = weight

    if not weights:
        weights = DEFAULT_WEIGHTS

    # Normalize weights to sum to 1.0
    total_weight = sum(weights.values())
    if total_weight > 0:
        weights = {k: v / total_weight for k, v in weights.items()}

    weighted_sum = 0.0
    effective_weight = 0.0

    for output in agent_outputs:
        if output.get("abstained") or output.get("score") is None:
            continue
        agent_id = output["agent_id"]
        weight = weights.get(agent_id, 1.0 / max(len(agent_outputs), 1))
        weighted_sum += output["score"] * weight
        effective_weight += weight

    if effective_weight == 0:
        return 0.0

    # Rescale if some agents abstained
    final_score = weighted_sum / effective_weight
    return round(min(max(final_score, 0.0), 10.0), 3)


async def recompute_rankings(db: AsyncSession, hackathon_id) -> List[Ranking]:
    """Recompute rankings for all completed evaluations in a hackathon."""
    result = await db.execute(
        select(Evaluation)
        .where(
            Evaluation.hackathon_id == hackathon_id,
            Evaluation.status == EvaluationStatus.completed,
            Evaluation.final_score.isnot(None),
        )
        .order_by(Evaluation.final_score.desc())
    )
    evaluations = result.scalars().all()

    if not evaluations:
        return []

    scores = [float(e.final_score) for e in evaluations]
    min_score = min(scores)
    max_score = max(scores)
    score_range = max_score - min_score

    rankings = []
    for rank_idx, evaluation in enumerate(evaluations, start=1):
        score = float(evaluation.final_score)
        normalized = (score - min_score) / score_range if score_range > 0 else 1.0
        percentile = ((len(evaluations) - rank_idx) / max(len(evaluations) - 1, 1)) * 100

        # Upsert ranking
        existing = await db.execute(
            select(Ranking).where(Ranking.submission_id == evaluation.submission_id)
        )
        ranking = existing.scalar_one_or_none()

        if ranking:
            ranking.rank = rank_idx
            ranking.normalized_score = round(normalized * 10, 3)
            ranking.percentile = round(percentile, 2)
        else:
            ranking = Ranking(
                hackathon_id=hackathon_id,
                submission_id=evaluation.submission_id,
                rank=rank_idx,
                normalized_score=round(normalized * 10, 3),
                percentile=round(percentile, 2),
            )
            db.add(ranking)

        rankings.append(ranking)

    await db.flush()
    return rankings
