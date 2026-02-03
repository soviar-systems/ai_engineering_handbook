"""
Tests for ADR validator.

Contract being tested:
- AdrValidator.supports(): Returns True for ADR documents (doc_type="adr" or adr_*.md filename)
- AdrValidator.validate(): Returns list of ValidationErrors for:
  - Missing required frontmatter fields
  - Invalid status values
  - Invalid date format
  - Invalid tags
  - Missing required sections
  - Title mismatch between header and frontmatter
"""

from pathlib import Path

import pytest

from vadocs import AdrValidator, Document, ValidationError
from vadocs.core.parsing import parse_frontmatter


class TestAdrValidatorSupports:
    """Tests for AdrValidator.supports() method.

    Contract: Returns True if document is an ADR (doc_type="adr" or filename starts with "adr_").
    """

    def test_supports_doc_type_adr(self, tmp_path: Path) -> None:
        """Supports documents with doc_type='adr'."""
        doc = Document(
            path=tmp_path / "any_name.md",
            content="# Content",
            doc_type="adr",
        )
        validator = AdrValidator()
        assert validator.supports(doc) is True

    def test_supports_adr_filename_pattern(self, tmp_path: Path) -> None:
        """Supports documents with adr_*.md filename pattern."""
        doc = Document(
            path=tmp_path / "adr_26001_test.md",
            content="# Content",
            doc_type=None,
        )
        validator = AdrValidator()
        assert validator.supports(doc) is True

    def test_not_supports_other_doc_type(self, tmp_path: Path) -> None:
        """Does not support documents with different doc_type."""
        doc = Document(
            path=tmp_path / "some_doc.md",
            content="# Content",
            doc_type="rfc",
        )
        validator = AdrValidator()
        assert validator.supports(doc) is False

    def test_not_supports_non_adr_filename(self, tmp_path: Path) -> None:
        """Does not support documents without adr_ prefix."""
        doc = Document(
            path=tmp_path / "design_doc.md",
            content="# Content",
            doc_type=None,
        )
        validator = AdrValidator()
        assert validator.supports(doc) is False


class TestAdrValidatorRequiredFields:
    """Tests for required field validation.

    Contract: Returns ValidationError for each missing required field.
    """

    def test_missing_required_field(self, tmp_path: Path) -> None:
        """Returns error when required field is missing."""
        content = """---
id: 26001
title: Test ADR
---

# ADR-26001: Test ADR
"""
        doc = Document(
            path=tmp_path / "adr_26001_test.md",
            content=content,
            frontmatter=parse_frontmatter(content),
            doc_type="adr",
        )
        config = {"required_fields": ["id", "title", "status", "date"]}

        validator = AdrValidator()
        errors = validator.validate(doc, config)

        # Should have errors for missing status and date
        error_types = [e.error_type for e in errors]
        assert "missing_field" in error_types
        assert any("status" in e.message for e in errors)
        assert any("date" in e.message for e in errors)

    def test_all_required_fields_present(self, tmp_path: Path) -> None:
        """Returns no errors when all required fields present."""
        content = """---
id: 26001
title: Test ADR
status: accepted
date: 2024-01-15
tags: [architecture]
---

# ADR-26001: Test ADR

## Status

Accepted

## Context

Context here.

## Decision

Decision here.

## Consequences

Consequences here.
"""
        doc = Document(
            path=tmp_path / "adr_26001_test.md",
            content=content,
            frontmatter=parse_frontmatter(content),
            doc_type="adr",
        )
        config = {
            "required_fields": ["id", "title", "status", "date", "tags"],
            "statuses": ["accepted", "proposed", "deprecated"],
            "tags": ["architecture"],
            "required_sections": ["Status", "Context", "Decision", "Consequences"],
        }

        validator = AdrValidator()
        errors = validator.validate(doc, config)

        assert len(errors) == 0

    def test_no_frontmatter_reports_all_missing(self, tmp_path: Path) -> None:
        """Reports all required fields as missing when no frontmatter."""
        content = """# ADR-26001: Test ADR

## Status

Accepted
"""
        doc = Document(
            path=tmp_path / "adr_26001_test.md",
            content=content,
            frontmatter=None,
            doc_type="adr",
        )
        config = {"required_fields": ["id", "title", "status"]}

        validator = AdrValidator()
        errors = validator.validate(doc, config)

        missing_field_errors = [e for e in errors if e.error_type == "missing_field"]
        assert len(missing_field_errors) == 3


class TestAdrValidatorStatus:
    """Tests for status validation.

    Contract: Returns ValidationError if status is not in valid statuses list.
    """

    def test_invalid_status(self, tmp_path: Path) -> None:
        """Returns error for invalid status value."""
        content = """---
id: 26001
status: invalid_status
---

# ADR-26001: Test
"""
        doc = Document(
            path=tmp_path / "adr_26001_test.md",
            content=content,
            frontmatter=parse_frontmatter(content),
            doc_type="adr",
        )
        config = {"statuses": ["accepted", "proposed", "deprecated"]}

        validator = AdrValidator()
        errors = validator.validate(doc, config)

        assert any(e.error_type == "invalid_status" for e in errors)

    def test_valid_status_case_insensitive(self, tmp_path: Path) -> None:
        """Accepts status regardless of case."""
        content = """---
id: 26001
status: ACCEPTED
---

# ADR-26001: Test
"""
        doc = Document(
            path=tmp_path / "adr_26001_test.md",
            content=content,
            frontmatter=parse_frontmatter(content),
            doc_type="adr",
        )
        config = {"statuses": ["accepted", "proposed"]}

        validator = AdrValidator()
        errors = validator.validate(doc, config)

        assert not any(e.error_type == "invalid_status" for e in errors)

    def test_no_status_validation_when_not_configured(self, tmp_path: Path) -> None:
        """Skips status validation when statuses not configured."""
        content = """---
id: 26001
status: anything
---

# ADR-26001: Test
"""
        doc = Document(
            path=tmp_path / "adr_26001_test.md",
            content=content,
            frontmatter=parse_frontmatter(content),
            doc_type="adr",
        )
        config = {}  # No statuses configured

        validator = AdrValidator()
        errors = validator.validate(doc, config)

        assert not any(e.error_type == "invalid_status" for e in errors)


class TestAdrValidatorDate:
    """Tests for date format validation.

    Contract: Returns ValidationError if date does not match YYYY-MM-DD format.
    """

    def test_invalid_date_format(self, tmp_path: Path) -> None:
        """Returns error for invalid date format."""
        content = """---
id: 26001
date: 15/01/2024
---

# ADR-26001: Test
"""
        doc = Document(
            path=tmp_path / "adr_26001_test.md",
            content=content,
            frontmatter=parse_frontmatter(content),
            doc_type="adr",
        )
        config = {}

        validator = AdrValidator()
        errors = validator.validate(doc, config)

        assert any(e.error_type == "invalid_date" for e in errors)

    def test_valid_date_format(self, tmp_path: Path) -> None:
        """Accepts valid YYYY-MM-DD date format."""
        content = """---
id: 26001
date: 2024-01-15
---

# ADR-26001: Test
"""
        doc = Document(
            path=tmp_path / "adr_26001_test.md",
            content=content,
            frontmatter=parse_frontmatter(content),
            doc_type="adr",
        )
        config = {}

        validator = AdrValidator()
        errors = validator.validate(doc, config)

        assert not any(e.error_type == "invalid_date" for e in errors)


class TestAdrValidatorTags:
    """Tests for tags validation.

    Contract: Returns ValidationError for each invalid tag not in allowed list.
    """

    def test_invalid_tag(self, tmp_path: Path) -> None:
        """Returns error for invalid tag."""
        content = """---
id: 26001
tags: [invalid_tag, architecture]
---

# ADR-26001: Test
"""
        doc = Document(
            path=tmp_path / "adr_26001_test.md",
            content=content,
            frontmatter=parse_frontmatter(content),
            doc_type="adr",
        )
        config = {"tags": ["architecture", "security"]}

        validator = AdrValidator()
        errors = validator.validate(doc, config)

        assert any(e.error_type == "invalid_tag" for e in errors)
        assert any("invalid_tag" in e.message for e in errors)

    def test_empty_tags_list(self, tmp_path: Path) -> None:
        """Returns error for empty tags list."""
        content = """---
id: 26001
tags: []
---

# ADR-26001: Test
"""
        doc = Document(
            path=tmp_path / "adr_26001_test.md",
            content=content,
            frontmatter=parse_frontmatter(content),
            doc_type="adr",
        )
        config = {"tags": ["architecture"]}

        validator = AdrValidator()
        errors = validator.validate(doc, config)

        assert any(e.error_type == "empty_tags" for e in errors)

    def test_all_valid_tags(self, tmp_path: Path) -> None:
        """No errors when all tags are valid."""
        content = """---
id: 26001
tags: [architecture, security]
---

# ADR-26001: Test
"""
        doc = Document(
            path=tmp_path / "adr_26001_test.md",
            content=content,
            frontmatter=parse_frontmatter(content),
            doc_type="adr",
        )
        config = {"tags": ["architecture", "security", "performance"]}

        validator = AdrValidator()
        errors = validator.validate(doc, config)

        assert not any(e.error_type == "invalid_tag" for e in errors)


class TestAdrValidatorSections:
    """Tests for required sections validation.

    Contract: Returns ValidationError for each missing required section.
    """

    def test_missing_required_section(self, tmp_path: Path) -> None:
        """Returns error for missing required section."""
        content = """---
id: 26001
---

# ADR-26001: Test

## Status

Accepted

## Context

Some context.
"""
        doc = Document(
            path=tmp_path / "adr_26001_test.md",
            content=content,
            frontmatter=parse_frontmatter(content),
            doc_type="adr",
        )
        config = {"required_sections": ["Status", "Context", "Decision", "Consequences"]}

        validator = AdrValidator()
        errors = validator.validate(doc, config)

        missing_sections = [e for e in errors if e.error_type == "missing_section"]
        assert len(missing_sections) == 2  # Decision and Consequences

    def test_all_required_sections_present(self, tmp_path: Path) -> None:
        """No errors when all required sections present."""
        content = """---
id: 26001
---

# ADR-26001: Test

## Status

Accepted

## Context

Context here.

## Decision

Decision here.

## Consequences

Consequences here.
"""
        doc = Document(
            path=tmp_path / "adr_26001_test.md",
            content=content,
            frontmatter=parse_frontmatter(content),
            doc_type="adr",
        )
        config = {"required_sections": ["Status", "Context", "Decision", "Consequences"]}

        validator = AdrValidator()
        errors = validator.validate(doc, config)

        assert not any(e.error_type == "missing_section" for e in errors)


class TestAdrValidatorTitle:
    """Tests for title consistency validation.

    Contract: Returns ValidationError if frontmatter title differs from header title.
    """

    def test_title_mismatch(self, tmp_path: Path) -> None:
        """Returns error when titles don't match."""
        content = """---
id: 26001
title: Wrong Title
---

# ADR-26001: Correct Title
"""
        doc = Document(
            path=tmp_path / "adr_26001_test.md",
            content=content,
            frontmatter=parse_frontmatter(content),
            doc_type="adr",
        )
        config = {}

        validator = AdrValidator()
        errors = validator.validate(doc, config)

        assert any(e.error_type == "title_mismatch" for e in errors)

    def test_title_match(self, tmp_path: Path) -> None:
        """No error when titles match."""
        content = """---
id: 26001
title: Test Title
---

# ADR-26001: Test Title
"""
        doc = Document(
            path=tmp_path / "adr_26001_test.md",
            content=content,
            frontmatter=parse_frontmatter(content),
            doc_type="adr",
        )
        config = {}

        validator = AdrValidator()
        errors = validator.validate(doc, config)

        assert not any(e.error_type == "title_mismatch" for e in errors)


class TestAdrValidatorIdentifier:
    """Tests for ADR number extraction.

    Contract: Extracts ADR number from frontmatter id, filename, or header.
    """

    def test_identifier_from_frontmatter(self, tmp_path: Path) -> None:
        """Extracts identifier from frontmatter id field."""
        content = """---
id: 26001
status: invalid
---

# ADR-26001: Test
"""
        doc = Document(
            path=tmp_path / "adr_26001_test.md",
            content=content,
            frontmatter=parse_frontmatter(content),
            doc_type="adr",
        )
        config = {"statuses": ["accepted"]}

        validator = AdrValidator()
        errors = validator.validate(doc, config)

        # Check that error references the correct ADR number
        assert any(e.identifier == 26001 for e in errors)

    def test_identifier_from_filename(self, tmp_path: Path) -> None:
        """Extracts identifier from filename when no frontmatter id."""
        content = """---
status: invalid
---

# ADR-26002: Test
"""
        doc = Document(
            path=tmp_path / "adr_26002_test.md",
            content=content,
            frontmatter=parse_frontmatter(content),
            doc_type="adr",
        )
        config = {"statuses": ["accepted"]}

        validator = AdrValidator()
        errors = validator.validate(doc, config)

        assert any(e.identifier == 26002 for e in errors)
