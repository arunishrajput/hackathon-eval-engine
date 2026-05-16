from pathlib import Path
from typing import Dict, Any, List
import subprocess
import json
import asyncio
from radon.complexity import cc_visit
from radon.metrics import mi_visit
import structlog

logger = structlog.get_logger()


async def run_static_analysis(repo_path: Path, files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run static analysis tools on the repository."""
    results = {
        "complexity": {},
        "maintainability": {},
        "linting": {},
        "summary": {},
    }

    python_files = [f for f in files if f["language"] == "Python"]
    if python_files:
        results["complexity"] = _analyze_python_complexity(python_files)
        results["maintainability"] = _analyze_python_maintainability(python_files)

    js_ts_files = [f for f in files if f["language"] in ("JavaScript", "TypeScript")]
    if js_ts_files:
        results["linting"] = await _run_eslint(repo_path)

    results["summary"] = _compute_summary(results, files)
    return results


def _analyze_python_complexity(files: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_cc = 0
    high_complexity = []

    for f in files:
        try:
            blocks = cc_visit(f["content"])
            for block in blocks:
                total_cc += block.complexity
                if block.complexity > 10:
                    high_complexity.append({
                        "file": f["path"],
                        "name": block.name,
                        "complexity": block.complexity,
                    })
        except Exception:
            pass

    return {
        "total_cyclomatic_complexity": total_cc,
        "high_complexity_functions": high_complexity[:20],
        "average_cc": total_cc / max(len(files), 1),
    }


def _analyze_python_maintainability(files: List[Dict[str, Any]]) -> Dict[str, Any]:
    mi_scores = []
    for f in files:
        try:
            score = mi_visit(f["content"], multi=True)
            if score is not None:
                mi_scores.append({"file": f["path"], "score": score})
        except Exception:
            pass

    if mi_scores:
        avg = sum(s["score"] for s in mi_scores) / len(mi_scores)
        return {"average_maintainability_index": round(avg, 2), "per_file": mi_scores[:10]}
    return {}


async def _run_eslint(repo_path: Path) -> Dict[str, Any]:
    try:
        proc = await asyncio.create_subprocess_exec(
            "eslint", "--ext", ".js,.ts,.jsx,.tsx", "--format", "json", str(repo_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(repo_path),
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
        data = json.loads(stdout.decode() or "[]")
        total_errors = sum(f.get("errorCount", 0) for f in data)
        total_warnings = sum(f.get("warningCount", 0) for f in data)
        return {"total_errors": total_errors, "total_warnings": total_warnings, "files_analyzed": len(data)}
    except Exception as e:
        logger.warning("ESLint failed", error=str(e))
        return {}


def _compute_summary(results: Dict, files: List[Dict]) -> Dict[str, Any]:
    total_lines = sum(f.get("lines", 0) for f in files)
    languages = list({f["language"] for f in files})
    return {
        "total_files": len(files),
        "total_lines": total_lines,
        "languages": languages,
        "has_tests": any("test" in f["path"].lower() or "spec" in f["path"].lower() for f in files),
        "has_readme": any("readme" in f["path"].lower() for f in files),
        "has_docker": any("dockerfile" in f["path"].lower() or "docker-compose" in f["path"].lower() for f in files),
    }
