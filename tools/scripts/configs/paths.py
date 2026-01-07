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
    "dist",
}

def is_ignored(path: str) -> bool:
    """Check if a given path string contains any excluded directory segments."""
    parts = path.split("/")
    return any(ignored in parts for ignored in EXCLUDED_DIRS)
