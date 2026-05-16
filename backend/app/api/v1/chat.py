from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage, MessageRole
from app.models.submission import Submission
from app.schemas.chat import ChatSessionRead, ChatMessageCreate, ChatMessageRead
from app.core.exceptions import NotFoundError, ForbiddenError
from app.chatbot.mentor import MentorBot
from datetime import datetime, timezone

router = APIRouter()


@router.post("/sessions/{submission_id}", response_model=ChatSessionRead, status_code=status.HTTP_201_CREATED)
async def create_or_get_session(
    submission_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub_result = await db.execute(select(Submission).where(Submission.id == submission_id))
    submission = sub_result.scalar_one_or_none()
    if not submission:
        raise NotFoundError("Submission not found")
    if submission.user_id != current_user.id:
        raise ForbiddenError()

    result = await db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(ChatSession.submission_id == submission_id, ChatSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()

    if not session:
        session = ChatSession(
            user_id=current_user.id,
            submission_id=submission_id,
            hackathon_id=submission.hackathon_id,
        )
        db.add(session)
        await db.flush()
        # Re-fetch with selectinload so messages relationship is populated
        # before Pydantic serializes the response (lazy access fails in async)
        result2 = await db.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.id == session.id)
        )
        session = result2.scalar_one()

    return session


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageRead)
async def send_message(
    session_id: UUID,
    message: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession).options(selectinload(ChatSession.messages)).where(ChatSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise NotFoundError("Chat session not found")
    if session.user_id != current_user.id:
        raise ForbiddenError()

    # Save user message
    user_msg = ChatMessage(
        session_id=session_id,
        role=MessageRole.user,
        content=message.content,
    )
    db.add(user_msg)
    session.last_message_at = datetime.now(timezone.utc)

    # Get AI response
    mentor = MentorBot(db)
    response_text, retrieved_chunks = await mentor.respond(
        session=session,
        user_message=message.content,
    )

    assistant_msg = ChatMessage(
        session_id=session_id,
        role=MessageRole.assistant,
        content=response_text,
        retrieved_chunks=retrieved_chunks,
    )
    db.add(assistant_msg)
    await db.flush()
    await db.refresh(assistant_msg)
    return assistant_msg
