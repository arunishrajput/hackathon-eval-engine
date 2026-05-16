# EVALON — Research & Technology Decisions

This document provides a comprehensive comparison of the technology alternatives considered during EVALON's design. Each section presents the candidates, a structured comparison, the decision made, and the rationale behind it.

---

## 1. Backend API Framework

### Context

The backend must handle async IO-heavy workloads (database queries, Ollama HTTP calls, Redis enqueue, git clone), integrate with Python AI libraries (LangGraph, radon, httpx), generate OpenAPI documentation automatically, and stream Server-Sent Events to connected clients. The choice of framework directly constrains all of these.

### Candidates
- FastAPI (Python)
- NestJS (TypeScript/Node.js)
- Django REST Framework (Python)

### Comparison

| Criterion | FastAPI | NestJS | Django REST |
|-----------|---------|--------|-------------|
| Native async/await | Yes (first-class) | Yes (Node.js event loop) | Partial (ASGI since 3.1, not idiomatic) |
| Async database ORM | SQLAlchemy 2.0 async | TypeORM async, Prisma | django-orm (sync-first) |
| Pydantic v2 validation | Built-in | External (class-validator) | DRF serializers (verbose) |
| OpenAPI docs | Auto-generated | Manual via decorators | drf-spectacular plugin |
| Python LLM ecosystem | Best (langchain, langgraph, httpx) | Poor (JS ecosystem) | Good but slower iteration |
| Dependency injection | FastAPI Depends() | Nest DI container | Not built-in |
| SSE streaming | StreamingResponse | Built-in EventEmitter | django-eventstream plugin |
| Cold start | Very fast | Moderate (Node startup) | Slow (Django app registry) |
| Type safety | Pydantic + mypy | TypeScript native | Optional, type stubs incomplete |

### Decision
**FastAPI** with async SQLAlchemy 2.0.

### Rationale
The evaluation pipeline makes heavily concurrent IO calls — database reads, git cloning, Ollama HTTP requests, Redis enqueue. FastAPI's async-first design means these all run on the same event loop without thread overhead. Pydantic v2 provides both request validation and settings management (`pydantic-settings`) in one dependency. The entire Python AI ecosystem (LangGraph, httpx, radon) integrates without impedance mismatch. NestJS was ruled out because the LLM tooling in JavaScript is immature compared to Python, and the team already writes Python. Django was ruled out because its ORM is synchronous by design and retrofitting async is fragile.

---

## 2. Storage: Database and Vector Index

### Context

EVALON needs to store highly relational data (users → hackathons → criteria → submissions → evaluations → agent results → rankings) with ACID transaction guarantees, plus 768-dimensional embedding vectors for the RAG chatbot. The storage solution must be self-hosted, Docker-native, and support both relational queries and vector similarity search without requiring multiple database services.

### Candidates
- PostgreSQL 16 + pgvector extension
- MongoDB Atlas (with Vector Search)
- Qdrant (dedicated vector database) + PostgreSQL
- Supabase (managed PostgreSQL + pgvector)

### Comparison

| Criterion | PostgreSQL + pgvector | MongoDB + Vector Search | Qdrant + Postgres | Supabase |
|-----------|----------------------|------------------------|-------------------|----------|
| Relational data model | Native | Document-only | Requires separate DB | Native |
| ACID transactions | Full | Multi-doc (limited) | No (vector store only) | Full |
| Vector similarity search | pgvector extension | Atlas Vector Search | Native, best-in-class | pgvector |
| Self-hosted | Yes | Difficult (Atlas cloud) | Yes | Managed only |
| Single service | Yes | No (separate vector) | No (two databases) | Yes (managed) |
| Python async client | asyncpg / SQLAlchemy | motor | qdrant-client | httpx |
| License | PostgreSQL (permissive) | SSPL (commercial risk) | Apache 2.0 | Apache 2.0 |
| JSONB for semi-structured data | First-class | Native | N/A | First-class |
| Operational complexity | Low (single container) | High | High (two containers) | Medium (vendor lock-in) |

### Decision
**PostgreSQL 16 + pgvector** in a single `pgvector/pgvector:pg16` container.

### Rationale
The evaluation data model is highly relational — users, hackathons, criteria, submissions, evaluations, agent_results, and rankings all have foreign key relationships and need ACID transactions (e.g., creating an evaluation and updating submission status atomically). Adding a separate vector database (Qdrant) would mean managing two stateful services and writing cross-database transaction logic. pgvector provides cosine similarity search over the 768-dim `nomic-embed-text` embeddings with acceptable performance for the scale (under 250 vectors per submission). MongoDB was eliminated due to its SSPL license and the need for a separate relational store. Supabase was ruled out because it requires a network connection to Supabase's cloud infrastructure, violating the local-first requirement.

---

## 3. Background Job Queue

### Context

Evaluation jobs run for 2–10 minutes and involve multiple async IO operations (Ollama calls, database writes, git clone). The job queue must support asyncio-native task execution, per-job timeout enforcement, job retry on failure, and isolation from the API server process so a long-running job does not block API responses.

### Candidates
- ARQ (async Redis queue for Python)
- Celery + Redis (or RabbitMQ)
- RQ (Redis Queue)
- FastAPI BackgroundTasks

### Comparison

| Criterion | ARQ | Celery | RQ | FastAPI BackgroundTasks |
|-----------|-----|--------|-----|------------------------|
| Async (asyncio-native) | Yes | Partial (celery[gevent]) | No (threads) | Yes |
| Worker concurrency model | asyncio coroutines | Prefork/gevent/threads | Forked processes | Tied to API process |
| Job timeout control | Yes (per-job) | Yes | Yes | No |
| Result storage | Redis (configurable TTL) | Redis/DB | Redis | None |
| Job retry logic | Built-in | Built-in | Built-in | None |
| Cron scheduling | Built-in | celery-beat | rq-scheduler | No |
| Monitoring UI | None built-in (use ARQ inspect) | Flower | RQ Dashboard | No |
| Dependencies | arq, redis | celery, kombu, redis/amqp | rq, redis | None |
| Configuration complexity | Low | High | Low | None |
| Isolation from API | Yes (separate process) | Yes | Yes | No (same process) |

### Decision
**ARQ** with Redis.

### Rationale
The evaluation job is an asyncio-heavy workload — it awaits Ollama HTTP calls, asyncpg database queries, and async git operations. Celery's default prefork worker model would require running a synchronous executor with `loop.run_until_complete()` inside each Celery task, adding complexity. ARQ runs tasks as native coroutines in an asyncio event loop, meaning all the async SQLAlchemy and httpx calls work naturally. ARQ also has a simpler configuration surface: `WorkerSettings` is a single class with five attributes. Celery's maturity and monitoring ecosystem (Flower) are real advantages, but the operational overhead is not justified at this scale. `FastAPI BackgroundTasks` was eliminated because it runs in the same process as the API server — a 10-minute evaluation job would block API thread capacity and crash the server on restart.

---

## 4. AI Orchestration Framework

### Context

The evaluation pipeline is a deterministic, sequential workflow: clone repository → analyze files → run AI agents → aggregate scores. The orchestration framework must support conditional routing (skip downstream nodes on failure), typed state propagation between nodes, and async execution throughout. It must not introduce autonomy or non-determinism into the scoring pipeline.

### Candidates
- LangGraph (StateGraph)
- CrewAI
- Custom sequential Python pipeline
- AutoGen (Microsoft)
- Raw LangChain LCEL

### Comparison

| Criterion | LangGraph | CrewAI | Custom pipeline | AutoGen | LangChain LCEL |
|-----------|-----------|--------|----------------|---------|----------------|
| Explicit state management | Yes (TypedDict) | No (agent-driven) | Manual | No | Partial |
| Deterministic execution | Yes (graph edges) | No (agents decide) | Yes | No | Partial |
| Conditional routing | Yes (add_conditional_edges) | No | Manual if/else | No | No |
| Fail-fast error handling | Yes | Limited | Manual | Limited | No |
| Debugging visibility | StateGraph.compile() + trace | Limited | Full control | Limited | Limited |
| Async support | Yes | Yes | Yes | Yes | Yes |
| Overhead / complexity | Low-medium | Medium | None | High | Medium |
| Best for | Deterministic pipelines | Multi-agent autonomy | Simple sequences | Conversational agents | Chain composition |

### Decision
**LangGraph** with a four-node `StateGraph`.

### Rationale
EVALON's evaluation pipeline is inherently a sequential, deterministic workflow — not an autonomous multi-agent system. The execution order is always `clone → analyze → evaluate → score`; there is no need for agents to decide what to do next. LangGraph's `StateGraph` maps perfectly to this: each stage is a node, transitions are explicit edges, and the `should_continue` conditional router implements fail-fast semantics cleanly. CrewAI and AutoGen are designed for scenarios where agents autonomously plan and delegate work — that autonomy would introduce non-determinism into a domain (scoring) where reproducibility matters. A custom pipeline was prototyped first but LangGraph adds value through its typed state propagation and conditional edge API, which would have required re-implementing manually. Raw LCEL lacks the conditional routing primitive needed for fail-fast behavior without nesting complex chain logic.

---

## 5. Local LLM Inference

### Context

The project must run fully locally with no external API keys (privacy, cost, and offline-demo constraints). The LLM runtime must support both text generation (for evaluation agents) and embedding generation (for the RAG chatbot), be deployable as a Docker container, and work on both CPU (development) and GPU (production) hardware without configuration changes.

### Candidates
- Ollama
- vLLM
- llama.cpp (direct)
- API-only (OpenAI / Anthropic)
- LocalAI

### Comparison

| Criterion | Ollama | vLLM | llama.cpp | API-only | LocalAI |
|-----------|--------|------|-----------|----------|---------|
| CPU support | Yes | Limited (GPU-first) | Yes | N/A | Yes |
| GPU acceleration | Yes (CUDA, Metal) | Yes (CUDA) | Yes | N/A | Yes |
| Docker deployment | Yes (official image) | Yes | Manual | N/A | Yes |
| REST API | Yes (/api/generate, /api/embeddings) | OpenAI-compatible | No | Yes | OpenAI-compatible |
| Model library | Large (ollama.com) | HuggingFace models | GGUF models | Vendor-locked | HuggingFace |
| Embedding support | Yes (nomic-embed-text etc.) | Limited | No | Yes | Yes |
| No API keys required | Yes | Yes | Yes | No | Yes |
| Operational complexity | Very low | High | High | None | Medium |
| Concurrent requests | Limited (single model loaded) | High (batching, paged attention) | None | High | Medium |

### Decision
**Ollama** with `qwen2.5-coder:7b`, `qwen2.5:7b`, and `nomic-embed-text`.

### Rationale
Ollama is the only option that satisfies all three requirements simultaneously: local inference (no API keys), Docker-native deployment, and embedding support in the same server. vLLM offers higher throughput via paged attention but requires a GPU and is significantly more complex to configure — it is the right choice for a production SaaS deployment but overkill for a hackathon demo environment where submissions arrive sporadically. API-only providers (OpenAI, Anthropic) were ruled out by the local-first requirement. llama.cpp does not expose an HTTP API natively, requiring a wrapper. The `qwen2.5-coder:7b` model was selected for code analysis because it was trained on code-heavy corpora and benchmarks well on code completion tasks at the 7B scale. `nomic-embed-text` was selected for embeddings because it produces 768-dimensional vectors with strong performance on retrieval tasks while being small enough to load alongside the larger models.

---

## 6. Vector Storage Strategy

### Context

The RAG mentor chatbot requires cosine similarity search over repository chunk embeddings, filtered by submission ID. The vector storage solution must integrate naturally with the existing PostgreSQL database, support filtered KNN queries (similarity search within a single submission's chunks), and not require a fourth infrastructure service in Docker Compose.

### Candidates
- pgvector (in-process with PostgreSQL)
- Qdrant (dedicated vector database)
- Chroma (in-process, SQLite-backed)
- Weaviate

### Comparison

| Criterion | pgvector | Qdrant | Chroma | Weaviate |
|-----------|----------|--------|--------|---------|
| Embedding dimensions | Up to 16,000 | Unlimited | Unlimited | Unlimited |
| Index types | IVFFlat, HNSW | HNSW | HNSW | HNSW |
| SQL joins with relational data | Native | No | No | No |
| Self-hosted Docker | Yes (bundled with PG) | Yes | Yes | Yes |
| Python async client | asyncpg / SQLAlchemy | qdrant-client | httpx | weaviate-client |
| Scale (vectors per collection) | Millions (with HNSW) | Hundreds of millions | Millions | Millions |
| Metadata filtering | PostgreSQL WHERE | Native | Native | Native |
| Operational overhead | None (shares PG) | One extra container | One extra container | One extra container |
| Concurrent writes | Full (PostgreSQL MVCC) | Yes | Limited (SQLite) | Yes |

### Decision
**pgvector** (co-located with PostgreSQL).

### Rationale
For EVALON's scale (maximum 250 vectors per submission, tens of thousands of submissions total), pgvector with an HNSW index is more than sufficient. The critical advantage over dedicated vector databases is that similarity search can be combined with SQL filtering in a single query — for example, `WHERE submission_id = $1 ORDER BY embedding <=> $2 LIMIT 4` filters by submission before doing vector search, which is exactly what the mentor chatbot requires. Running a separate Qdrant container would require writing cross-database queries or loading all submission embeddings into Qdrant's client-side filtering, both of which are less efficient than a native PostgreSQL filtered KNN query. Chroma was evaluated and works locally but uses SQLite under the hood, which does not support concurrent writes from multiple workers. Weaviate is a strong choice for production vector-heavy workloads but adds operational complexity inappropriate for a self-hosted single-node deployment.

---

## Embedding Chunk Strategy

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Code chunk size | 1,500 characters | Typically covers 1–2 function bodies; small enough for focused retrieval |
| Code chunk overlap | 200 characters | Prevents splitting across function signatures and docstrings |
| Max files per repo | 50 | Caps embedding cost to approximately 250 vectors; sufficient for RAG quality |
| Max chunks per file | 5 | Avoids over-indexing large generated files |
| README chunking | By markdown headers | Preserves semantic boundaries (sections > arbitrary character counts) |
| Vector dimensions | 768 | nomic-embed-text default; strong retrieval quality, low storage overhead |

---

## Scoring Design Rationale

### Weighted Aggregation vs. Confidence-Weighted Scoring

The current implementation uses a straightforward weighted average of agent scores with the weights normalized to sum to 1.0 after excluding abstained agents. The `confidence` field is stored in `agent_results` for every evaluation but is not currently incorporated into the weighted average.

A confidence-weighted variant was prototyped that multiplied each agent's weight by its reported confidence before normalizing. This produced slightly different rankings but introduced a new concern: LLMs consistently over-report confidence (values cluster around 0.7–0.9 regardless of actual evidence quality). Until a calibration dataset is available to validate LLM confidence reports against human expert scores, the simpler unweighted approach produces more predictable and auditable results.

### Static Analysis as LLM Grounding

A key design decision is that static analysis (radon complexity scores, ESLint error counts) is passed to the LLM agents as part of their prompt context, not used as a score directly. This grounds the LLM's reasoning in objective evidence while allowing the model to apply contextual judgment — a high cyclomatic complexity is acceptable in a game engine, less so in a utility library. This hybrid approach avoids both the brittleness of pure rule-based scoring and the hallucination risk of pure LLM scoring with no factual anchor.

The core principle: **the LLM generates no raw numbers; it only interprets tool output.** Every numeric input to the LLM prompt (total cyclomatic complexity, average maintainability index, ESLint error count, file count) is computed deterministically by a tool. The LLM's job is to explain what those numbers mean for this specific project, not to estimate them.

---

## Research Conclusions by Category

| Category | Decision | Decisive Factor | Rejected alternative |
|----------|----------|-----------------|----------------------|
| Backend framework | FastAPI | Native asyncio + Python LLM ecosystem | NestJS (JS ecosystem mismatch) |
| Database | PostgreSQL + pgvector | Single service for relational + vector; ACID | Qdrant + Postgres (two services) |
| Job queue | ARQ | Pure asyncio; no monkey-patching | Celery (eventlet breaks asyncio) |
| AI orchestration | LangGraph | Conditional edges for fail-fast routing | CrewAI (non-deterministic agent autonomy) |
| LLM runtime | Ollama | Local-first; Docker-native; embedding support | vLLM (GPU required; no embedding) |
| Vector search | pgvector | SQL-joined filtered KNN; no extra container | Qdrant (extra container; cross-DB joins) |
| Evaluation strategy | Hybrid (static + LLM) | Evidence-grounded; no hallucinated numbers | Pure LLM scoring (inconsistent; unverifiable) |

---

## Scoring Design Rationale

### Weighted Aggregation vs. Confidence-Weighted Scoring

The current implementation uses a straightforward weighted average of agent scores with the weights normalized to sum to 1.0 after excluding abstained agents. A confidence-weighted variant was prototyped that multiplied each agent's weight by its reported confidence before normalizing. This produced slightly different rankings but introduced a new concern: LLMs consistently over-report confidence (values cluster around 0.7–0.9 regardless of actual evidence quality). Until a calibration dataset is available to validate LLM confidence reports against human expert scores, the simpler unweighted approach produces more predictable and auditable results.

### Static Analysis as LLM Grounding

A key design decision is that static analysis (radon complexity scores, ESLint error counts) is passed to the LLM agents as part of their prompt context, not used as a score directly. This grounds the LLM's reasoning in objective evidence while allowing the model to apply contextual judgment — a high cyclomatic complexity is acceptable in a game engine, less so in a utility library. This hybrid approach avoids both the brittleness of pure rule-based scoring and the hallucination risk of pure LLM scoring with no factual anchor.
