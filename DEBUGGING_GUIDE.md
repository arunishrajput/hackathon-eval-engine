# EVALON — Debugging Guide

This guide covers failure diagnosis, log inspection, agent isolation testing, adding new agents, and useful database queries. When you hit a problem, start with the quick-reference table below.

---

## Quick-Reference: Common Failure Modes

| Symptom | Likely cause | First command |
|---------|-------------|---------------|
| Submission stuck at `pending` | ARQ worker not running or Redis unreachable | `docker compose ps worker` |
| Submission stuck at `cloning` | Git clone timeout or repo URL invalid | `make worker-logs` |
| Evaluation `failed` immediately | Ollama model not loaded | `curl http://localhost:11434/api/tags` |
| Frontend shows no data | Backend unreachable via Nginx | `docker compose logs nginx` |
| `/api/health` shows `degraded` | One of postgres/redis/ollama is down | `docker compose ps` |
| `alembic upgrade head` fails | Migration conflict or DB not ready | `docker compose logs postgres` |
| JSON parse error in agent logs | LLM returned non-JSON or truncated response | Check Ollama logs + prompt template |
| `vector dimension mismatch` | Wrong embed model producing different dimension | Check `OLLAMA_EMBED_MODEL` env var |

---

## 1. How to Inspect ARQ Job Status

ARQ stores job metadata in Redis. To inspect the queue and running jobs:

```bash
# Check queue depth (pending jobs)
docker compose exec redis redis-cli llen arq:queue

# List all ARQ keys
docker compose exec redis redis-cli keys "arq:*"

# Inspect a specific job (replace JOB_KEY with an arq:job:* key from above)
docker compose exec redis redis-cli get arq:job:YOUR_JOB_KEY

# Watch queue in real time
docker compose exec redis redis-cli monitor | grep arq
```

To check job status from the Python side:

```bash
make shell
python -c "
import asyncio
from arq import create_pool
from arq.connections import RedisSettings
from app.config import settings

async def inspect():
    redis = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    # List queued jobs
    jobs = await redis.queued_jobs()
    for j in jobs:
        print(f'job_id={j.job_id} function={j.function} enqueue_time={j.enqueue_time}')
    await redis.close()

asyncio.run(inspect())
"
```

---

## 2. How to Read Evaluation Pipeline Logs

The ARQ worker logs every pipeline stage transition using structlog. Logs are structured JSON in production and human-readable in development.

```bash
# Follow worker logs in real time
make worker-logs

# Search for logs related to a specific submission
docker compose logs worker 2>&1 | grep "YOUR_SUBMISSION_ID"

# Watch for agent completions
docker compose logs worker 2>&1 | grep "Agent completed"

# Watch for failures
docker compose logs worker 2>&1 | grep -E "(failed|error|ERROR)"
```

Key log fields to look for:

| Log message | What it means |
|------------|---------------|
| `Starting evaluation job` | Job picked up by worker |
| `Cloning repository` | `clone_node` starting git clone |
| `Clone failed` | Git clone error — check `repo_url` validity and network |
| `Analysis failed` | Static analysis raised an exception |
| `Agent completed` | One agent finished; check `score` and `agent_id` |
| `Failed to parse ... response` | LLM returned non-JSON; agent abstained |
| `Evaluation job persisted` | Results saved to DB; check `pipeline_status` field |
| `embed_repository failed (non-fatal)` | Embedding failed but evaluation still succeeded |
| `recompute_rankings failed (non-fatal)` | Ranking update failed; can be triggered manually |

---

## 3. How to Test a Single Agent in Isolation

You can run any agent outside the full pipeline to test prompt changes or debug LLM responses:

```bash
make shell
python -c "
import asyncio
from app.agents.registry import get_agent
from app.agents.llm_provider import get_llm_provider

# Build a minimal evaluation context
context = {
    'submission_id': 'test-001',
    'repo_url': 'https://github.com/karpathy/micrograd',
    'hackathon_description': 'Build something with AI',
    'criteria': [],
    'file_count': 10,
    'language_breakdown': {'Python': 8, 'Markdown': 2},
    'has_tests': True,
    'has_readme': True,
    'has_docker': False,
    'total_lines': 500,
    'key_files': [
        {
            'path': 'micrograd/engine.py',
            'language': 'Python',
            'lines': 100,
            'snippet': 'class Value:\n    def __init__(self, data, _children=(), _op=\"\"):\n        self.data = data\n        self.grad = 0\n'
        }
    ],
    'code_samples': [],
    'static_analysis': {
        'summary': {'total_files': 10, 'total_lines': 500, 'languages': ['Python'], 'has_tests': True, 'has_readme': True, 'has_docker': False},
        'complexity': {'total_cyclomatic_complexity': 12, 'average_cc': 1.5, 'high_complexity_functions': []},
        'maintainability': {'average_maintainability_index': 72.5},
        'linting': {},
    },
    'readme_content': '# micrograd\nA tiny autograd engine.',
}

async def test_agent(agent_id):
    llm = get_llm_provider()
    agent = get_agent(agent_id, llm)
    output = await agent.evaluate(context)
    print(f'Agent: {agent_id}')
    print(f'Score: {output.score}')
    print(f'Confidence: {output.confidence}')
    print(f'Abstained: {output.abstained}')
    print(f'Reasoning: {output.reasoning[:300]}')
    print(f'Strengths: {output.strengths}')
    print(f'Weaknesses: {output.weaknesses}')
    print(f'Processing time: {output.processing_time_ms}ms')

asyncio.run(test_agent('code_quality'))
"
```

Replace `'code_quality'` with `'repo_understanding'` or `'innovation'` to test other agents.

---

## 4. How to Add a New Evaluator Agent

Follow these steps to add a new evaluation agent to the pipeline:

### Step 1: Create the agent class

Create `backend/app/agents/your_agent.py`:

```python
import json
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from app.agents.base import BaseAgent, AgentOutput
from app.config import settings
import structlog

logger = structlog.get_logger()
PROMPT_DIR = Path(__file__).parent / "prompts"


class YourAgent(BaseAgent):
    """Describe what your agent evaluates."""

    agent_id = "your_agent"
    prompt_version = "1.0"

    async def _evaluate(self, context: Dict[str, Any]) -> AgentOutput:
        env = Environment(loader=FileSystemLoader(str(PROMPT_DIR)), autoescape=False)
        template = env.get_template("your_agent.j2")
        prompt = template.render(**context)

        response = await self.llm.generate(
            prompt=prompt,
            model=settings.OLLAMA_REASONING_MODEL,
            temperature=0.2,
        )
        return self._parse_response(response)

    def _parse_response(self, response: str) -> AgentOutput:
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON found")
            data = json.loads(response[start:end])
            return AgentOutput(
                agent_id=self.agent_id,
                score=float(data.get("score", 0)),
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", ""),
                evidence=data.get("evidence", []),
                strengths=data.get("strengths", []),
                weaknesses=data.get("weaknesses", []),
            )
        except Exception as e:
            logger.warning("Parse failed", agent=self.agent_id, error=str(e))
            return AgentOutput(
                agent_id=self.agent_id, score=None, confidence=None,
                reasoning=response[:500], abstained=True, abstain_reason=str(e)
            )
```

### Step 2: Create the Jinja2 prompt template

Create `backend/app/agents/prompts/your_agent.j2`. The template has access to the full `context` dict including `file_count`, `language_breakdown`, `key_files`, `code_samples`, `static_analysis`, `hackathon_description`, and `criteria`.

Your prompt must instruct the LLM to return a JSON object with this exact structure:
```json
{
  "score": 7.5,
  "confidence": 0.8,
  "reasoning": "Explanation of the score...",
  "evidence": ["file path or observation 1", "file path or observation 2"],
  "strengths": ["strength 1", "strength 2"],
  "weaknesses": ["weakness 1"]
}
```

### Step 3: Register in the agent registry

In `backend/app/agents/registry.py`:
```python
from app.agents.your_agent import YourAgent

AGENT_REGISTRY: Dict[str, Type[BaseAgent]] = {
    "repo_understanding": RepoUnderstandingAgent,
    "code_quality": CodeQualityAgent,
    "innovation": InnovationAgent,
    "your_agent": YourAgent,  # add this line
}
```

### Step 4: Wire into the evaluate node

In `backend/app/orchestration/nodes.py`, add `"your_agent"` to the `agent_ids` list in `evaluate_node()`:

```python
agent_ids = ["repo_understanding", "code_quality", "innovation", "your_agent"]
```

### Step 5: Add a criterion in the database

After `make seed` or via the admin API, add a criterion with `agent_id = "your_agent"` and a non-zero weight. The aggregator will pick it up automatically.

### Step 6: Test in isolation

Use the isolation test pattern from Section 3 above with `agent_id = "your_agent"`.

---

## 5. How to Verify Ollama is Running Correctly

```bash
# Check Ollama server version and status
curl http://localhost:11434/api/version

# List loaded models
curl http://localhost:11434/api/tags | python3 -m json.tool

# Test text generation (should return JSON with a "response" field)
curl -s http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:7b",
  "prompt": "Return a JSON object with key \"status\" and value \"ok\".",
  "stream": false
}' | python3 -m json.tool

# Test embedding (should return a "embedding" array of 768 floats)
curl -s http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "hello world"
}' | python3 -c "import sys, json; e=json.load(sys.stdin)['embedding']; print(f'Dimensions: {len(e)}, first value: {e[0]:.4f}')"
```

If `qwen2.5:7b` generates non-JSON responses, run a direct test with an explicit JSON instruction. If the model is still failing after 3 attempts, check that it downloaded completely:

```bash
docker compose exec ollama ollama show qwen2.5:7b
```

Look for `parameters` and `template` sections — if they are absent, the model may have downloaded incompletely. Remove and re-pull:

```bash
docker compose exec ollama ollama rm qwen2.5:7b
docker compose exec ollama ollama pull qwen2.5:7b
```

---

## 6. Useful Database Queries

Open a psql session:
```bash
docker compose exec postgres psql -U hackeval -d hackeval
```

### Recent evaluations with scores

```sql
SELECT
    e.id,
    s.repo_url,
    e.status,
    e.final_score,
    e.started_at,
    e.completed_at,
    EXTRACT(EPOCH FROM (e.completed_at - e.started_at))::int AS duration_seconds
FROM evaluations e
JOIN submissions s ON s.id = e.submission_id
ORDER BY e.created_at DESC
LIMIT 10;
```

### Per-agent scores for a specific evaluation

```sql
SELECT
    ar.agent_id,
    ar.score_raw,
    ar.confidence,
    ar.abstained,
    ar.abstain_reason,
    ar.processing_time_ms,
    LEFT(ar.reasoning, 200) AS reasoning_preview
FROM agent_results ar
WHERE ar.evaluation_id = 'YOUR_EVALUATION_UUID'
ORDER BY ar.agent_id;
```

### Submissions by status in a hackathon

```sql
SELECT status, COUNT(*) as count
FROM submissions
WHERE hackathon_id = 'YOUR_HACKATHON_UUID'
GROUP BY status
ORDER BY count DESC;
```

### Current leaderboard for a hackathon

```sql
SELECT
    r.rank,
    u.email,
    s.repo_url,
    e.final_score,
    r.normalized_score,
    r.percentile
FROM rankings r
JOIN submissions s ON s.id = r.submission_id
JOIN users u ON u.id = s.user_id
JOIN evaluations e ON e.submission_id = s.id
WHERE r.hackathon_id = 'YOUR_HACKATHON_UUID'
ORDER BY r.rank;
```

### Check embedding counts per submission

```sql
SELECT
    s.repo_url,
    COUNT(re.id) AS embedding_count
FROM submissions s
LEFT JOIN repo_embeddings re ON re.submission_id = s.id
WHERE s.hackathon_id = 'YOUR_HACKATHON_UUID'
GROUP BY s.id, s.repo_url
ORDER BY embedding_count DESC;
```

---

## 7. How to Reset a Stuck Evaluation

If a submission is stuck in `cloning`, `analyzing`, or `evaluating` state (usually because the worker crashed mid-job):

```bash
make shell
python -c "
import asyncio
from uuid import UUID
from app.database import AsyncSessionLocal
from app.models.submission import Submission, SubmissionStatus
from app.models.evaluation import Evaluation, EvaluationStatus
from sqlalchemy import select

SUBMISSION_ID = 'YOUR_SUBMISSION_UUID'

async def reset():
    async with AsyncSessionLocal() as db:
        # Reset submission status
        result = await db.execute(select(Submission).where(Submission.id == UUID(SUBMISSION_ID)))
        submission = result.scalar_one_or_none()
        if submission:
            submission.status = SubmissionStatus.pending
            submission.error_message = None

        # Reset evaluation if one exists
        eval_result = await db.execute(
            select(Evaluation).where(Evaluation.submission_id == UUID(SUBMISSION_ID))
        )
        evaluation = eval_result.scalar_one_or_none()
        if evaluation:
            evaluation.status = EvaluationStatus.pending
            evaluation.final_score = None
            evaluation.report = None

        await db.commit()
        print(f'Reset submission {SUBMISSION_ID} to pending')

asyncio.run(reset())
"
```

Then re-enqueue the evaluation:

```bash
python -c "
import asyncio
from app.jobs.tasks import enqueue_evaluation

asyncio.run(enqueue_evaluation('YOUR_SUBMISSION_UUID'))
print('Evaluation re-enqueued')
"
```

---

## 8. Rebuilding After Code Changes

```bash
# Rebuild images after Dockerfile or requirements.txt changes
make build && make up

# Rebuild a single service
docker compose build backend && docker compose up -d backend worker

# Apply new migrations after model changes
make migrate
```

After adding a new Alembic migration:
```bash
docker compose exec backend alembic revision --autogenerate -m "add new table"
make migrate
```
