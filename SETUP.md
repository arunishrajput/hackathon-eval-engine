# EVALON — Setup Guide

This guide walks through every step required to get EVALON running locally, including prerequisites, environment configuration, model downloads, database initialization, and the full demo walkthrough.

---

## Prerequisites

| Requirement | Minimum | Recommended |
|------------|---------|-------------|
| Docker Engine | 24.0 | latest |
| Docker Compose | v2.20 | latest |
| RAM | 8 GB | 16 GB |
| Free disk | 15 GB | 25 GB |
| CPU | 4 cores | 8 cores |
| GPU | none (CPU inference works) | NVIDIA with CUDA 12+ |

> **Note on GPU support**: Ollama will run on CPU if no GPU is detected. CPU inference is functional but slow — expect 60–120 seconds per evaluation agent call on a modern laptop. With an NVIDIA GPU, this drops to under 10 seconds per call. See the GPU section below for how to enable it.

---

## Step 1 — Clone the repository

```bash
git clone https://github.com/your-org/hackathon-eval-engine.git
cd hackathon-eval-engine
```

---

## Step 2 — Configure environment variables

```bash
cp .env.example .env
```

Open `.env` in your editor. The minimum required change before starting:

```dotenv
# REQUIRED: Change this to a random 32+ character string
SECRET_KEY=your-random-secret-key-minimum-32-characters-long
```

All other defaults work out of the box for local development. Key settings to be aware of:

```dotenv
# LLM Models — these must match what you pull into Ollama
OLLAMA_CODE_MODEL=qwen2.5-coder:7b
OLLAMA_REASONING_MODEL=qwen2.5:7b
OLLAMA_EMBED_MODEL=nomic-embed-text

# Evaluation limits
MAX_REPO_SIZE_MB=50
MAX_CLONE_TIME_SECONDS=120

# CORS — add your frontend URL if running outside Docker
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:80
```

For a full reference of every environment variable and its effect, see the [README Environment Variables table](README.md#environment-variables).

---

## Step 3 — (Optional) Enable NVIDIA GPU for Ollama

Edit `docker-compose.yml` and uncomment the GPU section in the `ollama` service:

```yaml
ollama:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all
            capabilities: [gpu]
```

You also need the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) installed on your host machine.

---

## Step 4 — Start all services

```bash
make up
```

This starts seven containers: postgres, redis, ollama, backend, worker, frontend, nginx.

On first run, Docker pulls all images (~4 GB). After that, the Ollama entrypoint script automatically downloads the three required models:
- `nomic-embed-text` (~270 MB)
- `qwen2.5:7b` (~4.4 GB)
- `qwen2.5-coder:7b` (~4.4 GB)

**Total download: approximately 9 GB.** On a 100 Mbps connection this takes 10–15 minutes.

Monitor startup progress:

```bash
docker compose logs -f ollama
```

You will see lines like:
```
pulling manifest
pulling xxxxxxxx... 100%
success
```

once all three models are downloaded and the Ollama service is healthy.

---

## Step 5 — Verify all services are healthy

```bash
make ps
```

All containers should show `healthy` in the STATUS column. If any show `starting` wait another minute and re-run.

Check the health endpoint:

```bash
curl http://localhost/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "env": "development",
  "services": {
    "postgres": "healthy",
    "redis": "healthy",
    "ollama": "healthy"
  }
}
```

---

## Step 6 — Run database migrations

```bash
make migrate
```

This runs `alembic upgrade head` inside the backend container, applying all migrations to create the full schema (users, hackathons, submissions, evaluations, agent_results, rankings, repo_embeddings, chat_sessions, chat_messages, criteria).

Verify migration ran cleanly:

```bash
docker compose exec backend alembic current
```

You should see the latest revision hash with `(head)` appended.

---

## Step 7 — Seed demo data

```bash
make seed
```

The seed script creates:
- **Admin account**: `admin@hackeval.dev` / `admin123`
- **Participant account**: `participant@hackeval.dev` / `test123`
- **Active hackathon**: "AI Hackathon 2025" (active, 7-day window)
- **Three evaluation criteria** with default weights:
  - Code Quality (40%) → `code_quality` agent
  - Innovation (35%) → `innovation` agent
  - Project Understanding (25%) → `repo_understanding` agent

The seed script is idempotent — running it twice skips if the admin account already exists.

---

## Step 8 — Verify Ollama models are present

```bash
docker compose exec ollama ollama list
```

Expected output (sizes are approximate):
```
NAME                     ID              SIZE    MODIFIED
qwen2.5-coder:7b         ...             4.7 GB  ...
qwen2.5:7b               ...             4.7 GB  ...
nomic-embed-text:latest  ...             274 MB  ...
```

If any model is missing, pull it manually:

```bash
docker compose exec ollama ollama pull qwen2.5-coder:7b
docker compose exec ollama ollama pull qwen2.5:7b
docker compose exec ollama ollama pull nomic-embed-text
```

---

## Step 9 — Access the platform

| Service | URL |
|---------|-----|
| Frontend | http://localhost |
| Swagger UI | http://localhost/api/docs |
| ReDoc | http://localhost/api/redoc |
| Health Check | http://localhost/api/health |
| Ollama API | http://localhost:11434 |

---

## Full Demo Walkthrough (13 steps)

This walkthrough exercises every major feature of the platform.

### 1. Log in as admin

Navigate to http://localhost and sign in with `admin@hackeval.dev` / `admin123`.

### 2. View the pre-seeded hackathon

From the admin dashboard, open "AI Hackathon 2025". Review the three criteria and their weights.

### 3. Create a custom hackathon (optional)

Click "New Hackathon", fill in title and description, and add at least one criterion with a weight. Set the criterion's agent to `code_quality`, `innovation`, or `repo_understanding`.

### 4. Log in as participant (in a separate browser or incognito window)

Sign in with `participant@hackeval.dev` / `test123`.

### 5. Join the hackathon

From the participant portal, find "AI Hackathon 2025" and click Join.

### 6. Submit a repository

Click "Submit Project" and enter a public GitHub URL, for example:

```
https://github.com/karpathy/micrograd
```

Click Submit. The frontend immediately shows the SSE progress stream.

### 7. Watch real-time evaluation progress

The progress bar advances through stages:
- **cloning** (10%) — repository being cloned via git with depth=1
- **analyzing** (30%) — static analysis running (radon for Python, ESLint for JS/TS)
- **evaluating** (60%) — all three AI agents running sequentially
- **scoring** (90%) — weighted score aggregation and report generation
- **completed** (100%) — evaluation persisted and rankings updated

On CPU inference this takes 3–8 minutes depending on hardware. On GPU it takes under 90 seconds.

### 8. Read the evaluation report

Once completed, click "View Report". The report shows:
- Final score (0–10)
- Per-agent scores with confidence ratings
- Strengths and weaknesses identified by each agent
- Evidence citations pointing to specific files
- Grade letter (A–F)

### 9. Open the mentor chatbot

Click "Ask Mentor" on the submission page. Ask questions like:
- "What is the most complex function in my codebase?"
- "How can I improve my test coverage?"
- "What does the Value class do?"

The chatbot retrieves relevant code chunks from the pgvector index and generates grounded answers.

### 10. Submit a second repository (as the same participant or different account)

To see the ranking system in action, submit a second repository. After evaluation completes, navigate to the Rankings tab.

### 11. View rankings as admin

Log in as admin and open the hackathon. The Rankings tab shows all submissions sorted by final score with rank positions and percentiles.

### 12. Finalize the hackathon (admin)

Once satisfied with submissions, click "Finalize Hackathon". This locks the rankings and publishes final results.

### 13. Test the health endpoint

```bash
curl http://localhost/api/health | python3 -m json.tool
```

All three services (postgres, redis, ollama) should report `"healthy"`.

---

## Creating an Additional Admin User

If you need a fresh admin account without using the seed script:

```bash
make shell
python -c "
import asyncio
from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password

async def create_admin():
    async with AsyncSessionLocal() as db:
        user = User(
            email='myadmin@example.com',
            hashed_password=hash_password('my_secure_password'),
            full_name='My Admin',
            role=UserRole.admin,
        )
        db.add(user)
        await db.commit()
        print(f'Admin created: {user.id}')

asyncio.run(create_admin())
"
```

---

## Development Mode

For hot-reload on both backend and frontend:

```bash
make dev
```

This merges `docker-compose.dev.yml` on top of the base compose file, switching the backend to `--reload --log-level debug` and the frontend to `npm run dev`.

---

## Troubleshooting

For common failure modes, log inspection commands, agent isolation testing, and database queries, see the full [DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md).

Quick reference for the most common issues:

| Symptom | First command to run |
|---------|---------------------|
| Service not starting | `docker compose logs <service-name>` |
| Migrations failing | `docker compose logs postgres` then `make migrate` |
| Evaluation stuck at pending | `docker compose exec redis redis-cli llen arq:queue` |
| Ollama models missing | `docker compose exec ollama ollama list` |
| Frontend not loading | `docker compose logs nginx` and `docker compose logs frontend` |
| Health check degraded | `curl http://localhost/api/health` to identify which service is down |

---

## Complete Troubleshooting Guide

### Problem: Ollama Models Not Pulling

**Symptom**: `docker compose logs -f ollama` shows `pulling manifest` for a long time then silently stops, or shows an error like `unexpected EOF` or `connection refused`.

**Cause 1 — Insufficient disk space**: The three required models total approximately 9 GB. Docker volumes may be on a partition with less free space than expected.

```bash
# Check Docker volume disk usage
docker system df -v

# Check host disk space
df -h
```

If disk is full, run `docker system prune` to remove unused images and volumes, then `make down && make up` to restart.

**Cause 2 — Docker Desktop memory limit too low**: Ollama requires at least 6 GB of memory to load `qwen2.5:7b`. On macOS, Docker Desktop defaults to 2 GB.

Open Docker Desktop → Settings → Resources → Memory → set to at least 8 GB → Apply & Restart.

**Cause 3 — Model pull timeout on slow connection**: The Ollama entrypoint script runs `ollama pull` synchronously. On slow connections, the pull may exceed Docker's default timeout.

```bash
# Pull models manually with no timeout
docker compose exec ollama ollama pull qwen2.5-coder:7b
docker compose exec ollama ollama pull qwen2.5:7b
docker compose exec ollama ollama pull nomic-embed-text
```

**Cause 4 — Ollama registry unreachable (corporate proxy)**: Set the `HTTPS_PROXY` variable in the `ollama` service environment in `docker-compose.yml`:

```yaml
ollama:
  environment:
    - HTTPS_PROXY=http://your-proxy:3128
```

---

### Problem: PostgreSQL Fails to Start

**Symptom**: `docker compose ps` shows the `postgres` container in `Exit 1` state or failing health check.

**Cause 1 — Port 5432 already in use**: A local PostgreSQL installation may be listening on port 5432.

```bash
# Check what's using port 5432
lsof -i :5432

# Option A: stop local postgres
sudo brew services stop postgresql@16

# Option B: change the published port in docker-compose.yml
ports:
  - "5433:5432"   # Use 5433 on the host instead
```

If you change the host port, also update `DATABASE_URL` in `.env` to `...localhost:5433/hackeval`.

**Cause 2 — Corrupted postgres data volume**: If the container was killed during initialization, the data directory may be corrupt.

```bash
# Stop all containers and remove the postgres volume
docker compose down
docker volume rm hackathon-eval-engine_postgres_data
make up && make migrate
```

**Warning**: This deletes all database data.

**Cause 3 — Wrong password**: If you previously ran with a different `POSTGRES_PASSWORD` in `.env`, the existing volume has the old password. Remove the volume and restart.

---

### Problem: ESLint Not Found During Evaluation

**Symptom**: Worker logs show `ESLint failed: [Errno 2] No such file or directory: 'eslint'` and JavaScript/TypeScript repositories show empty linting results.

**Cause**: The `eslint` binary is not on the PATH inside the worker container.

**Check if ESLint is installed in the container:**

```bash
docker compose exec worker which eslint
docker compose exec worker eslint --version
```

**Fix — Rebuild the backend image:**

```bash
docker compose build backend worker
docker compose up -d worker
```

The `Dockerfile` installs ESLint globally via `npm install -g eslint`. If the build was cached from before this line was added, the old layer will be used.

**Fix — Install in the running container (temporary):**

```bash
docker compose exec worker npm install -g eslint
```

This is not persistent across container restarts. Rebuild the image for a permanent fix.

**Workaround if you don't need JS/TS linting:**

The evaluation pipeline is resilient to missing tools — if ESLint fails, `results["linting"]` in the static analysis output is empty, and the `CodeQualityAgent` will note the absence of linting data in its reasoning. Python repositories using only `radon` are unaffected.

---

### Problem: Evaluation Stuck at `evaluating` Stage

**Symptom**: The SSE stream shows `stage: "evaluating"` for more than 5 minutes without advancing.

**Cause 1 — Ollama running out of memory**: On low-memory systems, Ollama may be swapping, causing extreme slowness.

```bash
# Check Ollama memory usage
docker stats ollama

# Check if Ollama is still responding
curl http://localhost:11434/api/version
```

If Ollama is unresponsive, restart it:
```bash
docker compose restart ollama
```

The ARQ job timeout is 600 seconds (10 minutes). If the job times out, the submission will be marked `failed`.

**Cause 2 — LLM producing non-JSON output**: If the model returns malformed JSON, the agent sets `abstained=True` and continues. But if the model hangs and never returns, the agent will time out after `OLLAMA_TIMEOUT` seconds (default 120).

```bash
# Watch worker logs during evaluation
docker compose logs -f worker
```

Look for lines like `"Ollama generate failed"` or `"Agent error"`.

**Cause 3 — Worker died mid-evaluation**: If the worker container crashed, the submission stays at `evaluating`.

```bash
docker compose ps worker
docker compose logs worker --tail 50
```

If the worker is not running, start it:
```bash
docker compose up -d worker
```

The ARQ job is not automatically retried (no `max_tries` configured). To manually retry, use the admin endpoint or delete the failed evaluation record from the database and re-submit.

---

### Problem: Frontend Shows Blank Page or 502 Error

**Symptom**: Navigating to `http://localhost` shows a blank page, or Nginx returns 502 Bad Gateway.

**Cause 1 — Next.js build still in progress on first start**: Next.js compilation on first container start takes 30–60 seconds.

```bash
docker compose logs -f frontend
```

Wait for the message `✓ Ready in X.Xms` before refreshing the browser.

**Cause 2 — Nginx cannot reach the frontend container**: Check that both containers are on the same Docker network.

```bash
docker compose exec nginx wget -O- http://frontend:3000 2>&1 | head -5
```

If this fails, the frontend container may not be running: `docker compose up -d frontend`.

**Cause 3 — CORS rejecting requests**: If accessing the frontend from a non-localhost origin, add the origin to `ALLOWED_ORIGINS` in `.env`:

```dotenv
ALLOWED_ORIGINS=http://localhost,http://192.168.1.100
```

Then restart the backend: `docker compose restart backend`.

---

## GPU Setup Instructions (NVIDIA Docker Runtime)

EVALON runs on CPU by default. GPU inference with Ollama is approximately 10–15x faster for 7B parameter models.

### Prerequisites

1. **NVIDIA GPU** with CUDA compute capability 6.0+ (Pascal or newer)
2. **NVIDIA driver** version 525+ (`nvidia-smi` should show CUDA 12.x)
3. **NVIDIA Container Toolkit** installed on the Docker host

### Step 1 — Install NVIDIA Container Toolkit (Linux)

```bash
# Add NVIDIA package repository
distribution=$(. /etc/os-release; echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Install
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit

# Restart Docker daemon
sudo systemctl restart docker
```

Verify: `docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu20.04 nvidia-smi`

### Step 2 — Enable GPU in docker-compose.yml

Open `docker-compose.yml` and uncomment the GPU section in the `ollama` service:

```yaml
ollama:
  image: ollama/ollama:latest
  volumes:
    - ollama_models:/root/.ollama
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all
            capabilities: [gpu]
```

### Step 3 — Restart the Ollama service

```bash
docker compose up -d ollama
```

### Step 4 — Verify GPU is in use

```bash
docker compose exec ollama ollama run qwen2.5:7b "Hello"
```

While this runs, in another terminal:
```bash
nvidia-smi
```

You should see `ollama` appearing in the GPU process list with non-zero memory usage.

### macOS (Apple Silicon)

Ollama on macOS automatically uses the Metal GPU backend. No additional configuration is needed — the Docker Mac VM has access to the host GPU via the Ollama Mac native binary. If running Ollama outside Docker on macOS, install it natively for best GPU performance:

```bash
brew install ollama
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

Then set `OLLAMA_BASE_URL=http://host.docker.internal:11434` in `.env` to point the containers at your native Ollama instance.

---

## How to Add a Custom Evaluator Agent

This section is a developer guide for adding a new evaluation agent to the pipeline.

### Step 1 — Create the agent file

Create `backend/app/agents/my_agent.py`:

```python
from typing import Dict, Any
from app.agents.base import BaseAgent, AgentOutput
from app.config import settings
from jinja2 import Template
import json

MY_PROMPT_TEMPLATE = """
You are evaluating a hackathon submission for {{ criterion_name }}.

Repository: {{ repo_url }}
Languages: {{ languages | join(', ') }}

{% if code_samples %}
Code samples:
{% for sample in code_samples %}
--- {{ sample.path }} ---
{{ sample.content[:500] }}
{% endfor %}
{% endif %}

Evaluate the submission and respond with ONLY a JSON object:
{
  "score": <float 0.0 to 10.0>,
  "confidence": <float 0.0 to 1.0>,
  "reasoning": "<one paragraph explanation>",
  "evidence": [{"file": "<path>", "observation": "<finding>"}],
  "strengths": ["<strength 1>", "<strength 2>"],
  "weaknesses": ["<weakness 1>", "<weakness 2>"]
}
"""


class MyCustomAgent(BaseAgent):
    agent_id = "my_agent"
    prompt_version = "1.0"

    async def _evaluate(self, context: Dict[str, Any]) -> AgentOutput:
        template = Template(MY_PROMPT_TEMPLATE)
        prompt = template.render(
            criterion_name="My Custom Criterion",
            repo_url=context.get("repo_url", ""),
            languages=context.get("file_summary", {}).get("languages", []),
            code_samples=context.get("code_samples", []),
        )

        raw_response = await self.llm.generate(
            prompt=prompt,
            model=settings.OLLAMA_REASONING_MODEL,
            temperature=0.1,
        )

        # Parse JSON — find the outermost {} block
        start = raw_response.find("{")
        end = raw_response.rfind("}") + 1
        if start == -1 or end == 0:
            return AgentOutput(
                agent_id=self.agent_id,
                score=None,
                confidence=None,
                reasoning="Failed to parse LLM response",
                abstained=True,
                abstain_reason="JSON not found in response",
            )

        data = json.loads(raw_response[start:end])
        return AgentOutput(
            agent_id=self.agent_id,
            score=float(data["score"]),
            confidence=float(data["confidence"]),
            reasoning=data["reasoning"],
            evidence=data.get("evidence", []),
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
        )
```

### Step 2 — Register the agent

Open `backend/app/agents/registry.py` and add the import and registry entry:

```python
from app.agents.my_agent import MyCustomAgent

AGENT_REGISTRY: Dict[str, Type[BaseAgent]] = {
    "repo_understanding": RepoUnderstandingAgent,
    "code_quality": CodeQualityAgent,
    "innovation": InnovationAgent,
    "comparative": ComparativeAgent,
    "my_agent": MyCustomAgent,   # Add this line
}
```

### Step 3 — Add a criterion in the database

After starting the platform, use the API or the admin UI to add a criterion to a hackathon with `agent_id = "my_agent"`:

```bash
curl -X POST http://localhost/api/v1/hackathons/{hackathon_id}/criteria \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Custom Criterion", "description": "...", "weight": 0.20, "agent_id": "my_agent"}'
```

Update the weights of existing criteria to sum to 1.0.

### Step 4 — Test in isolation

```bash
make shell

python -c "
import asyncio
from app.agents.my_agent import MyCustomAgent
from app.agents.llm_provider import get_llm_provider

async def test():
    agent = MyCustomAgent(get_llm_provider())
    context = {
        'repo_url': 'https://github.com/karpathy/micrograd',
        'file_summary': {'languages': ['Python'], 'total_files': 10, 'has_tests': True},
        'code_samples': [{'path': 'micrograd/engine.py', 'content': 'class Value: ...'}],
    }
    result = await agent.evaluate(context)
    print(f'Score: {result.score}')
    print(f'Abstained: {result.abstained}')
    print(f'Reasoning: {result.reasoning[:200]}')

asyncio.run(test())
"
```

### Step 5 — Write unit tests

Follow the pattern in `backend/tests/test_agents/test_base.py`. Create `backend/tests/test_agents/test_my_agent.py` with tests for:
- Valid JSON output → non-abstained result with score in [0, 10]
- Malformed JSON response → abstained result with `abstain_reason`
- Missing JSON → abstained result

Run: `docker compose exec backend pytest tests/test_agents/ -v`
