import argparse
import sys
from typing import List, Optional

from tools.scripts.hooks.check_broken_links import check_broken_links

# Import the hooks
from tools.scripts.hooks.jupytext_sync import jupytext_sync
from tools.scripts.hooks.jupytext_verify_pair import jupytext_verify_pair


def main(argv: Optional[List[str]] = None):
    parser = argparse.ArgumentParser(
        description="Toolkit CLI: Orchestrating Notebook Integrity & Maintenance."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- Sync Subcommand ---
    sync_parser = subparsers.add_parser("sync", help="Sync or Verify Jupytext pairs.")
    sync_parser.add_argument(
        "--check",
        action="store_true",
        help="CI Mode: Verify integrity without modifying files.",
    )
    sync_parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Files or directories to process (default: root).",
    )

    # --- Links Subcommand ---
    links_parser = subparsers.add_parser(
        "links", help="Check for broken Markdown links."
    )
    links_parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Files or directories to scan (default: root).",
    )

    args = parser.parse_args(argv)

    # Routing Logic
    success = False

    if args.command == "sync":
        if args.check:
            # CI Mode: Verify
            success = jupytext_verify_pair.run(args.paths)
        else:
            # Local Mode: Fix/Sync
            success = jupytext_sync.run(args.paths)

    elif args.command == "links":
        success = check_broken_links.run(args.paths)

    # Exit Code Propagation
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
