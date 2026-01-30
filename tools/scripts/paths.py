"""
Centralized path configurations for the toolkit.
"""

# Directories that should always be excluded from notebook/link scans
BROKEN_LINKS_EXCLUDE_DIRS = {
    ".git",
    ".ipynb_checkpoints",
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
    "path/to/file.ipynb",
    "path/to/adr_26001_slug.md",
    "path/to/adr_26002_slug.md",
    "./intro/",
    "valid.md",  # Added for test_validate_link_with_exclusions
}

BROKEN_LINKS_EXCLUDE_FILES = [".aider.chat.history.md"]

# Reuse for jupytext - same directories should be excluded
JUPYTEXT_EXCLUDE_DIRS = BROKEN_LINKS_EXCLUDE_DIRS

# API key scanning configuration - placeholder indicators for false positive detection
API_KEYS_PLACEHOLDER_INDICATORS = {
    "[", "<", "${", "{{",
    "example", "placeholder", "your_", "test_", "fake_",
}

# Files to exclude from API key scanning (contain test keys by design)
API_KEYS_EXCLUDE_FILES = {
    "tools/tests/test_check_api_keys.py",
    "tools/docs/scripts_instructions/check_api_keys_py_script.md",
}


def is_excluded(path: str) -> bool:
    """Check if path should be excluded from jupytext processing."""
    return any(excl in path for excl in JUPYTEXT_EXCLUDE_DIRS)
