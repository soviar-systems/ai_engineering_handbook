#!/usr/bin/env python3
"""
Verify that if one file of a pair is staged, the other is too.

CLI: uv run tools/scripts/jupytext_verify_pair.py file1.md file2.ipynb
  Exit 0 if all pairs are properly staged, 1 if any pair is incomplete
"""
import subprocess
import sys
from pathlib import Path

from paths import is_excluded


def get_pair_path(file_path: str) -> str | None:
    """Get the paired file path (.md <-> .ipynb)."""
    path = Path(file_path)
    if path.suffix == ".md":
        return str(path.with_suffix(".ipynb"))
    elif path.suffix == ".ipynb":
        return str(path.with_suffix(".md"))
    return None


def is_staged(file_path: str) -> bool:
    """Check if file is staged in git index."""
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--cached", file_path],
        capture_output=True,
    )
    if result.returncode != 0:
        return False

    # Check if there are staged changes for this file
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", file_path],
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())


def has_unstaged_changes(file_path: str) -> bool:
    """Check if file has unstaged changes."""
    result = subprocess.run(
        ["git", "diff", "--exit-code", file_path],
        capture_output=True,
    )
    return result.returncode != 0


def main() -> int:
    if len(sys.argv) < 2:
        return 0

    files = sys.argv[1:]

    # Filter to .md/.ipynb files only
    valid_files = [
        f for f in files if f.endswith(".md") or f.endswith(".ipynb")
    ]

    # Skip files in excluded directories
    files_to_check = [f for f in valid_files if not is_excluded(f)]

    if not files_to_check:
        return 0

    # Track checked pairs to avoid duplicates
    checked_pairs: set[tuple[str, str]] = set()
    failed = False

    for file_path in files_to_check:
        pair_path = get_pair_path(file_path)
        if pair_path is None:
            continue

        # Create normalized pair key
        pair_key = tuple(sorted([file_path, pair_path]))
        if pair_key in checked_pairs:
            continue
        checked_pairs.add(pair_key)

        # Check if pair file exists
        if not Path(pair_path).exists():
            continue

        file_staged = is_staged(file_path)
        pair_staged = is_staged(pair_path)

        # Neither staged -> OK (skip)
        if not file_staged and not pair_staged:
            continue

        # One staged, other not -> FAIL
        if file_staged and not pair_staged:
            print(f"FAIL: {file_path} is staged but {pair_path} is not")
            failed = True
            continue

        if pair_staged and not file_staged:
            print(f"FAIL: {pair_path} is staged but {file_path} is not")
            failed = True
            continue

        # Both staged - check for unstaged changes
        if has_unstaged_changes(file_path):
            print(f"FAIL: {file_path} has unstaged changes")
            failed = True

        if has_unstaged_changes(pair_path):
            print(f"FAIL: {pair_path} has unstaged changes")
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
