"""
vadoc - Documentation validation engine with YAML frontmatter sync.

A general-purpose Python package for validating structured documentation:
- ADR validation
- YAML frontmatter sync
- Extensible for other doc types (RFCs, design docs, changelogs)

Usage:
    from vadoc import AdrValidator, SyncFixer, Document
    from vadoc.core.parsing import parse_frontmatter
    from pathlib import Path

    # Load document
    path = Path("architecture/adr/adr_26001_example.md")
    content = path.read_text()
    doc = Document(
        path=path,
        content=content,
        frontmatter=parse_frontmatter(content),
        doc_type="adr"
    )

    # Validate
    validator = AdrValidator()
    errors = validator.validate(doc, config)

    # Fix (with dry-run)
    fixer = SyncFixer()
    result = fixer.fix(doc, config, dry_run=True)
"""

from vadoc.core.models import Document, SyncField, SyncResult, ValidationError
from vadoc.core.parsing import (
    extract_section_content,
    extract_status,
    parse_frontmatter,
)
from vadoc.fixers.adr_fixer import AdrFixer
from vadoc.fixers.base import Fixer
from vadoc.fixers.sync_fixer import SyncFixer
from vadoc.validators.adr import AdrValidator
from vadoc.validators.base import Validator
from vadoc.validators.frontmatter import FrontmatterValidator
from vadoc.validators.myst_glossary import AdrTermValidator, MystGlossaryValidator

__version__ = "0.1.0"

__all__ = [
    # Models
    "Document",
    "ValidationError",
    "SyncField",
    "SyncResult",
    # Parsing
    "parse_frontmatter",
    "extract_status",
    "extract_section_content",
    # Validators
    "Validator",
    "AdrValidator",
    "FrontmatterValidator",
    "MystGlossaryValidator",
    "AdrTermValidator",
    # Fixers
    "Fixer",
    "AdrFixer",
    "SyncFixer",
    # Version
    "__version__",
]
