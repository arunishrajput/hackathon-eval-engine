import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, Enum, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import enum


class SubmissionStatus(str, enum.Enum):
    pending = "pending"
    cloning = "cloning"
    analyzing = "analyzing"
    evaluating = "evaluating"
    completed = "completed"
    failed = "failed"


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hackathon_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("hackathons.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    repo_url: Mapped[str] = mapped_column(String(500), nullable=False)
    repo_name: Mapped[str | None] = mapped_column(String(255))
    repo_description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[SubmissionStatus] = mapped_column(Enum(SubmissionStatus), default=SubmissionStatus.pending)
    error_message: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    clone_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    analysis_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evaluation_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    hackathon: Mapped["Hackathon"] = relationship("Hackathon", back_populates="submissions")
    user: Mapped["User"] = relationship("User", back_populates="submissions")
    evaluation: Mapped["Evaluation | None"] = relationship("Evaluation", back_populates="submission", uselist=False)
    ranking: Mapped["Ranking | None"] = relationship("Ranking", back_populates="submission", uselist=False)
    chat_sessions: Mapped[list["ChatSession"]] = relationship("ChatSession", back_populates="submission")
    embeddings: Mapped[list["RepoEmbedding"]] = relationship("RepoEmbedding", back_populates="submission")

    __table_args__ = (
        Index("ix_submissions_hackathon_status", "hackathon_id", "status"),
    )
