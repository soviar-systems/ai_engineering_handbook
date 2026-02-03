"""
Tests for vadoc parsing utilities.

Contract being tested:
- parse_frontmatter(): Extract YAML frontmatter from markdown content
- extract_status(): Get status from frontmatter or markdown section
- extract_section_content(): Get content of a markdown section
"""

import pytest


class TestParseFrontmatter:
    """Tests for parse_frontmatter function.

    Contract: Parses YAML frontmatter delimited by --- markers at file start.
    Returns dict if valid, None if no frontmatter or invalid YAML.
    """

    def test_valid_frontmatter(self) -> None:
        """Parses valid YAML frontmatter."""
        from vadocs.core.parsing import parse_frontmatter

        content = """---
title: Test Document
status: accepted
tags: [architecture]
---

# Content here
"""
        result = parse_frontmatter(content)

        assert result is not None
        assert result["title"] == "Test Document"
        assert result["status"] == "accepted"
        assert result["tags"] == ["architecture"]

    def test_no_frontmatter(self) -> None:
        """Returns None when no frontmatter present."""
        from vadocs.core.parsing import parse_frontmatter

        content = "# Just a heading\n\nSome content."
        result = parse_frontmatter(content)

        assert result is None

    def test_frontmatter_not_at_start(self) -> None:
        """Returns None when --- is not at file start."""
        from vadocs.core.parsing import parse_frontmatter

        content = """Some text first

---
title: Test
---
"""
        result = parse_frontmatter(content)

        assert result is None

    def test_invalid_yaml(self) -> None:
        """Returns None for invalid YAML."""
        from vadocs.core.parsing import parse_frontmatter

        content = """---
title: [invalid yaml
  - broken
---
"""
        result = parse_frontmatter(content)

        assert result is None

    def test_empty_frontmatter(self) -> None:
        """Handles empty frontmatter."""
        from vadocs.core.parsing import parse_frontmatter

        content = """---
---

# Content
"""
        result = parse_frontmatter(content)

        # Empty YAML is valid and returns None (parsed as Python None)
        assert result is None


class TestExtractStatus:
    """Tests for extract_status function.

    Contract: Extracts status from:
    1. YAML frontmatter 'status' field (priority)
    2. Markdown '## Status' section content (fallback)
    Returns normalized lowercase string, or None if not found.
    """

    def test_status_from_frontmatter(self) -> None:
        """Extracts status from YAML frontmatter."""
        from vadocs.core.parsing import extract_status

        content = """---
status: Accepted
---

# Document

## Status

Different status here
"""
        result = extract_status(content)

        # Frontmatter takes priority, normalized to lowercase
        assert result == "accepted"

    def test_status_from_markdown_section(self) -> None:
        """Extracts status from markdown section when no frontmatter."""
        from vadocs.core.parsing import extract_status

        content = """# Document

## Status

Proposed

## Context
"""
        result = extract_status(content)

        assert result == "proposed"

    def test_no_status_found(self) -> None:
        """Returns None when no status found."""
        from vadocs.core.parsing import extract_status

        content = """# Document

## Context

Some context.
"""
        result = extract_status(content)

        assert result is None

    def test_status_normalized_lowercase(self) -> None:
        """Status is normalized to lowercase."""
        from vadocs.core.parsing import extract_status

        content = """---
status: ACCEPTED
---
"""
        result = extract_status(content)

        assert result == "accepted"


class TestExtractSectionContent:
    """Tests for extract_section_content function.

    Contract: Extracts content between a ## Section header and the next
    ## header (or end of file). Returns None if section not found.
    """

    def test_extract_existing_section(self) -> None:
        """Extracts content from existing section."""
        from vadocs.core.parsing import extract_section_content

        content = """# Document

## Context

This is the context.
Multiple lines.

## Decision

This is the decision.
"""
        result = extract_section_content(content, "Context")

        assert result is not None
        assert "This is the context." in result
        assert "Multiple lines." in result
        assert "This is the decision." not in result

    def test_extract_last_section(self) -> None:
        """Extracts content from last section (no following header)."""
        from vadocs.core.parsing import extract_section_content

        content = """# Document

## Context

This is the context.

## Decision

This is the final section.
"""
        result = extract_section_content(content, "Decision")

        assert result is not None
        assert "This is the final section." in result

    def test_section_not_found(self) -> None:
        """Returns None when section doesn't exist."""
        from vadocs.core.parsing import extract_section_content

        content = """# Document

## Context

Some content.
"""
        result = extract_section_content(content, "NonExistent")

        assert result is None

    def test_empty_section(self) -> None:
        """Handles empty section (header with no content before next header)."""
        from vadocs.core.parsing import extract_section_content

        content = """# Document

## Empty

## Next

Content here.
"""
        result = extract_section_content(content, "Empty")

        assert result is not None
        # Content should be empty or whitespace only
        assert result.strip() == ""

    def test_section_name_case_sensitive(self) -> None:
        """Section name matching is case-sensitive."""
        from vadocs.core.parsing import extract_section_content

        content = """# Document

## Context

Content.
"""
        # Exact case match
        assert extract_section_content(content, "Context") is not None
        # Wrong case
        assert extract_section_content(content, "context") is None
