"""
Tests for Frontmatter validator.

Contract being tested:
- FrontmatterValidator.supports(): Returns True for documents with YAML frontmatter
- FrontmatterValidator.validate(): Returns list of ValidationErrors for:
  - Missing required fields
  - Invalid field values (not in allowed list)
"""

from pathlib import Path

import pytest

from vadocs import Document, FrontmatterValidator, ValidationError
from vadocs.core.parsing import parse_frontmatter


class TestFrontmatterValidatorSupports:
    """Tests for FrontmatterValidator.supports() method.

    Contract: Returns True if document has YAML frontmatter (parsed or parseable).
    """

    def test_supports_document_with_frontmatter(self, tmp_path: Path) -> None:
        """Supports documents with parsed frontmatter."""
        doc = Document(
            path=tmp_path / "doc.md",
            content="# Content",
            frontmatter={"title": "Test"},
        )
        validator = FrontmatterValidator()
        assert validator.supports(doc) is True

    def test_supports_document_with_parseable_frontmatter(self, tmp_path: Path) -> None:
        """Supports documents with parseable frontmatter in content."""
        content = """---
title: Test
---

# Content
"""
        doc = Document(
            path=tmp_path / "doc.md",
            content=content,
            frontmatter=None,  # Not pre-parsed
        )
        validator = FrontmatterValidator()
        assert validator.supports(doc) is True

    def test_not_supports_document_without_frontmatter(self, tmp_path: Path) -> None:
        """Does not support documents without frontmatter."""
        doc = Document(
            path=tmp_path / "doc.md",
            content="# Just content\n\nNo frontmatter here.",
            frontmatter=None,
        )
        validator = FrontmatterValidator()
        assert validator.supports(doc) is False


class TestFrontmatterValidatorRequiredFields:
    """Tests for required fields validation.

    Contract: Returns ValidationError for each missing required field.
    """

    def test_missing_required_field(self, tmp_path: Path) -> None:
        """Returns error for missing required field."""
        content = """---
title: Test
---

# Content
"""
        doc = Document(
            path=tmp_path / "doc.md",
            content=content,
            frontmatter=parse_frontmatter(content),
        )
        config = {"required_fields": ["title", "author", "date"]}

        validator = FrontmatterValidator()
        errors = validator.validate(doc, config)

        missing_errors = [e for e in errors if e.error_type == "missing_field"]
        assert len(missing_errors) == 2  # author and date

    def test_all_required_fields_present(self, tmp_path: Path) -> None:
        """No errors when all required fields present."""
        content = """---
title: Test
author: John
date: 2024-01-15
---

# Content
"""
        doc = Document(
            path=tmp_path / "doc.md",
            content=content,
            frontmatter=parse_frontmatter(content),
        )
        config = {"required_fields": ["title", "author", "date"]}

        validator = FrontmatterValidator()
        errors = validator.validate(doc, config)

        assert len(errors) == 0

    def test_missing_frontmatter_when_required_fields(self, tmp_path: Path) -> None:
        """Returns missing_frontmatter error when no frontmatter but fields required."""
        doc = Document(
            path=tmp_path / "doc.md",
            content="# Just content",
            frontmatter=None,
        )
        config = {"required_fields": ["title"]}

        validator = FrontmatterValidator()
        errors = validator.validate(doc, config)

        assert any(e.error_type == "missing_frontmatter" for e in errors)

    def test_no_error_when_no_required_fields(self, tmp_path: Path) -> None:
        """No error when no required fields configured."""
        doc = Document(
            path=tmp_path / "doc.md",
            content="# Just content",
            frontmatter=None,
        )
        config = {}  # No required fields

        validator = FrontmatterValidator()
        errors = validator.validate(doc, config)

        assert len(errors) == 0


class TestFrontmatterValidatorAllowedValues:
    """Tests for allowed values validation.

    Contract: Returns ValidationError for field values not in allowed list.
    """

    def test_invalid_value(self, tmp_path: Path) -> None:
        """Returns error for value not in allowed list."""
        content = """---
status: invalid
---

# Content
"""
        doc = Document(
            path=tmp_path / "doc.md",
            content=content,
            frontmatter=parse_frontmatter(content),
        )
        config = {"allowed_values": {"status": ["draft", "published", "archived"]}}

        validator = FrontmatterValidator()
        errors = validator.validate(doc, config)

        assert any(e.error_type == "invalid_value" for e in errors)
        assert any("invalid" in e.message and "status" in e.message for e in errors)

    def test_valid_value(self, tmp_path: Path) -> None:
        """No error for valid value."""
        content = """---
status: published
---

# Content
"""
        doc = Document(
            path=tmp_path / "doc.md",
            content=content,
            frontmatter=parse_frontmatter(content),
        )
        config = {"allowed_values": {"status": ["draft", "published", "archived"]}}

        validator = FrontmatterValidator()
        errors = validator.validate(doc, config)

        assert not any(e.error_type == "invalid_value" for e in errors)

    def test_invalid_value_in_list_field(self, tmp_path: Path) -> None:
        """Returns error for invalid value in list field."""
        content = """---
tags: [valid, invalid_tag]
---

# Content
"""
        doc = Document(
            path=tmp_path / "doc.md",
            content=content,
            frontmatter=parse_frontmatter(content),
        )
        config = {"allowed_values": {"tags": ["valid", "also_valid"]}}

        validator = FrontmatterValidator()
        errors = validator.validate(doc, config)

        assert any(e.error_type == "invalid_value" for e in errors)
        assert any("invalid_tag" in e.message for e in errors)

    def test_all_valid_values_in_list(self, tmp_path: Path) -> None:
        """No error when all list values are valid."""
        content = """---
tags: [valid, also_valid]
---

# Content
"""
        doc = Document(
            path=tmp_path / "doc.md",
            content=content,
            frontmatter=parse_frontmatter(content),
        )
        config = {"allowed_values": {"tags": ["valid", "also_valid", "another"]}}

        validator = FrontmatterValidator()
        errors = validator.validate(doc, config)

        assert not any(e.error_type == "invalid_value" for e in errors)

    def test_missing_field_not_validated_for_allowed_values(self, tmp_path: Path) -> None:
        """Missing field doesn't trigger allowed_values error."""
        content = """---
title: Test
---

# Content
"""
        doc = Document(
            path=tmp_path / "doc.md",
            content=content,
            frontmatter=parse_frontmatter(content),
        )
        config = {"allowed_values": {"status": ["draft", "published"]}}

        validator = FrontmatterValidator()
        errors = validator.validate(doc, config)

        # Should not have error since status field is missing (not invalid)
        assert not any(e.error_type == "invalid_value" for e in errors)


class TestFrontmatterValidatorIdentifier:
    """Tests for error identifier in validation errors.

    Contract: ValidationError.identifier should be the filename.
    """

    def test_identifier_is_filename(self, tmp_path: Path) -> None:
        """Error identifier is the filename."""
        content = """---
title: Test
---

# Content
"""
        doc = Document(
            path=tmp_path / "my_document.md",
            content=content,
            frontmatter=parse_frontmatter(content),
        )
        config = {"required_fields": ["missing_field"]}

        validator = FrontmatterValidator()
        errors = validator.validate(doc, config)

        assert len(errors) > 0
        assert errors[0].identifier == "my_document.md"
