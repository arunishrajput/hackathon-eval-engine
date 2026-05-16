# ADR-001: Backend Framework Choice — FastAPI

**Status**: Accepted  
**Date**: 2026-05-15

---

## Context

The evaluation engine needs to handle several concurrent IO-heavy workloads:
- Streaming LLM responses from Ollama (multi-second calls)
- Database queries during pipeline execution
- SSE streams to multiple concurrent clients waiting for evaluation progress
- Background job dispatch to Redis

A synchronous framework would block the event loop on any of these operations, degrading throughput under concurrent load without requiring a thread-per-request model.

## Decision

**FastAPI** with async SQLAlchemy 2.0 and uvicorn.

## Rationale

| Criterion | FastAPI | Django | Flask | Litestar |
|-----------|---------|--------|-------|----------|
| Native async support | ✅ First-class | ⚠️ Via channels | ⚠️ Partial | ✅ First-class |
| Pydantic v2 integration | ✅ Built-in | ❌ Third-party | ❌ Third-party | ✅ Built-in |
| Auto OpenAPI/Swagger docs | ✅ | ❌ | ❌ | ✅ |
| Ecosystem maturity | ✅ Large | ✅ Largest | ✅ Large | ⚠️ Smaller |
| Dependency injection | ✅ Elegant | ⚠️ Signals/middleware | ❌ Manual | ✅ |
| SSE support | ✅ StreamingResponse | ⚠️ Channels required | ⚠️ Manual | ✅ |

FastAPI was chosen because:
1. It was designed for async IO from the ground up — no sync-to-async adapter needed
2. The `Depends()` injection system fits the auth middleware pattern exactly
3. Pydantic v2 is built-in for schema validation and settings loading (`pydantic-settings`)
4. `StreamingResponse` supports SSE with correct content-type without additional libraries
5. Automatic OpenAPI generation reduces API documentation burden

## Consequences

### Positive
- All database calls, LLM calls, and Redis pub/sub run non-blocking
- Dependency injection makes auth middleware clean and testable
- SwaggerUI available at `/api/docs` with zero extra configuration

### Negative
- Requires understanding of Python `async/await` patterns throughout
- SQLAlchemy async sessions require careful commit/rollback management
- Background tasks cannot be run in-process (must use ARQ) — this is by design

### Risks
- If the team adds synchronous blocking calls inside async routes, they will block the event loop and degrade performance. Code review must catch `time.sleep()`, synchronous `requests`, and synchronous file I/O inside async functions.
