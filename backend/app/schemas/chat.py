from pydantic import BaseModel, Field
from typing import List, Any, Optional
from datetime import datetime
from uuid import UUID
from app.models.chat import MessageRole


class ChatMessageRead(BaseModel):
    id: UUID
    role: MessageRole
    content: str
    retrieved_chunks: List[Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionRead(BaseModel):
    id: UUID
    user_id: UUID
    submission_id: UUID
    hackathon_id: UUID
    created_at: datetime
    last_message_at: Optional[datetime] = None
    messages: List[ChatMessageRead] = []

    model_config = {"from_attributes": True}


class ChatMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
