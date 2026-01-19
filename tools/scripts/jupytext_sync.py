#!/usr/bin/env python3
"""
Sync md-ipynb pairs using jupytext.

CLI: uv run tools/scripts/jupytext_sync.py [--test] file1.md file2.ipynb
  --test: Run in test mode (--to ipynb --test) instead of sync
  Exit 0 on success, 1 on failure
"""
import argparse
import subprocess
import sys
from pathlib import Path

from paths import is_excluded


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync md-ipynb pairs using jupytext")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode (--to ipynb --test) instead of sync",
    )
    parser.add_argument("files", nargs="*", help="Files to sync")
    args = parser.parse_args()

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


if __name__ == "__main__":
    sys.exit(main())
