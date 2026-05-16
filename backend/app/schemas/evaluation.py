from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID
from app.models.evaluation import EvaluationStatus


class AgentResultRead(BaseModel):
    id: UUID
    agent_id: str
    criterion_id: Optional[UUID]
    score_raw: Optional[float]
    confidence: Optional[float]
    evidence: List[Any]
    strengths: List[Any]
    weaknesses: List[Any]
    reasoning: Optional[str]
    abstained: bool
    abstain_reason: Optional[str]
    processing_time_ms: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class EvaluationRead(BaseModel):
    id: UUID
    submission_id: UUID
    hackathon_id: UUID
    status: EvaluationStatus
    final_score: Optional[float]
    report: Optional[dict]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    model_versions: dict
    created_at: datetime
    agent_results: List[AgentResultRead] = []

    model_config = {"from_attributes": True}


class EvaluationTrigger(BaseModel):
    submission_id: UUID
    force_re_evaluate: bool = False
