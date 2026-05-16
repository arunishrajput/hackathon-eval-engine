from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from uuid import UUID
from datetime import datetime, timezone
from app.database import get_db
from app.dependencies import get_current_admin
from app.models.user import User
from app.models.hackathon import Hackathon
from app.models.submission import Submission, SubmissionStatus
from app.models.ranking import Ranking
from app.models.evaluation import Evaluation, EvaluationStatus
from app.schemas.user import UserRead, UserUpdate
from app.schemas.hackathon import HackathonRead
from app.schemas.ranking import RankingRead
from app.scoring.aggregator import recompute_rankings
from app.core.exceptions import NotFoundError
from app.config import settings
import httpx

router = APIRouter()


@router.get("/hackathons")
async def admin_list_all_hackathons(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all hackathons including drafts, with submission/evaluation stats."""
    result = await db.execute(select(Hackathon).order_by(Hackathon.created_at.desc()))
    hackathons = result.scalars().all()

    enriched = []
    for h in hackathons:
        sub_result = await db.execute(
            select(
                func.count(Submission.id).label("total"),
                func.count(
                    Submission.id.filter(Submission.status == SubmissionStatus.completed)
                ).label("completed"),
                func.count(
                    Submission.id.filter(Submission.status == SubmissionStatus.failed)
                ).label("failed"),
            ).where(Submission.hackathon_id == h.id)
        )
        stats = sub_result.one()
        enriched.append({
            "id": str(h.id),
            "title": h.title,
            "status": h.status.value,
            "created_at": h.created_at.isoformat(),
            "start_date": h.start_date.isoformat() if h.start_date else None,
            "end_date": h.end_date.isoformat() if h.end_date else None,
            "submissions_total": stats.total,
            "submissions_completed": stats.completed,
            "submissions_failed": stats.failed,
        })
    return enriched


@router.get("/queue/status")
async def queue_status(current_admin: User = Depends(get_current_admin)):
    """Return ARQ job queue statistics via Redis inspection."""
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL)
        queue_len = await r.llen("arq:queue")
        running_keys = await r.keys("arq:job:*")
        await r.aclose()
        return {
            "status": "connected",
            "queued_jobs": queue_len,
            "active_jobs": len(running_keys),
        }
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}


@router.get("/users", response_model=List[UserRead])
async def list_users(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.patch("/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User not found")
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(user, k, v)
    await db.flush()
    await db.refresh(user)
    return user


@router.post("/hackathons/{hackathon_id}/finalize-rankings", response_model=List[RankingRead])
async def finalize_rankings_admin(
    hackathon_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    rankings = await recompute_rankings(db, hackathon_id)
    now = datetime.now(timezone.utc)
    for ranking in rankings:
        ranking.finalized = True
        ranking.finalized_at = now
        ranking.finalized_by = current_admin.id
    await db.flush()
    return rankings


@router.get("/hackathons/{hackathon_id}/submissions")
async def admin_list_submissions(
    hackathon_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Submission, User, Evaluation)
        .join(User, Submission.user_id == User.id)
        .outerjoin(Evaluation, Evaluation.submission_id == Submission.id)
        .where(Submission.hackathon_id == hackathon_id)
        .order_by(Submission.submitted_at.desc())
    )
    return [
        {
            "submission_id": str(row.Submission.id),
            "user_id": str(row.User.id),
            "user_name": row.User.full_name or row.User.email,
            "repo_url": row.Submission.repo_url,
            "status": row.Submission.status.value,
            "final_score": float(row.Evaluation.final_score) if row.Evaluation and row.Evaluation.final_score else None,
            "submitted_at": row.Submission.submitted_at.isoformat(),
            "error_message": row.Submission.error_message,
        }
        for row in result.all()
    ]


@router.post("/evaluations/{submission_id}/retry")
async def retry_evaluation(
    submission_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Reset a failed evaluation and re-enqueue it."""
    result = await db.execute(select(Submission).where(Submission.id == submission_id))
    submission = result.scalar_one_or_none()
    if not submission:
        raise NotFoundError("Submission not found")

    submission.status = SubmissionStatus.pending
    submission.error_message = None
    await db.flush()

    from app.jobs.tasks import enqueue_evaluation
    await enqueue_evaluation(str(submission_id))
    return {"message": "Evaluation re-queued", "submission_id": str(submission_id)}
