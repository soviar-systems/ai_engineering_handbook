"""
Tests for MyST glossary term validators.

Contract being tested:
- MystGlossaryValidator.supports(): Returns True for markdown files
- AdrTermValidator.validate(): Returns ValidationErrors for broken {term}`ADR XXXXX` references
  (should use hyphen separator like {term}`ADR-26001`)
"""

from pathlib import Path

import pytest

from vadocs import AdrTermValidator, Document, MystGlossaryValidator, ValidationError


class TestMystGlossaryValidatorSupports:
    """Tests for MystGlossaryValidator.supports() method.

    Contract: Returns True for markdown files (.md extension).
    """

    def test_supports_markdown_file(self, tmp_path: Path) -> None:
        """Supports markdown files."""
        doc = Document(
            path=tmp_path / "doc.md",
            content="# Content",
        )
        validator = AdrTermValidator()
        assert validator.supports(doc) is True

    def test_not_supports_non_markdown_file(self, tmp_path: Path) -> None:
        """Does not support non-markdown files."""
        doc = Document(
            path=tmp_path / "doc.txt",
            content="# Content",
        )
        validator = AdrTermValidator()
        assert validator.supports(doc) is False

    def test_not_supports_other_extensions(self, tmp_path: Path) -> None:
        """Does not support other file extensions."""
        for ext in [".rst", ".html", ".py", ".yaml"]:
            doc = Document(
                path=tmp_path / f"doc{ext}",
                content="# Content",
            )
            validator = AdrTermValidator()
            assert validator.supports(doc) is False


class TestAdrTermValidatorBrokenReferences:
    """Tests for AdrTermValidator detecting broken term references.

    Contract: Detects {term}`ADR XXXXX` (space separator) and suggests {term}`ADR-XXXXX` (hyphen).
    """

    def test_detects_broken_term_reference_with_space(self, tmp_path: Path) -> None:
        """Detects broken reference using space instead of hyphen."""
        content = """# Document

See {term}`ADR 26001` for details.
"""
        doc = Document(
            path=tmp_path / "doc.md",
            content=content,
        )
        config = {}

        validator = AdrTermValidator()
        errors = validator.validate(doc, config)

        assert len(errors) == 1
        assert errors[0].error_type == "broken_term_reference"
        assert "ADR-26001" in errors[0].message  # Suggested fix

    def test_multiple_broken_references(self, tmp_path: Path) -> None:
        """Detects multiple broken references in same document."""
        content = """# Document

See {term}`ADR 26001` and {term}`ADR 26002` for details.
"""
        doc = Document(
            path=tmp_path / "doc.md",
            content=content,
        )
        config = {}

        validator = AdrTermValidator()
        errors = validator.validate(doc, config)

        assert len(errors) == 2
        assert any(e.identifier == 26001 for e in errors)
        assert any(e.identifier == 26002 for e in errors)

    def test_broken_reference_on_multiple_lines(self, tmp_path: Path) -> None:
        """Detects broken references across multiple lines."""
        content = """# Document

First reference: {term}`ADR 26001`

Second reference: {term}`ADR 26002`
"""
        doc = Document(
            path=tmp_path / "doc.md",
            content=content,
        )
        config = {}

        validator = AdrTermValidator()
        errors = validator.validate(doc, config)

        assert len(errors) == 2

    def test_no_error_for_correct_reference(self, tmp_path: Path) -> None:
        """No error for correctly formatted reference."""
        content = """# Document

See {term}`ADR-26001` for details.
"""
        doc = Document(
            path=tmp_path / "doc.md",
            content=content,
        )
        config = {}

        validator = AdrTermValidator()
        errors = validator.validate(doc, config)

        assert len(errors) == 0

    def test_no_error_for_non_adr_terms(self, tmp_path: Path) -> None:
        """No error for other term references."""
        content = """# Document

See {term}`some_term` and {term}`another term` for details.
"""
        doc = Document(
            path=tmp_path / "doc.md",
            content=content,
        )
        config = {}

        validator = AdrTermValidator()
        errors = validator.validate(doc, config)

        assert len(errors) == 0


class TestAdrTermValidatorConfiguration:
    """Tests for AdrTermValidator configuration options.

    Contract: Supports configurable separator and pattern via term_reference config.
    """

    def test_custom_separator(self, tmp_path: Path) -> None:
        """Uses custom separator from config."""
        content = """# Document

See {term}`ADR 26001` for details.
"""
        doc = Document(
            path=tmp_path / "doc.md",
            content=content,
        )
        config = {
            "term_reference": {
                "separator": "_",
            }
        }

        validator = AdrTermValidator()
        errors = validator.validate(doc, config)

        assert len(errors) == 1
        assert "ADR_26001" in errors[0].message  # Custom separator in suggestion

    def test_custom_pattern(self, tmp_path: Path) -> None:
        """Uses custom pattern from config."""
        content = """# Document

See {term}`RFC 1234` for details.
"""
        doc = Document(
            path=tmp_path / "doc.md",
            content=content,
        )
        config = {
            "term_reference": {
                "broken_pattern": r"\{term\}`RFC (\d+)`",
                "separator": "-",
            }
        }

        # Need to create a validator that handles RFC pattern
        # For now, using default AdrTermValidator won't catch this
        validator = AdrTermValidator()
        errors = validator.validate(doc, config)

        # With custom pattern, it should detect RFC references
        assert len(errors) == 1


class TestAdrTermValidatorErrorMessage:
    """Tests for error message format.

    Contract: Error message includes file path, line number, original, and suggestion.
    """

    def test_error_message_includes_line_number(self, tmp_path: Path) -> None:
        """Error message includes line number."""
        content = """# Document

Line 3 here.

See {term}`ADR 26001` for details.
"""
        doc = Document(
            path=tmp_path / "doc.md",
            content=content,
        )
        config = {}

        validator = AdrTermValidator()
        errors = validator.validate(doc, config)

        assert len(errors) == 1
        # Line 5 contains the broken reference
        assert ":5:" in errors[0].message or "5:" in errors[0].message

    def test_error_message_includes_original_and_suggestion(self, tmp_path: Path) -> None:
        """Error message includes original text and suggested fix."""
        content = """See {term}`ADR 26001` for details."""
        doc = Document(
            path=tmp_path / "doc.md",
            content=content,
        )
        config = {}

        validator = AdrTermValidator()
        errors = validator.validate(doc, config)

        assert len(errors) == 1
        assert "{term}`ADR 26001`" in errors[0].message
        assert "{term}`ADR-26001`" in errors[0].message
