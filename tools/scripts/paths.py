"""
Centralized path configurations and discovery utilities for the toolkit.

Scope: shared constants (exclusion lists) and config discovery functions
used by validation scripts. Does NOT contain validation logic.

Public interface:
    vadocs_config_dir(repo_root) — resolve .vadocs/ path from pyproject.toml
    VALIDATION_EXCLUDE_DIRS — directories excluded from all validation
    BROKEN_LINKS_EXCLUDE_LINK_STRINGS — strings excluded from link validation
    BROKEN_LINKS_EXCLUDE_FILES — files excluded from link validation
    API_KEYS_PLACEHOLDER_INDICATORS — false positive indicators for API key scanning
    API_KEYS_EXCLUDE_FILES — files excluded from API key scanning
    is_excluded(path) — check if path should be excluded from jupytext processing

Dependencies:
    - tomllib (stdlib) for pyproject.toml parsing

Key design decisions:
    - Exclusion constants will migrate to .vadocs/validation/ (tracked in techdebt.md)
    - vadocs_config_dir() reads [tool.vadocs] config_dir from pyproject.toml —
      single entry point for all .vadocs/ config discovery
"""

import tomllib
from pathlib import Path

# pyproject.toml discovery keys — single point of change.
# _TOOL_SECTION is the proto-package identity (like __tool_name__ in mature packages).
# On vadocs extraction: move to vadocs/__init__.py as __tool_name__.
_TOOL_SECTION = "vadocs"
_CONFIG_DIR_KEY = "config_dir"

# Internal directory conventions
_HUB_CONFIG_NAME = "conf.json"
_TYPES_DIR = "types"
_SPOKE_SUFFIX = ".conf.json"


def get_config_path(repo_root: Path, doc_type: str | None = None) -> Path:
    """Resolve a vadocs config path from pyproject.toml [tool.vadocs].

    Args:
        repo_root: Repository root directory.
        doc_type: Document type name (e.g., "evidence", "adr").
                  If None, returns the hub config path.

    Returns:
        Hub:   <config_dir>/conf.json
        Spoke: <config_dir>/types/<doc_type>.conf.json
    """
    with open(repo_root / "pyproject.toml", "rb") as f:
        config_dir = tomllib.load(f)["tool"][_TOOL_SECTION][_CONFIG_DIR_KEY]
    base = repo_root / config_dir
    if doc_type is None:
        return base / _HUB_CONFIG_NAME
    return base / _TYPES_DIR / f"{doc_type}{_SPOKE_SUFFIX}"


# Directories excluded from all validation scripts (links, jupytext, ADR, etc.)
VALIDATION_EXCLUDE_DIRS = {
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
    "misc",
}

# Strings that should be excluded from link validation
BROKEN_LINKS_EXCLUDE_LINK_STRINGS = {
    "path/to/file.md",
    "path/to/file.ipynb",
    "path/to/adr_26001_slug.md",
    "path/to/adr_26002_slug.md",
    "./intro/",
    "valid.md",  # Added for test_validate_link_with_exclusions
    "repo-root-relative/path",  # Example in architecture_decision_workflow_guide.md
}

BROKEN_LINKS_EXCLUDE_FILES = [".aider.chat.history.md"]


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
    return any(excl in path for excl in VALIDATION_EXCLUDE_DIRS)
