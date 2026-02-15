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

# Instruction on check_adr.py script

+++

---
title: Instruction on check_adr.py script
author: Vadim Rudakov, rudakow.wadim@gmail.com
date: 2026-02-08
options:
  version: 0.5.0
  birth: 2026-01-30
---

+++

## **1. Architectural Overview: The SVA Principle**

+++

This [script](/tools/scripts/check_adr.py) validates ADR (Architecture Decision Record) files in `architecture/adr/` for format compliance and synchronization with the index at `architecture/adr_index.md`.

It ensures:
- **Index Sync**: Every ADR file has a corresponding entry in the index
- **No Orphans**: No index entries point to non-existent files
- **Correct Links**: Links in the index point to the correct file paths
- **Numerical Order**: Index entries are in numerical order
- **Valid Status**: Status values match allowed values from config
- **Required Frontmatter**: YAML frontmatter contains id, title, date, status, tags
- **Date Format**: Date field matches YYYY-MM-DD (ISO 8601)
- **Valid Tags**: Tags are from predefined list in config
- **Required Sections**: Document contains Context, Decision, Consequences, Alternatives, References, Participants
- **Duplicate Sections**: No `##` section header appears more than once in the same ADR
- **Term References**: MyST `{term}` cross-references use correct hyphen format (`{term}`ADR-26001``)

All validation rules are defined in [`adr_config.yaml`](/architecture/adr/adr_config.yaml) (Single Source of Truth).

This tool is designed to serve as a quality gate in CI/CD, ensuring consistent ADR format and index synchronization.

:::{hint} **SVA = right tool for the job**
:class: dropdown
It adheres to the **Smallest Viable Architecture (SVA)** principle.

SVA isn't about minimal *code* — it's about **minimal *cognitive and operational overhead***.

* **Zero External Dependencies**: Uses only the Python standard library (`argparse`, `re`, `subprocess`, `sys`, `pathlib`).
* **Pattern-Based Detection**: Parses ADR headers and index entries using regex patterns.
* **Git Integration**: Optional `--check-staged` mode for pre-commit integration.
:::

+++

## **2. Quick Reference**

+++

### Command Cheat Sheet

| Task | Command |
|------|---------|
| Validate all ADRs | `uv run tools/scripts/check_adr.py` |
| Verbose validation | `uv run tools/scripts/check_adr.py --verbose` |
| Auto-fix issues | `uv run tools/scripts/check_adr.py --fix` |
| Migrate legacy ADRs | `uv run tools/scripts/check_adr.py --migrate` |
| Check staged only | `uv run tools/scripts/check_adr.py --check-staged` |
| Check term references | `uv run tools/scripts/check_adr.py --check-terms` |
| Fix term references | `uv run tools/scripts/check_adr.py --fix-terms` |
| Run tests | `uv run pytest tools/tests/test_check_adr.py -v` |
| Run tests + coverage | `uv run pytest tools/tests/test_check_adr.py --cov=tools.scripts.check_adr` |

+++

### Typical Workflow

```bash
# 1. Create/edit ADR
cp architecture/adr/adr_template.md architecture/adr/adr_NNNNN_slug.md
# Edit the file...

# 2. Validate
uv run tools/scripts/check_adr.py --verbose

# 3. Fix any issues
uv run tools/scripts/check_adr.py --fix

# 4. Commit
git add architecture/adr/ architecture/adr_index.md
git commit -m "feat: Add ADR NNNNN"
```

+++

### Key Files

| File | Purpose |
|------|---------|
| `tools/scripts/check_adr.py` | Main validation script |
| `tools/tests/test_check_adr.py` | Test suite (150+ tests, 98% coverage) |
| `architecture/adr/adr_config.yaml` | SSoT for validation rules |
| `architecture/adr/adr_template.md` | Template for new ADRs |
| `architecture/adr_index.md` | Partitioned index (auto-generated) |

+++

## **3. Key Capabilities & Logic**

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

**Index Synchronization Errors:**

| Error Type | Description |
|------------|-------------|
| `missing_in_index` | ADR file exists but has no index entry |
| `orphan_in_index` | Index entry points to non-existent file |
| `wrong_link` | Index link path doesn't match actual file path |
| `wrong_order` | Index entries are not in numerical order |
| `duplicate_number` | Multiple files have the same ADR number |
| `wrong_section` | ADR placed in wrong index section (based on status) |

**Format Validation Errors:**

| Error Type | Description |
|------------|-------------|
| `invalid_status` | Status not in allowed list from config |
| `title_mismatch` | Frontmatter title differs from header title |
| `missing_field` | Required frontmatter field missing (id, title, date, status, tags) |
| `invalid_date` | Date doesn't match YYYY-MM-DD format |
| `invalid_tag` | Tag not in allowed list from config |
| `empty_tags` | Tags list is empty (at least one required) |
| `missing_section` | Required document section not found |
| `duplicate_section` | Same `##` header appears more than once in the ADR |
| `broken_term_reference` | `{term}`ADR 26001`` should use hyphen: `{term}`ADR-26001`` |

+++

### D. Auto-Fix Mode (`--fix`)

When run with `--fix`, the script:

1. **Fixes invalid statuses**: Prompts to correct typos (e.g., "prposed" → "proposed")
2. **Fixes title mismatches**: Prompts to update frontmatter title to match header
3. **Fixes duplicate sections**: Prompts to merge duplicate `##` headers (keeps first, concatenates bodies)
4. **Regenerates partitioned index**: Groups ADRs by status into sections:
   - *Active Architecture*: accepted ADRs
   - *Evolutionary Proposals*: proposed ADRs
   - *Historical Context*: rejected, superseded, deprecated ADRs
5. **Annotates superseded entries**: Adds " — superseded by {term}`ADR-XXXXX`" to index entries for ADRs with `superseded_by` set in frontmatter
6. **Sorts entries** by ADR number within each section
7. **Removes orphan entries** pointing to non-existent files
8. **Runs promotion gate validation**: Same checks as `--verbose` mode (accepted ADRs must have ≥2 alternatives and non-empty Participants)
9. **Reports all changes** made

### E. Migration Mode (`--migrate`)

When run with `--migrate`, the script adds YAML frontmatter to legacy ADRs:

1. **Scans** all ADR files without YAML frontmatter
2. **Extracts** title from `# ADR NNNNN: Title` header
3. **Extracts** status from `## Status` section (or uses default "proposed")
4. **Corrects** status typos using the corrections map
5. **Generates** frontmatter with id, title, date (from file mtime), status, tags
6. **Writes** updated file with frontmatter prepended

### F. Configuration (`adr_config.yaml`)

All validation rules are defined in [`adr_config.yaml`](/architecture/adr/adr_config.yaml):

```yaml
# Required frontmatter fields
required_fields: [id, title, date, status, tags]

# Date format (regex)
date_format: "^\\d{4}-\\d{2}-\\d{2}$"

# Valid tags
tags: [architecture, documentation, hardware, model, workflow, ...]

# Required document sections
required_sections: [Context, Decision, Consequences, Alternatives, References, Participants]

# Valid statuses
statuses: [proposed, accepted, rejected, superseded, deprecated]

# Status to section mapping for partitioned index
sections:
  Active Architecture: [accepted]
  Evolutionary Proposals: [proposed]
  Historical Context: [rejected, superseded, deprecated]

# Typo corrections (typo → correct)
status_corrections:
  proposed: [prposed, draft, pending, wip]
  accepted: [acepted, approved, active]
  ...
```

+++

## **4. Operational Guide**

+++

### CLI Options

| Option | Description |
|--------|-------------|
| `--verbose`, `-v` | Show detailed output including counts |
| `--fix` | Automatically fix index and prompt to fix status/title issues |
| `--migrate` | Add YAML frontmatter to legacy ADRs without it |
| `--check-staged` | Only check staged ADR files (for pre-commit) |
| `--check-terms` | Validate `{term}` references use hyphen format (ADR-26001) |
| `--fix-terms` | Auto-fix broken term references (space → hyphen) |

+++

### Basic Usage

```{code-cell}
cd ../../../
```

```{code-cell}
# Validate ADR index synchronization (default)
env -u VIRTUAL_ENV uv run tools/scripts/check_adr.py
```

```{code-cell}
# Verbose output
env -u VIRTUAL_ENV uv run tools/scripts/check_adr.py --verbose
```

```{code-cell}
# Auto-fix issues
env -u VIRTUAL_ENV uv run tools/scripts/check_adr.py --fix --verbose
```

```{code-cell}
# Check only staged files (for pre-commit)
env -u VIRTUAL_ENV uv run tools/scripts/check_adr.py --check-staged --verbose
```

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All ADRs are synchronized with the index |
| `1` | One or more synchronization errors found |

+++

## **5. Validation Layers**

+++

### Pre-commit Hook

The script runs automatically via pre-commit when ADR or index files change:

```yaml
- id: check-adr-index
  name: Check ADR Index
  entry: uv run --active tools/scripts/check_adr.py
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
      run: uv run tools/scripts/check_adr.py --verbose
```

:::{important} **Pre-commit / CI desync pattern**
Pre-commit hooks typically run in "fix and move on" mode (`--fix`), while CI runs in "validate everything" mode (`--verbose`). If these two modes have different validation coverage, a gap emerges: pre-commit passes locally, but CI fails on the same commit.

The fix: `--fix` mode must run the same validation gates as `--verbose` before returning exit 0. In this script, both modes now run promotion gate validation (ADR-26025) after sync checks.
:::

+++

## **6. Test Suite**

+++

The [test suite](/tools/tests/test_check_adr.py) provides 150+ tests with 96% coverage:

| Test Class | Coverage |
|------------|----------|
| `TestGetAdrFiles` | ADR file discovery, template exclusion, sorting |
| `TestParseIndex` | Glossary parsing, entry extraction, section detection |
| `TestValidateSync` | Sync validation (missing, orphan, wrong link, order) |
| `TestAutoFixIndex` | Fix mode (add entries, maintain order, remove orphans) |
| `TestCli` | CLI integration (exit codes, verbose, fix, migrate flags) |
| `TestValidateFrontmatterFields` | Required field validation |
| `TestValidateDateFormat` | ISO date format validation |
| `TestValidateTags` | Tag validation against allowed list |
| `TestValidateSections` | Required section detection |
| `TestMigrateLegacyAdr` | Legacy ADR migration |
| `TestCliMigrateMode` | `--migrate` CLI mode |
| `TestStatusValidation` | Status value validation |
| `TestTitleMismatchHandling` | Title mismatch detection and fix |
| `TestPartitionedIndex` | Status-based index partitioning |
| `TestEdgeCases` | Special characters, whitespace, edge cases |
| `TestTermReferenceDetection` | Broken term reference pattern matching |
| `TestTermReferenceValidation` | Term reference error generation |
| `TestTermReferenceFix` | Term reference auto-fix |
| `TestTermReferenceCliFlags` | `--check-terms` and `--fix-terms` CLI |
| `TestPromotionGateAlternatives` | Accepted ADRs require ≥2 alternatives |
| `TestPromotionGateParticipants` | Accepted ADRs require non-empty Participants |
| `TestPromotionGateCLIIntegration` | Promotion gate feeds into exit code |
| `TestDuplicateSections` | Duplicate `##` header detection |
| `TestFixDuplicateSections` | Duplicate section merge with user confirmation |
| `TestPromotionGateInFixMode` | `--fix` mode runs promotion gate validation |

Run tests with:

```bash
uv run pytest tools/tests/test_check_adr.py -v
```

```{code-cell}
env -u VIRTUAL_ENV uv run pytest tools/tests/test_check_adr.py -q
```

```{code-cell}
env -u VIRTUAL_ENV uv run pytest tools/tests/test_check_adr.py --cov=tools.scripts.check_adr --cov-report=term-missing -q
```

## **7. Common Scenarios**

+++

### Scenario 1: Adding a New ADR

**Goal**: Create a new ADR and add it to the index.

```bash
# 1. Copy template
cp architecture/adr/adr_template.md architecture/adr/adr_26018_my_new_decision.md

# 2. Edit the file (update frontmatter and content)
# - Set id: 26018
# - Set title: "My New Decision"
# - Set date: 2026-02-01
# - Set status: proposed
# - Set tags: [architecture]
# - Fill in Context, Decision, Consequences, etc.

# 3. Validate (will show "missing_in_index" error)
uv run tools/scripts/check_adr.py --verbose

# 4. Auto-fix to add to index
uv run tools/scripts/check_adr.py --fix

# 5. Stage changes
git add architecture/adr/adr_26018_my_new_decision.md architecture/adr_index.md
```

+++

### Scenario 2: Migrating Legacy ADRs

**Goal**: Add YAML frontmatter to old ADRs that only have markdown format.

```bash
# 1. Check which ADRs need migration (look for "missing_field" errors)
uv run tools/scripts/check_adr.py --verbose

# Example output:
# - ADR 26001 missing required field: 'id'
# - ADR 26001 missing required field: 'date'
# ...

# 2. Run migration to add frontmatter automatically
uv run tools/scripts/check_adr.py --migrate

# Example output:
# Migrated: adr_26001_use_of_python.md
# Migrated: adr_26002_adoption_of_pre_commit.md
# Migrated 2 ADR file(s).

# 3. Regenerate the partitioned index
uv run tools/scripts/check_adr.py --fix

# 4. Review and commit
git diff architecture/adr/
git add architecture/adr/ architecture/adr_index.md
```

+++

### Scenario 3: Fixing a Status Typo

**Goal**: Correct a misspelled status value.

```bash
# 1. Validation shows invalid status
uv run tools/scripts/check_adr.py --verbose

# Output:
# - ADR 26005 has invalid status: 'prposed' (valid: accepted, deprecated, proposed, rejected, superseded)

# 2. Run fix mode (will prompt for correction)
uv run tools/scripts/check_adr.py --fix

# Interactive prompt:
# ADR 26005 has invalid status: 'prposed'
# Valid statuses: accepted, deprecated, proposed, rejected, superseded
# Suggested correction: 'prposed' -> 'proposed'
# Apply suggested fix 'proposed'? [Y/n/custom]:
# (Press Enter to accept)

# 3. Stage the fixed file
git add architecture/adr/adr_26005_*.md
```

+++

### Scenario 4: Fixing Title Mismatch

**Goal**: Sync frontmatter title with header title.

```bash
# 1. Validation shows title mismatch
uv run tools/scripts/check_adr.py --verbose

# Output:
# - ADR 26003 has mismatched titles: header='Adoption of Gitlint', frontmatter='Old Title'

# 2. Run fix mode (will prompt for confirmation)
uv run tools/scripts/check_adr.py --fix

# Interactive prompt:
# ADR 26003 title mismatch:
#   Header title:      'Adoption of Gitlint'
#   Frontmatter title: 'Old Title'
# The header title is authoritative. Update frontmatter to match?
# Apply fix? [y/N]: y

# 3. Stage the fixed file
git add architecture/adr/adr_26003_*.md
```

+++

### Scenario 5: Renaming an ADR File

**Goal**: Rename an ADR file and update the index.

```bash
# 1. Rename the file
mv architecture/adr/adr_26001_old_name.md architecture/adr/adr_26001_new_name.md

# 2. Validation detects wrong link
uv run tools/scripts/check_adr.py --verbose

# Output:
# - ADR 26001 has wrong link: /architecture/adr/adr_26001_old_name.md (expected /architecture/adr/adr_26001_new_name.md)

# 3. Auto-fix updates the index
uv run tools/scripts/check_adr.py --fix

# 4. Stage changes
git add architecture/adr/adr_26001_new_name.md architecture/adr_index.md
git rm architecture/adr/adr_26001_old_name.md
```

+++

### Scenario 6: Changing ADR Status

**Goal**: Move an ADR from "proposed" to "accepted".

```bash
# 1. Edit the ADR file and change status in frontmatter
# From: status: proposed
# To:   status: accepted

# 2. Validation detects wrong section placement
uv run tools/scripts/check_adr.py --verbose

# Output:
# - ADR 26010 is in section 'Evolutionary Proposals' but should be in 'Active Architecture'

# 3. Auto-fix regenerates the partitioned index
uv run tools/scripts/check_adr.py --fix

# 4. Stage changes
git add architecture/adr/adr_26010_*.md architecture/adr_index.md
```

+++

### Scenario 7: Adding a New Valid Tag

**Goal**: Use a new tag that's not in the allowed list.

```bash
# 1. Validation shows invalid tag
uv run tools/scripts/check_adr.py --verbose

# Output:
# - ADR 26015 has invalid tag: 'performance' (valid: architecture, ci, documentation, ...)

# 2. Option A: Use an existing tag instead
# Edit the ADR and change to a valid tag

# 3. Option B: Add the new tag to config (if it should be allowed)
# Edit architecture/adr/adr_config.yaml:
# tags:
#   - architecture
#   - ...
#   - performance  # Add new tag

# 4. Re-run validation
uv run tools/scripts/check_adr.py --verbose
```

+++

### Scenario 8: Pre-commit Validation

**Goal**: Validate ADRs before committing.

```bash
# The pre-commit hook runs automatically when you commit ADR files
git add architecture/adr/adr_26018_new_feature.md
git commit -m "feat: Add ADR 26018"

# If validation fails, you'll see:
# Check ADR Index...................................................Failed
# - ADR 26018 (adr_26018_new_feature.md) not in index
# Run with --fix to update the index automatically.

# Fix and retry:
uv run tools/scripts/check_adr.py --fix
git add architecture/adr_index.md
git commit -m "feat: Add ADR 26018"
```

### Scenario 9: Fixing Duplicate Sections

**Goal**: Merge duplicate `##` headers in an ADR file.

```bash
# 1. Validation shows duplicate section
uv run tools/scripts/check_adr.py --verbose

# Output:
# - ADR 26026 has duplicate section: '## Participants' (2 occurrences)

# 2. Run fix mode (will prompt for confirmation)
uv run tools/scripts/check_adr.py --fix

# Interactive prompt:
# ADR 26026 has 2 '## Participants' sections:
#   1. (empty)
#   2. 1. Test Author
# Merged result under single '## Participants':
#   1. Test Author
# Apply merge? [Y/n]: y

# 3. Stage the fixed file
git add architecture/adr/adr_26026_*.md
```
