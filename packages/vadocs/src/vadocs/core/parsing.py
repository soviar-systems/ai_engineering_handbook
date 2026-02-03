"""
Parsing utilities for YAML frontmatter and markdown content.

This module provides low-level parsing functions used by validators and
the sync engine. All functions are stateless and work on string content.

Key functions:
- parse_frontmatter(): Extract YAML frontmatter from markdown
- extract_status(): Get status from frontmatter or markdown section
- extract_section_content(): Get content of a specific markdown section

Design notes:
- Functions return None rather than raising exceptions for missing data
- Status is always normalized to lowercase for consistent comparison
- Section extraction is case-sensitive to match markdown conventions

Regex patterns:
- FRONTMATTER_PATTERN: Matches YAML between --- delimiters at file start
- STATUS_SECTION_PATTERN: Matches first word after ## Status header
- SECTION_HEADER_PATTERN: Matches any ## level header

Extension points:
- Add new extraction functions for other metadata fields
- Add section content parsing (e.g., extract list items, code blocks)
"""

import re

import yaml

# Matches YAML frontmatter at the start of file, delimited by ---
# Group 1 captures the YAML content between delimiters
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Matches the status word after ## Status header
# Group 1 captures the first word (the status value)
STATUS_SECTION_PATTERN = re.compile(r"^##\s+Status\s*\n+\s*(\w+)", re.MULTILINE)

# Matches any ## level section header
# Group 1 captures the section name
SECTION_HEADER_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def parse_frontmatter(content: str) -> dict | None:
    """Parse YAML frontmatter from file content.

    Frontmatter must be at the very start of the file, delimited by ---
    markers on their own lines.

    Args:
        content: File content that may contain YAML frontmatter.

    Returns:
        Parsed frontmatter as dictionary, or None if:
        - No frontmatter present
        - Frontmatter not at file start
        - Invalid YAML syntax

    Example:
        >>> content = "---\\ntitle: Test\\n---\\n\\n# Content"
        >>> parse_frontmatter(content)
        {'title': 'Test'}
    """
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        return None

    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None


def extract_status(content: str) -> str | None:
    """Extract status from document content.

    Checks two sources in order of priority:
    1. YAML frontmatter 'status' field
    2. Content under '## Status' markdown section

    Args:
        content: Document content (markdown with optional frontmatter).

    Returns:
        Normalized lowercase status string, or None if not found.

    Example:
        >>> content = "---\\nstatus: Accepted\\n---\\n"
        >>> extract_status(content)
        'accepted'
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


def extract_section_content(content: str, section_name: str) -> str | None:
    """Extract content of a markdown section.

    Finds the section with the given name (## Section Name) and returns
    all content between it and the next ## header (or end of file).

    Args:
        content: Document content (markdown).
        section_name: Name of the section to extract (case-sensitive).

    Returns:
        Section content as string (may be empty), or None if section not found.

    Example:
        >>> content = "## Context\\n\\nSome context.\\n\\n## Decision\\n"
        >>> extract_section_content(content, "Context")
        '\\nSome context.\\n\\n'
    """
    # Find all section headers and their positions
    headers = list(SECTION_HEADER_PATTERN.finditer(content))

    # Find our target section
    target_start = None
    target_end = None

    for i, match in enumerate(headers):
        if match.group(1) == section_name:
            # Found our section - content starts after the header line
            target_start = match.end()
            # Content ends at next header or end of file
            if i + 1 < len(headers):
                target_end = headers[i + 1].start()
            else:
                target_end = len(content)
            break

    if target_start is None:
        return None

    return content[target_start:target_end]
