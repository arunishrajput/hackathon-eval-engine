from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID
from datetime import datetime, timezone
from app.database import get_db
from app.dependencies import get_current_user, get_current_admin
from app.models.user import User, UserRole
from app.models.hackathon import Hackathon, HackathonStatus, HackathonParticipant
from app.models.criterion import Criterion
from app.models.ranking import Ranking
from app.models.submission import Submission
from app.models.evaluation import Evaluation, EvaluationStatus
from app.schemas.hackathon import (
    HackathonCreate, HackathonRead, HackathonUpdate,
    CriterionCreate, CriterionRead, CriterionBulkUpdate,
)
from app.core.exceptions import NotFoundError, ForbiddenError, BadRequestError, ConflictError

router = APIRouter()


def _assert_owner(hackathon: Hackathon, current_user: User) -> None:
    if hackathon.admin_id != current_user.id and current_user.role != UserRole.admin:
        raise ForbiddenError("Only the hackathon owner or an admin can perform this action.")


@router.get("/", response_model=List[HackathonRead])
async def list_hackathons(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Hackathon).options(selectinload(Hackathon.criteria))
        .where(Hackathon.status != HackathonStatus.draft)
        .order_by(Hackathon.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=HackathonRead, status_code=status.HTTP_201_CREATED)
async def create_hackathon(
    data: HackathonCreate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    hackathon = Hackathon(
        title=data.title,
        description=data.description,
        admin_id=current_user.id,
        start_date=data.start_date,
        end_date=data.end_date,
        max_submissions=data.max_submissions,
        settings=data.settings or {
            "allow_private_repos": False,
            "max_repo_size_mb": 50,
            "evaluation_mode": "standard",
            "show_rankings_before_finalization": False,
        },
    )
    db.add(hackathon)
    await db.flush()

    if data.criteria:
        for i, crit in enumerate(data.criteria):
            criterion = Criterion(
                hackathon_id=hackathon.id,
                name=crit.name,
                description=crit.description,
                weight=crit.weight,
                agent_id=crit.agent_id,
                display_order=i,
            )
            db.add(criterion)

    await db.flush()
    result = await db.execute(
        select(Hackathon).options(selectinload(Hackathon.criteria)).where(Hackathon.id == hackathon.id)
    )
    return result.scalar_one()


@router.get("/{hackathon_id}", response_model=HackathonRead)
async def get_hackathon(hackathon_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Hackathon).options(selectinload(Hackathon.criteria)).where(Hackathon.id == hackathon_id)
    )
    hackathon = result.scalar_one_or_none()
    if not hackathon:
        raise NotFoundError("Hackathon not found")
    return hackathon


@router.patch("/{hackathon_id}", response_model=HackathonRead)
async def update_hackathon(
    hackathon_id: UUID,
    data: HackathonUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Hackathon).where(Hackathon.id == hackathon_id))
    hackathon = result.scalar_one_or_none()
    if not hackathon:
        raise NotFoundError("Hackathon not found")
    _assert_owner(hackathon, current_user)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(hackathon, key, value)

    await db.flush()
    result = await db.execute(
        select(Hackathon).options(selectinload(Hackathon.criteria)).where(Hackathon.id == hackathon_id)
    )
    return result.scalar_one()


@router.delete("/{hackathon_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hackathon(
    hackathon_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Hackathon).where(Hackathon.id == hackathon_id))
    hackathon = result.scalar_one_or_none()
    if not hackathon:
        raise NotFoundError("Hackathon not found")
    _assert_owner(hackathon, current_user)
    await db.delete(hackathon)


@router.patch("/{hackathon_id}/status", response_model=HackathonRead)
async def transition_status(
    hackathon_id: UUID,
    new_status: HackathonStatus,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Hackathon).where(Hackathon.id == hackathon_id))
    hackathon = result.scalar_one_or_none()
    if not hackathon:
        raise NotFoundError("Hackathon not found")
    _assert_owner(hackathon, current_user)

    valid_transitions = {
        HackathonStatus.draft: [HackathonStatus.active],
        HackathonStatus.active: [HackathonStatus.evaluating, HackathonStatus.draft],
        HackathonStatus.evaluating: [HackathonStatus.finalized],
        HackathonStatus.finalized: [],
    }
    if new_status not in valid_transitions.get(hackathon.status, []):
        raise BadRequestError(f"Cannot transition from {hackathon.status} to {new_status}")

    hackathon.status = new_status
    await db.flush()
    result = await db.execute(
        select(Hackathon).options(selectinload(Hackathon.criteria)).where(Hackathon.id == hackathon_id)
    )
    return result.scalar_one()


@router.get("/{hackathon_id}/criteria", response_model=List[CriterionRead])
async def list_criteria(hackathon_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Criterion)
        .where(Criterion.hackathon_id == hackathon_id)
        .order_by(Criterion.display_order)
    )
    return result.scalars().all()


@router.post("/{hackathon_id}/criteria", response_model=CriterionRead, status_code=status.HTTP_201_CREATED)
async def add_criterion(
    hackathon_id: UUID,
    data: CriterionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Hackathon).where(Hackathon.id == hackathon_id))
    hackathon = result.scalar_one_or_none()
    if not hackathon:
        raise NotFoundError("Hackathon not found")
    _assert_owner(hackathon, current_user)

    criterion = Criterion(
        hackathon_id=hackathon_id,
        name=data.name,
        description=data.description,
        weight=data.weight,
        agent_id=data.agent_id,
        display_order=data.display_order,
    )
    db.add(criterion)
    await db.flush()
    await db.refresh(criterion)
    return criterion


@router.put("/{hackathon_id}/criteria", response_model=List[CriterionRead])
async def replace_criteria(
    hackathon_id: UUID,
    data: CriterionBulkUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Replace all criteria for a hackathon (bulk update)."""
    result = await db.execute(select(Hackathon).where(Hackathon.id == hackathon_id))
    hackathon = result.scalar_one_or_none()
    if not hackathon:
        raise NotFoundError("Hackathon not found")
    _assert_owner(hackathon, current_user)

    total_weight = sum(c.weight for c in data.criteria)
    if abs(total_weight - 1.0) > 0.01:
        raise BadRequestError(f"Criterion weights must sum to 1.0 (got {total_weight:.3f})")

    # Delete existing criteria
    existing_result = await db.execute(
        select(Criterion).where(Criterion.hackathon_id == hackathon_id)
    )
    for crit in existing_result.scalars().all():
        await db.delete(crit)
    await db.flush()

    new_criteria = []
    for i, crit_data in enumerate(data.criteria):
        crit = Criterion(
            hackathon_id=hackathon_id,
            name=crit_data.name,
            description=crit_data.description,
            weight=crit_data.weight,
            agent_id=crit_data.agent_id,
            display_order=i,
        )
        db.add(crit)
        new_criteria.append(crit)

    await db.flush()
    for c in new_criteria:
        await db.refresh(c)
    return new_criteria


@router.get("/{hackathon_id}/participants")
async def list_participants(
    hackathon_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Hackathon).where(Hackathon.id == hackathon_id))
    hackathon = result.scalar_one_or_none()
    if not hackathon:
        raise NotFoundError("Hackathon not found")
    _assert_owner(hackathon, current_user)

    result = await db.execute(
        select(HackathonParticipant, User)
        .join(User, HackathonParticipant.user_id == User.id)
        .where(HackathonParticipant.hackathon_id == hackathon_id)
    )
    return [
        {
            "user_id": str(row.User.id),
            "email": row.User.email,
            "full_name": row.User.full_name,
            "joined_at": row.HackathonParticipant.joined_at.isoformat(),
        }
        for row in result.all()
    ]


@router.post("/{hackathon_id}/join", status_code=status.HTTP_201_CREATED)
async def join_hackathon(
    hackathon_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Hackathon).where(Hackathon.id == hackathon_id))
    hackathon = result.scalar_one_or_none()
    if not hackathon:
        raise NotFoundError("Hackathon not found")
    if hackathon.status != HackathonStatus.active:
        raise BadRequestError("This hackathon is not accepting participants.")

    existing = await db.execute(
        select(HackathonParticipant).where(
            HackathonParticipant.hackathon_id == hackathon_id,
            HackathonParticipant.user_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictError("You are already a participant.")

    participant = HackathonParticipant(
        hackathon_id=hackathon_id,
        user_id=current_user.id,
    )
    db.add(participant)
    await db.flush()
    return {"message": "Successfully joined hackathon", "hackathon_id": str(hackathon_id)}


@router.get("/{hackathon_id}/submissions")
async def list_hackathon_submissions(
    hackathon_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Hackathon).where(Hackathon.id == hackathon_id))
    hackathon = result.scalar_one_or_none()
    if not hackathon:
        raise NotFoundError("Hackathon not found")
    _assert_owner(hackathon, current_user)

    result = await db.execute(
        select(Submission, User)
        .join(User, Submission.user_id == User.id)
        .where(Submission.hackathon_id == hackathon_id)
        .order_by(Submission.submitted_at.desc())
    )
    return [
        {
            "submission_id": str(row.Submission.id),
            "user_id": str(row.User.id),
            "user_name": row.User.full_name,
            "repo_url": row.Submission.repo_url,
            "status": row.Submission.status.value,
            "submitted_at": row.Submission.submitted_at.isoformat(),
        }
        for row in result.all()
    ]


@router.post("/{hackathon_id}/finalize")
async def finalize_rankings(
    hackathon_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Finalize rankings — makes them visible to all participants."""
    result = await db.execute(select(Hackathon).where(Hackathon.id == hackathon_id))
    hackathon = result.scalar_one_or_none()
    if not hackathon:
        raise NotFoundError("Hackathon not found")
    _assert_owner(hackathon, current_user)

    # Check all evaluations are done
    pending_result = await db.execute(
        select(func.count(Submission.id))
        .where(
            Submission.hackathon_id == hackathon_id,
            Submission.status.in_(["pending", "cloning", "analyzing", "evaluating"]),
        )
    )
    pending_count = pending_result.scalar_one()
    if pending_count > 0:
        raise BadRequestError(f"{pending_count} submission(s) still in progress. Wait for all evaluations to complete.")

    rankings_result = await db.execute(
        select(Ranking).where(Ranking.hackathon_id == hackathon_id)
    )
    finalized_count = 0
    for ranking in rankings_result.scalars().all():
        ranking.finalized = True
        ranking.finalized_at = datetime.now(timezone.utc)
        ranking.finalized_by = current_user.id
        finalized_count += 1

    hackathon.status = HackathonStatus.finalized
    await db.flush()
    return {"message": f"Rankings finalized for {finalized_count} submissions."}
