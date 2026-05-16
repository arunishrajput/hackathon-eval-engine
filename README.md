# EVALON — Hackathon Evaluation Engine

> AI-native hackathon infrastructure: submit a GitHub repo, receive a panel-quality engineering review in under 3 minutes.

EVALON is a full-stack platform that clones, analyzes, and evaluates hackathon submissions using a multi-stage pipeline combining static analysis tools with specialized AI agents powered by local LLMs (Ollama). Every score traces to specific evidence observed in the repository — no hallucinated numbers, no generic summaries.

---

## What is EVALON?

Traditional hackathon judging is slow, inconsistent, and opaque. EVALON automates the engineering review layer while making every decision auditable. Three specialized AI agents evaluate each submission independently:

- **Repository Understanding Agent** — identifies project purpose, architecture pattern, and documentation quality
- **Code Quality Agent** — interprets radon/ESLint/Semgrep output into actionable findings grounded in real metrics
- **Innovation Agent** — evaluates problem originality, solution creativity, and technical sophistication

After evaluation, participants receive a detailed report with evidence-backed scores, a prioritized improvement list, and access to a RAG-powered mentor chatbot that answers questions about their specific code.

---

## Features

- **Automated evaluation pipeline** — clone → static analysis → AI agents → ranked report, fully hands-off
- **Explainable scores** — every criterion score links to specific file references and metrics
- **Multi-criteria hackathons** — configurable judging criteria with custom weights per hackathon
- **Real-time progress** — SSE stream shows live pipeline stages as they run
- **AI Mentor Chatbot** — RAG-powered chatbot lets participants ask questions about their evaluation
- **Admin dashboard** — manage hackathons, review all submissions, finalize rankings
- **Finalization gate** — participants cannot see rankings until admin explicitly finalizes
- **100% local** — runs entirely on Docker Compose with Ollama; no cloud API keys required

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | FastAPI (Python 3.11) | Async REST API |
| Task Queue | ARQ + Redis 7 | Background evaluation jobs |
| ORM | SQLAlchemy 2.0 async | Database access |
| Migrations | Alembic | Schema versioning |
| AI Orchestration | LangGraph 0.2 | Evaluation pipeline graph |
| LLM Runtime | Ollama | Local inference |
| Code Model | qwen2.5-coder:7b | Code understanding/review |
| Reasoning Model | qwen2.5:7b | Architecture/innovation scoring |
| Embedding Model | nomic-embed-text | RAG embeddings (768-dim) |
| Static Analysis | radon, semgrep, ESLint | Language-specific metrics |
| Database | PostgreSQL 16 + pgvector | Storage + vector search |
| Frontend | Next.js 14 (App Router) | React web application |
| Styling | Tailwind CSS | Component library |
| Charts | Recharts | Score radar chart |
| Reverse Proxy | Nginx | Routes /api → backend, / → frontend |
| Containers | Docker Compose | Full-stack orchestration |

---

## Quick Start

### Prerequisites

- Docker 24+ and Docker Compose v2
- 8 GB RAM minimum (16 GB recommended for comfortable Ollama inference)
- NVIDIA GPU optional but significantly speeds up LLM inference
- 10 GB disk space for Ollama models

### 1. Clone and configure

```bash
git clone <repo-url> evalon
cd evalon
cp .env.example .env
# Edit .env — at minimum change SECRET_KEY to a random 32-char string
```

### 2. Start all services

```bash
make up
```

The Ollama container automatically pulls the required models on first start (~5 GB download). This takes 5–15 minutes depending on your connection.

### 3. Run database migrations

```bash
make migrate
```

### 4. Seed demo data

```bash
make seed
```

### 5. Access the platform

| Service | URL |
|---------|-----|
| Frontend | http://localhost |
| API | http://localhost/api |
| API Docs (Swagger) | http://localhost/api/docs |

---

## Demo Accounts

After running `make seed`:

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@hackeval.dev | admin123 |
| Participant | participant@hackeval.dev | test123 |

---

## Suggested Demo Repositories

These small public repos produce interesting evaluation reports:

| Repository | Notes |
|-----------|-------|
| `https://github.com/tiangolo/fastapi` | Python/FastAPI — exercises radon complexity |
| `https://github.com/pallets/flask` | Classic Python web — good code quality baseline |
| `https://github.com/fastapi/typer` | CLI Python project — different project type |

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing secret (min 32 chars) | **Change this!** |
| `DATABASE_URL` | PostgreSQL async URL | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `OLLAMA_BASE_URL` | Ollama API base URL | `http://localhost:11434` |
| `OLLAMA_CODE_MODEL` | Model for code analysis | `qwen2.5-coder:7b` |
| `OLLAMA_REASONING_MODEL` | Model for reasoning | `qwen2.5:7b` |
| `OLLAMA_EMBED_MODEL` | Model for embeddings | `nomic-embed-text` |
| `OLLAMA_TIMEOUT` | LLM call timeout (seconds) | `120` |
| `MAX_REPO_SIZE_MB` | Maximum clone size | `50` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

---

## Makefile Commands

```bash
make up         # Start all services
make down       # Stop all services
make logs       # Follow all service logs
make migrate    # Run Alembic migrations
make seed       # Create demo accounts and hackathon
make test       # Run pytest suite
make shell      # Shell in the backend container
make clean      # Stop and remove all volumes
```

---

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for system diagrams and component interaction.  
See [SETUP.md](SETUP.md) for full setup and troubleshooting guide.  
See [DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md) for how to inspect jobs, agents, and pipeline failures.

---

## License

MIT License
