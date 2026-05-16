# Project Structure

```
hackathon-eval-engine/
├── docker-compose.yml          # Production services
├── docker-compose.dev.yml      # Dev overrides (hot reload)
├── .env.example                # Environment template
├── Makefile                    # Common commands
├── nginx/nginx.conf            # Reverse proxy config
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic/                # DB migrations
│   └── app/
│       ├── main.py             # FastAPI app entry point
│       ├── config.py           # Pydantic settings
│       ├── database.py         # SQLAlchemy async engine
│       ├── dependencies.py     # FastAPI dependencies (auth)
│       ├── core/               # Security, exceptions, middleware
│       ├── models/             # SQLAlchemy ORM models
│       ├── schemas/            # Pydantic request/response schemas
│       ├── api/v1/             # FastAPI route handlers
│       ├── pipeline/           # Repo ingestion & analysis
│       ├── agents/             # LLM evaluation agents + prompts
│       ├── orchestration/      # LangGraph state machine
│       ├── scoring/            # Score aggregation & reporting
│       ├── embedding/          # pgvector chunking & retrieval
│       ├── chatbot/            # RAG mentor bot
│       ├── jobs/               # arq worker & task definitions
│       └── utils/              # File, git, logging utilities
│
└── frontend/
    └── src/
        ├── app/                # Next.js App Router pages
        │   ├── auth/           # Login, register
        │   ├── admin/          # Admin dashboard & management
        │   └── participant/    # Submission, evaluation, leaderboard
        ├── components/         # Reusable UI components
        ├── lib/                # API client, types, auth utils
        ├── store/              # Zustand state (auth)
        └── hooks/              # Custom React hooks
```
