"""
Core data models for vadocs.

This module defines the fundamental data structures used throughout vadoc:

- Document: Represents a documentation file (ADR, RFC, etc.) with its content
  and parsed metadata. This is the primary input to validators and fixers.

- ValidationError: Represents a single validation failure. Validators return
  lists of these. The error_type field enables programmatic categorization.

- SyncField: Represents a field that may exist in both YAML frontmatter and
  markdown body (e.g., title, status, date). Used by the sync engine to
  detect mismatches and determine sync direction.

- SyncResult: Return type for sync operations. Includes both the list of
  changes made and any errors encountered.

Design notes:
- All models are dataclasses for simplicity and immutability
- Optional fields use None rather than sentinel values
- The is_synced property on SyncField encapsulates the sync logic

Extension points:
- Add new fields to Document for additional metadata (e.g., parsed sections)
- ValidationError.error_type can be extended with new categories
- SyncField could be subclassed for field-specific sync logic
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Document:
    """Represents a documentation file.

    Attributes:
        path: Path to the file.
        content: Raw file content.
        frontmatter: Parsed YAML frontmatter (if present).
        doc_type: Document type identifier (e.g., "adr", "rfc").
    """

    path: Path
    content: str
    frontmatter: dict | None = None
    doc_type: str | None = None


@dataclass
class ValidationError:
    """Represents a validation error.

    Attributes:
        identifier: Numeric or string identifier for the error context (e.g., ADR number).
        error_type: Category of error (e.g., "missing_field", "invalid_status").
        message: Human-readable error description.
    """

    identifier: int | str
    error_type: str
    message: str


@dataclass
class SyncField:
    """Represents a field that can be synchronized between YAML and markdown.

    Attributes:
        name: Field name.
        yaml_value: Value from YAML frontmatter.
        markdown_value: Value from markdown content.
    """

    name: str
    yaml_value: str | None = None
    markdown_value: str | None = None

    @property
    def is_synced(self) -> bool:
        """Return True if values match or only one source has a value.

        Returns False if both are None (no data to sync) or if values differ.
        """
        if self.yaml_value is None and self.markdown_value is None:
            return False
        if self.yaml_value is None or self.markdown_value is None:
            return True
        return self.yaml_value == self.markdown_value


@dataclass
class SyncResult:
    """Represents the result of a sync operation.

    Attributes:
        modified: True if any changes were made.
        changes: List of changes made (human-readable descriptions).
        errors: List of errors encountered during sync.
    """

    modified: bool
    changes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
