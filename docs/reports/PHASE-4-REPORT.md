# Phase 4 Report — AI Evaluation Agents

**Status**: Completed
**Date**: 2026-05-15
**Phase duration**: Day 3–4

---

## Summary

Phase 4 built the multi-agent evaluation layer: three specialized AI agents (RepoUnderstanding, CodeQuality, Innovation), the LangGraph orchestration graph, Jinja2 prompt templates, the OllamaProvider HTTP client, and the ARQ task wiring. By the end of Phase 4, a complete end-to-end evaluation run could be triggered from a submission ID and would produce structured agent outputs with scores, evidence, strengths, and weaknesses persisted to the database.

---

## What Was Built

### Agent Framework
- **`backend/app/agents/base.py`** — `BaseAgent` abstract class with `evaluate()` wrapper that handles exception catching, graceful abstention, and `processing_time_ms` measurement; `AgentOutput` dataclass with all result fields
- **`backend/app/agents/registry.py`** — `AGENT_REGISTRY` dict mapping agent ID strings to `BaseAgent` subclasses; `get_agent()` factory; `list_agents()` utility

### Concrete Agents
- **`backend/app/agents/repo_understanding.py`** — `RepoUnderstandingAgent` (uses `qwen2.5:7b` at temperature 0.1): evaluates project structure, documentation quality, README completeness, architectural clarity
- **`backend/app/agents/code_quality.py`** — `CodeQualityAgent` (uses `qwen2.5-coder:7b` at temperature 0.1): interprets radon CC/MI and ESLint output; selects 3–5 representative code samples; evaluates complexity, style, test presence
- **`backend/app/agents/innovation.py`** — `InnovationAgent` (uses `qwen2.5:7b` at temperature 0.3): evaluates problem novelty, solution creativity, technical sophistication, hackathon theme alignment; receives up to 4 innovation-relevant files selected by keyword scoring
- **`backend/app/agents/comparative.py`** — `ComparativeAgent` (stub): registered in `AGENT_REGISTRY`, always returns `abstained=True`; architecture hook for the comparative evaluation feature in v1.1

### LLM Provider
- **`backend/app/agents/llm_provider.py`** — `OllamaProvider` async HTTP client with `generate()` and `embed()` methods; module-level singleton via `get_llm_provider()` to reuse the `httpx.AsyncClient` across evaluations; configurable timeout via `settings.OLLAMA_TIMEOUT`

### Prompt Templates
- **`backend/app/agents/prompts/repo_understanding.j2`** — Jinja2 template instructing the LLM to evaluate structure and documentation; includes JSON output schema in the prompt with anti-hallucination instruction ("only reference file paths that appear in the provided context")
- **`backend/app/agents/prompts/code_quality.j2`** — injects radon CC/MI metrics and ESLint results as structured facts; instructs LLM to interpret (not invent) the provided metrics
- **`backend/app/agents/prompts/innovation.j2`** — includes hackathon description for theme alignment; temperature 0.3 allows more creative reasoning

### LangGraph Orchestration
- **`backend/app/orchestration/state.py`** — `EvaluationState` TypedDict with all inter-node fields
- **`backend/app/orchestration/nodes.py`** — `clone_node`, `analyze_node`, `evaluate_node`, `score_node` async functions; `should_continue` conditional router
- **`backend/app/orchestration/graph.py`** — compiled `StateGraph` with conditional edges; module-level `evaluation_graph` object

### ARQ Task Wiring
- **`backend/app/jobs/tasks.py`** — `run_evaluation(ctx, submission_id)` 9-step ARQ task: load submission, load criteria, upsert Evaluation record, invoke LangGraph, persist AgentResult rows, trigger `embed_repository`, trigger `recompute_rankings`, handle all errors

---

## Key Decisions Made

- **Sequential agent execution** in `evaluate_node` — agents run in a `for` loop rather than `asyncio.gather()` to avoid saturating the single Ollama server
- **JSON output parsing with `find`/`rfind`** — LLMs sometimes prepend preamble ("Sure, here is the JSON:"); the parser extracts `raw[raw.find('{'):raw.rfind('}')+1]` to handle preamble without regex
- **`should_continue` as a single router** — one function replacing four duplicated failure checks; any node sets `status = "failed"` and the router handles routing to `END`
- **Shared LLM provider singleton** — all agents call `get_llm_provider()` which returns a module-level singleton to avoid per-agent `httpx.AsyncClient` creation overhead
- **Agent scores on 0–10 scale** — LLMs produce more calibrated scores on a 0–10 scale than 0–100; all stored `agent_results.score_raw` values are on 0–10

---

## Known Issues / Technical Debt

- JSON parsing from LLM output relies on `find`/`rfind` for the outermost `{}`. Small models occasionally emit malformed JSON (trailing commas). **Debt**: add a `json-repair` library fallback.
- Agent prompts are English-only. Non-English READMEs may reduce evaluation quality. **Debt**: detect README language and add multilingual instructions.
- The InnovationAgent keyword-based file selection is a heuristic. **Debt**: consider embedding-based file selection for innovation-relevant samples.
- `qwen2.5-coder:7b` occasionally refuses to output a numeric score for very trivial files. The abstention mechanism catches this correctly.

---

## Verification Checklist

- [x] `BaseAgent.evaluate()` returns `abstained=True` when `_evaluate()` raises any exception
- [x] `AgentOutput.processing_time_ms` is always set (>= 0) — all 14 `test_base.py` unit tests pass
- [x] LangGraph graph compiles without errors (`evaluation_graph = build_evaluation_graph()` succeeded)
- [x] `evaluation_graph.ainvoke(initial_state)` completes end-to-end on micrograd test repository
- [x] A simulated agent failure routes pipeline to `status == "failed"` and does not execute `score_node`
- [x] `AgentResult` rows saved to database with correct `evaluation_id`, `agent_id`, `score_raw`, `evidence`
- [x] All 4 agent IDs registered in `AGENT_REGISTRY`: `repo_understanding`, `code_quality`, `innovation`, `comparative`
- [x] `OllamaProvider.generate()` returns non-empty string against live Ollama
- [x] `OllamaProvider.embed()` returns list of 768 floats for a test string
