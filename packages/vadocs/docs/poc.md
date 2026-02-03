# vadocs v0.1.0 - Proof of Concept

## Motivation

The `ai_engineering_book` repository contains several validation scripts in `tools/scripts/` that share common patterns: YAML frontmatter parsing, configuration loading, validation error reporting. Each script duplicates parsing logic, and the validation functionality cannot be reused in other repositories.

**Solution**: Extract common validation logic into a reusable Python package (`vadocs`) that can be installed via `uv add`.

## Goal

Create a minimal viable package that proves:

1. Installability as a uv dependency from GitHub
2. YAML frontmatter validation works correctly
3. ADR-specific validation (fields, status, tags, sections)
4. Configuration loading from YAML files

## Implementation Summary

- **Core models**: `Document`, `ValidationError`, `SyncField`, `SyncResult`
- **Validators**: `FrontmatterValidator`, `AdrValidator`, `AdrTermValidator`
- **Fixers**: `AdrFixer`, `SyncFixer`
- **Config**: `load_config()` for YAML files
- **Tests**: 79 passing

## What's NOT in v0.1.0

- CLI interface (library-only)
- pyproject.toml `[tool.vadocs]` config loading
- Project scaffolding (`vadocs init`)
- Index sync validation

## Further Steps

- **v0.2.0**: CLI + pyproject.toml config
- **v0.3.0**: Index sync validation
- **v0.4.0**: Additional validators (broken links, jupytext)
- **v1.0.0**: PyPI release, stable API

---

## PoC Validation Checklist

Execute each step manually. Mark `[x]` when passed.

### 1. Installation

```bash
cd /path/to/your/project
uv add "vadocs @ git+https://github.com/USERNAME/vadocs.git"
```

- [ ] **PASS**: Command completes without errors

### 2. Import verification

```bash
uv run python -c "from vadocs import AdrValidator, Document, load_config, parse_frontmatter; print('OK')"
```

- [ ] **PASS**: Prints `OK`

### 3. Config loading

```bash
uv run python -c "
from pathlib import Path
from vadocs import load_config
config = load_config(Path('architecture/adr/adr_config.yaml'))
print('statuses:', config.get('statuses'))
print('required_fields:', config.get('required_fields'))
"
```

- [ ] **PASS**: Prints statuses list (proposed, accepted, etc.)
- [ ] **PASS**: Prints required_fields list (id, title, date, status, tags)

### 4. Valid ADR produces no errors

Pick a known valid ADR file and run:

```bash
uv run python -c "
from pathlib import Path
from vadocs import AdrValidator, Document, load_config, parse_frontmatter

config = load_config(Path('architecture/adr/adr_config.yaml'))
adr_path = Path('architecture/adr/adr_26001_use_myst_markdown.md')  # <-- change to your ADR
content = adr_path.read_text()
doc = Document(path=adr_path, content=content, frontmatter=parse_frontmatter(content), doc_type='adr')
errors = AdrValidator().validate(doc, config)
print(f'Errors: {len(errors)}')
for e in errors: print(f'  [{e.error_type}] {e.message}')
"
```

- [ ] **PASS**: Prints `Errors: 0`

### 5. Missing field detected

Create a test file `/tmp/test_adr.md`:

```markdown
---
id: 99999
title: Test ADR
status: accepted
---

# ADR-99999: Test ADR
```

Run validation:

```bash
uv run python -c "
from pathlib import Path
from vadocs import AdrValidator, Document, load_config, parse_frontmatter

config = load_config(Path('architecture/adr/adr_config.yaml'))
content = Path('/tmp/test_adr.md').read_text()
doc = Document(path=Path('/tmp/test_adr.md'), content=content, frontmatter=parse_frontmatter(content), doc_type='adr')
errors = AdrValidator().validate(doc, config)
print(f'Errors: {len(errors)}')
for e in errors: print(f'  [{e.error_type}] {e.message}')
"
```

- [ ] **PASS**: Reports `missing_field` for `date`
- [ ] **PASS**: Reports `missing_field` for `tags`

### 6. Invalid status detected

Create `/tmp/test_adr_status.md`:

```markdown
---
id: 99999
title: Test ADR
date: 2024-01-15
status: invalid_status
tags: [architecture]
---

# ADR-99999: Test ADR
```

Run validation:

```bash
uv run python -c "
from pathlib import Path
from vadocs import AdrValidator, Document, load_config, parse_frontmatter

config = load_config(Path('architecture/adr/adr_config.yaml'))
content = Path('/tmp/test_adr_status.md').read_text()
doc = Document(path=Path('/tmp/test_adr_status.md'), content=content, frontmatter=parse_frontmatter(content), doc_type='adr')
errors = AdrValidator().validate(doc, config)
for e in errors: print(f'  [{e.error_type}] {e.message}')
"
```

- [ ] **PASS**: Reports `invalid_status` error

### 7. Invalid tag detected

Create `/tmp/test_adr_tag.md`:

```markdown
---
id: 99999
title: Test ADR
date: 2024-01-15
status: accepted
tags: [nonexistent_tag]
---

# ADR-99999: Test ADR
```

Run validation:

```bash
uv run python -c "
from pathlib import Path
from vadocs import AdrValidator, Document, load_config, parse_frontmatter

config = load_config(Path('architecture/adr/adr_config.yaml'))
content = Path('/tmp/test_adr_tag.md').read_text()
doc = Document(path=Path('/tmp/test_adr_tag.md'), content=content, frontmatter=parse_frontmatter(content), doc_type='adr')
errors = AdrValidator().validate(doc, config)
for e in errors: print(f'  [{e.error_type}] {e.message}')
"
```

- [ ] **PASS**: Reports `invalid_tag` error

---

## Result

**Date**: _______________

**Tester**: _______________

**All criteria passed**: [ ] YES / [ ] NO

**Notes**:
