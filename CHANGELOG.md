# Changelog

All notable changes to EVALON are documented in this file.

The format follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-05-16

### Added

#### Infrastructure
- Docker Compose stack with seven services: PostgreSQL 16 with pgvector extension, Redis 7 Alpine, Ollama (local LLM runtime), FastAPI backend, ARQ worker, Next.js 14 frontend, Nginx reverse proxy
- `docker-compose.dev.yml` overlay for hot-reload development mode (backend `--reload`, frontend `next dev`)
- Alembic migration `001_initial_schema.py` creating all 10 database tables with correct types, indexes, and HNSW index on `repo_embeddings.embedding vector(768)`
- PostgreSQL extensions: `uuid-ossp` (UUID primary keys) and `vector` (pgvector)
- Named Docker volumes: `postgres_data`, `redis_data`, `ollama_models`, `workspace` (shared between backend and worker)
- Nginx configuration with `proxy_buffering off` for SSE stream compatibility
- `Makefile` with targets: `up`, `down`, `logs`, `migrate`, `seed`, `test`, `shell`, `clean`, `ps`, `dev`
- `.env.example` covering all 15 environment variables with inline documentation
- Resource health checks for all containers with configurable retry intervals

#### Authentication and Authorization
- JWT access tokens (30-minute expiry) and refresh tokens (7-day expiry) using `python-jose` and `bcrypt` via `passlib`
- `POST /api/v1/auth/register` — participant account creation with bcrypt password hashing
- `POST /api/v1/auth/login` — JSON body login returning access and refresh tokens
- `POST /api/v1/auth/token` — OAuth2 form login for Swagger UI compatibility
- `POST /api/v1/auth/refresh` — exchange refresh token for new access token
- `GET /api/v1/auth/me` — authenticated user profile endpoint
- Role-based access control: `admin` and `participant` roles; `require_admin()` FastAPI dependency
- JWT extracted from `Authorization: Bearer` header via `get_current_user()` dependency

#### Hackathon Management
- Full hackathon CRUD: create, read, update, list; admin-only create/update; JSONB `settings` column
- Hackathon status enum: `draft → active → evaluating → finalized`
- Per-hackathon evaluation criteria with weights, agent_id binding, and display order
- `POST /hackathons/{id}/join` — participant join with duplicate detection (409 on duplicate)
- `POST /hackathons/{id}/criteria` — admin adds weighted criterion linked to a specific agent
- `POST /admin/hackathons/{id}/finalize` — locks rankings and publishes final results
- `show_rankings_before_finalization` settings flag controlling participant leaderboard visibility

#### Repository Ingestion Pipeline
- `clone_repository()` via GitPython with depth=1 shallow clone, configurable 120-second timeout, and 50 MB size limit
- `collect_files()` with Pygments-based language detection; binary file skip by extension whitelist; 512 KB per-file content limit
- `extract_readme()` for Markdown README content extraction
- `run_static_analysis()` — Python: radon cyclomatic complexity and maintainability index (called programmatically); JavaScript/TypeScript: ESLint JSON output via subprocess with 30-second timeout
- `build_evaluation_context()` assembling structured context dict for agent consumption
- `cleanup_repository()` removing workspace directory after evaluation

#### LangGraph Evaluation Pipeline
- Four-node `StateGraph[EvaluationState]` compiled at module load: `clone_node → analyze_node → evaluate_node → score_node`
- `EvaluationState` TypedDict propagating all inter-node data without mutable state
- `should_continue` conditional router: any node failure routes immediately to `END` without executing downstream nodes
- LangGraph conditional edges declared with named targets (`analyze`, `evaluate`, `score`, `end`)
- Module-level compiled `evaluation_graph` object reused across all worker invocations

#### AI Evaluation Agents
- `BaseAgent` abstract class with `evaluate()` wrapper: exception catching → `abstained=True` on any error; `processing_time_ms` measurement; `agent_id` and `prompt_version` stamping
- `AgentOutput` dataclass: `score` (0–10), `confidence` (0–1), `reasoning`, `evidence` (file citations), `strengths`, `weaknesses`, `abstained`, `abstain_reason`, `processing_time_ms`, `model_version`, `prompt_version`
- **RepoUnderstandingAgent** (`repo_understanding`): `qwen2.5:7b` at temperature 0.1; evaluates project structure, documentation quality, README completeness, architectural clarity
- **CodeQualityAgent** (`code_quality`): `qwen2.5-coder:7b` at temperature 0.1; interprets radon/ESLint metrics; selects 3–5 representative code samples
- **InnovationAgent** (`innovation`): `qwen2.5:7b` at temperature 0.3; evaluates problem novelty, solution creativity, theme alignment; innovation-relevant file selection via keyword scoring
- **ComparativeAgent** (`comparative`): stub implementation registered in `AGENT_REGISTRY`; returns `abstained=True`; architecture hook for v1.1
- `AGENT_REGISTRY` dict + `get_agent(agent_id, llm_provider)` factory
- Jinja2 prompt templates in `backend/app/agents/prompts/` with anti-hallucination instructions and inline JSON output schema
- `OllamaProvider` async HTTP client: `generate()` and `embed()` methods; module-level singleton via `get_llm_provider()`

#### Scoring and Ranking
- `aggregate_scores(agent_outputs, criteria)`: weighted average with abstained agent exclusion and weight renormalization; default weights fallback (code_quality 40%, repo_understanding 30%, innovation 30%); result clamped to [0.0, 10.0] and rounded to 3 decimal places
- `generate_report()`: structured JSONB report with `final_score`, `grade` (A+ through F), `agent_summaries`, `top_strengths`, `top_weaknesses`, `metadata`
- Letter grade scale: A+ (≥9.0), A (≥8.0), B+ (≥7.0), B (≥6.0), C+ (≥5.0), C (≥4.0), D (≥3.0), F (<3.0)
- `recompute_rankings()`: min-max normalized score + percentile computed for all completed evaluations per hackathon; upserts `Ranking` rows after every evaluation

#### RAG Mentor Chatbot
- `chunk_file()`: 1,500-character sliding window chunks with 200-character overlap; `chunk_readme()`: Markdown header section splitter
- `embed_repository()`: up to 50 files × 5 chunks per file embedded via `nomic-embed-text`; stored in `repo_embeddings (vector(768))`; runs post-evaluation as a non-fatal step
- `retrieve_similar_chunks()`: pgvector cosine similarity search via raw SQL `<=>` operator; submission-scoped filter; returns top-k chunks with similarity scores
- `MentorBot`: retrieves top-4 chunks, fetches evaluation report summary, builds Jinja2 mentor prompt, calls `qwen2.5:7b` at temperature 0.4; returns response and retrieved chunk citations
- Chat session management: `ChatSession` and `ChatMessage` models; history capped at 10 messages for LLM context
- Chat API: `POST /chat/sessions`, `POST /chat/sessions/{id}/messages`, `GET /chat/sessions/{id}/history`

#### REST API
- 30+ endpoints across 7 resource groups under `/api/v1/`
- `GET /api/health` — comprehensive health check for postgres, redis, and ollama
- `GET /submissions/{id}/status` — SSE stream with `progress`, `completed`, `error` events; polls every 2 seconds; `X-Accel-Buffering: no` header for Nginx compatibility
- Consistent JSON error responses via custom exception handlers (`NotFoundError`, `ForbiddenError`, `BadRequestError`, `UnauthorizedError`)
- Request logging via structlog `RequestLoggingMiddleware`
- CORS configured via `ALLOWED_ORIGINS` environment variable

#### Frontend (Next.js 14)
- App Router with TypeScript, Tailwind CSS, Radix UI primitives
- Zustand auth store with localStorage persistence
- **Participant portal**: hackathon listing, submission form with client-side URL validation, SSE-powered evaluation progress page, evaluation report viewer, leaderboard with current-user highlight, RAG mentor chat with citation display
- **Admin portal**: hackathon management, criteria weight editor with real-time sum validation, submission status table, rankings table, finalization button
- `useEvaluationStream` hook wrapping `EventSource` with stage tracking and `onComplete` callback
- `ScoreRadarChart` — Recharts radar chart with per-agent scores and reference lines at 5.0 and 7.5
- `AgentResultCard` — expandable card with score badge, confidence, reasoning, evidence, strengths/weaknesses
- `ProgressStream` — animated stage timeline (Queued → Cloning → Analyzing → Evaluating → Complete)
- `ChatInterface` — message list with retrieved chunk citations and auto-scroll
- `LeaderboardTable` — trophy icons for top 3, percentile badge column

#### ARQ Job Queue
- `run_evaluation(ctx, submission_id)` ARQ task with 9-step execution: load submission, load criteria, upsert evaluation record, invoke LangGraph graph, persist agent results, update submission status, embed repository, recompute rankings, handle all errors
- `WorkerSettings`: `max_jobs=5`, `job_timeout=600` (10 minutes), `keep_result=3600` (1 hour)
- `enqueue_evaluation()`: non-blocking enqueue; Redis unavailability is logged but does not fail the HTTP response
- Idempotent task execution: upsert on `Evaluation` record prevents duplicate rows on job retry

#### Documentation
- `README.md` — project overview, feature list, tech stack table, 5-command quick start, demo accounts, environment variable reference, Makefile commands
- `SETUP.md` — 9-step setup guide, GPU enablement instructions, complete 13-step demo walkthrough, troubleshooting quick-reference table
- `ARCHITECTURE.md` — Mermaid diagrams (system topology, pipeline sequence, RAG chatbot flow), database ER description, API surface table, design patterns section
- `RESEARCH.md` — 6 technology comparison tables covering framework, database, queue, AI orchestration, LLM runtime, and vector search decisions
- `FUTURE_SCOPE.md` — 7 detailed future feature designs with technical specifications and schema changes
- `DEBUGGING_GUIDE.md` — ARQ job inspection, agent isolation guide, database queries, common failure modes
- `CHANGELOG.md` — this file; version 1.0.0 feature inventory
- `docs/decisions/ADR-001` through `ADR-005` — Architecture Decision Records with context, decision, comparison table, key insight, and consequences
- `docs/reports/PHASE-1-REPORT.md` through `PHASE-8-REPORT.md` — phase implementation reports with deliverables, decisions, technical debt, and verification checklists

#### Test Suite
- `backend/tests/test_api/test_auth.py` — registration, login, token refresh, role enforcement
- `backend/tests/test_api/test_hackathons.py` — CRUD, criteria management, participant join/duplicate
- `backend/tests/test_pipeline/test_file_processor.py` — file collection, binary skip, language detection
- `backend/tests/test_agents/test_base.py` — 14 tests: exception → abstain, timing, agent_id stamping
- `backend/tests/test_scoring/test_aggregator.py` — 11 tests: all aggregation edge cases
- `backend/tests/test_scoring/test_normalizer.py` — normalize_score, compute_percentile, z_score_normalize
- `backend/tests/conftest.py` — async SQLite test database fixture via `aiosqlite`; `pytest.ini` with `asyncio_mode = auto`

#### Seed Script
- `backend/app/scripts/seed.py` — idempotent seed creating admin account (`admin@hackeval.dev` / `admin123`), participant account (`participant@hackeval.dev` / `test123`), "AI Hackathon 2025" hackathon with three weighted criteria
