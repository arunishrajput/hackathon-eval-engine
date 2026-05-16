import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, Integer, Boolean, Numeric, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class Ranking(Base):
    __tablename__ = "rankings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hackathon_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("hackathons.id"), nullable=False)
    submission_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    percentile: Mapped[float | None] = mapped_column(Numeric(5, 2))
    normalized_score: Mapped[float | None] = mapped_column(Numeric(6, 3))
    finalized: Mapped[bool] = mapped_column(Boolean, default=False)
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finalized_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    computation_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    hackathon: Mapped["Hackathon"] = relationship("Hackathon", back_populates="rankings")
    submission: Mapped["Submission"] = relationship("Submission", back_populates="ranking")

    __table_args__ = (
        Index("ix_rankings_hackathon_rank", "hackathon_id", "rank"),
    )
