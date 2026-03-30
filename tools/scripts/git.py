"""
Shared git utilities for validation scripts.

Scope: repo root detection, staged file queries, and historical file discovery.
Does NOT contain validation logic — pure git operations.

Public interface:
    detect_repo_root() — resolve repository root via git, with __file__ fallback
    get_staged_files() — list of files in the git staging area
    get_historical_paths(pattern) — all paths that ever matched a glob in git history

Dependencies:
    - git CLI (subprocess calls)

Key design decisions:
    - detect_repo_root() uses git rev-parse with Path(__file__) fallback,
      matching CLAUDE.md convention
    - get_staged_files() returns set[str] of repo-relative paths
    - get_historical_paths() uses git log --diff-filter=A to find all files
      ever added, including deleted ones (needed because evidence sources
      are deleted after extraction — filesystem alone misses retired IDs)
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


def get_historical_paths(directory: str) -> set[str]:
    """Get all repo-relative paths that ever existed in a directory.

    Scans full git history via `git log --name-only`, filters to the
    given directory, and deduplicates. Includes files that were later
    deleted (e.g., evidence sources removed after extraction).

    Args:
        directory: Repo-relative directory path (e.g., "architecture/evidence/sources/").
                   Trailing slash is normalized.

    Returns:
        Set of repo-relative file paths (e.g., {"architecture/evidence/sources/S-26001_foo.md"}).
        Empty set if git is unavailable or directory never existed.
    """
    directory = directory.rstrip("/") + "/"
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--name-only", "--", directory],
            capture_output=True,
            text=True,
            check=True,
        )
        return {
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip().startswith(directory)
        }
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()
