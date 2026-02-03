"""
MyST glossary term reference validators.

Validates MyST Markdown glossary cross-references. MyST uses {term}`entry`
syntax to link to glossary definitions. The term must match the glossary
entry exactly, including any separators or formatting.

This module provides:
- MystGlossaryValidator: Base validator for any term reference issues
- AdrTermValidator: ADR-specific validator for ADR-XXXXX references

Common issues:
- Space vs hyphen: {term}`ADR 26001` vs {term}`ADR-26001`
- Case mismatch: {term}`adr-26001` vs {term}`ADR-26001`
- Typos in term names

Configuration for AdrTermValidator:
- term_reference.separator: Expected separator (default: "-")
- term_reference.broken_pattern: Regex to match broken references

Usage:
    from vadocs.validators.myst_glossary import AdrTermValidator

    validator = AdrTermValidator()
    config = {
        "term_reference": {
            "separator": "-",
            "broken_pattern": r"\\{term\\}`ADR (\\d+)`",
        }
    }
    errors = validator.validate(document, config)

Extension points:
- Subclass MystGlossaryValidator for other term reference patterns
- Add new pattern validators as separate classes
"""

import re
from abc import abstractmethod

from vadocs.core.models import Document, ValidationError
from vadocs.validators.base import Validator


class MystGlossaryValidator(Validator):
    """Base validator for MyST glossary term references.

    Subclass this to create validators for specific term reference patterns.
    Override get_patterns() to define what patterns to check for.
    """

    name = "myst_glossary"

    def supports(self, document: Document) -> bool:
        """Check if document may contain MyST term references.

        Supports any markdown document (may contain MyST syntax).
        """
        return document.path.suffix == ".md"

    def validate(self, document: Document, config: dict) -> list[ValidationError]:
        """Validate term references against configured patterns.

        Args:
            document: The document to validate.
            config: Configuration for pattern matching.

        Returns:
            List of validation errors for broken term references.
        """
        errors: list[ValidationError] = []

        patterns = self.get_patterns(config)

        for pattern_info in patterns:
            pattern = pattern_info["pattern"]
            make_suggestion = pattern_info["make_suggestion"]
            error_type = pattern_info.get("error_type", "broken_term_reference")

            compiled = re.compile(pattern)

            for line_num, line in enumerate(document.content.splitlines(), start=1):
                for match in compiled.finditer(line):
                    original = match.group(0)
                    suggested = make_suggestion(match)
                    identifier = pattern_info.get("get_identifier", lambda m: m.group(0))(
                        match
                    )

                    errors.append(
                        ValidationError(
                            identifier=identifier,
                            error_type=error_type,
                            message=f"{document.path}:{line_num}: "
                            f"'{original}' should be '{suggested}'",
                        )
                    )

        return errors

    @abstractmethod
    def get_patterns(self, config: dict) -> list[dict]:
        """Return list of pattern configurations to check.

        Each pattern config is a dict with:
        - pattern: Regex pattern string
        - make_suggestion: Callable(match) -> str for fix suggestion
        - error_type: (optional) Error type string
        - get_identifier: (optional) Callable(match) -> identifier

        Args:
            config: Configuration dictionary.

        Returns:
            List of pattern configuration dicts.
        """


class AdrTermValidator(MystGlossaryValidator):
    """Validator for ADR term references.

    Detects broken {term}`ADR XXXXX` references that should use hyphen
    separator to match glossary entries like ADR-26001.

    This is a specialized validator for the common case of ADR glossary
    references using incorrect separators.
    """

    name = "myst"  # Registered as "myst" for backward compatibility

    # Default patterns
    DEFAULT_BROKEN_PATTERN = r"\{term\}`ADR (\d+)`"
    DEFAULT_SEPARATOR = "-"

    def get_patterns(self, config: dict) -> list[dict]:
        """Return ADR term reference patterns to check.

        Configurable via term_reference section in config:
        - separator: Expected separator (default: "-")
        - broken_pattern: Regex for broken references (default: space separator)
        """
        term_config = config.get("term_reference", {})
        broken_pattern = term_config.get("broken_pattern", self.DEFAULT_BROKEN_PATTERN)
        separator = term_config.get("separator", self.DEFAULT_SEPARATOR)

        return [
            {
                "pattern": broken_pattern,
                "make_suggestion": lambda m, sep=separator: f"{{term}}`ADR{sep}{m.group(1)}`",
                "error_type": "broken_term_reference",
                "get_identifier": lambda m: int(m.group(1)),
            }
        ]


# Alias for entry point registration (backward compatibility)
MystTermValidator = AdrTermValidator
