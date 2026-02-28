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

---
title: "Instruction on generate_changelog.py script"
author: Vadim Rudakov, rudakow.wadim@gmail.com
date: 2026-02-28
options:
  version: 1.1.0
  birth: 2026-02-16
---

# Instruction on generate_changelog.py script

+++

:::{important} Configuration source
This script reads its configuration — type-to-section mapping, section ordering, and exclusion patterns — from `pyproject.toml [tool.commit-convention]` (`changelog-sections` and `changelog-exclude-patterns`). That section is the single source of truth shared with `validate_commit_msg.py`. The rules themselves are defined in [Production Git Workflow Standards](/tools/docs/git/01_production_git_workflow_standards.ipynb).
:::

+++

## **1. Architectural Overview: The SVA Principle**

+++

This [script](/tools/scripts/generate_changelog.py) generates hierarchical CHANGELOG entries from structured git commit bodies ({term}`ADR-26024`). It is the "cooking" step in the **Ingredients-First** pattern:

1. **At commit time**: `validate_commit_msg.py` ensures every commit body contains parseable bullets (the "ingredients").
2. **At release time**: `generate_changelog.py` extracts those bullets from git history and formats them into the project's CHANGELOG format.

The script produces deterministic, traceable output — every CHANGELOG line maps 1:1 to a commit body bullet. No LLM involved.

It adheres to the **Smallest Viable Architecture (SVA)** principle.

:::{hint} **SVA = right tool for the job**
SVA isn't about minimal *code* — it's about **minimal *cognitive and operational overhead***.

* **Zero External Dependencies**: Uses only the Python standard library (`argparse`, `subprocess`, `tomllib`, `pathlib`, `re`, `dataclasses`).
* **Configuration from pyproject.toml**: Type-to-section mapping and section ordering are loaded from `pyproject.toml [tool.commit-convention.changelog-sections]` — a single source of truth shared with `validate_commit_msg.py`.
* **`--first-parent` scanning**: Filters out feature branch noise, scanning only squashed trunk commits produced by Squash-and-Merge.
:::

+++

## **2. Key Capabilities & Logic**

+++

### CHANGELOG Output Format

The script produces the project's hierarchical CHANGELOG format:

```
release 2.5.0
* **New Features:**
    - Add login page
        - Created: auth/login.py — new login page
        - Updated: auth/urls.py — added login route
* **Bug Fixes:**
    - Correct token expiry
        - Fixed: auth/token.py — expiry was off by one
```

**Hierarchy:**

| Level | Format | Source |
|-------|--------|--------|
| Version header | `release X.Y.Z` or `Unreleased` | `--version` flag |
| Section | `* **Section Name:**` | `pyproject.toml [tool.commit-convention.changelog-sections]` |
| Topic | `    - Capitalized subject` | Commit subject line (4-space indent) |
| Sub-item | `        - Body bullet` | Commit body bullet (8-space indent) |

+++

### Commit Parsing

Each commit is parsed from `git log --format=%H%n%s%n%b%nEND_COMMIT_MARKER`:

* **Hash** — first line
* **Subject** — second line, parsed for type, optional scope, and description
* **Body** — remaining lines, filtered for bullets only

**Excluded from bullets:**
* ArchTag lines (`ArchTag:TAG-NAME`)
* Git trailers (`Co-Authored-By: ...` after a blank line)
* Prose context lines
* Bullets matching exclusion patterns from `pyproject.toml [tool.commit-convention.changelog-exclude-patterns]`

+++

### Legacy Commit Handling

Commits predating the structured body convention (no bullets) are included with their subject line only — no sub-items. This ensures graceful degradation when scanning history that spans the convention adoption date.

+++

### Section Ordering

Sections appear in the order defined by `pyproject.toml [tool.commit-convention.changelog-sections]` key order. Types not in the mapping are appended at the end with their type name capitalized.

+++

### Exclusion Patterns

Commits and bullets matching patterns from `pyproject.toml [tool.commit-convention.changelog-exclude-patterns]` are filtered from output. Matching is case-insensitive substring search.

* **Commit level**: subject matches pattern → entire commit dropped
* **Bullet level**: bullet matches pattern → only that bullet dropped

Use `--verbose` / `-v` to print excluded items to stderr for debugging.

:::{warning} Self-referencing trap
Commit body bullets that *mention* an exclusion pattern as literal text will be filtered out. For example, a bullet describing the addition of the `CLAUDE.md` pattern will itself match that pattern. When writing bullets about exclusion config changes, avoid the literal pattern strings — describe the intent instead (e.g., "added housekeeping exclusion patterns" rather than listing the pattern values).

After committing, verify no important bullets were silently dropped:

```bash
uv run tools/scripts/generate_changelog.py --verbose HEAD~1..HEAD 1>/dev/null
```

Empty stderr means all bullets survived. Any output shows what was excluded.
:::

+++

## **3. Technical Architecture**

+++

The script follows top-down design:

* **`main()`** — entry point, instantiates CLI
* **`generate_changelog(ref_range, version, *, verbose)`** — orchestrates parsing → filtering → grouping → formatting
* **`parse_commits(ref_range, *, verbose)`** — runs `git log --first-parent`, splits on marker, calls parser
* **`parse_single_commit(raw, *, verbose)`** — extracts hash, type, scope, subject, bullets from raw text
* **`_extract_bullets(body_lines, *, verbose)`** — extracts bullet lines, filters by exclusion patterns
* **`_matches_exclude_pattern(text)`** — case-insensitive pattern check against `EXCLUDE_PATTERNS`
* **`_filter_excluded_commits(commits, *, verbose)`** — drops commits matching exclusion patterns
* **`group_by_type(commits)`** — groups `list[Commit]` into `dict[str, list[Commit]]`
* **`format_changelog(groups, version)`** — produces the hierarchical CHANGELOG string
* **`GenerateChangelogCLI`** — argument parsing, stdout/file output, `--verbose` flag

Module constants: `TYPE_TO_SECTION`, `SECTION_ORDER`, `EXCLUDE_PATTERNS`.

The `Commit` dataclass holds: `hash`, `type`, `scope`, `subject`, `bullets`.

+++

## **4. Operational Guide**

+++

### Configuration Reference

* **Script**: `tools/scripts/generate_changelog.py`
* **Configuration**: `pyproject.toml [tool.commit-convention.changelog-sections]` for section mapping, `pyproject.toml [tool.commit-convention.changelog-exclude-patterns]` for exclusion patterns
* **Standards**: [Production Git Workflow Standards](/tools/docs/git/01_production_git_workflow_standards.ipynb) § Release-Time CHANGELOG Generation

+++

### Command Line Interface

```bash
generate_changelog.py REF_RANGE [--version VERSION] [--prepend FILE] [-v|--verbose]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `REF_RANGE` | Git ref range (e.g., `v2.4.0..HEAD`) | Required |
| `--version` | Version label for the header | `Unreleased` |
| `--prepend` | Prepend output to an existing file | stdout |
| `-v`, `--verbose` | Print excluded commits and bullets to stderr | off |

+++

### Usage Examples

```{code-cell}
cd ../../..
```

#### Generate changelog from last tag to HEAD - dry run

```{code-cell}
env -u VIRTUAL_ENV uv run tools/scripts/generate_changelog.py v2.5.0..HEAD | head -n10
```

#### With version label - dry run

```{code-cell}
env -u VIRTUAL_ENV uv run tools/scripts/generate_changelog.py v2.5.0..HEAD --version 2.5.0 | head -n5
```

#### Generate from concrete 3 commits - dry run

```{code-cell}
env -u VIRTUAL_ENV uv run tools/scripts/generate_changelog.py HEAD~10..HEAD~7 | head -n10
```

#### Prepend to existing CHANGELOG

+++

```bash
uv run tools/scripts/generate_changelog.py v2.4.0..HEAD --version 2.6.0 --prepend CHANGELOG
```

+++

#### Check excluded patterns

```{code-cell}
stdout_log="/tmp/changelog_stdout"
stderr_log="/tmp/changelog_stderr"
env -u VIRTUAL_ENV uv run tools/scripts/generate_changelog.py v2.5.0..HEAD --verbose 1>"${stdout_log}" 2>"${stderr_log}"
```

```{code-cell}
wc -l "${stdout_log}"
head "${stdout_log}"
```

```{code-cell}
wc -l "${stderr_log}"
head "${stderr_log}"
```

## **5. Test Suite**

+++

The script is accompanied by a test suite (`test_generate_changelog.py`) with 76 tests covering:

* **Commit parsing**: Hash, type, scope, subject, bullet extraction, trailer/ArchTag exclusion
* **Grouping**: Type-based grouping, order preservation, empty input
* **Formatting**: Version header, section headers (bold markdown), indentation hierarchy, capitalization, section ordering, legacy commits
* **Git integration**: `--first-parent` flag, multi-commit parsing, empty ranges (mocked subprocess)
* **CLI integration**: Required arguments, stdout output, `--version` flag, `--prepend` file writing (with blank line separator), `--verbose` flag
* **Exclusion patterns**: Config loading, commit-level filtering, bullet-level filtering, case-insensitivity, verbose stderr output, parametrized coverage of all configured patterns

+++

### Running the Tests

```bash
# Run all tests
uv run pytest tools/tests/test_generate_changelog.py

# Run with coverage
uv run pytest tools/tests/test_generate_changelog.py --cov=tools.scripts.generate_changelog --cov-report=term-missing
```

```{code-cell}
env -u VIRTUAL_ENV uv run pytest tools/tests/test_generate_changelog.py -q
```

```{code-cell}
env -u VIRTUAL_ENV uv run pytest tools/tests/test_generate_changelog.py --cov=tools.scripts.generate_changelog --cov-report=term-missing -q
```
