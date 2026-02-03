"""
ADR (Architecture Decision Record) validator.

Validates ADR documents for:
- Required YAML frontmatter fields (id, title, date, status, tags)
- Valid status values
- Date format (YYYY-MM-DD)
- Valid tags from allowed list
- Required markdown sections (Context, Decision, Consequences, etc.)
- Title consistency between header and frontmatter

Configuration (from adr_config.yaml):
- required_fields: List of required frontmatter fields
- statuses: List of valid status values
- tags: List of valid tags
- required_sections: List of required markdown sections
- date_format: Regex pattern for date validation

This validator is the core of check_adr.py functionality, extracted for reuse.

Usage:
    from vadocs.validators.adr import AdrValidator

    validator = AdrValidator()
    config = load_config("adr_config.yaml")
    errors = validator.validate(document, config)
"""

import re

from vadocs.core.models import Document, ValidationError
from vadocs.core.parsing import SECTION_HEADER_PATTERN, parse_frontmatter
from vadocs.validators.base import Validator


class AdrValidator(Validator):
    """Validator for Architecture Decision Records (ADRs).

    Validates ADR documents against a configuration that defines:
    - Required frontmatter fields
    - Valid statuses and tags
    - Required document sections
    - Date format
    """

    name = "adr"

    def supports(self, document: Document) -> bool:
        """Check if document is an ADR.

        Supports documents with doc_type="adr" or files matching adr_*.md pattern.
        """
        if document.doc_type == "adr":
            return True
        # Also check filename pattern
        return document.path.name.startswith("adr_") and document.path.suffix == ".md"

    def validate(self, document: Document, config: dict) -> list[ValidationError]:
        """Validate ADR document.

        Args:
            document: The ADR document to validate.
            config: Configuration with valid statuses, tags, required fields, etc.

        Returns:
            List of validation errors found.
        """
        errors: list[ValidationError] = []

        # Extract ADR number from filename or frontmatter
        adr_number = self._extract_adr_number(document)

        # Parse frontmatter if not already parsed
        frontmatter = document.frontmatter
        if frontmatter is None:
            frontmatter = parse_frontmatter(document.content)

        # Validate required fields
        errors.extend(self._validate_required_fields(adr_number, frontmatter, config))

        # Validate status
        errors.extend(self._validate_status(adr_number, frontmatter, config))

        # Validate date format
        errors.extend(self._validate_date(adr_number, frontmatter, config))

        # Validate tags
        errors.extend(self._validate_tags(adr_number, frontmatter, config))

        # Validate required sections
        errors.extend(self._validate_sections(adr_number, document.content, config))

        # Validate title consistency
        errors.extend(self._validate_title(adr_number, document.content, frontmatter))

        return errors

    def _extract_adr_number(self, document: Document) -> int:
        """Extract ADR number from document."""
        # Try frontmatter first
        if document.frontmatter and "id" in document.frontmatter:
            try:
                return int(document.frontmatter["id"])
            except (ValueError, TypeError):
                pass

        # Try filename pattern adr_XXXXX_*.md
        import re

        match = re.match(r"adr_(\d+)_", document.path.name)
        if match:
            return int(match.group(1))

        # Try header pattern # ADR-XXXXX:
        header_match = re.search(r"^#\s+ADR-(\d+):", document.content, re.MULTILINE)
        if header_match:
            return int(header_match.group(1))

        return 0  # Unknown

    def _validate_required_fields(
        self, adr_number: int, frontmatter: dict | None, config: dict
    ) -> list[ValidationError]:
        """Check required frontmatter fields are present."""
        errors = []
        required_fields = config.get("required_fields", [])

        if frontmatter is None:
            for field in required_fields:
                errors.append(
                    ValidationError(
                        identifier=adr_number,
                        error_type="missing_field",
                        message=f"ADR {adr_number} missing required field: '{field}'",
                    )
                )
            return errors

        for field in required_fields:
            if field not in frontmatter:
                errors.append(
                    ValidationError(
                        identifier=adr_number,
                        error_type="missing_field",
                        message=f"ADR {adr_number} missing required field: '{field}'",
                    )
                )

        return errors

    def _validate_status(
        self, adr_number: int, frontmatter: dict | None, config: dict
    ) -> list[ValidationError]:
        """Check status is valid."""
        errors = []
        valid_statuses = set(config.get("statuses", []))

        if not valid_statuses:
            return errors  # No validation if statuses not configured

        if frontmatter is None:
            return errors  # Missing frontmatter handled elsewhere

        status = frontmatter.get("status")
        if status is None:
            return errors  # Missing field handled elsewhere

        status_lower = str(status).lower()
        if status_lower not in valid_statuses:
            errors.append(
                ValidationError(
                    identifier=adr_number,
                    error_type="invalid_status",
                    message=f"ADR {adr_number} has invalid status: '{status}' "
                    f"(valid: {', '.join(sorted(valid_statuses))})",
                )
            )

        return errors

    def _validate_date(
        self, adr_number: int, frontmatter: dict | None, config: dict
    ) -> list[ValidationError]:
        """Check date format is YYYY-MM-DD."""
        errors = []
        date_format = config.get("date_format", r"^\d{4}-\d{2}-\d{2}$")

        if frontmatter is None:
            return errors

        date_value = frontmatter.get("date")
        if date_value is None:
            return errors

        date_str = str(date_value)
        if not re.match(date_format, date_str):
            errors.append(
                ValidationError(
                    identifier=adr_number,
                    error_type="invalid_date",
                    message=f"ADR {adr_number} has invalid date format: '{date_str}' "
                    "(expected YYYY-MM-DD)",
                )
            )

        return errors

    def _validate_tags(
        self, adr_number: int, frontmatter: dict | None, config: dict
    ) -> list[ValidationError]:
        """Check all tags are from allowed list."""
        errors = []
        valid_tags = set(config.get("tags", []))

        if not valid_tags:
            return errors  # No validation if tags not configured

        if frontmatter is None:
            return errors

        tags = frontmatter.get("tags")
        if tags is None:
            return errors

        if not isinstance(tags, list):
            tags = [tags]

        if len(tags) == 0:
            errors.append(
                ValidationError(
                    identifier=adr_number,
                    error_type="empty_tags",
                    message=f"ADR {adr_number} has empty tags list (at least one tag required)",
                )
            )
            return errors

        for tag in tags:
            if tag not in valid_tags:
                errors.append(
                    ValidationError(
                        identifier=adr_number,
                        error_type="invalid_tag",
                        message=f"ADR {adr_number} has invalid tag: '{tag}' "
                        f"(valid: {', '.join(sorted(valid_tags))})",
                    )
                )

        return errors

    def _validate_sections(
        self, adr_number: int, content: str, config: dict
    ) -> list[ValidationError]:
        """Check required sections are present."""
        errors = []
        required_sections = config.get("required_sections", [])

        if not required_sections:
            return errors

        # Find all section headers
        found_sections = set()
        for match in SECTION_HEADER_PATTERN.finditer(content):
            found_sections.add(match.group(1))

        for section in required_sections:
            if section not in found_sections:
                errors.append(
                    ValidationError(
                        identifier=adr_number,
                        error_type="missing_section",
                        message=f"ADR {adr_number} missing required section: '## {section}'",
                    )
                )

        return errors

    def _validate_title(
        self, adr_number: int, content: str, frontmatter: dict | None
    ) -> list[ValidationError]:
        """Check title consistency between header and frontmatter."""
        errors = []

        if frontmatter is None:
            return errors

        frontmatter_title = frontmatter.get("title")
        if frontmatter_title is None:
            return errors

        # Extract title from header
        header_match = re.search(r"^#\s+ADR-\d+:\s+(.+)$", content, re.MULTILINE)
        if not header_match:
            return errors

        header_title = header_match.group(1).strip()

        if frontmatter_title != header_title:
            errors.append(
                ValidationError(
                    identifier=adr_number,
                    error_type="title_mismatch",
                    message=f"ADR {adr_number} has mismatched titles: "
                    f"header='{header_title}', frontmatter='{frontmatter_title}'",
                )
            )

        return errors
