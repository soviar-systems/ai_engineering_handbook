---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.0
kernelspec:
  name: bash
  display_name: Bash
  language: bash
---

# Instruction on check_adr_index.py script

+++

---

Owner: Vadim Rudakov, rudakow.wadim@gmail.com
Version: 0.1.3
Birth: 2026-01-30
Last Modified: 2026-01-30

---

+++

## **1. Architectural Overview: The SVA Principle**

+++

This [script](/tools/scripts/check_adr_index.py) validates that ADR (Architecture Decision Record) files in `architecture/adr/` are synchronized with the index at `architecture/adr_index.md`.

It ensures:
- Every ADR file has a corresponding entry in the index
- No orphan entries exist (entries pointing to non-existent files)
- Links in the index point to the correct file paths
- Index entries are in numerical order

This tool is designed to serve as a quality gate in CI/CD, ensuring the ADR index stays synchronized with ADR files.

:::{hint} **SVA = right tool for the job**
:class: dropdown
It adheres to the **Smallest Viable Architecture (SVA)** principle.

SVA isn't about minimal *code* — it's about **minimal *cognitive and operational overhead***.

* **Zero External Dependencies**: Uses only the Python standard library (`argparse`, `re`, `subprocess`, `sys`, `pathlib`).
* **Pattern-Based Detection**: Parses ADR headers and index entries using regex patterns.
* **Git Integration**: Optional `--check-staged` mode for pre-commit integration.
:::

+++

## **2. Key Capabilities & Logic**

+++

### A. ADR File Discovery

The script discovers ADR files by:

| Step | Description |
|------|-------------|
| **Glob pattern** | Finds files matching `architecture/adr/adr_*.md` |
| **Template exclusion** | Excludes `adr_template.md` |
| **Header parsing** | Extracts number and title from `# ADR NNNNN: Title` header |
| **Sorting** | Returns files sorted by ADR number ascending |

+++

### B. Index Parsing

The script parses the MyST glossary format:

```text
:::{glossary}
ADR 26001
: [Title](path/to/adr_26001_slug.md)

ADR 26002
: [Another Title](path/to/adr_26002_slug.md)
:::
```

| Field | Extraction |
|-------|------------|
| **Number** | From `ADR NNNNN` line |
| **Title** | From markdown link text `[Title]` |
| **Link** | From markdown link path `(/path/to/file.md)` |

+++

### C. Validation Rules

| Error Type | Description |
|------------|-------------|
| `missing_in_index` | ADR file exists but has no index entry |
| `orphan_in_index` | Index entry points to non-existent file |
| `wrong_link` | Index link path doesn't match actual file path |
| `wrong_order` | Index entries are not in numerical order |
| `duplicate_number` | Multiple files have the same ADR number |

+++

### D. Auto-Fix Mode

When run with `--fix`, the script:

1. Reads all valid ADR files
2. Regenerates the index with correct entries
3. Sorts entries by ADR number
4. Removes orphan entries
5. Reports all changes made

+++

## **3. Operational Guide**

+++

### CLI Options

| Option | Description |
|--------|-------------|
| `--verbose`, `-v` | Show detailed output including counts |
| `--fix` | Automatically fix index by regenerating it |
| `--check-staged` | Only check staged ADR files (for pre-commit) |

+++

### Basic Usage

```{code-cell}
cd ../../../
```

```{code-cell}
# Validate ADR index synchronization (default)
env -u VIRTUAL_ENV uv run tools/scripts/check_adr_index.py
```

```{code-cell}
# Verbose output
env -u VIRTUAL_ENV uv run tools/scripts/check_adr_index.py --verbose
```

```{code-cell}
# Auto-fix issues
env -u VIRTUAL_ENV uv run tools/scripts/check_adr_index.py --fix --verbose
```

```{code-cell}
# Check only staged files (for pre-commit)
env -u VIRTUAL_ENV uv run tools/scripts/check_adr_index.py --check-staged --verbose
```

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All ADRs are synchronized with the index |
| `1` | One or more synchronization errors found |

+++

## **4. Validation Layers**

+++

### Pre-commit Hook

The script runs automatically via pre-commit when ADR or index files change:

```yaml
- id: check-adr-index
  name: Check ADR Index
  entry: uv run --active tools/scripts/check_adr_index.py
  language: python
  files: ^architecture/(adr/adr_.*\.md|adr_index\.md)$
  pass_filenames: false
  stages: [pre-commit, manual]
```

+++

### GitHub Actions

The script runs in CI via the `adr-index` job in `quality.yml`:

```yaml
adr-index:
  runs-on: ubuntu-latest
  steps:
    - name: Run ADR Index Check
      run: uv run tools/scripts/check_adr_index.py --verbose
```

+++

## **5. Test Suite**

+++

The [test suite](/tools/tests/test_check_adr_index.py) covers:

| Test Class | Coverage |
|------------|----------|
| `TestGetAdrFiles` | ADR file discovery, template exclusion, sorting |
| `TestParseIndex` | Glossary parsing, entry extraction |
| `TestValidateSync` | Sync validation (missing, orphan, wrong link, order) |
| `TestAutoFixIndex` | Fix mode (add entries, maintain order, remove orphans) |
| `TestCli` | CLI integration (exit codes, verbose, fix flag) |
| `TestEdgeCases` | Edge cases (special characters, whitespace, relative paths) |

Run tests with:

```bash
uv run pytest tools/tests/test_check_adr_index.py -v
```

```{code-cell}
env -u VIRTUAL_ENV uv run pytest tools/tests/test_check_adr_index.py -q
```

```{code-cell}
env -u VIRTUAL_ENV uv run pytest tools/tests/test_check_adr_index.py --cov=. --cov-report=term-missing -q
```

## **6. Common Scenarios**

+++

### Adding a New ADR

1. Create new ADR file: `architecture/adr/adr_26014_new_feature.md`
2. Run validation: `uv run tools/scripts/check_adr_index.py`
3. See error: "ADR 26014 (adr_26014_new_feature.md) not in index"
4. Fix automatically: `uv run tools/scripts/check_adr_index.py --fix`

+++

### Renaming an ADR

1. Rename file: `adr_26001_old.md` → `adr_26001_new.md`
2. Run validation: detects wrong link
3. Fix: `uv run tools/scripts/check_adr_index.py --fix`

+++

### Removing an ADR

1. Delete ADR file
2. Run validation: detects orphan entry
3. Fix: `uv run tools/scripts/check_adr_index.py --fix`
