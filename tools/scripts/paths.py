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
