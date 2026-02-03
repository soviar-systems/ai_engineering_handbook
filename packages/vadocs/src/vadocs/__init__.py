"""
vadocs - Documentation validation engine with YAML frontmatter sync.

A general-purpose Python package for validating structured documentation:
- ADR validation
- YAML frontmatter sync
- Extensible for other doc types (RFCs, design docs, changelogs)

Usage:
    from vadocs import AdrValidator, SyncFixer, Document
    from vadocs.core.parsing import parse_frontmatter
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

from vadocs.core.models import Document, SyncField, SyncResult, ValidationError
from vadocs.core.parsing import (
    extract_section_content,
    extract_status,
    parse_frontmatter,
)
from vadocs.fixers.adr_fixer import AdrFixer
from vadocs.fixers.base import Fixer
from vadocs.fixers.sync_fixer import SyncFixer
from vadocs.validators.adr import AdrValidator
from vadocs.validators.base import Validator
from vadocs.validators.frontmatter import FrontmatterValidator
from vadocs.validators.myst_glossary import AdrTermValidator, MystGlossaryValidator
from vadocs.config import load_config

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
    # Config
    "load_config",
    # Version
    "__version__",
]
