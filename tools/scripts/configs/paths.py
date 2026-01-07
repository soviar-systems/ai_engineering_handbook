"""
Centralized path configurations for the toolkit.
"""

# Directories that should always be excluded from notebook/link scans
EXCLUDED_DIRS = {
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


def is_ignored(path: str) -> bool:
    """Check if a given path string contains any excluded directory segments."""
    for p in EXCLUDED_DIRS:
        if p in path:
            return True
    return False
