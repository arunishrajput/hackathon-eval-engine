from arq import create_pool
from arq.connections import RedisSettings
from app.config import settings
from typing import Optional
import structlog

logger = structlog.get_logger()

_redis_pool = None


async def get_redis_pool():
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    return _redis_pool


async def enqueue(job_name: str, *args, **kwargs) -> Optional[str]:
    """Generic job enqueue helper."""
    try:
        pool = await get_redis_pool()
        job = await pool.enqueue_job(job_name, *args, **kwargs)
        return job.job_id if job else None
    except Exception as e:
        logger.error("Failed to enqueue job", job=job_name, error=str(e))
        return None


async def close_pool():
    global _redis_pool
    if _redis_pool:
        await _redis_pool.close()
        _redis_pool = None
