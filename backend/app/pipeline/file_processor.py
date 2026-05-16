from pathlib import Path
from typing import List, Dict, Any, Optional
from pygments.lexers import get_lexer_for_filename, ClassNotFound
import structlog

logger = structlog.get_logger()

IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", "coverage", ".pytest_cache", ".mypy_cache",
}

TEXT_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".cpp",
    ".c", ".h", ".cs", ".rb", ".php", ".swift", ".kt", ".scala", ".r",
    ".md", ".txt", ".yaml", ".yml", ".json", ".toml", ".ini", ".cfg",
    ".sh", ".bash", ".zsh", ".dockerfile", ".sql", ".html", ".css",
    ".scss", ".env.example",
}

MAX_FILE_SIZE_BYTES = 512 * 1024  # 512 KB per file
SNIPPET_CHARS = 300


def collect_files(repo_path: Path) -> List[Dict[str, Any]]:
    """Walk the repository and collect text files with their content.

    Returns a list of dicts with keys:
        path, language, lines, size_bytes, content, snippet
    """
    files = []

    for file_path in repo_path.rglob("*"):
        if file_path.is_dir():
            continue
        # Skip ignored directory trees
        if any(part in IGNORE_DIRS for part in file_path.parts):
            continue
        if file_path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
            logger.debug("Skipping large file", path=str(file_path))
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            relative_path = str(file_path.relative_to(repo_path))
            language = _detect_language(file_path)
            line_count = content.count("\n") + 1

            files.append({
                "path": relative_path,
                "content": content,
                "language": language,
                "size_bytes": file_path.stat().st_size,
                "lines": line_count,
                "snippet": content[:SNIPPET_CHARS],
            })
        except Exception as e:
            logger.warning("Failed to read file", path=str(file_path), error=str(e))

    return files


def _detect_language(file_path: Path) -> str:
    try:
        lexer = get_lexer_for_filename(file_path.name)
        return lexer.name
    except ClassNotFound:
        return "Unknown"


def extract_readme(files: List[Dict[str, Any]]) -> Optional[str]:
    """Find and return README content from the collected files list.

    Checks for README.md, README.rst, README.txt, and README (no extension).
    Returns None if not found (rather than empty string) to allow callers to
    distinguish "no readme" from "empty readme".
    """
    priority_names = ("readme.md", "readme.rst", "readme.txt", "readme")
    # Build a lookup keyed by lower-cased basename so we can honour priority order
    readme_map: Dict[str, str] = {}
    for f in files:
        basename = f["path"].split("/")[-1].lower()
        if basename in priority_names and basename not in readme_map:
            readme_map[basename] = f["content"]

    for name in priority_names:
        if name in readme_map:
            return readme_map[name]

    return None


def build_file_tree(repo_path: Path, max_depth: int = 8) -> str:
    """Return a text tree representation of the repository.

    Ignored directories (node_modules, .git, etc.) are skipped.
    The output resembles the Unix `tree` command.
    """
    lines: List[str] = []

    def _walk(path: Path, prefix: str, depth: int) -> None:
        if depth > max_depth:
            return

        try:
            entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except PermissionError:
            return

        visible = [e for e in entries if e.name not in IGNORE_DIRS]
        for i, entry in enumerate(visible):
            connector = "└── " if i == len(visible) - 1 else "├── "
            lines.append(f"{prefix}{connector}{entry.name}")
            if entry.is_dir():
                extension = "    " if i == len(visible) - 1 else "│   "
                _walk(entry, prefix + extension, depth + 1)

    lines.append(repo_path.name)
    _walk(repo_path, "", 1)
    return "\n".join(lines)


def detect_project_type(files: List[Dict[str, Any]]) -> str:
    """Detect the primary framework/project type from file patterns.

    Returns a human-readable string such as "Python/FastAPI", "Node.js/React",
    "Go module", etc.  Falls back to "Unknown" if nothing matches.
    """
    paths = {f["path"].lower() for f in files}
    filenames = {p.split("/")[-1] for p in paths}

    # ---------- Python frameworks ----------
    if "requirements.txt" in filenames or "pyproject.toml" in filenames or "setup.py" in filenames:
        content_all = " ".join(f["content"].lower() for f in files if f["language"] == "Python")
        if "fastapi" in content_all:
            return "Python/FastAPI"
        if "django" in content_all:
            return "Python/Django"
        if "flask" in content_all:
            return "Python/Flask"
        return "Python"

    # ---------- JavaScript / TypeScript frameworks ----------
    if "package.json" in filenames:
        pkg_content = ""
        for f in files:
            if f["path"].lower().endswith("package.json") and "/" not in f["path"].replace("package.json", "").rstrip("/"):
                pkg_content = f["content"].lower()
                break
        if '"next"' in pkg_content or '"next.js"' in pkg_content:
            return "Node.js/Next.js"
        if '"react"' in pkg_content:
            return "Node.js/React"
        if '"vue"' in pkg_content:
            return "Node.js/Vue"
        if '"express"' in pkg_content:
            return "Node.js/Express"
        if '"angular"' in pkg_content or '"@angular/core"' in pkg_content:
            return "Node.js/Angular"
        return "Node.js"

    # ---------- Go ----------
    if "go.mod" in filenames:
        return "Go module"

    # ---------- Rust ----------
    if "cargo.toml" in filenames:
        return "Rust/Cargo"

    # ---------- Java / JVM ----------
    if "pom.xml" in filenames:
        return "Java/Maven"
    if "build.gradle" in filenames or "build.gradle.kts" in filenames:
        return "Java/Gradle"

    # ---------- Ruby ----------
    if "gemfile" in filenames or "gemfile.lock" in filenames:
        return "Ruby"

    # ---------- PHP ----------
    if "composer.json" in filenames:
        return "PHP/Composer"

    # ---------- Dockerfile-only / generic ----------
    if "dockerfile" in filenames or any("docker-compose" in p for p in paths):
        return "Docker/Containerised app"

    return "Unknown"


def get_language_stats(files: List[Dict[str, Any]]) -> Dict[str, int]:
    """Return a dict mapping language name -> total line count, sorted descending."""
    stats: Dict[str, int] = {}
    for f in files:
        lang = f["language"]
        stats[lang] = stats.get(lang, 0) + f["lines"]
    return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))
