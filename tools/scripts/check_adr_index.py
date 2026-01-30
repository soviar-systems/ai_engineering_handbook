#!/usr/bin/env python3
"""
ADR Index Synchronization Validator.

Validates that ADR files in architecture/adr/ are synchronized with
architecture/adr_index.md. Supports validation mode (default) and
auto-fix mode (--fix).

Exit codes:
    0: All ADRs are synchronized with the index
    1: Synchronization errors found
"""

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# ======================
# Configuration
# ======================

# Paths relative to repository root
ADR_DIR = Path("architecture/adr")
INDEX_PATH = Path("architecture/adr_index.md")

# Files to exclude from ADR discovery
EXCLUDED_FILES = {"adr_template.md"}

# Regex patterns
ADR_HEADER_PATTERN = re.compile(r"^#\s+ADR\s+(\d+):\s+(.+)$", re.MULTILINE)
INDEX_ENTRY_PATTERN = re.compile(
    r"^ADR\s+(\d+)\s*\n:\s*\[([^\]]+)\]\(([^)]+)\)",
    re.MULTILINE,
)
GLOSSARY_BLOCK_PATTERN = re.compile(r":::\{glossary\}(.*?):::", re.DOTALL)


# ======================
# Data Classes
# ======================


@dataclass
class AdrFile:
    """Represents an ADR file on disk."""

    path: Path
    number: int
    title: str


@dataclass
class IndexEntry:
    """Represents an entry in the ADR index."""

    number: int
    title: str
    link: str


@dataclass
class ValidationError:
    """Represents a validation error."""

    number: int
    error_type: str
    message: str


# ======================
# Core Functions
# ======================


def get_adr_files() -> list[AdrFile]:
    """Discover and parse all ADR files in the ADR directory.

    Returns:
        List of AdrFile objects sorted by number ascending.
        Files without valid headers are skipped.
    """
    adr_files = []

    if not ADR_DIR.exists():
        return []

    for filepath in ADR_DIR.glob("adr_*.md"):
        if filepath.name in EXCLUDED_FILES:
            continue

        content = filepath.read_text(encoding="utf-8")
        match = ADR_HEADER_PATTERN.search(content)

        if match:
            number = int(match.group(1))
            title = match.group(2).strip()
            adr_files.append(AdrFile(path=filepath, number=number, title=title))

    return sorted(adr_files, key=lambda x: x.number)


def parse_index() -> list[IndexEntry]:
    """Parse the ADR index file and extract all entries.

    Returns:
        List of IndexEntry objects in the order they appear in the file.

    Raises:
        FileNotFoundError: If the index file does not exist.
    """
    if not INDEX_PATH.exists():
        raise FileNotFoundError(f"Index file not found: {INDEX_PATH}")

    content = INDEX_PATH.read_text(encoding="utf-8")

    # Find the glossary block
    glossary_match = GLOSSARY_BLOCK_PATTERN.search(content)
    if not glossary_match:
        return []

    glossary_content = glossary_match.group(1)

    entries = []
    for match in INDEX_ENTRY_PATTERN.finditer(glossary_content):
        number = int(match.group(1))
        title = match.group(2).strip()
        link = match.group(3).strip()
        entries.append(IndexEntry(number=number, title=title, link=link))

    return entries


def validate_sync(
    adr_files: list[AdrFile], index_entries: list[IndexEntry]
) -> list[ValidationError]:
    """Validate that ADR files and index entries are synchronized.

    Args:
        adr_files: List of discovered ADR files
        index_entries: List of parsed index entries

    Returns:
        List of ValidationError objects describing any issues found.
    """
    errors: list[ValidationError] = []

    # Build lookup maps
    files_by_number: dict[int, list[AdrFile]] = {}
    for f in adr_files:
        files_by_number.setdefault(f.number, []).append(f)

    entries_by_number: dict[int, IndexEntry] = {}
    for e in index_entries:
        entries_by_number[e.number] = e

    # Check for duplicate ADR numbers
    for number, files in files_by_number.items():
        if len(files) > 1:
            filenames = ", ".join(f.path.name for f in files)
            errors.append(
                ValidationError(
                    number=number,
                    error_type="duplicate_number",
                    message=f"ADR {number} has multiple files: {filenames}",
                )
            )

    # Check for ADRs missing from index
    for number, files in files_by_number.items():
        if number not in entries_by_number:
            file = files[0]
            errors.append(
                ValidationError(
                    number=number,
                    error_type="missing_in_index",
                    message=f"ADR {number} ({file.path.name}) not in index",
                )
            )

    # Check for orphan entries (in index but no file)
    for number, entry in entries_by_number.items():
        if number not in files_by_number:
            errors.append(
                ValidationError(
                    number=number,
                    error_type="orphan_in_index",
                    message=f"ADR {number} in index but file not found",
                )
            )

    # Check for wrong links
    for number, entry in entries_by_number.items():
        if number in files_by_number:
            file = files_by_number[number][0]
            expected_link = f"/architecture/adr/{file.path.name}"
            if entry.link != expected_link:
                errors.append(
                    ValidationError(
                        number=number,
                        error_type="wrong_link",
                        message=f"ADR {number} has wrong link: {entry.link} (expected {expected_link})",
                    )
                )

    # Check for ordering
    if index_entries:
        numbers = [e.number for e in index_entries]
        if numbers != sorted(numbers):
            errors.append(
                ValidationError(
                    number=0,
                    error_type="wrong_order",
                    message="Index entries are not in numerical order",
                )
            )

    return errors


def fix_index() -> list[str]:
    """Fix the index file by regenerating it from ADR files.

    Returns:
        List of changes made.
    """
    adr_files = get_adr_files()
    changes: list[str] = []

    # Try to parse existing entries to preserve titles if possible
    existing_titles: dict[int, str] = {}
    try:
        for entry in parse_index():
            existing_titles[entry.number] = entry.title
    except FileNotFoundError:
        pass

    # Build new index content
    lines = ["# ADR Index\n", "\n", ":::{glossary}\n"]

    for adr in adr_files:
        # Use title from file (authoritative)
        title = adr.title
        link = f"/architecture/adr/{adr.path.name}"

        lines.append(f"ADR {adr.number}\n")
        lines.append(f": [{title}]({link})\n")
        lines.append("\n")

        # Track changes
        if adr.number not in existing_titles:
            changes.append(f"Added ADR {adr.number}: {title}")

    lines.append(":::\n")

    # Check for removed entries
    current_numbers = {f.number for f in adr_files}
    for number in existing_titles:
        if number not in current_numbers:
            changes.append(f"Removed orphan entry ADR {number}")

    # Write the file
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text("".join(lines), encoding="utf-8")

    return changes


def get_staged_adr_files() -> list[Path]:
    """Get list of staged ADR files from git.

    Returns:
        List of paths to staged ADR files.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            check=True,
            capture_output=True,
            text=True,
        )
        staged_files = result.stdout.strip().split("\n")
        return [
            Path(f)
            for f in staged_files
            if f.startswith("architecture/adr/adr_") and f.endswith(".md")
        ]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


# ======================
# CLI
# ======================


def main(argv: list[str] | None = None) -> int:
    """Main entry point.

    Args:
        argv: Command line arguments (uses sys.argv if None)

    Returns:
        Exit code (0 for success, 1 for errors)
    """
    parser = argparse.ArgumentParser(
        description="Validate ADR index synchronization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix index by adding missing entries",
    )
    parser.add_argument(
        "--check-staged",
        action="store_true",
        help="Only check staged ADR files (for pre-commit)",
    )

    args = parser.parse_args(argv)

    if args.verbose:
        print("Checking ADR index synchronization...")

    # Handle fix mode
    if args.fix:
        if args.verbose:
            print("Running in fix mode...")

        changes = fix_index()

        if changes:
            print(f"Updated {INDEX_PATH}:")
            for change in changes:
                print(f"  - {change}")
            print()
            print("To complete the fix, stage the updated index:")
            print(f"  git add {INDEX_PATH}")
        else:
            if args.verbose:
                print("Index is already in sync. No changes needed.")

        # Verify after fix
        adr_files = get_adr_files()
        try:
            index_entries = parse_index()
        except FileNotFoundError:
            index_entries = []

        errors = validate_sync(adr_files, index_entries)
        if errors:
            print("Errors remain after fix (manual intervention required):")
            for error in errors:
                print(f"  - {error.message}")
            return 1

        return 0

    # Handle check-staged mode
    if args.check_staged:
        staged = get_staged_adr_files()
        if not staged:
            if args.verbose:
                print("No staged ADR files to check.")
            return 0

        if args.verbose:
            print(f"Checking {len(staged)} staged ADR files...")

    # Standard validation
    adr_files = get_adr_files()

    try:
        index_entries = parse_index()
    except FileNotFoundError:
        if adr_files:
            print(f"Error: Index file not found at {INDEX_PATH}")
            print("Run with --fix to create it.")
            return 1
        if args.verbose:
            print("No ADR files and no index file. Nothing to check.")
        return 0

    if args.verbose:
        print(f"Found {len(adr_files)} ADR files")
        print(f"Found {len(index_entries)} index entries")

    errors = validate_sync(adr_files, index_entries)

    if errors:
        print(f"{INDEX_PATH} is out of sync with ADR files:")
        for error in errors:
            print(f"  - {error.message}")
        print()
        print("Run with --fix to update the index automatically.")
        return 1

    if args.verbose:
        print("All ADRs are synchronized with the index.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
