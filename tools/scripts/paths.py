"""
Centralized path configurations for the toolkit.
"""

# Directories that should always be excluded from notebook/link scans
DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".pytest_cache",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "build",
    "_build",
    "dist",
    "in_progress",
    "pr/",
    "architecture",
}

DEFAULT_EXCLUDE_FILES = [".aider.chat.history.md"]


def is_ignored_dir(path: str) -> bool:
    """Check if a given path string contains any excluded directory segments."""
    for p in DEFAULT_EXCLUDE_DIRS:
        if p in path:
            return True
    return False
