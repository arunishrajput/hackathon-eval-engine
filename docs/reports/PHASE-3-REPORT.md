# Phase 3 Report — Repository Ingestion Pipeline

**Status**: Completed
**Date**: 2026-05-15
**Phase duration**: Day 2–3

---

## Summary

Phase 3 built the complete repository ingestion and static analysis pipeline. The pipeline transforms a raw GitHub URL into a structured context dict that AI agents can reason about — including a file listing with language detection, static analysis metrics, and curated code samples. The SSE endpoint that streams evaluation progress to the frontend was also finalized in this phase.

---

## What Was Built

### Repository Ingestion
- **`backend/app/pipeline/ingestion.py`** — `clone_repository()` via GitPython with depth=1 shallow clone, configurable 120-second timeout (enforced via `asyncio.wait_for()`), and post-clone size validation (configurable `MAX_REPO_SIZE_MB`, default 50 MB); `cleanup_repository()` removes the workspace directory after evaluation
- Cloning is run in a thread pool executor (`loop.run_in_executor(None, _clone_sync, ...)`) to avoid blocking the asyncio event loop during the synchronous git operation

### File Processor
- **`backend/app/pipeline/file_processor.py`** — `collect_files()` walks the cloned repository, uses Pygments for language detection, skips binary files by extension whitelist (`.pyc`, `.png`, `.jpg`, `.gif`, `.zip`, `.tar`, `.whl`, `.lock`, etc.), enforces a 512 KB per-file content limit, and returns a list of file dicts with `path`, `language`, `content`, `lines`, `size_bytes`
- `extract_readme()` — finds and returns the raw content of `README.md` or `README.rst` (case-insensitive)
- Language distribution statistics computed from the file list

### Static Analysis
- **`backend/app/pipeline/static_analysis.py`** — `run_static_analysis()` dispatches to language-specific analyzers based on file language:
  - **Python**: `radon.complexity.cc_visit()` called programmatically (not subprocess) for per-function cyclomatic complexity; `radon.metrics.mi_visit()` for per-file maintainability index (0–100 scale)
  - **JavaScript/TypeScript**: `eslint --ext .js,.ts,.jsx,.tsx --format json` called via `asyncio.create_subprocess_exec()` with 30-second timeout; error and warning counts aggregated
  - **Summary**: total files, total lines, language list, `has_tests`, `has_readme`, `has_docker` computed from file paths
- High-complexity functions (cyclomatic complexity > 10) collected into a deduplicated list capped at 20 items

### Context Builder
- **`backend/app/pipeline/context_builder.py`** — `build_evaluation_context()` assembles the structured context dict consumed by all three evaluation agents, including: code samples (3–5 files, prioritized by language and line count), static analysis summary, file tree representation, and README content

### LangGraph Integration
- `clone_node`, `analyze_node` — async LangGraph node functions in `backend/app/orchestration/nodes.py` that populate the `EvaluationState` dict and advance `state["status"]`
- `should_continue` conditional router that inspects `state["status"] == "failed"` to route to `END`

---

## Key Decisions Made

- **Binary file skip by extension whitelist** — files are skipped if their extension is in a known binary set rather than attempting to decode; avoids chardet overhead and encoding errors from `.pyc`, `.jpg`, `.whl` files
- **512 KB per-file content limit** — files larger than 512 KB (typically generated files, lockfiles, bundled JS) are skipped to prevent polluting the LLM context with irrelevant content
- **radon called programmatically** — unlike ESLint (subprocess), radon is a Python library called directly via `cc_visit()` and `mi_visit()`, which is faster and avoids JSON serialization/deserialization overhead
- **ESLint as subprocess** — ESLint requires Node.js; called via `asyncio.create_subprocess_exec()` with a 30-second timeout and `--format json` for structured output
- **Depth-1 clone** — `Repo.clone_from(url, dest, depth=1)` fetches only the latest commit, minimizing network transfer and disk usage for large repositories

---

## Known Issues / Technical Debt

- Semgrep is installed but not yet integrated into the `run_static_analysis()` function in this phase (added to `requirements.txt` as a dependency for Phase 4+). **Debt**: wire semgrep output into the `CodeQualityAgent` context.
- ESLint requires Node.js in the backend/worker Docker image, adding approximately 300 MB to the image size. **Debt**: consider a dedicated linting sidecar container or a pre-compiled ESLint binary.
- The file processor does not detect encoding; it assumes UTF-8 and skips files that raise `UnicodeDecodeError`. This may cause language-detection misses for Windows-encoded codebases. **Debt**: add chardet fallback for non-UTF-8 files.
- `build_file_tree()` generates a textual directory tree but truncates at depth 4. Very deeply nested repositories (monorepos) may not show all relevant structure to the agents.

---

## Verification Checklist

- [x] `clone_repository("https://github.com/karpathy/micrograd", "test-id")` clones successfully within timeout
- [x] Size check rejects a hypothetical 60 MB repo (manually tested with a large test fixture)
- [x] `collect_files()` on micrograd returns Python files with correct language detection, skipping `.pyc` cache files
- [x] `radon.cc_visit()` on a Python file with known complexity produces correct CC values
- [x] ESLint subprocess invoked correctly on a JS file; `total_errors` and `total_warnings` populated
- [x] `run_static_analysis()` returns `has_tests: true` for repos with files containing "test" in path
- [x] `has_readme: true` detected for repos with README.md
- [x] SSE events emitted in order: `cloning` → `analyzing` → `evaluating` → `scoring` → `completed`
- [x] Cloned 3 public repos (flask, fastapi, micrograd); file trees extracted correctly
- [x] Language detection correctly identified Python, JavaScript, and mixed repos
