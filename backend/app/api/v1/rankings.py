from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.ranking import Ranking
from app.models.submission import Submission
from app.models.evaluation import Evaluation
from app.schemas.ranking import LeaderboardResponse, LeaderboardEntry
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("/{hackathon_id}/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    hackathon_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Ranking, Submission, Evaluation, User)
        .join(Submission, Ranking.submission_id == Submission.id)
        .join(Evaluation, Evaluation.submission_id == Submission.id)
        .join(User, Submission.user_id == User.id)
        .where(Ranking.hackathon_id == hackathon_id)
        .order_by(Ranking.rank)
    )
    rows = result.all()

    entries = [
        LeaderboardEntry(
            rank=row.Ranking.rank,
            submission_id=row.Ranking.submission_id,
            user_full_name=row.User.full_name,
            repo_name=row.Submission.repo_name,
            final_score=float(row.Evaluation.final_score) if row.Evaluation.final_score else None,
            normalized_score=float(row.Ranking.normalized_score) if row.Ranking.normalized_score else None,
            percentile=float(row.Ranking.percentile) if row.Ranking.percentile else None,
        )
        for row in rows
    ]

    finalized = all(row.Ranking.finalized for row in rows) if rows else False

    return LeaderboardResponse(
        hackathon_id=hackathon_id,
        total_submissions=len(entries),
        finalized=finalized,
        entries=entries,
    )
