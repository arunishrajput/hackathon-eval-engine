from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class RankingRead(BaseModel):
    id: UUID
    hackathon_id: UUID
    submission_id: UUID
    rank: int
    percentile: Optional[float]
    normalized_score: Optional[float]
    finalized: bool
    finalized_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class LeaderboardEntry(BaseModel):
    rank: int
    submission_id: UUID
    user_full_name: Optional[str]
    repo_name: Optional[str]
    final_score: Optional[float]
    normalized_score: Optional[float]
    percentile: Optional[float]


class LeaderboardResponse(BaseModel):
    hackathon_id: UUID
    total_submissions: int
    finalized: bool
    entries: List[LeaderboardEntry]
