# Phase 1 Report — Infrastructure

**Status**: Completed
**Date**: 2026-05-15
**Phase duration**: Day 1

---

## Summary

Phase 1 established the complete infrastructure foundation: Docker Compose service topology, PostgreSQL schema with pgvector, SQLAlchemy models, and Alembic migrations. By the end of Phase 1, `make up && make migrate` produced a fully initialized database with all tables, indexes, and extensions in place.

---

## What Was Built

- **`docker-compose.yml`** — defines seven services: `postgres` (pgvector/pgvector:pg16), `redis` (redis:7-alpine), `ollama` (ollama/ollama:latest), `backend` (FastAPI), `worker` (ARQ), `frontend` (Next.js), `nginx` (reverse proxy) with health checks, named volumes, and restart policies
- **`docker-compose.dev.yml`** — overlay file enabling hot-reload for backend (`--reload`) and frontend (`next dev`)
- **`Makefile`** — convenience targets: `up`, `down`, `logs`, `migrate`, `seed`, `test`, `shell`, `clean`, `ps`, `dev`
- **`.env.example`** — all environment variables with safe defaults and inline documentation
- **`backend/alembic.ini`** and **`backend/alembic/env.py`** — Alembic configuration pointing to `DATABASE_URL` from environment
- **`backend/alembic/versions/001_initial_schema.py`** — initial migration enabling `uuid-ossp` and `vector` extensions and creating 10 tables: users, hackathons, hackathon_participants, criteria, submissions, evaluations, agent_results, rankings, chat_sessions, chat_messages, and repo_embeddings
- **`backend/app/models/`** — SQLAlchemy 2.0 ORM model classes for all 10 tables using `MappedColumn` and `DeclarativeBase`
- **`backend/app/database.py`** — async engine and `AsyncSessionLocal` factory using asyncpg
- **`backend/app/config.py`** — `pydantic-settings` Settings class loading all environment variables with type validation
- **`backend/init.sql`** — database initialization SQL for extension setup
- **`nginx/nginx.conf`** — reverse proxy routing `/api/` to FastAPI on port 8000, all other paths to Next.js on port 3000; includes `proxy_buffering off` for SSE streams

---

## Key Decisions Made

- **pgvector/pgvector:pg16 Docker image** — chosen over stock postgres:16 to avoid manual extension compilation
- **HNSW index** on `repo_embeddings.embedding` — chosen over IVFFlat because HNSW provides good recall without requiring a training phase
- **UUID primary keys via `uuid_generate_v4()`** — avoids integer sequence contention under concurrent inserts from the worker
- **JSONB columns** for `evaluations.report`, `hackathons.settings`, `agent_results.evidence/strengths/weaknesses` — allows schema evolution without migrations for semi-structured data
- **`vector(768)` fixed dimension** — tied to `nomic-embed-text` output; documented as a constraint requiring migration if the embedding model changes
- **Workspace volume** — `backend` and `worker` containers share a Docker volume for cloned repositories

---

## Known Issues / Technical Debt

- The `repo_embeddings` table is created via raw SQL `op.execute()` rather than SQLAlchemy table constructs because SQLAlchemy did not support the `vector` type at writing time. **Debt**: migrate to the `pgvector` Python library's SQLAlchemy type integration when stable.
- `docker-compose.yml` does not pin image tags to specific patch versions. **Debt**: pin all service images to exact digests before production deployment.
- The Nginx config does not include TLS termination. **Debt**: add Let's Encrypt / Certbot integration for production.
- `alembic.ini` sqlalchemy.url placeholder is not used at runtime — env.py overrides it from Settings; could be confusing for new contributors.
- The `updated_at` columns use `onupdate=func.now()` at ORM level — this only fires when SQLAlchemy is the updater, not raw SQL.

---

## Verification Checklist

- [x] All 10 ORM model files created and importable
- [x] Alembic migration parses without errors
- [x] `docker compose up -d` starts all seven containers without errors
- [x] `make migrate` runs `alembic upgrade head` and exits with code 0
- [x] `docker compose exec backend alembic current` shows `001 (head)`
- [x] `curl http://localhost/api/health` returns `{"status": "healthy", ...}` with all three services healthy
- [x] PostgreSQL extensions `uuid-ossp` and `vector` confirmed present via `pg_extension` catalog
- [x] HNSW index on `repo_embeddings.embedding` confirmed via `pg_indexes`
- [x] Docker Compose YAML validates successfully
- [x] `.env.example` covers all Settings fields
