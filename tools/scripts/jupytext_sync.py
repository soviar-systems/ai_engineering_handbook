#!/usr/bin/env python3
"""
Sync md-ipynb pairs using jupytext.

CLI: uv run tools/scripts/jupytext_sync.py [--test] [--all] file1.md file2.ipynb
  --test: Run in test mode (--to ipynb --test) instead of sync
  --all: Find and process all paired notebooks in the repository
  Exit 0 on success, 1 on failure
"""

import argparse
import subprocess
import sys
from pathlib import Path

from tools.scripts.paths import is_excluded


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync md-ipynb pairs using jupytext")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode (--to ipynb --test) instead of sync",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Find and process all paired notebooks in the repository",
    )
    parser.add_argument("files", nargs="*", help="Files to sync")
    args = parser.parse_args()

    # Determine files to process
    if args.all:
        files_to_process = find_all_paired_notebooks()
        if not files_to_process:
            print("No paired notebooks found.")
            return 0
    else:
        if not args.files:
            return 0

        # Filter to .md/.ipynb files only
        valid_files = [
            f for f in args.files if f.endswith(".md") or f.endswith(".ipynb")
        ]

        # Skip files in excluded directories
        files_to_process = [f for f in valid_files if not is_excluded(f)]

    if not files_to_process:
        return 0

    failed = False
    for file_path in files_to_process:
        path = Path(file_path)
        if not path.exists():
            print(f"Warning: {file_path} does not exist, skipping")
            continue

        if args.test:
            cmd = ["uv", "run", "jupytext", "--to", "ipynb", "--test", file_path]
        else:
            cmd = ["uv", "run", "jupytext", "--sync", file_path]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"FAIL: {file_path}")
            if result.stderr:
                print(result.stderr)
            failed = True
        else:
            if result.stdout:
                print(result.stdout.strip())

    return 1 if failed else 0


def find_all_paired_notebooks(root: Path | None = None) -> list[str]:
    """Find all .md files that have a paired .ipynb file."""
    if root is None:
        root = Path.cwd()

    paired_files = []
    for md_file in root.rglob("*.md"):
        md_str = str(md_file)
        # Skip excluded directories
        if is_excluded(md_str):
            continue
        # Check if paired .ipynb exists
        ipynb_file = md_file.with_suffix(".ipynb")
        if ipynb_file.exists():
            paired_files.append(md_str)

    return sorted(paired_files)


if __name__ == "__main__":
    sys.exit(main())
