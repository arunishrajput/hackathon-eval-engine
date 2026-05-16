import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, Integer, Enum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base
import enum


class HackathonStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    evaluating = "evaluating"
    finalized = "finalized"


class Hackathon(Base):
    __tablename__ = "hackathons"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    admin_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status: Mapped[HackathonStatus] = mapped_column(Enum(HackathonStatus), default=HackathonStatus.draft)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    max_submissions: Mapped[int] = mapped_column(Integer, default=100)
    settings: Mapped[dict] = mapped_column(JSONB, default=lambda: {
        "allow_private_repos": False,
        "max_repo_size_mb": 50,
        "evaluation_mode": "standard",
        "show_rankings_before_finalization": False,
    })
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    admin: Mapped["User"] = relationship("User", back_populates="hackathons", foreign_keys=[admin_id])
    criteria: Mapped[list["Criterion"]] = relationship("Criterion", back_populates="hackathon", cascade="all, delete-orphan")
    submissions: Mapped[list["Submission"]] = relationship("Submission", back_populates="hackathon")
    participants: Mapped[list["HackathonParticipant"]] = relationship("HackathonParticipant", back_populates="hackathon")
    rankings: Mapped[list["Ranking"]] = relationship("Ranking", back_populates="hackathon")


class HackathonParticipant(Base):
    __tablename__ = "hackathon_participants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hackathon_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("hackathons.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    hackathon: Mapped["Hackathon"] = relationship("Hackathon", back_populates="participants")
    user: Mapped["User"] = relationship("User", back_populates="participations")
