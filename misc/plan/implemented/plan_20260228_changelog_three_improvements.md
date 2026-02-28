# Plan: Changelog Generator — Three Improvements

## Context

The changelog generator (`tools/scripts/generate_changelog.py`) needs three formatting and filtering improvements:
1. Missing blank line between new and existing content when using `--prepend`
2. Section headers lack visual emphasis — need markdown bold
3. Housekeeping commits (CLAUDE.md, aider, misc/, jupytext sync) pollute the CHANGELOG

Config follows ADR-26029 (`pyproject.toml [tool.X]`). TDD approach: tests first.

## Files to Modify

| File | Change |
|------|--------|
| `pyproject.toml` | Add `changelog-exclude-patterns` key |
| `tools/tests/test_generate_changelog.py` | ~11 new tests |
| `tools/scripts/generate_changelog.py` | 3 edits + 2 new functions + 1 new constant |
| `tools/docs/scripts_instructions/generate_changelog_py_script.md` | Version bump, bold headers, exclusion docs |

## Step 1 — Config (`pyproject.toml`)

Add after `archtag-required-types` line (before `[tool.commit-convention.changelog-sections]`):

```toml
changelog-exclude-patterns = ["CLAUDE.md", "aider", "misc/", "jupytext sync"]
```

## Step 2 — Tests First (`test_generate_changelog.py`)

### 2a. Import `EXCLUDE_PATTERNS` and `_filter_excluded_commits`

### 2b. New test in `TestGenerateChangelogCLI`

- `test_prepend_inserts_blank_line_between_new_and_existing` — assert `"new release\n\nold release"` in content

### 2c. New test in `TestFormatChangelog`

- `test_section_headers_are_bold_markdown` — assert `f"**{section_name}:**"` in section line

### 2d. New class `TestExcludePatterns` (~9 tests)

- `test_exclude_patterns_loaded_from_config` — non-empty list
- `test_commit_with_excluded_subject_omitted` — `_filter_excluded_commits` drops matching commit
- `test_commit_exclusion_is_case_insensitive`
- `test_bullet_matching_exclude_pattern_is_removed` — via `parse_single_commit`
- `test_bullet_exclusion_is_case_insensitive`
- `test_no_exclusion_when_pattern_not_present` — clean commits pass through
- `test_each_configured_pattern_filters_commits` — parametrized over `EXCLUDE_PATTERNS`
- `test_each_configured_pattern_filters_bullets` — parametrized over `EXCLUDE_PATTERNS`

## Step 3 — Implementation (`generate_changelog.py`)

### 3a. New module constant (after `SECTION_ORDER`)

```python
EXCLUDE_PATTERNS: list[str] = list(_CONFIG.get("changelog-exclude-patterns", []))
```

### 3b. Two new helper functions (after `_extract_bullets`)

```python
def _matches_exclude_pattern(text: str) -> bool:
    text_lower = text.lower()
    return any(p.lower() in text_lower for p in EXCLUDE_PATTERNS)

def _filter_excluded_commits(commits: list[Commit]) -> list[Commit]:
    return [c for c in commits if not _matches_exclude_pattern(c.subject)]
```

### 3c. Bullet filtering — add at end of `_extract_bullets`, before return

```python
bullets = [b for b in bullets if not _matches_exclude_pattern(b)]
```

### 3d. Wire commit filtering into `generate_changelog()`

```python
commits = parse_commits(ref_range)
commits = _filter_excluded_commits(commits)  # NEW
```

### 3e. Bold section headers — line 282

`f"* {section_name}:"` → `f"* **{section_name}:**"`

### 3f. Prepend blank line — line 347

`output + existing` → `output + "\n" + existing`

## Step 4 — Doc Update (`tools/docs/scripts_instructions/generate_changelog_py_script.md`)

### 4a. Frontmatter (lines 17-19)
- `date: 2026-02-18` → `date: 2026-02-28`
- `version: 1.0.2` → `version: 1.0.3`

### 4b. CHANGELOG Output Format example (lines 64-73)
Update to show bold section headers:
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

### 4c. Hierarchy table (line 80)
`* Section Name:` → `* **Section Name:**`

### 4d. "Excluded from bullets" list (after line 97)
Add new bullet:
- Bullets matching exclusion patterns from `pyproject.toml [tool.commit-convention.changelog-exclude-patterns]`

### 4e. New subsection after "Section Ordering" (after line 109)
```markdown
### Exclusion Patterns

Commits and bullets matching patterns from `pyproject.toml [tool.commit-convention.changelog-exclude-patterns]` are filtered from output. Matching is case-insensitive substring search.

* **Commit level**: subject matches pattern → entire commit dropped
* **Bullet level**: bullet matches pattern → only that bullet dropped
```

### 4f. Configuration source hint (line 28)
Add `changelog-exclude-patterns` to the list of config keys read from `pyproject.toml`.

### 4g. Technical Architecture — function listing (lines 119-126)
Add:
- `_matches_exclude_pattern(text)` — case-insensitive pattern check
- `_filter_excluded_commits(commits)` — drops commits matching exclusion patterns
- `EXCLUDE_PATTERNS` to module constants list

### 4h. Configuration Reference (line 138)
Add: `pyproject.toml [tool.commit-convention.changelog-exclude-patterns]` for exclusion patterns

### 4i. Test Suite section (line 195)
- Update count: 56 → ~67
- Add "Exclusion patterns" to coverage areas list

## Verification

```bash
uv run pytest tools/tests/test_generate_changelog.py -v
uv run tools/scripts/generate_changelog.py v2.6.0..HEAD
uv run tools/scripts/generate_changelog.py v2.6.0..HEAD --version 2.7.0 --prepend /tmp/test_changelog.md && cat /tmp/test_changelog.md
```
