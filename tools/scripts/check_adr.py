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
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# Note: BROKEN_LINKS_EXCLUDE_DIRS is a shared exclusion set used by multiple
# validation scripts. The name is historical; see misc/plan/plan_20260202_refactor_paths_py_exclusions.md
# for planned refactoring to VALIDATION_EXCLUDE_DIRS.
from tools.scripts.paths import BROKEN_LINKS_EXCLUDE_DIRS

# ======================
# Configuration
# ======================

# Paths relative to repository root
ADR_DIR = Path("architecture/adr")
INDEX_PATH = Path("architecture/adr_index.md")

# Files to exclude from ADR discovery
EXCLUDED_FILES = {"adr_template.md"}

# Regex patterns
ADR_HEADER_PATTERN = re.compile(r"^#\s+ADR-(\d+):\s+(.+)$", re.MULTILINE)
INDEX_ENTRY_PATTERN = re.compile(
    r"^ADR-(\d+)\s*\n:\s*\[([^\]]+)\]\(([^)]+)\)",
    re.MULTILINE,
)
GLOSSARY_BLOCK_PATTERN = re.compile(r":::\{glossary\}(.*?):::", re.DOTALL)
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
STATUS_SECTION_PATTERN = re.compile(r"^##\s+Status\s*\n+\s*(\w+)", re.MULTILINE)
SECTION_HEADER_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)

# =============================================================================
# Term Reference Patterns
# =============================================================================
# MyST glossary cross-references use {term}`ENTRY` syntax where ENTRY must
# match the glossary definition exactly. Our glossary defines "ADR-26001"
# (hyphen), so references must use {term}`ADR-26001` (hyphen), NOT
# {term}`ADR 26001` (space).
#
# See adr_config.yaml term_reference section for the Single Source of Truth.
# These defaults are fallbacks if config doesn't specify patterns.
# =============================================================================
DEFAULT_BROKEN_TERM_PATTERN = r"\{term\}`ADR (\d+)`"
DEFAULT_TERM_SEPARATOR = "-"

# Config file path
ADR_CONFIG_PATH = Path("architecture/adr/adr_config.yaml")


def load_adr_config() -> dict:
    """Load ADR configuration from YAML file.

    Returns:
        Configuration dictionary with statuses, sections, and default_status.

    Raises:
        FileNotFoundError: If config file doesn't exist.
    """
    if not ADR_CONFIG_PATH.exists():
        raise FileNotFoundError(f"ADR config not found: {ADR_CONFIG_PATH}")

    content = ADR_CONFIG_PATH.read_text(encoding="utf-8")
    return yaml.safe_load(content)


def _build_status_sections(config: dict) -> dict[str, str]:
    """Build status-to-section mapping from config.

    Args:
        config: Loaded configuration dictionary.

    Returns:
        Dictionary mapping each status to its section name.
    """
    mapping = {}
    for section_name, statuses in config.get("sections", {}).items():
        for status in statuses:
            mapping[status] = section_name
    return mapping


def _build_status_corrections(config: dict) -> dict[str, str]:
    """Build typo-to-correct-status mapping from config.

    Args:
        config: Loaded configuration dictionary.

    Returns:
        Dictionary mapping each typo/synonym to its correct status.
    """
    mapping = {}
    for correct_status, typos in config.get("status_corrections", {}).items():
        for typo in typos:
            mapping[typo.lower()] = correct_status
    return mapping


# Load config and build derived constants
# These are module-level for backward compatibility with tests
_config = load_adr_config()
VALID_STATUSES: set[str] = set(_config.get("statuses", []))
STATUS_SECTIONS: dict[str, str] = _build_status_sections(_config)
DEFAULT_STATUS: str = _config.get("default_status", "proposed")
SECTION_ORDER: list[str] = list(_config.get("sections", {}).keys())
STATUS_CORRECTIONS: dict[str, str] = _build_status_corrections(_config)
REQUIRED_FIELDS: list[str] = _config.get("required_fields", [])
VALID_TAGS: set[str] = set(_config.get("tags", []))
REQUIRED_SECTIONS: list[str] = _config.get("required_sections", [])
DATE_FORMAT_PATTERN: str = _config.get("date_format", r"^\d{4}-\d{2}-\d{2}$")

# Term reference validation (from config or defaults)
_term_config = _config.get("term_reference", {})
TERM_SEPARATOR: str = _term_config.get("separator", DEFAULT_TERM_SEPARATOR)
BROKEN_TERM_PATTERN: re.Pattern = re.compile(
    _term_config.get("broken_pattern", DEFAULT_BROKEN_TERM_PATTERN)
)


# ======================
# Data Classes
# ======================


@dataclass
class AdrFile:
    """Represents an ADR file on disk."""

    path: Path
    number: int
    title: str
    status: str | None = None
    frontmatter_title: str | None = None
    frontmatter: dict | None = None
    content: str | None = None


@dataclass
class IndexEntry:
    """Represents an entry in the ADR index."""

    number: int
    title: str
    link: str
    section: str | None = None


@dataclass
class ValidationError:
    """Represents a validation error."""

    number: int
    error_type: str
    message: str


@dataclass
class BrokenTermReference:
    """Represents a broken MyST term reference.

    Tracks {term}`ADR 26001` patterns that should use hyphen: {term}`ADR-26001`
    """

    file_path: Path
    line_number: int
    adr_number: int
    original: str

    @property
    def suggested_fix(self) -> str:
        """Return the corrected term reference with hyphen."""
        return f"{{term}}`ADR-{self.adr_number}`"


# ======================
# Core Functions
# ======================


def parse_frontmatter(content: str) -> dict | None:
    """Parse YAML frontmatter from file content.

    Args:
        content: File content that may contain YAML frontmatter.

    Returns:
        Parsed frontmatter as dictionary, or None if no valid frontmatter.
    """
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        return None

    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None


def extract_status(content: str) -> str | None:
    """Extract status from ADR content.

    Supports both YAML frontmatter (priority) and markdown ## Status section.

    Args:
        content: ADR file content.

    Returns:
        Normalized lowercase status string, or None if not found.
    """
    # Priority 1: YAML frontmatter
    frontmatter = parse_frontmatter(content)
    if frontmatter and "status" in frontmatter:
        return str(frontmatter["status"]).lower()

    # Priority 2: Markdown ## Status section
    match = STATUS_SECTION_PATTERN.search(content)
    if match:
        return match.group(1).lower()

    return None


def validate_frontmatter_fields(adr_file: AdrFile) -> list[ValidationError]:
    """Check required frontmatter fields are present.

    Args:
        adr_file: ADR file to validate.

    Returns:
        List of ValidationError for missing required fields.
    """
    errors = []

    if adr_file.frontmatter is None:
        # No frontmatter at all - report all required fields as missing
        for field in REQUIRED_FIELDS:
            errors.append(
                ValidationError(
                    number=adr_file.number,
                    error_type="missing_field",
                    message=f"ADR {adr_file.number} missing required field: '{field}'",
                )
            )
        return errors

    for field in REQUIRED_FIELDS:
        if field not in adr_file.frontmatter:
            errors.append(
                ValidationError(
                    number=adr_file.number,
                    error_type="missing_field",
                    message=f"ADR {adr_file.number} missing required field: '{field}'",
                )
            )

    return errors


def validate_date_format(adr_file: AdrFile) -> list[ValidationError]:
    """Check date field matches YYYY-MM-DD format.

    Args:
        adr_file: ADR file to validate.

    Returns:
        List of ValidationError if date format is invalid.
    """
    errors = []

    if adr_file.frontmatter is None:
        return errors  # Missing frontmatter is handled by validate_frontmatter_fields

    date_value = adr_file.frontmatter.get("date")
    if date_value is None:
        return errors  # Missing date is handled by validate_frontmatter_fields

    # Convert to string (in case YAML parsed it as date object)
    date_str = str(date_value)

    if not re.match(DATE_FORMAT_PATTERN, date_str):
        errors.append(
            ValidationError(
                number=adr_file.number,
                error_type="invalid_date",
                message=f"ADR {adr_file.number} has invalid date format: '{date_str}' (expected YYYY-MM-DD)",
            )
        )

    return errors


def validate_tags(adr_file: AdrFile) -> list[ValidationError]:
    """Check all tags are from the allowed list.

    Args:
        adr_file: ADR file to validate.

    Returns:
        List of ValidationError for invalid tags.
    """
    errors = []

    if adr_file.frontmatter is None:
        return errors  # Missing frontmatter is handled by validate_frontmatter_fields

    tags = adr_file.frontmatter.get("tags")
    if tags is None:
        return errors  # Missing tags is handled by validate_frontmatter_fields

    if not isinstance(tags, list):
        tags = [tags]  # Handle single tag as string

    if len(tags) == 0:
        errors.append(
            ValidationError(
                number=adr_file.number,
                error_type="empty_tags",
                message=f"ADR {adr_file.number} has empty tags list (at least one tag required)",
            )
        )
        return errors

    for tag in tags:
        if tag not in VALID_TAGS:
            errors.append(
                ValidationError(
                    number=adr_file.number,
                    error_type="invalid_tag",
                    message=f"ADR {adr_file.number} has invalid tag: '{tag}' (valid: {', '.join(sorted(VALID_TAGS))})",
                )
            )

    return errors


def validate_sections(adr_file: AdrFile) -> list[ValidationError]:
    """Check required sections are present in document body.

    Args:
        adr_file: ADR file to validate.

    Returns:
        List of ValidationError for missing required sections.
    """
    errors = []

    if adr_file.content is None:
        return errors

    # Find all section headers (## SectionName) and detect duplicates
    section_counts: dict[str, int] = {}
    for match in SECTION_HEADER_PATTERN.finditer(adr_file.content):
        name = match.group(1)
        section_counts[name] = section_counts.get(name, 0) + 1

    for name, count in section_counts.items():
        if count > 1:
            errors.append(
                ValidationError(
                    number=adr_file.number,
                    error_type="duplicate_section",
                    message=f"ADR {adr_file.number} has duplicate section: '## {name}' ({count} occurrences)",
                )
            )

    found_sections = set(section_counts)

    for required_section in REQUIRED_SECTIONS:
        if required_section not in found_sections:
            errors.append(
                ValidationError(
                    number=adr_file.number,
                    error_type="missing_section",
                    message=f"ADR {adr_file.number} missing required section: '## {required_section}'",
                )
            )

    return errors


# Pattern to detect alternative entries in ## Alternatives section.
# Matches three real-world formats found in this repo:
#   - "- **Name**: ..."   (dash bullet + bold)
#   - "* **Name**: ..."   (asterisk bullet + bold)
#   - "### Name"          (subheading per alternative)
#   - "1. **Name**: ..."  (numbered list)
_ALTERNATIVE_ENTRY_PATTERN = re.compile(
    r"^(?:[-*]\s+\*\*|\d+\.\s+|###\s+)", re.MULTILINE
)


def _extract_section_body(content: str, section_name: str) -> str:
    """Extract the body text of a named ## section.

    Returns text between the section header and the next ## header (or EOF).

    Args:
        content: Full ADR content string.
        section_name: Section name without '## ' prefix.

    Returns:
        Section body text, or empty string if section not found.
    """
    pattern = re.compile(
        rf"^##\s+{re.escape(section_name)}\s*$\n(.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(content)
    return match.group(1).strip() if match else ""


def fix_duplicate_sections(adr_files: list[AdrFile]) -> bool:
    """Merge duplicate ## section headers in ADR files.

    For each ADR with duplicate section headers, shows the user what will
    be merged and prompts for confirmation. Keeps the first header and
    concatenates all bodies (preserving order).

    Args:
        adr_files: List of ADR files to check and fix.

    Returns:
        True if any file was modified, False otherwise.
    """
    any_modified = False

    for adr in adr_files:
        if adr.content is None:
            continue

        # Count section occurrences
        section_counts: dict[str, int] = {}
        for match in SECTION_HEADER_PATTERN.finditer(adr.content):
            name = match.group(1)
            section_counts[name] = section_counts.get(name, 0) + 1

        duplicates = {name for name, count in section_counts.items() if count > 1}
        if not duplicates:
            continue

        content = adr.content
        for section_name in duplicates:
            # Find all occurrences of this section and their bodies
            pattern = re.compile(
                rf"^##\s+{re.escape(section_name)}\s*$\n(.*?)(?=^##\s|\Z)",
                re.MULTILINE | re.DOTALL,
            )
            matches = list(pattern.finditer(content))
            if len(matches) <= 1:
                continue

            # Collect all bodies
            bodies = [m.group(1).strip() for m in matches]
            merged_body = "\n\n".join(b for b in bodies if b)

            # Show user what will be merged and ask for confirmation
            print(f"\nADR {adr.number} has {len(matches)} '## {section_name}' sections:")
            for i, body in enumerate(bodies, 1):
                preview = body[:80] if body else "(empty)"
                print(f"  {i}. {preview}")
            print(f"\nMerged result under single '## {section_name}':")
            preview = merged_body[:120] if merged_body else "(empty)"
            print(f"  {preview}")

            response = input("Apply merge? [Y/n]: ").strip().lower()
            if response not in ("", "y"):
                print("Merge rejected. Please fix duplicate sections manually.")
                return False

            # Remove all occurrences after the first
            # Process in reverse order to preserve offsets
            for m in reversed(matches[1:]):
                content = content[:m.start()] + content[m.end():]

            # Replace the first occurrence's body with the merged body
            first = pattern.search(content)
            if first:
                replacement = f"## {section_name}\n\n{merged_body}\n\n"
                content = content[:first.start()] + replacement + content[first.end():]

        if content != adr.content:
            adr.path.write_text(content, encoding="utf-8")
            any_modified = True
            print(f"  Fixed duplicate sections in ADR {adr.number}")

    return any_modified


def validate_promotion_gate(
    adr_file: AdrFile,
) -> tuple[list[ValidationError], list[ValidationError]]:
    """Validate promotion gate criteria (ADR-26025).

    For accepted ADRs, checks are hard errors:
      - ## Alternatives must have ≥2 entries
      - ## Participants must be non-empty

    For proposed ADRs, empty Alternatives is a warning (not error).

    Args:
        adr_file: ADR file to validate.

    Returns:
        Tuple of (errors, warnings). Both are lists of ValidationError.
    """
    errors: list[ValidationError] = []
    warnings: list[ValidationError] = []

    if adr_file.content is None or adr_file.status is None:
        return errors, warnings

    alternatives_body = _extract_section_body(adr_file.content, "Alternatives")
    participants_body = _extract_section_body(adr_file.content, "Participants")

    alt_count = len(_ALTERNATIVE_ENTRY_PATTERN.findall(alternatives_body))

    if adr_file.status == "accepted":
        if alt_count < 2:
            errors.append(
                ValidationError(
                    number=adr_file.number,
                    error_type="insufficient_alternatives",
                    message=(
                        f"ADR {adr_file.number} is accepted but has {alt_count} alternative(s) "
                        f"(promotion gate requires ≥2)"
                    ),
                )
            )
        if not participants_body:
            errors.append(
                ValidationError(
                    number=adr_file.number,
                    error_type="empty_participants",
                    message=f"ADR {adr_file.number} is accepted but has empty ## Participants",
                )
            )

    elif adr_file.status == "proposed":
        if alt_count == 0:
            warnings.append(
                ValidationError(
                    number=adr_file.number,
                    error_type="no_alternatives_proposed",
                    message=(
                        f"ADR {adr_file.number} is proposed with no alternatives listed "
                        f"(consider adding alternatives before promotion)"
                    ),
                )
            )

    return errors, warnings


def migrate_legacy_adr(filepath: Path) -> bool:
    """Add YAML frontmatter to legacy ADR file without it.

    Args:
        filepath: Path to the ADR file to migrate.

    Returns:
        True if migration was performed, False if file already has frontmatter.
    """
    content = filepath.read_text(encoding="utf-8")

    # Check if file already has frontmatter
    if parse_frontmatter(content) is not None:
        return False  # Already has frontmatter, skip

    # Extract ADR number and title from header
    header_match = ADR_HEADER_PATTERN.search(content)
    if not header_match:
        return False  # Can't migrate without valid header

    adr_number = int(header_match.group(1))
    adr_title = header_match.group(2).strip()

    # Extract status from markdown section (or use default)
    status_match = STATUS_SECTION_PATTERN.search(content)
    if status_match:
        status = status_match.group(1).lower()
        # Validate/correct the status
        if status not in VALID_STATUSES:
            corrected = STATUS_CORRECTIONS.get(status)
            status = corrected if corrected else DEFAULT_STATUS
    else:
        status = DEFAULT_STATUS

    # Get file modification date
    import datetime

    mtime = filepath.stat().st_mtime
    date_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")

    # Build frontmatter
    frontmatter = f"""---
id: {adr_number}
title: {adr_title}
date: {date_str}
status: {status}
tags: [architecture]
superseded_by: null
---

"""

    # Write updated content
    new_content = frontmatter + content
    filepath.write_text(new_content, encoding="utf-8")

    return True


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

            # Extract status and frontmatter title
            status = extract_status(content)
            frontmatter = parse_frontmatter(content)
            frontmatter_title = frontmatter.get("title") if frontmatter else None

            adr_files.append(
                AdrFile(
                    path=filepath,
                    number=number,
                    title=title,
                    status=status,
                    frontmatter_title=frontmatter_title,
                    frontmatter=frontmatter,
                    content=content,
                )
            )

    return sorted(adr_files, key=lambda x: x.number)


def parse_index() -> list[IndexEntry]:
    """Parse the ADR index file and extract all entries.

    Returns:
        List of IndexEntry objects in the order they appear in the file.
        Each entry includes its section if the index is partitioned.

    Raises:
        FileNotFoundError: If the index file does not exist.
    """
    if not INDEX_PATH.exists():
        raise FileNotFoundError(f"Index file not found: {INDEX_PATH}")

    content = INDEX_PATH.read_text(encoding="utf-8")

    entries = []

    # Find all section headers and their positions
    section_positions = []
    for match in SECTION_HEADER_PATTERN.finditer(content):
        section_positions.append((match.start(), match.group(1)))

    # Find all glossary blocks
    for glossary_match in GLOSSARY_BLOCK_PATTERN.finditer(content):
        glossary_start = glossary_match.start()
        glossary_content = glossary_match.group(1)

        # Determine which section this glossary belongs to
        current_section = None
        for pos, section_name in section_positions:
            if pos < glossary_start:
                current_section = section_name
            else:
                break

        # Parse entries in this glossary block
        for match in INDEX_ENTRY_PATTERN.finditer(glossary_content):
            number = int(match.group(1))
            title = match.group(2).strip()
            link = match.group(3).strip()
            entries.append(
                IndexEntry(number=number, title=title, link=link, section=current_section)
            )

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

    # Check for ordering (within each section for partitioned index)
    if index_entries:
        # Group by section for ordering check
        sections_seen = []
        current_section = None
        current_numbers = []

        for entry in index_entries:
            if entry.section != current_section:
                if current_numbers and current_numbers != sorted(current_numbers):
                    errors.append(
                        ValidationError(
                            number=0,
                            error_type="wrong_order",
                            message=f"Index entries in section '{current_section}' are not in numerical order",
                        )
                    )
                current_section = entry.section
                current_numbers = [entry.number]
                if current_section:
                    sections_seen.append(current_section)
            else:
                current_numbers.append(entry.number)

        # Check final section
        if current_numbers and current_numbers != sorted(current_numbers):
            section_msg = f" in section '{current_section}'" if current_section else ""
            errors.append(
                ValidationError(
                    number=0,
                    error_type="wrong_order",
                    message=f"Index entries{section_msg} are not in numerical order",
                )
            )

    # Check for invalid statuses
    for adr in adr_files:
        if adr.status is not None and adr.status not in VALID_STATUSES:
            errors.append(
                ValidationError(
                    number=adr.number,
                    error_type="invalid_status",
                    message=f"ADR {adr.number} has invalid status: '{adr.status}' (valid: {', '.join(sorted(VALID_STATUSES))})",
                )
            )

    # Check for required frontmatter fields
    for adr in adr_files:
        errors.extend(validate_frontmatter_fields(adr))

    # Check for date format
    for adr in adr_files:
        errors.extend(validate_date_format(adr))

    # Check for valid tags
    for adr in adr_files:
        errors.extend(validate_tags(adr))

    # Check for required sections
    for adr in adr_files:
        errors.extend(validate_sections(adr))

    # Check for title mismatch between header and frontmatter
    for adr in adr_files:
        if adr.frontmatter_title is not None and adr.frontmatter_title != adr.title:
            errors.append(
                ValidationError(
                    number=adr.number,
                    error_type="title_mismatch",
                    message=f"ADR {adr.number} has mismatched titles: header='{adr.title}', frontmatter='{adr.frontmatter_title}'",
                )
            )

    # Check for wrong section placement
    for adr in adr_files:
        if adr.number in entries_by_number:
            entry = entries_by_number[adr.number]
            if entry.section is not None:  # Only check if index is partitioned
                effective_status = adr.status if adr.status else DEFAULT_STATUS
                expected_section = STATUS_SECTIONS.get(effective_status)
                if expected_section and entry.section != expected_section:
                    errors.append(
                        ValidationError(
                            number=adr.number,
                            error_type="wrong_section",
                            message=f"ADR {adr.number} is in section '{entry.section}' but should be in '{expected_section}'",
                        )
                    )

    return errors


# ======================
# Term Reference Validation
# ======================


def get_all_md_files(root: Path) -> list[Path]:
    """Find all markdown files in the repository.

    Args:
        root: Root directory to search from.

    Returns:
        List of paths to .md files, excluding directories from paths.py SSoT.
    """
    md_files = []

    for filepath in root.rglob("*.md"):
        # Skip files in excluded directories (SSoT: tools/scripts/paths.py)
        if any(excluded in filepath.parts for excluded in BROKEN_LINKS_EXCLUDE_DIRS):
            continue
        md_files.append(filepath)

    return sorted(md_files)


def find_broken_term_references(files: list[Path]) -> list[BrokenTermReference]:
    """Scan files for broken MyST term references.

    Finds {term}`ADR 26001` patterns (space separator) that should use
    {term}`ADR-26001` (hyphen separator) to match glossary entries.

    Args:
        files: List of markdown files to scan.

    Returns:
        List of BrokenTermReference objects describing each broken reference.
    """
    broken_refs = []

    for filepath in files:
        try:
            content = filepath.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        for line_num, line in enumerate(content.splitlines(), start=1):
            for match in BROKEN_TERM_PATTERN.finditer(line):
                adr_number = int(match.group(1))
                broken_refs.append(
                    BrokenTermReference(
                        file_path=filepath,
                        line_number=line_num,
                        adr_number=adr_number,
                        original=match.group(0),
                    )
                )

    return broken_refs


def validate_term_references(files: list[Path]) -> list[ValidationError]:
    """Validate MyST term references in files.

    Args:
        files: List of markdown files to validate.

    Returns:
        List of ValidationError objects for broken term references.
    """
    broken_refs = find_broken_term_references(files)
    errors = []

    for ref in broken_refs:
        errors.append(
            ValidationError(
                number=ref.adr_number,
                error_type="broken_term_reference",
                message=(
                    f"{ref.file_path}:{ref.line_number}: "
                    f"'{ref.original}' should be '{ref.suggested_fix}'"
                ),
            )
        )

    return errors


def fix_term_references(files: list[Path]) -> list[Path]:
    """Fix broken term references in files.

    Replaces {term}`ADR 26001` with {term}`ADR-26001` to match glossary format.

    Args:
        files: List of markdown files to fix.

    Returns:
        List of paths to files that were modified.
    """
    modified_files = []

    for filepath in files:
        try:
            content = filepath.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        # Replace space with configured separator (hyphen by default)
        new_content = BROKEN_TERM_PATTERN.sub(
            rf"{{term}}`ADR{TERM_SEPARATOR}\1`", content
        )

        if new_content != content:
            filepath.write_text(new_content, encoding="utf-8")
            modified_files.append(filepath)

    return modified_files


def fix_invalid_status(adr_file: AdrFile) -> bool:
    """Fix invalid status by suggesting correction or prompting for input.

    Args:
        adr_file: ADR file with invalid status.

    Returns:
        True if fix was applied, False if rejected or cancelled.
    """
    if adr_file.status is None or adr_file.status in VALID_STATUSES:
        return True  # No invalid status

    invalid_status = adr_file.status.lower()
    suggested = STATUS_CORRECTIONS.get(invalid_status)

    print(f"\nADR {adr_file.number} has invalid status: '{adr_file.status}'")
    print(f"Valid statuses: {', '.join(sorted(VALID_STATUSES))}")

    if suggested:
        print(f"\nSuggested correction: '{invalid_status}' -> '{suggested}'")
        response = input(f"Apply suggested fix '{suggested}'? [Y/n/custom]: ").strip().lower()

        if response == "" or response == "y":
            new_status = suggested
        elif response == "n":
            return False
        else:
            # User typed a custom value
            new_status = response
    else:
        print("\nNo automatic correction found.")
        new_status = input(f"Enter correct status (or press Enter to skip): ").strip().lower()

        if not new_status:
            return False

    # Validate the new status
    if new_status not in VALID_STATUSES:
        print(f"  '{new_status}' is not a valid status. Skipping.")
        return False

    # Update the file
    content = adr_file.path.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(content)

    if frontmatter:
        # Update YAML frontmatter
        def replace_status(match: re.Match) -> str:
            frontmatter_content = match.group(1)
            updated = re.sub(
                r"^status:\s*.+$",
                f"status: {new_status}",
                frontmatter_content,
                flags=re.MULTILINE,
            )
            return f"---\n{updated}\n---\n"

        new_content = FRONTMATTER_PATTERN.sub(replace_status, content)
    else:
        # Update markdown ## Status section
        new_content = STATUS_SECTION_PATTERN.sub(
            f"## Status\n\n{new_status.capitalize()}",
            content,
        )

    adr_file.path.write_text(new_content, encoding="utf-8")
    print(f"  Updated {adr_file.path.name}: status -> '{new_status}'")

    # Update the adr_file object for subsequent validation
    adr_file.status = new_status
    return True


def fix_title_mismatch(adr_file: AdrFile) -> bool:
    """Fix title mismatch by updating frontmatter to match header.

    Prompts user for confirmation before making changes.

    Args:
        adr_file: ADR file with mismatched titles.

    Returns:
        True if fix was applied, False if rejected or no fix needed.
    """
    if adr_file.frontmatter_title is None or adr_file.frontmatter_title == adr_file.title:
        return True  # No mismatch

    print(f"\nADR {adr_file.number} title mismatch:")
    print(f"  Header title:      '{adr_file.title}'")
    print(f"  Frontmatter title: '{adr_file.frontmatter_title}'")
    print(f"\nThe header title is authoritative. Update frontmatter to match?")

    response = input("Apply fix? [y/N]: ").strip().lower()
    if response != "y":
        return False

    # Read and update the file
    content = adr_file.path.read_text(encoding="utf-8")

    # Replace the title in frontmatter
    # Match the frontmatter and update title field
    def replace_title(match: re.Match) -> str:
        frontmatter_content = match.group(1)
        # Replace title line
        updated = re.sub(
            r"^title:\s*.+$",
            f"title: {adr_file.title}",
            frontmatter_content,
            flags=re.MULTILINE,
        )
        return f"---\n{updated}\n---\n"

    new_content = FRONTMATTER_PATTERN.sub(replace_title, content)
    adr_file.path.write_text(new_content, encoding="utf-8")

    print(f"  Updated {adr_file.path.name}")
    return True


def fix_index() -> list[str]:
    """Fix the index file by regenerating it from ADR files.

    Generates a partitioned index grouped by status.

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

    # Group ADRs by section
    sections: dict[str, list[AdrFile]] = {section: [] for section in SECTION_ORDER}
    for adr in adr_files:
        effective_status = adr.status if adr.status else DEFAULT_STATUS
        section = STATUS_SECTIONS.get(effective_status, STATUS_SECTIONS[DEFAULT_STATUS])
        sections[section].append(adr)

    # Build new index content with partitioned sections
    lines = ["# ADR Index\n"]

    for section_name in SECTION_ORDER:
        section_adrs = sections.get(section_name, [])
        if not section_adrs:
            continue  # Skip empty sections

        lines.append(f"\n## {section_name}\n")
        lines.append("\n:::{glossary}\n")

        for adr in sorted(section_adrs, key=lambda x: x.number):
            title = adr.title
            link = f"/architecture/adr/{adr.path.name}"

            # Build annotation for superseded ADRs
            annotation = ""
            if adr.frontmatter and adr.frontmatter.get("superseded_by"):
                successor = adr.frontmatter["superseded_by"]
                annotation = f" — superseded by {{term}}`{successor}`"

            lines.append(f"ADR-{adr.number}\n")
            lines.append(f": [{title}]({link}){annotation}\n")
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
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Add YAML frontmatter to legacy ADRs without it",
    )
    parser.add_argument(
        "--check-terms",
        action="store_true",
        help="Validate {term}`ADR-XXXXX` references in all .md files",
    )
    parser.add_argument(
        "--fix-terms",
        action="store_true",
        help="Fix broken term references ({term}`ADR 26001` -> {term}`ADR-26001`)",
    )

    args = parser.parse_args(argv)

    if args.verbose:
        print("Checking ADR index synchronization...")

    # Handle migrate mode
    if args.migrate:
        if args.verbose:
            print("Running in migrate mode...")

        if not ADR_DIR.exists():
            print(f"Error: ADR directory not found: {ADR_DIR}")
            return 1

        migrated_count = 0
        for filepath in ADR_DIR.glob("adr_*.md"):
            if filepath.name in EXCLUDED_FILES:
                continue

            if migrate_legacy_adr(filepath):
                print(f"Migrated: {filepath.name}")
                migrated_count += 1

        if migrated_count > 0:
            print(f"\nMigrated {migrated_count} ADR file(s).")
            print("Run --fix to regenerate the index.")
        else:
            print("No legacy ADRs found to migrate.")

        return 0

    # Handle --fix-terms mode
    if args.fix_terms:
        if args.verbose:
            print("Scanning for broken term references...")

        # Get repository root (parent of architecture/)
        repo_root = ADR_DIR.parent.parent
        md_files = get_all_md_files(repo_root)

        if args.verbose:
            print(f"Found {len(md_files)} markdown files to scan.")

        modified = fix_term_references(md_files)

        if modified:
            print(f"Fixed term references in {len(modified)} file(s):")
            for filepath in modified:
                print(f"  - {filepath.relative_to(repo_root)}")
        else:
            if args.verbose:
                print("No broken term references found.")

        return 0

    # Handle --check-terms mode
    if args.check_terms:
        if args.verbose:
            print("Validating term references...")

        # Get repository root (parent of architecture/)
        repo_root = ADR_DIR.parent.parent
        md_files = get_all_md_files(repo_root)

        if args.verbose:
            print(f"Found {len(md_files)} markdown files to scan.")

        errors = validate_term_references(md_files)

        if errors:
            print(f"Found {len(errors)} broken term reference(s):")
            for error in errors:
                print(f"  - {error.message}")
            print()
            print("Run with --fix-terms to fix automatically.")
            return 1

        if args.verbose:
            print("All term references are valid.")

        return 0

    # Handle fix mode
    if args.fix:
        if args.verbose:
            print("Running in fix mode...")

        # First, fix ADR file issues (statuses, titles) before regenerating index
        adr_files = get_adr_files()
        files_modified = []

        # Fix invalid statuses
        for adr in adr_files:
            if adr.status is not None and adr.status not in VALID_STATUSES:
                if fix_invalid_status(adr):
                    files_modified.append(adr.path.name)

        # Fix title mismatches
        for adr in adr_files:
            if adr.frontmatter_title is not None and adr.frontmatter_title != adr.title:
                if fix_title_mismatch(adr):
                    if adr.path.name not in files_modified:
                        files_modified.append(adr.path.name)

        # Fix duplicate sections (with user confirmation)
        if fix_duplicate_sections(adr_files):
            for adr in adr_files:
                if adr.path.name not in files_modified:
                    files_modified.append(adr.path.name)

        # Re-read ADR files after fixes to get updated data
        if files_modified:
            print(f"\nFixed {len(files_modified)} ADR file(s).")
            adr_files = get_adr_files()

        # Now regenerate the index
        changes = fix_index()

        if changes:
            print(f"\nUpdated {INDEX_PATH}:")
            for change in changes:
                print(f"  - {change}")
            print()
            print("To complete the fix, stage the updated files:")
            if files_modified:
                for f in files_modified:
                    print(f"  git add architecture/adr/{f}")
            print(f"  git add {INDEX_PATH}")
        else:
            if args.verbose:
                print("Index is already in sync. No changes needed.")

        # Verify after fix
        try:
            index_entries = parse_index()
        except FileNotFoundError:
            index_entries = []

        errors = validate_sync(adr_files, index_entries)
        if errors:
            print("\nErrors remain after fix (manual intervention required):")
            for error in errors:
                print(f"  - {error.message}")
            return 1

        # Promotion gate validation (same as --verbose mode)
        gate_errors: list[ValidationError] = []
        gate_warnings: list[ValidationError] = []
        for adr in adr_files:
            errs, warns = validate_promotion_gate(adr)
            gate_errors.extend(errs)
            gate_warnings.extend(warns)

        if gate_warnings:
            print("Promotion gate warnings:")
            for warning in gate_warnings:
                print(f"  ⚠ {warning.message}")

        if gate_errors:
            print("Promotion gate errors:")
            for error in gate_errors:
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

    # Promotion gate validation (ADR-26025)
    gate_errors: list[ValidationError] = []
    gate_warnings: list[ValidationError] = []
    for adr in adr_files:
        errs, warns = validate_promotion_gate(adr)
        gate_errors.extend(errs)
        gate_warnings.extend(warns)

    if gate_warnings:
        print("Promotion gate warnings:")
        for warning in gate_warnings:
            print(f"  ⚠ {warning.message}")

    if gate_errors:
        print("Promotion gate errors:")
        for error in gate_errors:
            print(f"  - {error.message}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
