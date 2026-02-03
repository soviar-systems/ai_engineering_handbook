"""
Integration tests for vadocs PoC.

These tests demonstrate the full workflow:
1. Load config from YAML file
2. Create a Document with frontmatter
3. Validate using validators
4. Verify correct errors are returned

This proves vadocs can be used as a library for frontmatter validation.
"""

from pathlib import Path

import pytest

from vadocs import (
    AdrValidator,
    Document,
    FrontmatterValidator,
    load_config,
    parse_frontmatter,
)


@pytest.fixture
def sample_adr_config() -> dict:
    """Sample ADR configuration matching adr_config.yaml structure."""
    return {
        "required_fields": ["id", "title", "date", "status", "tags"],
        "statuses": ["proposed", "accepted", "rejected", "superseded", "deprecated"],
        "tags": ["architecture", "security", "testing", "documentation"],
        "date_format": r"^\d{4}-\d{2}-\d{2}$",
        "required_sections": ["Status", "Context", "Decision", "Consequences"],
    }


class TestFrontmatterValidationWorkflow:
    """Integration tests for YAML frontmatter validation workflow."""

    def test_valid_frontmatter_passes(self, tmp_path: Path, sample_adr_config: dict) -> None:
        """Valid frontmatter produces no errors."""
        content = """---
id: 26001
title: Test ADR
date: 2024-01-15
status: accepted
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

        validator = AdrValidator()
        errors = validator.validate(doc, sample_adr_config)

        assert len(errors) == 0

    def test_missing_required_field_detected(
        self, tmp_path: Path, sample_adr_config: dict
    ) -> None:
        """Missing required field produces ValidationError."""
        content = """---
id: 26001
title: Test ADR
status: accepted
---

# ADR-26001: Test ADR
"""
        doc = Document(
            path=tmp_path / "adr_26001_test.md",
            content=content,
            frontmatter=parse_frontmatter(content),
            doc_type="adr",
        )

        validator = AdrValidator()
        errors = validator.validate(doc, sample_adr_config)

        # Missing: date, tags, required sections
        assert len(errors) > 0
        assert any(e.error_type == "missing_field" for e in errors)

    def test_invalid_status_detected(
        self, tmp_path: Path, sample_adr_config: dict
    ) -> None:
        """Invalid status produces ValidationError."""
        content = """---
id: 26001
title: Test ADR
date: 2024-01-15
status: invalid_status
tags: [architecture]
---

# ADR-26001: Test ADR
"""
        doc = Document(
            path=tmp_path / "adr_26001_test.md",
            content=content,
            frontmatter=parse_frontmatter(content),
            doc_type="adr",
        )

        validator = AdrValidator()
        errors = validator.validate(doc, sample_adr_config)

        assert any(e.error_type == "invalid_status" for e in errors)

    def test_invalid_tag_detected(
        self, tmp_path: Path, sample_adr_config: dict
    ) -> None:
        """Invalid tag produces ValidationError."""
        content = """---
id: 26001
title: Test ADR
date: 2024-01-15
status: accepted
tags: [invalid_tag]
---

# ADR-26001: Test ADR
"""
        doc = Document(
            path=tmp_path / "adr_26001_test.md",
            content=content,
            frontmatter=parse_frontmatter(content),
            doc_type="adr",
        )

        validator = AdrValidator()
        errors = validator.validate(doc, sample_adr_config)

        assert any(e.error_type == "invalid_tag" for e in errors)


class TestConfigLoading:
    """Tests for config loading functionality."""

    def test_load_config_from_yaml(self, tmp_path: Path) -> None:
        """load_config reads YAML file correctly."""
        config_content = """
required_fields:
  - title
  - status
statuses:
  - draft
  - published
"""
        config_path = tmp_path / "test_config.yaml"
        config_path.write_text(config_content)

        config = load_config(config_path)

        assert config["required_fields"] == ["title", "status"]
        assert config["statuses"] == ["draft", "published"]

    def test_load_config_file_not_found(self, tmp_path: Path) -> None:
        """load_config raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "nonexistent.yaml")


class TestGenericFrontmatterValidator:
    """Tests for generic FrontmatterValidator (not ADR-specific)."""

    def test_validates_any_document_with_frontmatter(self, tmp_path: Path) -> None:
        """FrontmatterValidator works for any document type."""
        content = """---
title: My Document
author: John Doe
---

# My Document

Content here.
"""
        doc = Document(
            path=tmp_path / "doc.md",
            content=content,
            frontmatter=parse_frontmatter(content),
        )
        config = {
            "required_fields": ["title", "author", "date"],
            "allowed_values": {"author": ["John Doe", "Jane Doe"]},
        }

        validator = FrontmatterValidator()
        errors = validator.validate(doc, config)

        # Missing date field
        assert any(e.error_type == "missing_field" and "date" in e.message for e in errors)
        # Author is valid
        assert not any(e.error_type == "invalid_value" for e in errors)
