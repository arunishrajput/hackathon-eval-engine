from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional
from uuid import UUID
from app.database import get_db, AsyncSessionLocal
from app.dependencies import get_current_user
from app.core.security import verify_token
from app.models.user import User
from app.models.evaluation import Evaluation
from app.models.submission import Submission
from app.schemas.evaluation import EvaluationRead
from app.core.exceptions import NotFoundError, ForbiddenError
import json
import asyncio

router = APIRouter()


@router.get("/{submission_id}", response_model=EvaluationRead)
async def get_evaluation(
    submission_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify submission ownership
    sub_result = await db.execute(select(Submission).where(Submission.id == submission_id))
    submission = sub_result.scalar_one_or_none()
    if not submission:
        raise NotFoundError("Submission not found")
    if submission.user_id != current_user.id and current_user.role.value != "admin":
        raise ForbiddenError()

    result = await db.execute(
        select(Evaluation)
        .options(selectinload(Evaluation.agent_results))
        .where(Evaluation.submission_id == submission_id)
    )
    evaluation = result.scalar_one_or_none()
    if not evaluation:
        raise NotFoundError("Evaluation not found")
    return evaluation


@router.get("/{submission_id}/stream")
async def stream_evaluation_progress(
    submission_id: UUID,
    token: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """SSE endpoint for real-time evaluation progress.

    Accepts token via ?token= query param because EventSource cannot
    send custom Authorization headers.
    """
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token required")

    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    user_result = await db.execute(select(User).where(User.id == user_id))
    current_user = user_result.scalar_one_or_none()
    if not current_user or not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Verify submission ownership
    sub_result = await db.execute(select(Submission).where(Submission.id == submission_id))
    submission = sub_result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    if submission.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    async def event_generator():
        # Use a fresh session per poll so the connection isn't held open
        for _ in range(360):  # Poll up to 6 minutes (360s at 1s intervals)
            async with AsyncSessionLocal() as poll_db:
                sub_result = await poll_db.execute(
                    select(Submission).where(Submission.id == submission_id)
                )
                sub = sub_result.scalar_one_or_none()

                eval_result = await poll_db.execute(
                    select(Evaluation)
                    .options(selectinload(Evaluation.agent_results))
                    .where(Evaluation.submission_id == submission_id)
                )
                evaluation = eval_result.scalar_one_or_none()

            # Use submission status for granular stages; fall back to evaluation status
            stage = sub.status.value if sub else "pending"
            if evaluation:
                data = {
                    "status": stage,
                    "final_score": float(evaluation.final_score) if evaluation.final_score else None,
                    "agent_count": len(evaluation.agent_results),
                }
                yield f"data: {json.dumps(data)}\n\n"

                if evaluation.status.value in ("completed", "failed"):
                    break
            else:
                yield f"data: {json.dumps({'status': stage})}\n\n"

            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
