"""
Generic frontmatter validator.

Validates YAML frontmatter in any markdown document for:
- Presence of required fields
- Field type validation
- Field value validation against allowed values

This is a general-purpose validator that can be configured for any
document type. For ADR-specific validation, use AdrValidator instead.

Configuration:
- required_fields: List of field names that must be present
- field_types: Dict mapping field names to expected types
- allowed_values: Dict mapping field names to lists of allowed values

Usage:
    from vadocs.validators.frontmatter import FrontmatterValidator

    validator = FrontmatterValidator()
    config = {
        "required_fields": ["title", "date"],
        "allowed_values": {"status": ["draft", "published"]},
    }
    errors = validator.validate(document, config)
"""

from vadocs.core.models import Document, ValidationError
from vadocs.core.parsing import parse_frontmatter
from vadocs.validators.base import Validator


class FrontmatterValidator(Validator):
    """Generic validator for YAML frontmatter.

    Validates frontmatter against configurable rules for required fields,
    types, and allowed values.
    """

    name = "frontmatter"

    def supports(self, document: Document) -> bool:
        """Check if document has frontmatter to validate.

        Supports any document with YAML frontmatter.
        """
        # Check if document has frontmatter
        if document.frontmatter is not None:
            return True
        # Try to parse frontmatter from content
        return parse_frontmatter(document.content) is not None

    def validate(self, document: Document, config: dict) -> list[ValidationError]:
        """Validate document frontmatter.

        Args:
            document: The document to validate.
            config: Configuration with required_fields, field_types, allowed_values.

        Returns:
            List of validation errors found.
        """
        errors: list[ValidationError] = []

        # Get identifier for error messages
        identifier = document.path.name

        # Parse frontmatter if not already parsed
        frontmatter = document.frontmatter
        if frontmatter is None:
            frontmatter = parse_frontmatter(document.content)

        if frontmatter is None:
            # Check if frontmatter is required
            required_fields = config.get("required_fields", [])
            if required_fields:
                errors.append(
                    ValidationError(
                        identifier=identifier,
                        error_type="missing_frontmatter",
                        message=f"{identifier}: Missing required YAML frontmatter",
                    )
                )
            return errors

        # Validate required fields
        errors.extend(self._validate_required_fields(identifier, frontmatter, config))

        # Validate allowed values
        errors.extend(self._validate_allowed_values(identifier, frontmatter, config))

        return errors

    def _validate_required_fields(
        self, identifier: str, frontmatter: dict, config: dict
    ) -> list[ValidationError]:
        """Check required fields are present."""
        errors = []
        required_fields = config.get("required_fields", [])

        for field in required_fields:
            if field not in frontmatter:
                errors.append(
                    ValidationError(
                        identifier=identifier,
                        error_type="missing_field",
                        message=f"{identifier}: Missing required field: '{field}'",
                    )
                )

        return errors

    def _validate_allowed_values(
        self, identifier: str, frontmatter: dict, config: dict
    ) -> list[ValidationError]:
        """Check field values are from allowed lists."""
        errors = []
        allowed_values = config.get("allowed_values", {})

        for field, allowed in allowed_values.items():
            if field not in frontmatter:
                continue

            value = frontmatter[field]
            # Handle list values (e.g., tags)
            if isinstance(value, list):
                for item in value:
                    if item not in allowed:
                        errors.append(
                            ValidationError(
                                identifier=identifier,
                                error_type="invalid_value",
                                message=f"{identifier}: Invalid value '{item}' for field '{field}' "
                                f"(allowed: {', '.join(str(v) for v in sorted(allowed))})",
                            )
                        )
            else:
                if value not in allowed:
                    errors.append(
                        ValidationError(
                            identifier=identifier,
                            error_type="invalid_value",
                            message=f"{identifier}: Invalid value '{value}' for field '{field}' "
                            f"(allowed: {', '.join(str(v) for v in sorted(allowed))})",
                        )
                    )

        return errors
