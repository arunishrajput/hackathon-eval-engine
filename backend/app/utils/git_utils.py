from pathlib import Path
from typing import Optional, Dict, Any
from git import Repo, InvalidGitRepositoryError
import structlog

logger = structlog.get_logger()


def get_repo_metadata(repo_path: Path) -> Dict[str, Any]:
    """Extract metadata from a cloned git repository."""
    try:
        repo = Repo(str(repo_path))
        commits = list(repo.iter_commits(max_count=100))
        authors = list({c.author.name for c in commits})

        return {
            "default_branch": repo.active_branch.name if not repo.head.is_detached else "detached",
            "total_commits": len(commits),
            "unique_authors": authors,
            "latest_commit_sha": commits[0].hexsha[:8] if commits else None,
            "latest_commit_date": commits[0].committed_datetime.isoformat() if commits else None,
            "latest_commit_message": commits[0].message.strip()[:100] if commits else None,
        }
    except InvalidGitRepositoryError:
        return {}
    except Exception as e:
        logger.warning("Failed to extract git metadata", error=str(e))
        return {}


def is_valid_git_url(url: str) -> bool:
    """Basic validation that a URL looks like a git repository."""
    valid_prefixes = ("https://github.com/", "https://gitlab.com/", "https://bitbucket.org/")
    return any(url.startswith(p) for p in valid_prefixes)
