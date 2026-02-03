# vadoc

Validation engine for Documentation-as-Code workflows.

## Why vadoc?

**Documentation-as-Code** treats documentation with the same rigor as source code: version control, automated validation, CI/CD pipelines, and programmatic access. But unlike code, documentation lacks mature tooling for enforcement.

**Problem**: Documentation quality degrades silently:
- Missing required sections in ADRs go unnoticed until review
- Metadata in YAML frontmatter drifts from markdown content
- Broken cross-references (glossary terms, internal links) accumulate
- Style and structure inconsistencies spread across large knowledge bases
- RAG pipelines ingest stale or malformed metadata

**Solution**: vadoc provides a validation framework for documentation, similar to what linters and type checkers do for code. It validates structure, enforces consistency, and can auto-fix common issues.

## Target Users

- **Documentation engineers** enforcing quality standards in large knowledge bases
- **Platform teams** building Documentation-as-Code pipelines with CI validation
- **AI/RAG system builders** requiring consistent, machine-readable metadata
- **Teams using ADRs** (Architecture Decision Records) with automated compliance checks
- **Static site maintainers** using MyST, Sphinx, or MkDocs

## Installation

```bash
pip install vadoc
```

## Quick Start

```python
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
```

## Features

### Validators
- **ADR Validation**: Required fields, valid statuses/tags, required sections, date format
- **Frontmatter Validation**: Generic YAML frontmatter rules for any document type
- **MyST Term Validation**: Detect broken `{term}` glossary references

### Fixers
- **Bi-directional Sync**: Synchronize YAML frontmatter ↔ markdown sections (title, status, date)
- **ADR Fixer**: Auto-correct invalid statuses, title mismatches

### Extensibility
- Base `Validator` and `Fixer` classes for custom rules
- Configuration-driven validation (pass your own `adr_config.yaml`)

## v0.2.0 Roadmap

- Plugin discovery via entry points
- CLI with subcommands (`vadoc validate`, `vadoc fix`)
- Third-party plugin support

## License

MIT
