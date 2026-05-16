# ADR-004: Background Job Queue — ARQ (Async Redis Queue)

**Status**: Accepted
**Date**: 2026-05-15

---

## Context

A complete evaluation job — clone repository, run static analysis, invoke three AI agents sequentially, aggregate scores, embed repository files, recompute rankings — takes between 2 and 10 minutes depending on repository size and hardware. On CPU inference with Ollama, a single agent call takes 60–120 seconds; on GPU inference it takes under 10 seconds per call.

The `POST /api/v1/submissions` endpoint must return an HTTP response in under a second. It cannot block the HTTP server thread or the event loop while waiting for Ollama to respond. Evaluation must run entirely outside the API process.

The team needed a background task queue that satisfies the following requirements:

1. **Async-native**: The evaluation task is written with `async def` and makes `await` calls to asyncpg, httpx (Ollama), and asyncio subprocess (static analysis). The queue worker must run these coroutines natively — not in a synchronous executor with `loop.run_until_complete()`.
2. **Redis-backed**: Redis is already in the stack as a session cache and health-check target. Adding a second message broker (RabbitMQ, SQS) would require another Docker container.
3. **Job persistence**: If the ARQ worker container crashes mid-evaluation, the job must not be lost. Redis AOF persistence ensures enqueued jobs survive container restarts.
4. **Per-job timeout**: An agent that hangs (e.g., Ollama running out of memory mid-inference) must not block the worker indefinitely. The queue must support per-job maximum duration enforcement.
5. **Operational simplicity**: The team is small; adding Celery's configuration surface (broker URL, result backend, concurrency model, Flower monitoring) is not justified at this scale.

---

## Decision

**ARQ (Async Redis Queue) 0.25**, backed by **Redis 7**.

The ARQ `WorkerSettings` class is defined in `backend/app/jobs/worker.py`. The worker is started as a separate Docker container via the command `python -m arq app.jobs.worker.WorkerSettings`. Job enqueueing from the API uses `arq.create_pool().enqueue_job("run_evaluation", submission_id)`. The queue name is `arq:queue`.

Worker settings:

```python
class WorkerSettings:
    functions = [run_evaluation]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 5            # Maximum 5 concurrent evaluation jobs
    job_timeout = 600       # 10 minutes maximum per job
    keep_result = 3600      # Retain result for 1 hour for debugging
    queue_name = "arq:queue"
```

---

## Comparison

| Criterion | ARQ 0.25 | Celery 5 + Redis | RQ (Redis Queue) | FastAPI BackgroundTasks |
|-----------|----------|-----------------|-------------------|------------------------|
| Async (asyncio-native) | Yes — tasks are `async def` coroutines | Partial — requires `celery[gevent]` or `celery[eventlet]` monkey-patching | No — tasks run in forked processes (sync only) | Yes — but tied to API process lifetime |
| Worker concurrency model | asyncio event loop — multiple coroutines on one thread | Prefork (default), gevent, or eventlet — all require sync-to-async bridges | Forked OS processes — one task per process | Runs inside uvicorn worker; shares event loop |
| Job persistence on worker crash | Yes — Redis AOF; job remains in queue | Yes | Yes | No — lost if the API process restarts |
| Per-job timeout | Yes — `job_timeout` per job | Yes — `time_limit` per task | Yes — `job_timeout` | No |
| Result storage | Redis (configurable TTL via `keep_result`) | Redis or database backend | Redis | None |
| Job retry on failure | Yes — configurable `max_tries` | Yes — built-in retry policies | Yes | No |
| Cron/scheduled jobs | Yes — `cron` class in WorkerSettings | Yes — celery-beat | Yes — rq-scheduler (separate process) | No |
| Monitoring UI | None built-in (use `arq inspect` CLI or Redis CLI) | Flower (excellent) | RQ Dashboard | No |
| Dependencies | `arq`, `redis` | `celery`, `kombu`, `redis` or `amqp`, optionally `flower` | `rq`, `redis` | None (built into FastAPI) |
| Configuration complexity | Very low — single `WorkerSettings` class | High — broker URL, result backend, concurrency, beat schedule | Low | None |
| asyncio compatibility | First-class | Requires monkey-patching (eventlet/gevent break asyncio) | Incompatible | First-class |
| SQLAlchemy async compatibility | Yes — `async with AsyncSessionLocal()` works directly | Requires workaround (`asyncio.run()` in task) | No | Yes |
| Ecosystem maturity | Young (active development, <5 years) | Very mature (>10 years, large ecosystem) | Mature | N/A |

---

## Key Insight

**ARQ is pure async Python — no eventlet or gevent monkey-patching is needed.**

Celery's default worker model uses `os.fork()` to spawn synchronous subprocess workers. Running async database calls (`await db.execute(...)`) and async HTTP calls (`await httpx_client.post(...)`) inside a Celery task requires either:
- Calling `asyncio.run()` inside each task (creates a new event loop per task, destroying connection pool reuse), or
- Enabling `gevent` or `eventlet` monkey-patching, which intercepts standard library socket calls to make them non-blocking — but this **breaks asyncio's own event loop** and is incompatible with asyncpg and the async SQLAlchemy session.

This makes Celery a poor fit for an async-heavy evaluation pipeline. ARQ was written specifically to solve this problem: tasks are `async def`, workers run an asyncio event loop, and all async libraries (asyncpg, httpx, asyncio.create_subprocess_exec) work as written.

RQ was eliminated immediately because it does not support async tasks at all.

FastAPI `BackgroundTasks` was prototyped as the simplest possible approach but rejected because it runs in the same OS process as the API server. A 10-minute evaluation job would hold a uvicorn worker thread, degrading API latency for all concurrent users. More critically, if the container restarts (OOM kill, deploy, crash), any in-progress background task is lost with no recovery path.

---

## Consequences

### Positive

- **Async-native evaluation task**: the `run_evaluation` ARQ task is a standard `async def` function. All `await` calls to the database, Ollama, and asyncio subprocess work without any bridging code.
- **Single broker for everything**: Redis serves as the ARQ queue broker, the job result store, and the platform health-check target. No second message broker is required.
- **Clean separation of concerns**: the API server enqueues jobs; the worker container executes them. A crash in either container does not affect the other.
- **Idempotent task design**: the `run_evaluation` task performs an upsert on the `Evaluation` row before executing the graph. If the job is retried after a crash (e.g., the worker container OOM-killed), the existing evaluation is updated rather than duplicating it.
- **Simple observable state**: because submissions track their own `status` enum (`pending → cloning → analyzing → evaluating → completed / failed`), the API can poll submission status from PostgreSQL for SSE without needing to query the ARQ job directly.

### Negative

- **Less ecosystem maturity than Celery**: ARQ has no equivalent to Flower's web UI, Celery's task routing, rate limiting primitives, or canvas workflows. Debugging requires `arq inspect` CLI commands or direct Redis key inspection.
- **No built-in deduplication**: if `POST /api/v1/submissions` is called twice for the same submission (e.g., due to a client retry), two `run_evaluation` jobs are enqueued. The idempotent upsert in the task prevents duplicate `Evaluation` rows, but the second job wastes compute. A submission-level lock (via Redis SETNX) would prevent this but adds complexity.
- **Worker must be a separate process**: unlike FastAPI `BackgroundTasks`, ARQ requires an explicitly started worker. Forgetting to start the worker container leaves submissions stuck at `pending`.
- **Redis as a single point of failure**: if Redis is unavailable, new submissions cannot be enqueued (the `enqueue_evaluation` function catches this and logs an error without raising, so the HTTP response still succeeds, but the evaluation job is silently lost). For production, Redis Sentinel or Redis Cluster is required.

### Risks

- **Job loss on Redis data loss**: ARQ uses Redis as both queue and result store. If Redis persistence is disabled (AOF/RDB not configured) and the Redis container is restarted, all queued jobs are lost. Mitigation: configure Redis with `appendonly yes` in production.
- **ARQ version stability**: ARQ 0.25 is the latest stable release as of the project start. The library is actively maintained but has changed the `WorkerSettings` interface between minor versions. Pinning to `arq==0.25.0` is intentional; upgrades require reviewing the changelog.
