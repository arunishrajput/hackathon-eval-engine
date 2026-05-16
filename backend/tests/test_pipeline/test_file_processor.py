"""
Unit tests for app.pipeline.file_processor.

Tests:
  - collect_files returns a list of dicts with required keys
  - collect_files skips ignored directories (node_modules, __pycache__, etc.)
  - collect_files skips files with unsupported extensions
  - extract_readme finds README.md content
  - extract_readme returns None when no README is present
  - extract_readme respects priority order (README.md > README.rst > README.txt)
  - detect_project_type returns 'Node.js' (or more specific) when package.json present
  - detect_project_type returns correct type for Python, Go, Rust
  - detect_project_type returns 'Unknown' for unrecognised projects
  - build_file_tree returns a string containing directory/file names
  - get_language_stats aggregates line counts by language
"""

import pytest
import os
from pathlib import Path
import tempfile

from app.pipeline.file_processor import (
    collect_files,
    extract_readme,
    detect_project_type,
    build_file_tree,
    get_language_stats,
)


# ---------------------------------------------------------------------------
# Fixture: temporary repository with controlled structure
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    """
    Create a minimal fake repository:

    my_project/
    ├── README.md
    ├── main.py
    ├── utils.py
    ├── package.json         (used by Node.js detection tests — harmless here)
    ├── node_modules/
    │   └── lodash/
    │       └── index.js     (should be ignored)
    ├── __pycache__/
    │   └── main.cpython-311.pyc  (ignored — wrong extension too)
    └── data/
        └── notes.txt
    """
    root = tmp_path / "my_project"
    root.mkdir()

    (root / "README.md").write_text("# My Project\nThis is a test readme.", encoding="utf-8")
    (root / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (root / "utils.py").write_text("def util(): pass\n", encoding="utf-8")

    # Node.js marker (plain — no react/next/express in content, so → 'Node.js')
    (root / "package.json").write_text('{"name": "my-app", "version": "1.0.0"}', encoding="utf-8")

    # Ignored dirs
    node_mod_dir = root / "node_modules" / "lodash"
    node_mod_dir.mkdir(parents=True)
    (node_mod_dir / "index.js").write_text("module.exports = {};", encoding="utf-8")

    pycache_dir = root / "__pycache__"
    pycache_dir.mkdir()
    (pycache_dir / "main.cpython-311.pyc").write_bytes(b"\x00\x01\x02")

    data_dir = root / "data"
    data_dir.mkdir()
    (data_dir / "notes.txt").write_text("Some notes here.", encoding="utf-8")

    return root


@pytest.fixture
def python_repo(tmp_path: Path) -> Path:
    """A minimal Python (FastAPI) repo."""
    root = tmp_path / "py_project"
    root.mkdir()
    (root / "requirements.txt").write_text("fastapi\nuvicorn\n", encoding="utf-8")
    (root / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n", encoding="utf-8")
    return root


@pytest.fixture
def go_repo(tmp_path: Path) -> Path:
    """A minimal Go module repo.

    Note: go.mod has no extension so collect_files skips it (not in
    TEXT_EXTENSIONS). The fixture is kept for completeness but detection tests
    that need it pass a manually-constructed files list instead.
    """
    root = tmp_path / "go_project"
    root.mkdir()
    (root / "go.mod").write_text("module example.com/myapp\n\ngo 1.21\n", encoding="utf-8")
    (root / "main.go").write_text('package main\nfunc main() {}\n', encoding="utf-8")
    return root


@pytest.fixture
def rust_repo(tmp_path: Path) -> Path:
    """A minimal Rust / Cargo repo."""
    root = tmp_path / "rust_project"
    root.mkdir()
    (root / "Cargo.toml").write_text('[package]\nname = "myapp"\nversion = "0.1.0"\n', encoding="utf-8")
    src = root / "src"
    src.mkdir()
    (src / "main.rs").write_text('fn main() {}\n', encoding="utf-8")
    return root


@pytest.fixture
def node_react_repo(tmp_path: Path) -> Path:
    """A Node.js/React repo."""
    root = tmp_path / "react_project"
    root.mkdir()
    (root / "package.json").write_text(
        '{"name": "my-app", "dependencies": {"react": "^18.0.0"}}',
        encoding="utf-8",
    )
    return root


@pytest.fixture
def node_next_repo(tmp_path: Path) -> Path:
    """A Node.js/Next.js repo."""
    root = tmp_path / "next_project"
    root.mkdir()
    (root / "package.json").write_text(
        '{"name": "my-app", "dependencies": {"next": "^14.0.0"}}',
        encoding="utf-8",
    )
    return root


# ---------------------------------------------------------------------------
# collect_files
# ---------------------------------------------------------------------------

def test_collect_files_returns_list(temp_repo: Path):
    """collect_files should return a list."""
    files = collect_files(temp_repo)
    assert isinstance(files, list)


def test_collect_files_required_keys(temp_repo: Path):
    """Every entry must contain path, language, content, lines, size_bytes, snippet."""
    required_keys = {"path", "language", "content", "lines", "size_bytes", "snippet"}
    files = collect_files(temp_repo)
    assert len(files) > 0
    for entry in files:
        assert required_keys.issubset(entry.keys()), (
            f"Entry missing keys: {required_keys - entry.keys()}"
        )


def test_collect_files_finds_python_files(temp_repo: Path):
    """Python source files (*.py) should be included."""
    files = collect_files(temp_repo)
    paths = {f["path"] for f in files}
    assert "main.py" in paths
    assert "utils.py" in paths


def test_collect_files_finds_readme(temp_repo: Path):
    """README.md should be included in the collected files."""
    files = collect_files(temp_repo)
    paths = {f["path"] for f in files}
    assert "README.md" in paths


def test_collect_files_skips_node_modules(temp_repo: Path):
    """Files inside node_modules/ must be excluded."""
    files = collect_files(temp_repo)
    paths = {f["path"] for f in files}
    assert all("node_modules" not in p for p in paths)


def test_collect_files_skips_pycache(temp_repo: Path):
    """Files inside __pycache__/ must be excluded."""
    files = collect_files(temp_repo)
    paths = {f["path"] for f in files}
    assert all("__pycache__" not in p for p in paths)


def test_collect_files_skips_binary_extensions(temp_repo: Path):
    """Files with unsupported extensions (e.g. .pyc) must not appear."""
    files = collect_files(temp_repo)
    paths = {f["path"] for f in files}
    assert all(not p.endswith(".pyc") for p in paths)


def test_collect_files_content_is_string(temp_repo: Path):
    """The 'content' field must be a string."""
    files = collect_files(temp_repo)
    for entry in files:
        assert isinstance(entry["content"], str)


def test_collect_files_lines_is_positive(temp_repo: Path):
    """'lines' must be a positive integer for non-empty files."""
    files = collect_files(temp_repo)
    for entry in files:
        assert isinstance(entry["lines"], int)
        assert entry["lines"] >= 1


def test_collect_files_path_is_relative(temp_repo: Path):
    """Paths should be relative to the repo root, not absolute."""
    files = collect_files(temp_repo)
    for entry in files:
        assert not os.path.isabs(entry["path"]), f"Path is absolute: {entry['path']}"


def test_collect_files_snippet_max_300_chars(temp_repo: Path):
    """The snippet field must be at most 300 characters."""
    files = collect_files(temp_repo)
    for entry in files:
        assert len(entry["snippet"]) <= 300


# ---------------------------------------------------------------------------
# extract_readme
# ---------------------------------------------------------------------------

def test_extract_readme_finds_readme_md(temp_repo: Path):
    """extract_readme should return the content of README.md."""
    files = collect_files(temp_repo)
    content = extract_readme(files)
    assert content is not None
    assert "My Project" in content


def test_extract_readme_returns_none_when_missing():
    """When no README is present extract_readme should return None."""
    files = [
        {"path": "main.py", "content": "print('hi')", "language": "Python",
         "lines": 1, "size_bytes": 12, "snippet": "print('hi')"},
    ]
    result = extract_readme(files)
    assert result is None


def test_extract_readme_prefers_md_over_txt(tmp_path: Path):
    """README.md should be preferred over README.txt."""
    files = [
        {"path": "README.txt", "content": "Text readme", "language": "Text",
         "lines": 1, "size_bytes": 11, "snippet": "Text readme"},
        {"path": "README.md", "content": "# Markdown readme", "language": "Markdown",
         "lines": 1, "size_bytes": 17, "snippet": "# Markdown readme"},
    ]
    result = extract_readme(files)
    assert result == "# Markdown readme"


def test_extract_readme_falls_back_to_rst(tmp_path: Path):
    """When only README.rst exists it should be returned."""
    files = [
        {"path": "README.rst", "content": "RST readme", "language": "RST",
         "lines": 1, "size_bytes": 10, "snippet": "RST readme"},
    ]
    result = extract_readme(files)
    assert result == "RST readme"


def test_extract_readme_case_insensitive_lookup(tmp_path: Path):
    """README.MD (uppercase extension) should be found."""
    # Our function lowercases the basename for lookup
    files = [
        {"path": "README.MD", "content": "Upper ext", "language": "Markdown",
         "lines": 1, "size_bytes": 9, "snippet": "Upper ext"},
    ]
    # Note: the current implementation splits on "/" and lowercases the basename.
    # "README.MD".lower() == "readme.md" which is in priority_names.
    result = extract_readme(files)
    assert result == "Upper ext"


# ---------------------------------------------------------------------------
# detect_project_type
# ---------------------------------------------------------------------------

def test_detect_project_type_node_generic(temp_repo: Path):
    """A plain package.json (no framework-specific deps) → 'Node.js'."""
    files = collect_files(temp_repo)
    project_type = detect_project_type(files)
    assert "Node.js" in project_type


def test_detect_project_type_node_react(node_react_repo: Path):
    """A package.json with 'react' dependency → 'Node.js/React'."""
    files = collect_files(node_react_repo)
    project_type = detect_project_type(files)
    assert project_type == "Node.js/React"


def test_detect_project_type_node_next(node_next_repo: Path):
    """A package.json with 'next' dependency → 'Node.js/Next.js'."""
    files = collect_files(node_next_repo)
    project_type = detect_project_type(files)
    assert project_type == "Node.js/Next.js"


def test_detect_project_type_python_fastapi(python_repo: Path):
    """requirements.txt + FastAPI import → 'Python/FastAPI'."""
    files = collect_files(python_repo)
    project_type = detect_project_type(files)
    assert project_type == "Python/FastAPI"


def test_detect_project_type_go():
    """A go.mod entry in the files list → 'Go module'.

    go.mod has no recognised extension so collect_files skips it.  We
    pass a manually-constructed list to test the detection logic directly.
    """
    files = [
        {
            "path": "go.mod",
            "content": "module example.com/myapp\n\ngo 1.21\n",
            "language": "Unknown",
            "lines": 3,
            "size_bytes": 38,
            "snippet": "module example.com/myapp",
        },
        {
            "path": "main.go",
            "content": "package main\nfunc main() {}\n",
            "language": "Go",
            "lines": 2,
            "size_bytes": 29,
            "snippet": "package main",
        },
    ]
    project_type = detect_project_type(files)
    assert project_type == "Go module"


def test_detect_project_type_rust(rust_repo: Path):
    """A Cargo.toml file → 'Rust/Cargo'."""
    files = collect_files(rust_repo)
    project_type = detect_project_type(files)
    assert project_type == "Rust/Cargo"


def test_detect_project_type_unknown(tmp_path: Path):
    """A repo with no recognisable marker files → 'Unknown'."""
    root = tmp_path / "mystery_project"
    root.mkdir()
    (root / "data.csv").write_text("col1,col2\n1,2\n")

    # data.csv is not in TEXT_EXTENSIONS, so collect_files returns empty → Unknown
    # Alternatively, just pass an empty list:
    result = detect_project_type([])
    assert result == "Unknown"


# ---------------------------------------------------------------------------
# build_file_tree
# ---------------------------------------------------------------------------

def test_build_file_tree_returns_string(temp_repo: Path):
    """build_file_tree should return a non-empty string."""
    tree = build_file_tree(temp_repo)
    assert isinstance(tree, str)
    assert len(tree) > 0


def test_build_file_tree_contains_root_name(temp_repo: Path):
    """The root directory name should appear in the tree output."""
    tree = build_file_tree(temp_repo)
    assert temp_repo.name in tree


def test_build_file_tree_contains_file_names(temp_repo: Path):
    """Known files like 'main.py' and 'README.md' should appear in the tree."""
    tree = build_file_tree(temp_repo)
    assert "main.py" in tree
    assert "README.md" in tree


def test_build_file_tree_skips_ignored_dirs(temp_repo: Path):
    """node_modules should not appear in the tree output."""
    tree = build_file_tree(temp_repo)
    assert "node_modules" not in tree


def test_build_file_tree_contains_tree_connectors(temp_repo: Path):
    """The tree output should use ├── or └── connectors."""
    tree = build_file_tree(temp_repo)
    assert "──" in tree


# ---------------------------------------------------------------------------
# get_language_stats
# ---------------------------------------------------------------------------

def test_get_language_stats_returns_dict(temp_repo: Path):
    """get_language_stats should return a dict."""
    files = collect_files(temp_repo)
    stats = get_language_stats(files)
    assert isinstance(stats, dict)


def test_get_language_stats_counts_lines(temp_repo: Path):
    """Python language count should be > 0 given the .py files."""
    files = collect_files(temp_repo)
    stats = get_language_stats(files)
    # There should be Python entries from main.py and utils.py
    assert "Python" in stats
    assert stats["Python"] >= 2


def test_get_language_stats_sorted_descending(temp_repo: Path):
    """Languages should be ordered by total line count descending."""
    files = collect_files(temp_repo)
    stats = get_language_stats(files)
    values = list(stats.values())
    assert values == sorted(values, reverse=True)


def test_get_language_stats_empty_files():
    """An empty file list returns an empty dict."""
    stats = get_language_stats([])
    assert stats == {}
