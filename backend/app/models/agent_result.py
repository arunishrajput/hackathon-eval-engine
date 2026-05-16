import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, Boolean, Integer, Numeric, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class AgentResult(Base):
    __tablename__ = "agent_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("evaluations.id"), nullable=False)
    agent_id: Mapped[str] = mapped_column(String(100), nullable=False)
    criterion_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("criteria.id"))
    score_raw: Mapped[float | None] = mapped_column(Numeric(6, 3))
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
    evidence: Mapped[list] = mapped_column(JSONB, default=list)
    strengths: Mapped[list] = mapped_column(JSONB, default=list)
    weaknesses: Mapped[list] = mapped_column(JSONB, default=list)
    reasoning: Mapped[str | None] = mapped_column(Text)
    abstained: Mapped[bool] = mapped_column(Boolean, default=False)
    abstain_reason: Mapped[str | None] = mapped_column(Text)
    prompt_version: Mapped[str | None] = mapped_column(String(50))
    model_version: Mapped[str | None] = mapped_column(String(100))
    processing_time_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    evaluation: Mapped["Evaluation"] = relationship("Evaluation", back_populates="agent_results")
    criterion: Mapped["Criterion | None"] = relationship("Criterion", back_populates="agent_results")

    __table_args__ = (
        Index("ix_agent_results_evaluation_agent", "evaluation_id", "agent_id"),
    )
