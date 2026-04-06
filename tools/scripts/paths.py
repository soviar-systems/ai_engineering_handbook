"""
Centralized path configurations and discovery utilities for the toolkit.

Scope: shared constants (exclusion lists) and config discovery functions
used by validation scripts. Does NOT contain validation logic.

Public interface:
    get_config_path(repo_root, doc_type) — resolve .vadocs/ config path
    get_external_repo_paths(repo_root) — load external repo directory paths from registry
    VALIDATION_EXCLUDE_DIRS — directories excluded from all validation
    BROKEN_LINKS_EXCLUDE_LINK_STRINGS — strings excluded from link validation
    BROKEN_LINKS_EXCLUDE_FILES — files excluded from link validation
    API_KEYS_PLACEHOLDER_INDICATORS — false positive indicators for API key scanning
    API_KEYS_EXCLUDE_FILES — files excluded from API key scanning
    is_excluded(path) — check if path should be excluded from jupytext processing

Dependencies:
    - json (stdlib) for registry parsing
    - tomllib (stdlib) for pyproject.toml parsing

Key design decisions:
    - External repo exclusion paths live in .vadocs/validation/external-repos.conf.json
      (ADR-26046) and are loaded at import time into VALIDATION_EXCLUDE_DIRS
    - get_config_path() reads [tool.vadocs] config_dir from pyproject.toml —
      single entry point for all .vadocs/ config discovery
"""

import json
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
_EXTERNAL_REPOS_CONFIG = "external-repos.conf.json"
_VALIDATION_DIR = "validation"


def get_config_path(repo_root: Path, doc_type: str | None = None) -> Path:
    """Resolve a vadocs config path from pyproject.toml [tool.vadocs].

    Args:
        repo_root: Repository root directory.
        doc_type: Document type name (e.g., "evidence", "adr").
                  If None, returns the hub config path.
                  Sub-types (e.g., "analysis", "retrospective") are resolved
                  to their parent config (e.g., "evidence") automatically.

    Returns:
        Hub:   <config_dir>/conf.json
        Type:  <config_dir>/types/<doc_type>.conf.json

    Sub-type resolution (TD-005):
        "analysis" → "evidence" (parent config)
        "retrospective" → "evidence" (parent config)
        "source" → "evidence" (parent config)
    """
    with open(repo_root / "pyproject.toml", "rb") as f:
        config_dir = tomllib.load(f)["tool"][_TOOL_SECTION][_CONFIG_DIR_KEY]
    base = repo_root / config_dir
    if doc_type is None:
        return base / _HUB_CONFIG_NAME
    # Sub-type → parent config resolution (TD-005)
    resolved_type = SUBTYPE_PARENT_MAP.get(doc_type, doc_type)
    return base / _TYPES_DIR / f"{resolved_type}{_SPOKE_SUFFIX}"


# Sub-type → parent config mapping for evidence artifacts (TD-005).
# Sub-types are defined under artifact_types in the parent config.
# When resolving config for a sub-type, load the parent config and extract
# the sub-type rules from artifact_types.<sub_type>.
SUBTYPE_PARENT_MAP = {
    "analysis": "evidence",
    "retrospective": "evidence",
    "source": "evidence",
}


def get_external_repo_paths(repo_root: Path) -> set[str]:
    """Load external repo directory paths from the registry.

    Reads .vadocs/validation/external-repos.conf.json (ADR-26046) and returns
    the set of relative paths that must be excluded from validation,
    git tracking, and documentation builds.

    Args:
        repo_root: Repository root directory.

    Returns:
        Set of relative paths (e.g., {"ai_agents/agents_source_code"}).
        Empty set if the registry does not exist yet.
    """
    config = repo_root / ".vadocs" / _VALIDATION_DIR / _EXTERNAL_REPOS_CONFIG
    if not config.exists():
        return set()
    with open(config) as f:
        data = json.load(f)
    return {entry["path"] for entry in data.get("entries", [])}


# Directories excluded from all validation scripts (links, jupytext, ADR, etc.)
# Static entries defined here. External repo paths are loaded from
# .vadocs/validation/external-repos.conf.json (ADR-26046) at import time.
_STATIC_EXCLUDE_DIRS = {
    ".git",
    ".ipynb_checkpoints",
    ".pytest_cache",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "build",
    "_build",
    "misc",
}

# Runtime: merge of static excludes + registry entries.
# This is the set that is_excluded() and all validation scripts check.
_VALIDATION_EXCLUDE_DIRS = _STATIC_EXCLUDE_DIRS | get_external_repo_paths(Path(__file__).resolve().parents[2])

# Public alias — scripts import this.
VALIDATION_EXCLUDE_DIRS = _VALIDATION_EXCLUDE_DIRS

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
    "[",
    "<",
    "${",
    "{{",
    "example",
    "placeholder",
    "your_",
    "test_",
    "fake_",
}

# Files to exclude from API key scanning (contain test keys by design)
API_KEYS_EXCLUDE_FILES = {
    "tools/tests/test_check_api_keys.py",
    "tools/docs/scripts_instructions/check_api_keys_py_script.md",
}


def is_excluded(path: str) -> bool:
    """Check if path should be excluded from jupytext processing."""
    return any(excl in path for excl in VALIDATION_EXCLUDE_DIRS)
