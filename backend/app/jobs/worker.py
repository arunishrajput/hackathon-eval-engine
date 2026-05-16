from arq.connections import RedisSettings
from app.config import settings
from app.jobs.tasks import run_evaluation


class WorkerSettings:
    """arq worker configuration."""
    functions = [run_evaluation]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 5
    job_timeout = 600  # 10 minutes max per job
    keep_result = 3600  # Keep results for 1 hour
    queue_name = "arq:queue"
    on_startup = None
    on_shutdown = None
