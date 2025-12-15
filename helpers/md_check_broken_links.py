#!/usr/bin/env python3
"""
Script to check broken links in markdown files.

Usage: check_broken_links.py [directory] [file_pattern]

This script is fully SVA (Smallest Viable Architecture) compliant, using only
Python's standard library (pathlib, re, sys, argparse, tempfile) for robust, local-only
link validation with full exclusion capabilities.
"""

import argparse
# import os  <-- REMOVED: No longer needed
import re
import sys
import tempfile
from pathlib import Path
from typing import List

# --- MAIN EXECUTION BLOCK ---


def main():
    """
    Run main function.

    Parses arguments, orchestrates the link checking process, handles file I/O,
    and reports results. All core logic is executed here.
    """
    # 1. Argument Parsing
    parser = argparse.ArgumentParser(
        description="Check for broken links in markdown files (Local Filesystem Only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Example: %(prog)s . "*.md" --exclude-dirs drafts --exclude-files LICENSE.md
Default directory: current directory
Default pattern: *.md""",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to search (default: current directory)",
    )
    parser.add_argument(
        "file_pattern",
        nargs="?",
        default="*.md",
        help="File pattern to match (default: *.md)",
    )
    # Argument for Directory Exclusion
    parser.add_argument(
        "--exclude-dirs",
        nargs="*",
        default=["in_progress", "pr"],
        help="Directory names to exclude from the check (e.g., in_progress drafts temp)",
    )
    # Argument for File Exclusion
    parser.add_argument(
        "--exclude-files",
        nargs="*",
        default=[".aider.chat.history.md"],
        help="Specific file names to exclude from the check (e.g., README.md LICENSE.md)",
    )
    # Argument for Verbose Mode
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Enable verbose mode for more output information.",
    )
    args = parser.parse_args()

    # 2. Setup and Directory Check
    verbose = args.verbose
    # Resolve the search_dir once and use it as the absolute reference point
    search_dir = Path(args.directory).resolve()
    if not search_dir.exists() or not search_dir.is_dir():
        print(f"Error: Directory does not exist: {search_dir}", file=sys.stderr)
        sys.exit(1)

    # Resolve exclusion list paths relative to the search_dir
    exclude_dir_paths = [search_dir / d for d in args.exclude_dirs]

    # 3. Resource Initialization (Temporary File for Reporting)
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tf:
        temp_file = Path(tf.name)

    # 4. Core Processing (Wrapped in try/finally for cleanup)
    try:
        # Find markdown files, passing all lists
        files = find_markdown_files(
            search_dir, args.file_pattern, exclude_dir_paths, args.exclude_files
        )

        if not files:
            print("No markdown files found!")
            if args.directory != "." or args.file_pattern != "*.md":
                sys.exit(0)
            return

        print(f"Found {len(files)} markdown files in {search_dir}")

        # Process each file, passing the absolute search_dir for correct relative reporting
        broken_links_found = False
        for file in files:
            # Pass search_dir as the reference for relative reporting
            if process_markdown_file(file, temp_file, search_dir, verbose=verbose):
                broken_links_found = True

        # Report results and set exit code
        report_results(temp_file, broken_links_found)

    finally:
        # 5. Cleanup
        if temp_file.exists():
            temp_file.unlink()


# --- HELPER FUNCTIONS ---


def is_absolute_url(link: str) -> bool:
    """Check if file is an absolute URL (Policy Violation Check)."""
    return bool(re.match(r"^https?://", link))


def get_path_from_link(link: str) -> str:
    """
    Get path component from link.

    Get path component from link (removing fragment identifier #anchor)
    AND remove markdown escape characters (e.g., r'\') from link paths.
    """
    path_only = link.split("#")[0]
    # FIX: Remove markdown escape character used for underscores in file names
    # This prevents 'file\_name.md' from failing resolution.
    return path_only.replace("\\", "")


def resolve_target_path(link_path_str: str, source_file: Path) -> Path:
    """Handle relative paths and absolute paths (relative to project root)."""
    link_path = Path(link_path_str)

    # Pathlib way to check for a root path link: Path('/').is_absolute() returns True
    # If the path starts with a separator (e.g., /path/to/file)
    if link_path.is_absolute():
        # Treat as absolute link relative to the project root (CWD where main() started).
        project_root = Path(".").resolve()

        # We need to strip the leading separator. Pathlib's string representation is OS specific.
        # We assume the link uses the forward slash as the separator standard in Markdown.
        # Path.is_absolute() is sufficient for logic, string manipulation is for sanitization.
        path_str_cleaned = str(link_path).lstrip(
            "/"
        )  # Use '/' as the canonical Markdown separator

        return project_root / path_str_cleaned
    else:
        # Relative path from source file's directory
        return source_file.parent / link_path


def extract_links_from_file(file: Path) -> list[str]:
    """Extract markdown links from file."""
    try:
        content = file.read_text(encoding="utf-8")
        # Match markdown links: [text](link)
        matches = re.findall(r"\[[^\]]*\]\(([^)]+)\)", content)
        # Return only the link part (the URL)
        return [match for match in matches]
    except UnicodeDecodeError:
        print(f"Warning: Cannot decode file {file}. Skipping.", file=sys.stderr)
        return []


def is_valid_target(target_file: Path) -> bool:
    """Check if the target exists OR if it is a directory containing a valid index file."""
    if target_file.exists():
        if target_file.is_dir():
            # Check for implicit index files (e.g., [Doc](/dir/))
            index_files = [target_file / "index.md", target_file / "README.md"]
            return any(p.exists() for p in index_files)
        # It's a file and it exists
        return True

    # Target file does not exist
    return False


def process_markdown_file(
    file: Path, temp_file: Path, root_dir: Path, verbose: bool = False
) -> bool:
    """
    Process individual markdown file and return True if broken links found.

    Accepts root_dir for correct relative path reporting.
    """
    # Report relative to the absolute root_dir passed from main()
    try:
        relative_path = file.relative_to(root_dir)
    except ValueError:
        relative_path = file

    # Only print this file info when verbose is TRUE
    if verbose:
        print(f"Checking file: {relative_path}")

    links = extract_links_from_file(file)
    broken_links_found = False

    for link in links:
        # 1. Policy check: Skip external URLs
        if is_absolute_url(link):
            if verbose:
                print(f"  SKIP External URL: {link}")
            continue

        # 2. Path Resolution
        link_path = get_path_from_link(link)

        # If the link path is empty (e.g., [Anchor](#anchor)), skip.
        if not link_path:
            continue

        # WRC 1.01 FIX: Skip paths that look like internal fragments or simple variables (e.g., 'args')
        # We cannot use os.path.sep. Instead, we check for both canonical (/) and Windows (\)
        # path separators used in links, and ensure it contains a dot (e.g., file extension)
        # to confirm it's a file path we should check.
        if (
            "/" not in link_path  # Check for common Unix/Markdown separator
            and "\\" not in link_path  # Check for common Windows separator
            and "."
            not in link_path  # Ensure it's not a file extension like .md or .png
        ):
            if verbose:
                print(f"  SKIP Internal Fragment/Variable: {link}")
            continue

        target_file = resolve_target_path(link_path, file)

        # 3. Existence Check (WRC 1.00)
        if not is_valid_target(target_file):
            with open(temp_file, "a", encoding="utf-8") as f:
                f.write(
                    f"BROKEN LINK: File '{relative_path}' contains broken link: {link}\n"
                )
            broken_links_found = True
        elif verbose:
            # Robust relative path reporting for targets
            try:
                target_relative_path = target_file.relative_to(root_dir)
            except ValueError:
                # If target is outside the root_dir (e.g., absolute link pointing outside)
                target_relative_path = target_file

            print(f"  OK: {link} -> {target_relative_path}")

    return broken_links_found


def find_markdown_files(
    search_dir: Path,
    file_pattern: str,
    exclude_dir_paths: List[Path],
    exclude_file_names: List[str],
) -> List[Path]:
    """Get list of markdown files, excluding those in specified directories or matching specified file names."""
    all_files = list(search_dir.rglob(file_pattern))

    if not exclude_dir_paths and not exclude_file_names:
        return all_files

    filtered_files = []

    for file in all_files:
        is_excluded = False
        resolved_file = file.resolve()

        # Check 1: Directory Exclusion
        for exclude_path in exclude_dir_paths:
            # Check if the file itself or any of its parents is in the exclusion path
            if exclude_path in resolved_file.parents or exclude_path == resolved_file:
                is_excluded = True
                break

        if is_excluded:
            continue

        # Check 2: File Name Exclusion
        if resolved_file.name in exclude_file_names:
            is_excluded = True

        if not is_excluded:
            filtered_files.append(file)

    return filtered_files


def report_results(temp_file: Path, broken_links_found: bool) -> None:
    """Report results and exit with appropriate code."""

    if broken_links_found:
        # --- Logic for BROKEN LINKS ---

        # 1. Open and read the entire content of the temp file ONCE
        report_content = ""
        try:
            with open(temp_file, "r", encoding="utf-8") as f:
                report_content = f.read()
        except FileNotFoundError:
            print("Error: Temporary report file not found.", file=sys.stderr)
            sys.exit(1)

        # 2. Count broken links from the content
        count = 0
        for line in report_content.splitlines():
            if "BROKEN LINK" in line:
                count += 1

        # 3. Print the summary and the full content
        print(f"\n❌ {count} Broken links found:")
        print(report_content, end="")

        sys.exit(1)  # Exit with error code

    else:
        # --- Logic for NO BROKEN LINKS ---
        print("\n✅ All links are valid!")
        sys.exit(0)  # Exit with success code


if __name__ == "__main__":
    main()
