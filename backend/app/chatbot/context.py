from typing import List, Dict, Any
from app.models.chat import ChatSession, ChatMessage


def build_chat_history(session: ChatSession, max_messages: int = 10) -> str:
    """Format recent chat history for the LLM context window."""
    messages = session.messages[-max_messages:] if session.messages else []
    history_lines = []
    for msg in messages:
        role = "User" if msg.role.value == "user" else "Assistant"
        history_lines.append(f"{role}: {msg.content}")
    return "\n".join(history_lines)


def build_mentor_prompt(
    user_question: str,
    chat_history: str,
    retrieved_chunks: List[Dict[str, Any]],
    evaluation_summary: str = "",
) -> str:
    """Construct the full prompt for the mentor chatbot."""
    context_text = "\n\n".join([
        f"[{chunk['chunk_type'].upper()} - {chunk.get('metadata', {}).get('file_path', 'unknown')}]\n{chunk['content'][:400]}"
        for chunk in retrieved_chunks
    ])

    return f"""You are a helpful hackathon mentor. You have access to the participant's code repository and evaluation results.
Be encouraging, specific, and actionable in your feedback.

## Evaluation Summary
{evaluation_summary or "Evaluation pending or not available."}

## Relevant Code Context
{context_text or "No relevant code found."}

## Conversation History
{chat_history or "No previous messages."}

## Participant Question
{user_question}

## Your Response
Provide specific, constructive guidance referencing the actual code when possible."""
