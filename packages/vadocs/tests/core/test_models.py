"""
Tests for vadoc core models.

Contract being tested:
- Document: Represents a documentation file with path, content, and frontmatter
- ValidationError: Represents a validation error with identifier, type, and message
- SyncField: Represents a field that can be synchronized between sources
- SyncResult: Represents the result of a sync operation
"""

from pathlib import Path

import pytest


class TestDocument:
    """Tests for the Document data class.

    Contract: Document represents a documentation file with:
    - path: Path to the file
    - content: Raw file content
    - frontmatter: Parsed YAML frontmatter (optional)
    - doc_type: Document type identifier (e.g., "adr", "rfc")
    """

    def test_document_creation_with_all_fields(self, tmp_path: Path) -> None:
        """Document can be created with all fields."""
        from vadocs.core.models import Document

        path = tmp_path / "test.md"
        content = "# Test"
        frontmatter = {"title": "Test"}

        doc = Document(path=path, content=content, frontmatter=frontmatter, doc_type="adr")

        assert doc.path == path
        assert doc.content == content
        assert doc.frontmatter == frontmatter
        assert doc.doc_type == "adr"

    def test_document_creation_minimal(self, tmp_path: Path) -> None:
        """Document can be created with minimal fields."""
        from vadocs.core.models import Document

        path = tmp_path / "test.md"
        content = "# Test"

        doc = Document(path=path, content=content)

        assert doc.path == path
        assert doc.content == content
        assert doc.frontmatter is None
        assert doc.doc_type is None


class TestValidationError:
    """Tests for the ValidationError data class.

    Contract: ValidationError represents a validation error with:
    - identifier: Numeric or string identifier for the error context
    - error_type: Category of error (e.g., "missing_field", "invalid_status")
    - message: Human-readable error description
    """

    def test_validation_error_creation(self) -> None:
        """ValidationError can be created with required fields."""
        from vadocs.core.models import ValidationError

        error = ValidationError(
            identifier=26001,
            error_type="missing_field",
            message="ADR 26001 missing required field: 'title'",
        )

        assert error.identifier == 26001
        assert error.error_type == "missing_field"
        assert "title" in error.message

    def test_validation_error_with_string_identifier(self) -> None:
        """ValidationError accepts string identifier."""
        from vadocs.core.models import ValidationError

        error = ValidationError(
            identifier="doc-001",
            error_type="invalid_format",
            message="Document has invalid format",
        )

        assert error.identifier == "doc-001"


class TestSyncField:
    """Tests for the SyncField data class.

    Contract: SyncField represents a field that can be synced:
    - name: Field name
    - yaml_value: Value from YAML frontmatter (optional)
    - markdown_value: Value from markdown content (optional)
    - is_synced: True if values match or only one exists
    """

    def test_sync_field_both_values_match(self) -> None:
        """SyncField is synced when both values match."""
        from vadocs.core.models import SyncField

        field = SyncField(name="title", yaml_value="Test", markdown_value="Test")

        assert field.is_synced is True

    def test_sync_field_values_mismatch(self) -> None:
        """SyncField is not synced when values differ."""
        from vadocs.core.models import SyncField

        field = SyncField(name="title", yaml_value="Test1", markdown_value="Test2")

        assert field.is_synced is False

    def test_sync_field_only_yaml(self) -> None:
        """SyncField is synced when only YAML value exists."""
        from vadocs.core.models import SyncField

        field = SyncField(name="title", yaml_value="Test", markdown_value=None)

        assert field.is_synced is True

    def test_sync_field_only_markdown(self) -> None:
        """SyncField is synced when only markdown value exists."""
        from vadocs.core.models import SyncField

        field = SyncField(name="title", yaml_value=None, markdown_value="Test")

        assert field.is_synced is True

    def test_sync_field_both_none(self) -> None:
        """SyncField is not synced when both values are None."""
        from vadocs.core.models import SyncField

        field = SyncField(name="title", yaml_value=None, markdown_value=None)

        assert field.is_synced is False


class TestSyncResult:
    """Tests for the SyncResult data class.

    Contract: SyncResult represents the result of a sync operation:
    - modified: True if any changes were made
    - changes: List of changes made (human-readable)
    - errors: List of errors encountered
    """

    def test_sync_result_no_changes(self) -> None:
        """SyncResult with no changes."""
        from vadocs.core.models import SyncResult

        result = SyncResult(modified=False, changes=[], errors=[])

        assert result.modified is False
        assert len(result.changes) == 0
        assert len(result.errors) == 0

    def test_sync_result_with_changes(self) -> None:
        """SyncResult with changes."""
        from vadocs.core.models import SyncResult

        result = SyncResult(
            modified=True,
            changes=["Updated title from 'Old' to 'New'"],
            errors=[],
        )

        assert result.modified is True
        assert len(result.changes) == 1

    def test_sync_result_with_errors(self) -> None:
        """SyncResult with errors."""
        from vadocs.core.models import SyncResult

        result = SyncResult(
            modified=False,
            changes=[],
            errors=["Cannot determine authoritative source"],
        )

        assert result.modified is False
        assert len(result.errors) == 1
