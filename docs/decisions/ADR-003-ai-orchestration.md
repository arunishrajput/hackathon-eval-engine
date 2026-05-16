# ADR-003: AI Orchestration — LangGraph 0.2 with Compiled StateGraph

**Status**: Accepted
**Date**: 2026-05-15

---

## Context

The evaluation pipeline for every submission follows four mandatory sequential stages:

1. **Clone** — shallow-clone the repository via GitPython, validate size, enumerate files
2. **Analyze** — run radon (cyclomatic complexity, maintainability index) and ESLint on the cloned source
3. **Evaluate** — invoke three specialized AI agents (RepoUnderstandingAgent, CodeQualityAgent, InnovationAgent) with the static analysis output as context
4. **Score** — aggregate per-agent scores into a final weighted score, generate the report, persist to DB

Each stage depends on the output of the previous stage and cannot run concurrently. Each stage can fail independently — a network error during clone, a timeout during analysis, or a JSON parse failure in an agent. When any stage fails, the pipeline must stop immediately and mark the submission as `failed` without executing downstream stages.

The pipeline runs inside an ARQ worker process (not the FastAPI API server), meaning it must be fully async-compatible. State must persist through the pipeline so that each node can read what the previous node produced without re-computing it.

The team evaluated three approaches for implementing this pipeline.

---

## Decision

**LangGraph 0.2** with a four-node `StateGraph[EvaluationState]` compiled into a reusable graph object.

The graph is defined in `backend/app/orchestration/graph.py` and compiled once at module load time into the module-level `evaluation_graph` object. Each node is a pure async function. The `EvaluationState` TypedDict in `backend/app/orchestration/state.py` carries all inter-node data. A single `should_continue` conditional router inspects `state["status"]` after each node and routes to `END` on failure or to the next node on success.

```python
# graph.py (simplified)
workflow = StateGraph(EvaluationState)
workflow.add_node("clone", clone_node)
workflow.add_node("analyze", analyze_node)
workflow.add_node("evaluate", evaluate_node)
workflow.add_node("score", score_node)
workflow.set_entry_point("clone")
workflow.add_conditional_edges("clone", should_continue, {"analyze": "analyze", "end": END})
workflow.add_conditional_edges("analyze", should_continue, {"evaluate": "evaluate", "end": END})
workflow.add_conditional_edges("evaluate", should_continue, {"score": "score", "end": END})
workflow.add_edge("score", END)
evaluation_graph = workflow.compile()
```

The ARQ task invokes the graph with `await evaluation_graph.ainvoke(initial_state)`, receives the final state dict, and persists results to the database.

---

## Comparison

| Criterion | LangGraph 0.2 | CrewAI | Custom async pipeline | AutoGen | Raw LangChain LCEL |
|-----------|---------------|--------|-----------------------|---------|---------------------|
| Explicit typed state management | Yes — TypedDict propagated through graph | No — agents communicate via shared memory | Manual — must design state passing | No — message-based | Partial — runnable input/output |
| Deterministic execution order | Yes — edges are declared at compile time | No — role-playing agents decide order | Yes — explicit `await` sequence | No — conversational turn-taking | Partial — chains are ordered but branching is complex |
| Conditional fail-fast routing | Yes — `add_conditional_edges` with named targets | Limited — no first-class routing primitive | Manual `if/else` in each step | Limited | No — no branching primitive; requires nested chain logic |
| Async-native execution | Yes — `ainvoke` runs all nodes as coroutines | Yes | Yes | Yes | Yes |
| Debugging / visualization | `graph.compile()` produces inspectable structure; LangSmith tracing optional | Limited | Full control; print statements | Limited | Limited |
| Overhead added vs. raw Python | Minimal — one compile step at startup | Medium — role definitions, crew setup | None | High — model selection, planner overhead | Medium — chain wrapping |
| Designed for deterministic pipelines | Yes — primary use case | No — designed for autonomous delegation | Yes | No — designed for multi-model conversation | Partially |
| Node isolation / testability | Yes — each node is a plain async function | No — agents tightly coupled to crew | Yes | Partial | Partial |
| State TypedDict enforcement | Yes | No | Manual | No | No |
| Human-in-the-loop checkpoint support | Yes (built-in persistence layer) | Limited | Manual | Limited | No |

---

## Key Insight

**LangGraph's conditional edges implement resilient agent failure handling with a single, centrally declared routing function.**

The alternative — a hand-written sequential pipeline — was prototyped first. It required duplicating the failure-check logic after every `await` call:

```python
# Custom pipeline (prototype — rejected)
repo_path = await clone_repository(repo_url)
if repo_path is None:
    await mark_failed(submission_id, "clone failed")
    return
files, analysis = await analyze_repository(repo_path)
if files is None:
    await mark_failed(submission_id, "analysis failed")
    return
agent_outputs = await run_agents(files, analysis)
if agent_outputs is None:
    await mark_failed(submission_id, "evaluation failed")
    return
# ... etc.
```

This approach has three problems: the `mark_failed` logic is duplicated four times (creating drift risk), there is no typed state object (data is passed as positional arguments, making refactoring fragile), and there is no built-in tracing. LangGraph eliminates all three: `should_continue` is declared once, `EvaluationState` enforces field access, and the compiled graph is inspectable.

CrewAI and AutoGen were eliminated because they introduce non-determinism that is actively harmful in a scoring context. CrewAI agents choose how to delegate tasks; AutoGen agents engage in multi-turn conversation. EVALON's pipeline has a fixed execution order — there is nothing to delegate or negotiate. Using an autonomous agent framework for a sequential pipeline adds complexity without adding capability.

---

## Consequences

### Positive

- **State isolation**: nodes cannot accidentally share mutable state because each receives an immutable copy of the TypedDict and returns a new dict with updated fields. This eliminates a class of concurrency bugs.
- **Visualization tooling**: `evaluation_graph.get_graph().draw_mermaid()` produces a Mermaid diagram of the compiled graph for documentation without additional tooling.
- **Future extensibility**: adding a fifth node (e.g., a security analysis node or a comparative node) requires adding one `workflow.add_node()` call and updating the edge map. The rest of the pipeline is unaffected.
- **LangSmith integration** (opt-in): setting `LANGCHAIN_TRACING_V2=true` and a LangSmith API key enables distributed trace collection for every pipeline run with no code changes.
- **Compile-time validation**: `workflow.compile()` raises `InvalidUpdateError` if the graph has unreachable nodes or invalid edge targets, catching configuration bugs at startup rather than at runtime.

### Negative

- **TypedDict discipline required**: every node must return a dict with valid `EvaluationState` keys. A node that returns an unexpected key silently drops the value (LangGraph merges the returned dict into the state). This requires careful review of node return types.
- **Startup overhead**: `workflow.compile()` at module load adds approximately 1–2 seconds to cold start. This is acceptable for a worker process but would be unacceptable in a serverless function with per-request cold starts.
- **Version pinning is critical**: LangGraph changed its API significantly between 0.1.x and 0.2.x. The `requirements.txt` pins `langgraph==0.2.14`. Upgrading requires verifying that the `StateGraph`, `add_conditional_edges`, and `ainvoke` APIs have not changed.
- **No built-in retry per node**: if `clone_node` fails due to a transient network error, LangGraph routes to END immediately. Retry logic must be implemented inside each node function (e.g., with `tenacity`), not at the graph level.

### Risks

- **State schema drift**: if `EvaluationState` fields are added or renamed without updating all nodes, nodes that read stale field names return `None` silently. Mitigation: add type annotations and use `mypy` to catch field access errors.
- **LangGraph ecosystem churn**: as of LangGraph 0.2, the library is still pre-1.0. Breaking changes in minor releases are documented in the changelog but require active monitoring. Pinning to a patch version (`==0.2.14`) rather than a minor range is intentional.
