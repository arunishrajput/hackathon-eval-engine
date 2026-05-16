from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.repo_embedding import RepoEmbedding
from app.agents.llm_provider import get_llm_provider
from app.embedding.chunker import chunk_file, chunk_readme
from app.pipeline.file_processor import extract_readme
import structlog

logger = structlog.get_logger()


async def embed_repository(
    db: AsyncSession,
    submission_id: str,
    files: List[Dict[str, Any]],
) -> int:
    """Generate and store embeddings for all repository chunks."""
    llm = get_llm_provider()
    total_embedded = 0

    # Chunk README
    readme = extract_readme(files)
    if readme:
        readme_chunks = chunk_readme(readme)
        for chunk in readme_chunks:
            await _embed_and_store(db, llm, submission_id, chunk)
            total_embedded += 1

    # Chunk code files (sample to avoid excessive API calls)
    code_files = [f for f in files if f.get("language") not in ("Unknown", "Text only")]
    for file_info in code_files[:50]:  # Cap at 50 files
        chunks = chunk_file(file_info)
        for chunk in chunks[:5]:  # Max 5 chunks per file
            try:
                await _embed_and_store(db, llm, submission_id, chunk)
                total_embedded += 1
            except Exception as e:
                logger.warning("Failed to embed chunk", file=file_info["path"], error=str(e))

    await db.flush()
    logger.info("Embedding complete", submission_id=submission_id, total=total_embedded)
    return total_embedded


async def _embed_and_store(
    db: AsyncSession,
    llm,
    submission_id: str,
    chunk: Dict[str, Any],
):
    embedding_vector = await llm.embed(chunk["chunk_content"])
    record = RepoEmbedding(
        submission_id=UUID(submission_id),
        chunk_type=chunk["chunk_type"],
        chunk_content=chunk["chunk_content"],
        embedding=embedding_vector,
        metadata_=chunk.get("metadata", {}),
    )
    db.add(record)
