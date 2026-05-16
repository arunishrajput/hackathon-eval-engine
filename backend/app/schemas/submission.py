from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.submission import SubmissionStatus


class SubmissionCreate(BaseModel):
    hackathon_id: UUID
    repo_url: str = Field(min_length=1, max_length=500)


class SubmissionRead(BaseModel):
    id: UUID
    hackathon_id: UUID
    user_id: UUID
    repo_url: str
    repo_name: Optional[str]
    repo_description: Optional[str]
    status: SubmissionStatus
    error_message: Optional[str]
    submitted_at: datetime
    clone_completed_at: Optional[datetime]
    analysis_completed_at: Optional[datetime]
    evaluation_completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class SubmissionStatusUpdate(BaseModel):
    status: SubmissionStatus
    error_message: Optional[str] = None
