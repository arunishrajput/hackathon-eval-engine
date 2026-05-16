from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.hackathon import HackathonStatus


class CriterionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    weight: float = Field(gt=0, le=1)
    agent_id: Optional[str] = None
    display_order: int = 0


class CriterionRead(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    weight: float
    agent_id: Optional[str]
    display_order: int

    model_config = {"from_attributes": True}


class HackathonCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_submissions: int = Field(default=100, gt=0)
    settings: Optional[dict] = None
    criteria: Optional[List[CriterionCreate]] = None


class HackathonRead(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    admin_id: UUID
    status: HackathonStatus
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    max_submissions: int
    settings: dict
    created_at: datetime
    criteria: List[CriterionRead] = []

    model_config = {"from_attributes": True}


class HackathonUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[HackathonStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_submissions: Optional[int] = None
    settings: Optional[dict] = None


class CriterionBulkUpdate(BaseModel):
    criteria: List[CriterionCreate]
