from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.models.repo_embedding import RepoEmbedding
from app.agents.llm_provider import get_llm_provider
import structlog

logger = structlog.get_logger()


async def retrieve_similar_chunks(
    db: AsyncSession,
    submission_id: str,
    query: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """Retrieve the top-k most similar chunks using cosine similarity."""
    llm = get_llm_provider()
    query_embedding = await llm.embed(query)

    # pgvector cosine similarity query
    result = await db.execute(
        text("""
            SELECT id, chunk_type, chunk_content, metadata,
                   1 - (embedding <=> :query_embedding::vector) AS similarity
            FROM repo_embeddings
            WHERE submission_id = :submission_id
            ORDER BY embedding <=> :query_embedding::vector
            LIMIT :top_k
        """),
        {
            "query_embedding": query_embedding,
            "submission_id": str(submission_id),
            "top_k": top_k,
        }
    )

    rows = result.fetchall()
    return [
        {
            "id": str(row.id),
            "chunk_type": row.chunk_type,
            "content": row.chunk_content,
            "metadata": row.metadata,
            "similarity": float(row.similarity),
        }
        for row in rows
    ]
