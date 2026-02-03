"""
Base class and protocol for vadocs validators.

Validators are plugins that check documentation for issues. They receive a
Document and configuration, and return a list of ValidationErrors.

Implementing a custom validator:
1. Subclass Validator
2. Set the `name` class attribute
3. Implement `validate()` to return validation errors
4. Implement `supports()` to indicate which document types are supported
5. Register via entry point in pyproject.toml

Example:
    class MyValidator(Validator):
        name = "my_validator"

        def validate(self, document: Document, config: dict) -> list[ValidationError]:
            errors = []
            if "required_field" not in document.frontmatter:
                errors.append(ValidationError(
                    identifier=document.path.name,
                    error_type="missing_field",
                    message="Missing required_field",
                ))
            return errors

        def supports(self, document: Document) -> bool:
            return document.doc_type == "my_doc_type"

Design notes:
- Validators are stateless; all context comes from arguments
- The config dict allows repo-specific customization (e.g., valid statuses)
- supports() enables selective validation based on document type
- ValidationErrors should have actionable messages

Protocol vs ABC:
- ValidatorProtocol is for type checking duck-typed validators
- Validator ABC provides default implementations and enforces interface
"""

from abc import ABC, abstractmethod
from typing import Protocol

from vadocs.core.models import Document, ValidationError


class ValidatorProtocol(Protocol):
    """Protocol for validator plugins (for duck typing)."""

    name: str

    def validate(self, document: Document, config: dict) -> list[ValidationError]:
        """Run validation on document."""
        ...

    def supports(self, document: Document) -> bool:
        """Return True if this validator can handle this document type."""
        ...


class Validator(ABC):
    """Abstract base class for validators.

    Subclass this to create a new validator. You must implement:
    - validate(): Returns list of validation errors
    - supports(): Returns True if validator handles this document type

    Attributes:
        name: Unique identifier for this validator (used in config/CLI).
    """

    name: str = "base"

    @abstractmethod
    def validate(self, document: Document, config: dict) -> list[ValidationError]:
        """Run validation on document.

        Args:
            document: The document to validate.
            config: Configuration dictionary (repo-specific settings).

        Returns:
            List of ValidationError objects for any issues found.
            Empty list if document is valid.
        """

    @abstractmethod
    def supports(self, document: Document) -> bool:
        """Check if this validator supports the given document.

        Args:
            document: The document to check.

        Returns:
            True if this validator can validate this document type.
        """

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name!r})>"
