from typing import Tuple, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.chat import ChatSession
from app.models.evaluation import Evaluation
from app.embedding.retriever import retrieve_similar_chunks
from app.chatbot.context import build_chat_history, build_mentor_prompt
from app.agents.llm_provider import get_llm_provider
from app.config import settings
import structlog

logger = structlog.get_logger()


class MentorBot:
    """RAG-powered mentor chatbot for hackathon participants."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_provider()

    async def respond(
        self,
        session: ChatSession,
        user_message: str,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Generate a mentor response and return (response_text, retrieved_chunks)."""

        # Retrieve relevant code chunks
        retrieved_chunks = await retrieve_similar_chunks(
            db=self.db,
            submission_id=str(session.submission_id),
            query=user_message,
            top_k=4,
        )

        # Get evaluation summary if available
        eval_result = await self.db.execute(
            select(Evaluation).where(Evaluation.submission_id == session.submission_id)
        )
        evaluation = eval_result.scalar_one_or_none()
        eval_summary = ""
        if evaluation and evaluation.report:
            report = evaluation.report
            eval_summary = (
                f"Final Score: {report.get('final_score', 'N/A')}/10 ({report.get('grade', '')})\n"
                f"Key Strengths: {', '.join(report.get('top_strengths', [])[:3])}\n"
                f"Areas to Improve: {', '.join(report.get('top_weaknesses', [])[:3])}"
            )

        # Build history and prompt
        chat_history = build_chat_history(session)
        prompt = build_mentor_prompt(
            user_question=user_message,
            chat_history=chat_history,
            retrieved_chunks=retrieved_chunks,
            evaluation_summary=eval_summary,
        )

        try:
            response = await self.llm.generate(
                prompt=prompt,
                model=settings.OLLAMA_REASONING_MODEL,
                temperature=0.4,
            )
        except Exception as e:
            logger.error("Mentor LLM failed", error=str(e))
            response = "I'm having trouble connecting to my reasoning engine right now. Please try again in a moment."

        return response, retrieved_chunks
