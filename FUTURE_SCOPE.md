# EVALON — Future Scope

This document provides detailed design specifications for planned future features. Each section explains the motivation, the technical approach, and the changes required to the existing codebase.

---

## 1. Comparative Intelligence Agent

**Status**: Stub implemented (`comparative.py` registered in `AGENT_REGISTRY`), evaluation logic not yet wired into the main pipeline.

### Motivation

The three current agents evaluate each submission in isolation. A comparative agent would evaluate a submission *relative to the field* — identifying whether a project is above average, average, or below average compared to other submissions in the same hackathon. This produces more discriminating rankings at the top of the leaderboard where absolute scores tend to cluster.

### Technical Design

The comparative agent requires at least 5 completed evaluations in a hackathon before it can produce a meaningful comparison.

**Design:**

After all standard agents complete, query `repo_embeddings` for the current submission's primary embedding. Run a pgvector similarity search across `repo_embeddings` of other completed submissions in the same hackathon (`WHERE hackathon_id = $1 AND submission_id != $2`) ordered by cosine distance. Select the top 5 most similar submissions.

Build a comparison context including:
- Current submission's agent scores and report summary
- 5 nearest-neighbor submissions' agent scores and brief summaries (no full code)
- Hackathon criteria and their descriptions

A Jinja2 template presents the current submission's scores alongside the comparison group. The agent is asked to produce a relative score adjustment (`delta` in [-2.0, +2.0]) and a comparative reasoning narrative.

The comparative delta is applied as a post-hoc adjustment to the final score, capped to the [0, 10] range. The adjustment is stored in a new `comparative_delta` column on `evaluations`.

### Database Changes Required

```sql
ALTER TABLE evaluations ADD COLUMN comparative_delta NUMERIC(4, 3);
ALTER TABLE evaluations ADD COLUMN comparison_submission_ids UUID[];
```

### Pipeline Changes

The comparative agent node runs *after* the `score_node` and requires the hackathon to have at least 5 completed evaluations. The `should_continue` router gets a new `comparative` path: `scoring → comparative → END`.

---

## 2. Private Repository Support (GitHub OAuth App)

### Motivation

Many serious hackathon participants use private repositories to protect work-in-progress code before the submission deadline. Currently, the ingestion pipeline only supports public GitHub URLs.

### Technical Design

**OAuth Flow:**

1. Admin enables `allow_private_repos: true` in hackathon settings.
2. Participant clicks "Authorize GitHub" on the submission page. Frontend redirects to GitHub OAuth with the `repo` scope.
3. GitHub redirects back to `GET /api/v1/auth/github/callback?code=...`. Backend exchanges the code for an access token using the GitHub Apps API.
4. The access token is stored encrypted (AES-256-GCM with the `SECRET_KEY` as the key derivation input) in a new `github_tokens` table: `(user_id UUID, encrypted_token TEXT, scopes TEXT[], expires_at TIMESTAMP)`.
5. On evaluation job startup, `clone_repository()` checks if the repo URL requires authentication. If so, it retrieves and decrypts the token and injects it via git credential helper: `Repo.clone_from(url, dest, env={"GIT_ASKPASS": helper_script})`.

**New database table:**

```sql
CREATE TABLE github_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    encrypted_token TEXT NOT NULL,
    scopes TEXT[] NOT NULL DEFAULT '{}',
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

**Security considerations**: Tokens must never appear in logs. The `clone_node` must sanitize the repo URL in all structlog calls when a token is involved. Token expiry must be checked before use; if expired, the submission should fail with a `TokenExpiredError` surfaced to the participant as a recoverable error.

---

## 3. Security Hardening Agent

### Motivation

Code security is a legitimate evaluation dimension for production-oriented hackathons. Manual security review is time-consuming; automated tools can surface high-severity findings in seconds.

### Technical Design

The `analyze_node` is extended with two parallel async subprocess calls:

**Trivy** (container/dependency scanning):

```python
proc = await asyncio.create_subprocess_exec(
    "trivy", "fs", "--format", "json", "--severity", "HIGH,CRITICAL",
    str(repo_path),
    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
)
stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
trivy_results = json.loads(stdout.decode() or "[]")
```

**Semgrep** (SAST with full rulesets):

```python
proc = await asyncio.create_subprocess_exec(
    "semgrep", "--config", "auto", "--json", "--quiet", str(repo_path),
    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
)
stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
semgrep_results = json.loads(stdout.decode() or '{"results": []}')
```

Both tools are added to the backend `Dockerfile`. Their JSON output is merged into `static_analysis["security"]` and passed to a new `SecurityAgent` that uses an LLM to categorize severity, explain risks, and score security posture on a 0–10 scale.

**Scoring impact**: Security is added as a fourth criterion with a configurable weight (default 0%) so existing hackathons are unaffected. Admins enable it by adding a `security` criterion with a non-zero weight.

**New database table:**

```sql
CREATE TABLE security_agent_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    trivy_findings JSONB,
    semgrep_findings JSONB,
    owasp_findings JSONB,
    security_score NUMERIC(4, 3),
    severity_summary JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

---

## 4. Multi-Tenant SaaS Architecture

### Current State

EVALON runs as a single-tenant application — all data shares one database, one Redis instance, and one Ollama server.

### Changes Required for Multi-Tenancy

**Organization model**: Add an `organizations` table. Hackathons, users, and all dependent entities are scoped to an organization. API authentication carries an `organization_id` in the JWT claims.

**Row-level security**: PostgreSQL RLS policies enforce organization isolation at the database level, preventing cross-tenant data leaks even if application-level scoping has a bug:

```sql
ALTER TABLE hackathons ENABLE ROW LEVEL SECURITY;
CREATE POLICY hackathon_org_isolation ON hackathons
    USING (organization_id = current_setting('app.current_org_id')::UUID);
```

**Tenant-aware job queue**: ARQ job names are prefixed with `org:{org_id}:run_evaluation` and each organization gets a dedicated queue with configurable per-tenant concurrency limits.

**Ollama isolation**: At scale, a shared Ollama instance becomes a bottleneck. The architecture moves to a model gateway (e.g., LiteLLM proxy) that load-balances across a pool of Ollama workers. This is transparent to `OllamaProvider` since it speaks to the same `/api/generate` endpoint.

**Billing hooks**: Evaluation jobs emit an event to a `usage_events` table: `(org_id, submission_id, tokens_in, tokens_out, model, timestamp)`. A nightly job aggregates usage per organization for billing purposes.

**Roles**: Add `org_admin` role that can manage hackathons within their organization but not across organizations.

---

## 5. Kubernetes Deployment

### Motivation

Docker Compose is appropriate for single-node deployments. At scale (multiple hackathons running concurrently, hundreds of submissions), the system needs horizontal scaling of the worker tier and automated failover.

### Resource Specifications

| Component | Deployment Type | Replicas | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-----------|----------------|----------|-------------|-----------|----------------|-------------|
| backend (FastAPI) | Deployment | 3 | 250m | 1000m | 256Mi | 512Mi |
| worker (ARQ) | Deployment | 5–20 (HPA) | 500m | 2000m | 512Mi | 1Gi |
| frontend (Next.js) | Deployment | 2 | 100m | 500m | 128Mi | 256Mi |
| postgres | StatefulSet | 1 (+ read replica) | 1000m | 4000m | 2Gi | 8Gi |
| redis | StatefulSet | 1 | 100m | 500m | 256Mi | 512Mi |
| nginx | Deployment | 2 | 50m | 200m | 64Mi | 128Mi |
| ollama | StatefulSet | 1 (GPU node) | 4000m | 8000m | 8Gi | 16Gi |

**Horizontal Pod Autoscaler for workers** — scales based on Redis queue depth:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: evalon-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: evalon-worker
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: External
    external:
      metric:
        name: redis_queue_length
        selector:
          matchLabels:
            queue: arq:queue
      target:
        type: AverageValue
        averageValue: "5"
```

**Persistent volumes**: `postgres_data`, `redis_data`, and `ollama_models` become PersistentVolumeClaims on fast SSD storage classes (minimum 100 IOPS/GB).

**Helm chart**: A Helm chart with `values.yaml` overrides for CPU/memory limits, Ollama model list, and ingress configuration allows one-command deployment to any Kubernetes cluster.

---

## 6. Streaming Chat Response

### Current State

The mentor chatbot returns a full response string only after Ollama completes the entire generation. For long responses (10–30 seconds), this creates a blank UI state that feels unresponsive.

### Technical Design

Ollama supports a streaming API: `POST /api/generate` with `"stream": true` returns newline-delimited JSON where each line is a token. The backend SSE endpoint forwards each token to the browser:

```python
async def stream_mentor_response(session_id: UUID, message: str):
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", f"{OLLAMA_URL}/api/generate",
                                  json={"model": model, "prompt": prompt, "stream": True}) as resp:
            async for line in resp.aiter_lines():
                if line:
                    chunk = json.loads(line)
                    yield f"data: {json.dumps({'token': chunk['response']})}\n\n"
                    if chunk.get("done"):
                        yield "data: [DONE]\n\n"
                        break
```

The frontend `ChatInterface` component switches from displaying the final response to appending tokens as they arrive via `EventSource`. The `streaming` prop (already wired in the component) is set to `true` to enable this mode.

---

## 7. UI/UX Evaluation Agent

### Motivation

Hackathon projects with web frontends currently receive no credit for visual design, user experience quality, or accessibility. An LLM with vision capability could evaluate screenshots of the running application.

### Technical Design

1. **Screenshot capture**: After the repository is cloned and analyzed, detect if the project has a web frontend (presence of `package.json` with frontend dependencies, `index.html`, or framework-specific config files). Attempt to start the application in a headless Docker container using Playwright.

2. **Screenshot agent**: A new `UIUXAgent` (using a multimodal model — `qwen2.5-vl:7b` if available in Ollama, or gated behind a feature flag requiring OpenAI GPT-4o) receives base64-encoded screenshots and evaluates:
   - Visual design quality (clean, professional, responsive)
   - Perceived UX clarity (clear navigation, appropriate feedback, no obvious broken states)
   - Accessibility indicators (visible focus states, appropriate contrast)

3. **Integration**: The `analyze_node` is extended with an optional screenshot capture step. Screenshots (resized to 1280×800, JPEG 85%) are stored as bytea in a new `submission_screenshots` table. If capture fails, the UI agent is skipped gracefully (abstains).

### Complexity and Gating

This feature requires container-in-container execution (Docker socket or a Playwright service container), which has significant security implications. It should be gated behind an admin-configurable `enable_ui_evaluation: true` hackathon setting and should only be enabled in trusted deployment environments.

---

## 8. Billing Integration — Per-Evaluation Pricing Model

### Motivation

In a multi-tenant SaaS deployment (see Section 5), different organizations will have different usage volumes. A per-evaluation pricing model allows smaller organizations to pay only for what they use and enables enterprise contracts with volume discounts.

### Pricing Model Design

**Unit of billing**: one evaluation = one LLM inference session (three agent calls + one embedding pass). The cost of one evaluation depends on:
- Total tokens consumed (prompt tokens + completion tokens) across all three agents
- Model tier used (7B models are cheaper than 13B or 70B models)
- Embedding token count (proportional to repository size)

**Suggested public pricing** (illustrative):
| Tier | Price per evaluation | Included per month | Overage |
|------|---------------------|-------------------|---------|
| Free | $0.00 | 10 evaluations | N/A |
| Starter | $0.05/eval | 200 evaluations | $0.05/eval |
| Pro | $0.03/eval | 1,000 evaluations | $0.03/eval |
| Enterprise | Custom | Unlimited | Custom |

### Technical Design

**Usage events table** (new):

```sql
CREATE TABLE usage_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    submission_id UUID REFERENCES submissions(id),
    evaluation_id UUID REFERENCES evaluations(id),
    event_type VARCHAR(50) NOT NULL,  -- 'evaluation_start', 'evaluation_complete', 'embedding'
    model_id VARCHAR(100),
    tokens_in INTEGER,
    tokens_out INTEGER,
    embedding_chunks INTEGER,
    cost_usd NUMERIC(10, 6),
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ix_usage_events_org_month ON usage_events (organization_id, date_trunc('month', recorded_at));
```

**Token counting**: After each `OllamaProvider.generate()` call, Ollama returns `prompt_eval_count` and `eval_count` in the response JSON. These are captured and written to `usage_events` within the ARQ task.

**Cost computation**: A `COST_PER_TOKEN` configuration table maps `(model_id, direction)` to `cost_usd_per_1k_tokens`. The nightly billing aggregation job (`aggregate_usage_nightly`) sums `cost_usd` per organization per month and writes to a `billing_periods` table.

**Stripe integration**:
1. Admin of an organization connects a Stripe payment method via `POST /api/v1/billing/setup-intent`
2. At the start of each month, the previous month's `billing_periods` row triggers a Stripe usage record via the Stripe Metered Billing API: `stripe.SubscriptionItem.create_usage_record(quantity=evaluation_count)`
3. Stripe invoices the organization automatically at the billing cycle end

**Free tier enforcement**: A `RateLimiter` middleware checks `usage_events` count for the current month against the organization's plan limit before enqueueing a new evaluation job. Evaluations attempted over the free tier limit receive a 402 Payment Required response with a link to upgrade.

**Audit trail**: Every `usage_events` row is immutable — updates are prohibited via PostgreSQL row-level policy. This creates a tamper-proof billing audit log.

### Database Changes Required

- `organizations` table (see Multi-Tenant section)
- `usage_events` table (above)
- `billing_periods` table: `(org_id, period_start, period_end, evaluation_count, total_tokens, total_cost_usd, stripe_invoice_id, status)`
- `organization_plans` table: `(org_id, plan_name, monthly_evaluation_limit, cost_per_eval_usd, stripe_subscription_id)`

---

## Short-Term Backlog

- [ ] Email notifications when evaluation completes (SendGrid / SMTP)
- [ ] GitHub webhook support for automatic re-evaluation on push (`X-GitHub-Event: push`)
- [ ] Export rankings as PDF (WeasyPrint) and CSV
- [ ] Admin ability to override individual agent scores with an audit trail
- [ ] Confidence-weighted scoring using LLM-reported confidence as a Bayesian multiplier
- [ ] Real-time WebSocket leaderboard updates (replace current polling in rankings view)
- [ ] GDPR-compliant data deletion: `DELETE /api/v1/users/me` cascades to all submissions, evaluations, and embeddings
- [ ] External hackathon platform API integration (Devpost, HackerEarth, Unstop)
- [ ] Admin score override with audit trail
- [ ] Rate limiting on auth endpoints (slowapi `@limiter.limit("10/minute")`)
- [ ] Refresh token blacklist (Redis-backed) for proper logout support
