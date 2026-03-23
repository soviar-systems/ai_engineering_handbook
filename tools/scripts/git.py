"""
Shared git utilities for validation scripts.

Scope: repo root detection and staged file queries.
Does NOT contain validation logic — pure git operations.

Public interface:
    detect_repo_root() — resolve repository root via git, with __file__ fallback
    get_staged_files() — list of files in the git staging area

Dependencies:
    - git CLI (subprocess calls)

Key design decisions:
    - detect_repo_root() uses git rev-parse with Path(__file__) fallback,
      matching CLAUDE.md convention
    - get_staged_files() returns set[str] of repo-relative paths
    - On vadocs extraction: becomes vadocs.git or vadocs.vcs module
"""

import subprocess
from pathlib import Path


def detect_repo_root() -> Path:
    """Detect repository root via git, with __file__ fallback."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip()).resolve()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path(__file__).resolve().parent.parent.parent


def get_staged_files() -> set[str]:
    """Get repo-relative paths of staged files from git."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )
        return {line.strip() for line in result.stdout.splitlines() if line.strip()}
    except subprocess.CalledProcessError:
        return set()
