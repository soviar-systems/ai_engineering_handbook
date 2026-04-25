#!/usr/bin/env python3
"""
Token Size Automation Utility.

Automates the calculation and update of the 'options.token_size' field in
YAML frontmatter for governed files. This eliminates manual entry errors
and prevents pre-commit hook failures caused by outdated token counts.

RATIONALE:
    LLM context window management requires accurate token counts of the
    actual artifacts being loaded. Using 'tiktoken' with the 'cl100k_base'
    encoding provides the industry standard for modern production-grade
    LLMs (GPT-4, etc.).

CONTRACT:
    - The utility only processes files with a valid YAML frontmatter block
      delimited by '---' at the start of the file.
    - Token counting is performed on the FULL file content (frontmatter + body),
      as this represents the actual bytes transferred to the LLM.
    - The 'options' field must be a dictionary. If it is missing or is a
      scalar, it is corrected to a dictionary to allow token_size insertion.
    - File body and '---' delimiters are preserved exactly.
    - YAML is dumped with 'default_flow_style=False' and 'sort_keys=False'
      to maintain human readability and avoid unstable diffs.
    - Malformed YAML is handled gracefully; the file is skipped without
      crashing the script.

Dependencies:
    - tiktoken (for accurate tokenization)
    - PyYAML (for frontmatter manipulation)
    - tools/scripts/git.py (to detect repository root)
    - tools/scripts/paths.py (to respect excluded directories)
"""

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Any

import tiktoken
import yaml

from tools.scripts.git import detect_repo_root
from tools.scripts.paths import VALIDATION_EXCLUDE_DIRS

# Setup logging
logger = logging.getLogger(__name__)

# Matches YAML frontmatter between --- fences at the start of a file.
# Consistent with check_frontmatter.py for structural alignment.
# We use a non-greedy match for the content and ensure the closing delimiter
# is followed by a newline to confirm it's on its own line.
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n([\s\S]*?)---\s*\n", re.DOTALL)

# ======================
# Main
# ======================

def main(argv: list[str] | None = None) -> int:
    """CLI entry point for token count automation.

    Args:
        argv: Command line arguments.

    Returns:
        0 on success, 1 on critical failure.
    """
    parser = argparse.ArgumentParser(
        description="Automate token_size updates in YAML frontmatter."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files or directories to update. Defaults to repo root.",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        choices=["md", "ipynb"],
        default="md",
        help="File extension to scan for (default: md).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log the changes that would be made without actually writing to disk.",
    )
    parser.add_argument(
        "--log-level",
        dest="log_level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO).",
    )
    args = parser.parse_args(argv)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s: %(message)s",
        stream=sys.stdout
    )

    # Resolve root and input paths
    repo_root = detect_repo_root()
    input_paths = [Path(p) for p in args.paths] if args.paths else [repo_root]
    files = scan_paths(input_paths, fmt=args.fmt)

    # Load governed extensions from hub config to filter files.
    # This ensures we only touch files intended to be governed.
    try:
        from tools.scripts.paths import get_config_path
        hub_path = get_config_path(repo_root)
        import json
        hub_config = json.loads(hub_path.read_text(encoding="utf-8"))
        governed_exts = hub_config.get("governed_extensions", [])
    except Exception as e:
        logger.error(f"Failed to load governance config: {e}")
        return 1

    updated_count = 0
    skipped_count = 0

    for file_path in files:
        if file_path.suffix not in governed_exts:
            continue

        if update_file_tokens(file_path, dry_run=args.dry_run):
            logger.info(f"Updated {file_path}")
            updated_count += 1
        else:
            skipped_count += 1
    logger.info(f"Finished. Updated: {updated_count}, Skipped: {skipped_count}")
    return 0

# ======================
# Core Logic
# ======================

def update_token_counts(root: Path, paths: list[Path], dry_run: bool = False) -> None:
    """Wrapper for updating multiple files.

    Args:
        root: The repository root (used for config discovery).
        paths: Input files or directories to update.
        dry_run: If True, log changes without writing to disk.
    """
    # Resolve input paths to actual files
    files = scan_paths(paths)

    for file_path in files:
        update_file_tokens(file_path, dry_run=dry_run)

def calculate_tokens(text: str) -> int:
    """Calculate token count using cl100k_base encoding.

    Returns:
        The number of tokens in the provided text.
    """
    # cl100k_base is the standard for current production-grade LLMs.
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def update_file_tokens(file_path: Path, dry_run: bool = False) -> bool:
    """Update the token_size field in a file's frontmatter.

    Args:
        file_path: Path to the file to update.
        dry_run: If True, calculate and log changes but do not write to disk.

    Returns:
        True if the file was updated (or would be updated in dry run),
        False if it was skipped.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        match = FRONTMATTER_PATTERN.match(content)
        if not match:
            msg = f"[{file_path.name}] No frontmatter match found. Content start: {repr(content[:20])}..."
            logger.debug(msg)
            return False

        fm_text = match.group(1)
        body = content[match.end():]
        msg = f"[{file_path.name}] Found frontmatter. Length: {len(fm_text)} chars"
        logger.debug(msg)

        # Parse frontmatter.
        # Contract: Malformed YAML must not crash the script.
        try:
            fm = yaml.safe_load(fm_text)
        except yaml.YAMLError as e:
            msg = f"[{file_path.name}] Malformed YAML frontmatter: {e}"
            logger.warning(msg)
            return False

        # Ensure frontmatter is a dictionary (handle empty files or --- \n ---)
        if fm is None:
            msg = f"[{file_path.name}] Frontmatter is empty (None), initializing as dict"
            logger.debug(msg)
            fm = {}
        elif not isinstance(fm, dict):
            # Adversary: frontmatter is a scalar (e.g. "--- \n hello \n ---")
            # Recover by wrapping it or starting fresh to allow governance.
            msg = f"[{file_path.name}] Frontmatter is {type(fm).__name__} instead of dict, recovering..."
            logger.debug(msg)
            fm = {"original_content": fm}

        # Ensure 'options' is a dictionary for token_size insertion.
        # Contract: Recover if options is missing or is a scalar (e.g. options: null)
        if "options" not in fm or not isinstance(fm["options"], dict):
            msg = f"[{file_path.name}] 'options' field missing or not a dict, initializing..."
            logger.debug(msg)
            fm["options"] = {}

        # Calculate tokens of the WHOLE file.
        # This ensures the value represents the actual cost of loading the
        # file into context, including the governance overhead.
        new_size = calculate_tokens(content)

        # Only write if the value has actually changed to avoid unnecessary IO/git churn
        current_size = fm["options"].get("token_size")
        if current_size == new_size:
            msg = f"[{file_path.name}] Token size already correct ({new_size}). Skipping write."
            logger.debug(msg)
            return False

        msg = f"[{file_path.name}] Updating token_size: {current_size} -> {new_size}"
        logger.debug(msg)
        fm["options"]["token_size"] = new_size

        if dry_run:
            msg = f"[{file_path.name}] Dry run: would have updated token_size to {new_size}"
            logger.info(msg)
            return True

        # Dump YAML.
        # default_flow_style=False: keeps it readable (block style), preventing
        # the serializer from converting dicts to [a, b] flow style.
        # sort_keys=False: preserves the author's original field order.
        new_fm_text = yaml.dump(fm, default_flow_style=False, sort_keys=False).strip()

        # Reconstruct the file.
        # Use a single write to maintain atomicity.
        # Explicitly ensure newlines around fences to satisfy FRONTMATTER_PATTERN.
        file_path.write_text(f"---\n{new_fm_text}\n---\n\n{body}", encoding="utf-8")
        return True
    except Exception as e:
        msg = f"Unexpected error updating {file_path}: {e}"
        logger.error(msg, exc_info=True)
        return False

# ======================
# Discovery
# ======================

def scan_paths(paths: list[Path], fmt: str = "md") -> list[Path]:
    """Resolve input paths to a list of files matching the format.

    Args:
        paths: Input files or directories.
        fmt: File extension to filter for.

    Returns:
        List of absolute Paths to candidates.
    """
    extension = f".{fmt}"
    files: list[Path] = []

    for path in paths:
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            for child in sorted(path.rglob(f"*{extension}")):
                # Respect global validation exclusions (e.g. .git, .venv)
                if any(part in VALIDATION_EXCLUDE_DIRS for part in child.parts):
                    continue
                files.append(child)

    return files

if __name__ == "__main__":
    sys.exit(main())
