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

    # --- Jupytext Sync Subcommand ---
    jupytext_sync_parser = subparsers.add_parser(
        "jupytext-sync", help="Sync or Verify Jupytext pairs."
    )
    jupytext_sync_parser.add_argument(
        "--test",
        action="store_true",
        help="Run jupytext --test to verify content synchronization.",
    )
    jupytext_sync_parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Files or directories to process (default: root).",
    )

    # --- Jupytext Verify Pair Subcommand (Add this section) ---
    # Used by pre-commit to check Git staging/index states
    jupytext_verify_pair_parser = subparsers.add_parser(
        "jupytext-verify-pair", help="Verify Jupytext pair integrity."
    )
    jupytext_verify_pair_parser.add_argument(
        "paths", nargs="*", default=["."], help="Files to verify."
    )

    # --- Check Broken Markdown Links Subcommand ---
    links_parser = subparsers.add_parser(
        "check-broken-links", help="Check for broken Markdown links."
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

    if args.command == "jupytext-sync":
        # if --test is passed, run 'test' mode
        # If not passed, run 'sync' (fix) mode
        success = jupytext_sync.run(args.paths, test_only=args.test)

    elif args.command == "jupytext-verify-pair":
        success = jupytext_verify_pair.run(args.paths)

    elif args.command == "check-broken-links":
        success = check_broken_links.run(args.paths)

    # Exit Code Propagation
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
