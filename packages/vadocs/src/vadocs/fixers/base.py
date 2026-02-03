"""
Base class and protocol for vadocs fixers.

Fixers are plugins that automatically correct documentation issues. They
receive a Document and configuration, and return a SyncResult indicating
what changes were made.

Implementing a custom fixer:
1. Subclass Fixer
2. Set the `name` class attribute
3. Implement `fix()` to perform corrections and return SyncResult
4. Implement `supports()` to indicate which document types are supported
5. Register via entry point in pyproject.toml

Example:
    class MyFixer(Fixer):
        name = "my_fixer"

        def fix(self, document: Document, config: dict, dry_run: bool = False) -> SyncResult:
            changes = []
            errors = []

            # Check for issue and fix it
            if needs_fix(document):
                if not dry_run:
                    apply_fix(document)
                changes.append("Fixed the issue")

            return SyncResult(
                modified=len(changes) > 0 and not dry_run,
                changes=changes,
                errors=errors,
            )

        def supports(self, document: Document) -> bool:
            return document.doc_type == "my_doc_type"

Design notes:
- Fixers should support dry_run mode to preview changes
- SyncResult.changes should be human-readable descriptions
- Fixers should be idempotent: running twice produces same result
- errors list is for issues that couldn't be automatically fixed

Protocol vs ABC:
- FixerProtocol is for type checking duck-typed fixers
- Fixer ABC provides default implementations and enforces interface
"""

from abc import ABC, abstractmethod
from typing import Protocol

from vadocs.core.models import Document, SyncResult


class FixerProtocol(Protocol):
    """Protocol for fixer plugins (for duck typing)."""

    name: str

    def fix(self, document: Document, config: dict, dry_run: bool = False) -> SyncResult:
        """Apply fixes to document."""
        ...

    def supports(self, document: Document) -> bool:
        """Return True if this fixer can handle this document type."""
        ...


class Fixer(ABC):
    """Abstract base class for fixers.

    Subclass this to create a new fixer. You must implement:
    - fix(): Applies fixes and returns SyncResult
    - supports(): Returns True if fixer handles this document type

    Attributes:
        name: Unique identifier for this fixer (used in config/CLI).
    """

    name: str = "base"

    @abstractmethod
    def fix(self, document: Document, config: dict, dry_run: bool = False) -> SyncResult:
        """Apply fixes to document.

        Args:
            document: The document to fix.
            config: Configuration dictionary (repo-specific settings).
            dry_run: If True, report what would change without modifying files.

        Returns:
            SyncResult with changes made and any errors encountered.
        """

    @abstractmethod
    def supports(self, document: Document) -> bool:
        """Check if this fixer supports the given document.

        Args:
            document: The document to check.

        Returns:
            True if this fixer can fix this document type.
        """

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name!r})>"
