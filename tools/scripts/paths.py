"""
Centralized path configurations for the toolkit.
"""

# Directories that should always be excluded from notebook/link scans
BROKEN_LINKS_EXCLUDE_DIRS = {
    ".git",
    ".pytest_cache",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "build",
    "_build",
    "dist",
    "misc/in_progress",
    "misc/pr",
}

# Strings that should be excluded from link validation
BROKEN_LINKS_EXCLUDE_LINK_STRINGS = {
    "path/to/file.md",
    "./intro/",
    "valid.md", # Added for test_validate_link_with_exclusions
}

BROKEN_LINKS_EXCLUDE_FILES = [".aider.chat.history.md"]

# Reuse for jupytext - same directories should be excluded
JUPYTEXT_EXCLUDE_DIRS = BROKEN_LINKS_EXCLUDE_DIRS

# API key scanning configuration - placeholder indicators for false positive detection
API_KEYS_PLACEHOLDER_INDICATORS = {
    "[", "<", "${", "{{",
    "example", "placeholder", "your_", "test_", "fake_",
}


def is_excluded(path: str) -> bool:
    """Check if path should be excluded from jupytext processing."""
    return any(excl in path for excl in JUPYTEXT_EXCLUDE_DIRS)
