from typing import Dict, Any, List, Optional
from app.pipeline.file_processor import extract_readme, get_language_stats, build_file_tree, detect_project_type


def build_evaluation_context(
    submission_id: str,
    repo_url: str,
    files: List[Dict[str, Any]],
    static_analysis: Dict[str, Any],
    hackathon_description: str = "",
    criteria: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Assemble the full context dict passed to all evaluation agents.

    The returned dict contains everything an agent needs: project metadata,
    static analysis metrics, representative code samples, and criteria weights.
    """
    readme = extract_readme(files)
    language_stats = get_language_stats(files)
    project_type = detect_project_type(files)

    # Representative file samples for agents that need to inspect code
    code_samples = _select_code_samples(files, max_files=5)
    key_files = _select_key_files(files)

    return {
        # ---- Identity ----
        "submission_id": submission_id,
        "repo_url": repo_url,

        # ---- Hackathon context ----
        "hackathon_description": hackathon_description,
        "criteria": criteria or [],

        # ---- Project overview ----
        "readme": readme[:3000] if readme else "",
        "project_type": project_type,
        "language_stats": language_stats,

        # ---- Static analysis ----
        "file_summary": static_analysis.get("summary", {}),
        "complexity": static_analysis.get("complexity", {}),
        "maintainability": static_analysis.get("maintainability", {}),
        "linting": static_analysis.get("linting", {}),

        # ---- Code samples (for agents that inspect code directly) ----
        "code_samples": code_samples,   # 3-5 substantive source files
        "key_files": key_files,          # top-level / entry-point files

        # ---- Aggregate counts ----
        "total_files": len(files),
    }


def _select_code_samples(
    files: List[Dict[str, Any]],
    max_files: int = 5,
    max_content_chars: int = 1200,
) -> List[Dict[str, Any]]:
    """Select 3-5 representative source code files for agent inspection.

    Prioritises files with the most lines that are actual source code
    (not config/lock files), capped at ``max_content_chars`` characters each.
    """
    # Prefer source code languages over configs
    source_languages = {
        "Python", "JavaScript", "TypeScript", "Go", "Rust", "Java",
        "C", "C++", "C#", "Ruby", "PHP", "Swift", "Kotlin", "Scala",
    }
    config_names = {
        "package-lock.json", "yarn.lock", "poetry.lock", "pipfile.lock",
        "package.json", "requirements.txt", "setup.py", "pyproject.toml",
    }

    def score(f: Dict[str, Any]) -> int:
        name = f["path"].split("/")[-1].lower()
        if name in config_names:
            return 0
        lang_bonus = 100 if f["language"] in source_languages else 10
        return f["lines"] + lang_bonus

    sorted_files = sorted(files, key=score, reverse=True)
    seen_langs: Dict[str, int] = {}
    samples = []

    for f in sorted_files:
        if len(samples) >= max_files:
            break
        lang = f["language"]
        # Allow at most 2 files of the same language to keep diversity
        if seen_langs.get(lang, 0) >= 2:
            continue
        seen_langs[lang] = seen_langs.get(lang, 0) + 1
        samples.append({
            "path": f["path"],
            "language": f["language"],
            "lines": f["lines"],
            "content": f["content"][:max_content_chars],
        })

    # Ensure we return at least 3 if possible
    if len(samples) < 3:
        for f in sorted_files:
            if len(samples) >= 3:
                break
            already = any(s["path"] == f["path"] for s in samples)
            if not already:
                samples.append({
                    "path": f["path"],
                    "language": f["language"],
                    "lines": f["lines"],
                    "content": f["content"][:max_content_chars],
                })

    return samples


def _select_key_files(
    files: List[Dict[str, Any]],
    max_files: int = 10,
    max_content_chars: int = 500,
) -> List[Dict[str, Any]]:
    """Select the most representative entry-point / config files for LLM context."""
    priority_names = {
        "main.py", "app.py", "index.js", "index.ts", "server.py", "server.js",
        "app.js", "app.ts", "package.json", "requirements.txt", "setup.py",
        "docker-compose.yml", "dockerfile",
    }

    selected: List[Dict[str, Any]] = []
    seen_paths: set = set()

    # Priority files first
    for f in files:
        name = f["path"].split("/")[-1].lower()
        if name in priority_names and f["path"] not in seen_paths:
            seen_paths.add(f["path"])
            selected.append({
                "path": f["path"],
                "language": f["language"],
                "snippet": f["content"][:max_content_chars],
                "lines": f["lines"],
            })

    # Fill remaining slots with largest diverse files
    for f in sorted(files, key=lambda x: x["lines"], reverse=True):
        if len(selected) >= max_files:
            break
        if f["path"] not in seen_paths:
            seen_paths.add(f["path"])
            selected.append({
                "path": f["path"],
                "language": f["language"],
                "snippet": f["content"][:max_content_chars],
                "lines": f["lines"],
            })

    return selected[:max_files]
