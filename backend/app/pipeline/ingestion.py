import os
import asyncio
import shutil
from pathlib import Path
from git import Repo, GitCommandError
from app.config import settings
from app.core.exceptions import IngestionError
import structlog

logger = structlog.get_logger()


async def clone_repository(repo_url: str, submission_id: str) -> Path:
    """Clone a git repository to the workspace directory."""
    dest_path = Path(settings.WORKSPACE_DIR) / submission_id

    if dest_path.exists():
        shutil.rmtree(dest_path)

    logger.info("Cloning repository", repo_url=repo_url, dest=str(dest_path))

    try:
        loop = asyncio.get_event_loop()
        await asyncio.wait_for(
            loop.run_in_executor(None, _clone_sync, repo_url, dest_path),
            timeout=settings.MAX_CLONE_TIME_SECONDS,
        )
    except asyncio.TimeoutError:
        raise IngestionError(f"Repository clone timed out after {settings.MAX_CLONE_TIME_SECONDS}s")
    except GitCommandError as e:
        raise IngestionError(f"Git clone failed: {e}")

    # Validate size
    total_size_mb = _get_dir_size_mb(dest_path)
    if total_size_mb > settings.MAX_REPO_SIZE_MB:
        shutil.rmtree(dest_path)
        raise IngestionError(f"Repository size {total_size_mb:.1f}MB exceeds limit of {settings.MAX_REPO_SIZE_MB}MB")

    return dest_path


def _clone_sync(repo_url: str, dest_path: Path):
    Repo.clone_from(repo_url, dest_path, depth=1)


def _get_dir_size_mb(path: Path) -> float:
    total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return total / (1024 * 1024)


def cleanup_repository(submission_id: str):
    dest_path = Path(settings.WORKSPACE_DIR) / submission_id
    if dest_path.exists():
        shutil.rmtree(dest_path)
        logger.info("Cleaned up repository", submission_id=submission_id)
