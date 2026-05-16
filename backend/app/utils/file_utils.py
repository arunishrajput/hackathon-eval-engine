from pathlib import Path
from typing import Optional
import hashlib


def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Compute hash of a file for deduplication."""
    h = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_read_text(file_path: Path, max_bytes: int = 512 * 1024) -> Optional[str]:
    """Safely read a text file with size limit and encoding fallback."""
    try:
        size = file_path.stat().st_size
        if size > max_bytes:
            return None
        return file_path.read_text(encoding="utf-8", errors="replace")
    except (OSError, PermissionError):
        return None


def get_extension(file_path: Path) -> str:
    return file_path.suffix.lower()


def is_binary_file(file_path: Path) -> bool:
    """Heuristic check: read a small chunk and check for null bytes."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
        return b"\x00" in chunk
    except (OSError, PermissionError):
        return True
