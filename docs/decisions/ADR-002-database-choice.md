# ADR-002: Database Choice — PostgreSQL 16 + pgvector

**Status**: Accepted
**Date**: 2026-05-15

---

## Context

The EVALON evaluation engine must persist two fundamentally different categories of data simultaneously:

1. **Relational data** — users, hackathons, criteria, submissions, evaluations, agent_results, rankings, and chat sessions all have explicit foreign-key relationships and require ACID transactions. For example, creating an evaluation and updating the submission status must be atomic — a partial write would leave the system in an inconsistent state.

2. **Vector embeddings** — after each evaluation, every file in the submitted repository is chunked and embedded via the `nomic-embed-text` model, producing 768-dimensional float vectors stored for RAG retrieval by the mentor chatbot. At a maximum of 50 files × 5 chunks per file = 250 vectors per submission, the total embedding store can reach millions of rows at hackathon scale.

The naive solution is to run two separate data stores: a relational database for structured data and a dedicated vector database for embeddings. However, this introduces cross-database query complexity, two connection pool configurations, two Docker containers to operate, and two sets of backup policies.

The team evaluated whether a single data store could serve both roles without unacceptable trade-offs.

---

## Decision

**PostgreSQL 16 with the pgvector extension**, packaged as the `pgvector/pgvector:pg16` Docker image.

All relational tables and the `repo_embeddings` vector table coexist in the same database instance. The `repo_embeddings` table uses a `vector(768)` column type provided by pgvector, indexed with an HNSW index (`vector_cosine_ops`) for sub-linear approximate nearest-neighbor search.

---

## Comparison

| Criterion | PostgreSQL + pgvector | MongoDB + Atlas Vector Search | Qdrant + PostgreSQL | Chroma (SQLite-backed) |
|-----------|----------------------|-------------------------------|---------------------|------------------------|
| Relational data model | Native — full SQL, joins, FK constraints | Document-only; no FK enforcement | Vector store only; requires separate relational DB | No relational model |
| ACID transactions | Full (row-level locking, WAL) | Multi-document transactions (limited; added in 4.0) | None; CP store only | No (SQLite WAL mode only) |
| Vector similarity search | IVFFlat + HNSW via pgvector extension | Atlas Vector Search (cloud-only) | Native HNSW; best-in-class throughput | HNSW via hnswlib |
| Self-hosted / local-first | Yes — single container | Difficult; Atlas requires cloud account | Yes — separate container | Yes — embedded library |
| Number of services needed | 1 | 2 (Mongo + separate relational) | 2 (Qdrant + Postgres) | 1 (in-process, but no SQL joins) |
| Filtered KNN queries | Native SQL WHERE + ORDER BY vector | Requires pre-filtering in application | Payload filtering built-in | Application-side filtering only |
| JSONB for semi-structured fields | First-class — used for report, settings, evidence | Native document store | Not applicable | Not applicable |
| Python async client | asyncpg / SQLAlchemy 2.0 async | motor (async) | qdrant-client | httpx or chromadb client |
| License | PostgreSQL license (permissive) | SSPL (commercial use risk) | Apache 2.0 | Apache 2.0 |
| Operational complexity (Docker Compose) | Low — 1 container, 1 volume | High — Atlas cloud + local Mongo | Medium — 2 containers | Low — embedded |
| Backup strategy | pg_dump covers everything | Separate backups for two stores | Two backup procedures | SQLite file copy |
| Maximum vector dimensions | 16,000 | Unlimited | Unlimited | Unlimited |

---

## Key Insight

**pgvector eliminates the need for a fourth service.**

At project start the Docker Compose file already included postgres, redis, ollama, backend, worker, frontend, and nginx — seven containers. Adding Qdrant would be an eighth. pgvector delivers sufficient vector search performance for EVALON's access pattern (filtered KNN: `WHERE submission_id = $1 ORDER BY embedding <=> $2 LIMIT 4`) while staying inside the existing PostgreSQL container with zero additional orchestration overhead.

The filtered query pattern is particularly important: the mentor chatbot must retrieve chunks scoped to a *specific* submission, not from the entire embedding corpus. pgvector enables this with a single SQL query combining a `WHERE` predicate and a vector `ORDER BY`. Qdrant's payload filtering achieves the same result but requires an extra round-trip through its REST API and introduces a foreign-key-equivalent relationship managed entirely in application code.

---

## Consequences

### Positive

- **Single operational surface**: pg_dump backs up both relational data and vector embeddings in one command. One connection pool serves all queries.
- **ACID transactions across relation and vector writes**: when the worker inserts agent_results and repo_embeddings in the same job, both can be rolled back atomically if the job crashes mid-write.
- **Native SQL joins**: the chatbot retriever query joins `repo_embeddings` with `submissions` to enforce submission-scoped retrieval without application-level filtering.
- **JSONB flexibility**: `evaluations.report`, `hackathons.settings`, `agent_results.evidence`, and `chat_messages.retrieved_chunks` are all JSONB columns — no schema migration required when the report structure evolves.
- **Extension availability**: `uuid-ossp` and `vector` are both enabled in the migration via `CREATE EXTENSION IF NOT EXISTS`.

### Negative

- **Fixed vector dimensions**: pgvector requires the vector dimension to be declared at column creation time (`vector(768)`). Switching to a different embedding model that produces a different dimension (e.g., 1024-dim or 384-dim) requires an `ALTER TABLE` migration and re-embedding all existing data. This makes embedding model changes expensive.
- **Index must be built post-bulk-insert**: for maximum IVFFlat/HNSW performance, the index should be created after initial bulk data load. On fresh deployments the migration creates the HNSW index immediately; at large scale (>100k vectors) it may need to be rebuilt with `REINDEX`.
- **Memory pressure**: loading the pgvector HNSW index graph into shared_buffers competes with query cache. The PostgreSQL container's memory limit must account for both.
- **Not designed for hundreds-of-millions of vectors**: at the scale of a SaaS product with thousands of hackathons and millions of submissions, a dedicated vector database with sharding and quantization would outperform pgvector. This is acceptable for the current single-tenant deployment.

### Risks

- **Vector index corruption on crash**: HNSW index writes are not fully WAL-protected in all pgvector versions. A hard kill of the postgres container during an index write can corrupt the index. Mitigation: add `max_connections` headroom, monitor for index-related log messages, and include `REINDEX` in runbook procedures.
- **Storage growth**: at 768 dimensions × 4 bytes/float = 3,072 bytes per vector, 50,000 submissions × 250 chunks = 38.4 GB of raw vector data before compression. PostgreSQL TOAST compression typically reduces this by 40–60%, but disk provisioning must account for growth.
- **pgvector version pinning**: breaking changes in the pgvector extension API between major versions have occurred. The Docker image tag `pgvector/pgvector:pg16` must be pinned to a specific version in production to prevent silent upgrade issues.
