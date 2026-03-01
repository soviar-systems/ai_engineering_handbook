# Plan: Changelog Self-Filtering Warning ~~in commit-msg Hook~~ via post-commit Hook

## Context

The changelog generator (`generate_changelog.py`) silently filters out commit bullets and entire commits matching exclusion patterns (`CLAUDE.md`, `aider`, `misc/`, `jupytext sync`). Developers only discover their bullets were filtered when they run the changelog generator with `--verbose`. This creates a feedback gap — the right time to learn about filtering is at commit time, not changelog generation time.

**Goal**: Show the developer their CHANGELOG entry (including filtered content) immediately after each commit.

## ~~Approach: Extend `validate_commit_msg.py`~~ (Rejected)

~~Chosen over creating a separate hook because:~~
~~- The script already parses subject + body bullets and loads `pyproject.toml [tool.commit-convention]`~~
~~- Avoids a new script/tests/docs triad (SVA principle)~~
~~- The warning runs only after validation passes — clean separation of concerns~~

**Rejected during implementation** — adding a dataclass, 4 functions, 13 tests, and duplicated filtering logic to `validate_commit_msg.py` violates the very SVA principle it was supposed to uphold. The existing `generate_changelog.py --verbose` already outputs exactly the right information.

## Approach: Post-commit hook (Implemented)

Add `generate_changelog.py --verbose HEAD~1..HEAD` as a `post-commit` hook in `.pre-commit-config.yaml`. This:
- Reuses existing logic (zero new code in scripts)
- Shows the full CHANGELOG entry the commit will produce
- Shows `[excluded bullet]` / `[excluded commit]` warnings via `--verbose`
- Includes an amend tip in the hook entry
- Never blocks the commit (informational only)

## Files to Modify (ADR-26011 Triad)

| File | Action |
|------|--------|
| `tools/scripts/validate_commit_msg.py` | Add warning logic |
| `tools/tests/test_validate_commit_msg.py` | Add tests (TDD — written first) |
| `tools/docs/scripts_instructions/validate_commit_msg_py_script.md` | Document new layer, bump to `1.1.0` |

## Implementation Details

### 1. New constant (after existing constants, ~line 48)

```python
EXCLUDE_PATTERNS: list[str] = list(_CONFIG.get("changelog-exclude-patterns", []))
```

### 2. New dataclass: `ChangelogWarning`

```python
@dataclass
class ChangelogWarning:
    kind: str    # "subject" or "bullet"
    text: str    # the matched text
    pattern: str # which pattern matched
```

Follows the project's pattern (generate_changelog.py uses `@dataclass` for `Commit`). More testable than returning formatted strings.

### 3. New functions

| Function | Signature | Purpose |
|----------|-----------|---------|
| `_matches_exclude_pattern` | `(text: str) -> bool` | Case-insensitive substring match against EXCLUDE_PATTERNS. Deliberate duplication of generate_changelog.py's function (stdlib-only constraint). |
| `_find_matching_pattern` | `(text: str) -> str \| None` | Returns WHICH pattern matched (for warning detail). |
| `check_changelog_exclusions` | `(subject: str, body_lines: list[str]) -> list[ChangelogWarning]` | Pure function — returns structured warnings. Checks subject (entire commit excluded) and individual bullets (bullet filtered). |
| `_print_changelog_warnings` | `(warnings: list[ChangelogWarning]) -> None` | Prints formatted warnings to stderr. Separated from logic for testability. |

### 4. Wire into CLI (`ValidateCommitMsgCLI.run()`)

After the `if errors: ... sys.exit(1)` block (only reached when validation passes):

```python
# Informational: changelog exclusion notice (does not affect exit code)
warnings = check_changelog_exclusions(subject, body_lines)
if warnings:
    _print_changelog_warnings(warnings)
```

### 5. Warning output format

```
Changelog notice: 2 bullet(s) will be filtered from CHANGELOG:
  ⚠ bullet: "- Updated: CLAUDE.md — added docs" (pattern: "CLAUDE.md")
  ⚠ bullet: "- Updated: misc/plan.md — saved plan" (pattern: "misc/")
```

When subject matches (entire commit excluded):
```
Changelog notice: entire commit will be excluded from CHANGELOG:
  ⚠ subject: "docs: update CLAUDE.md" (pattern: "CLAUDE.md")
```

Uses `⚠` to distinguish from `✗` (validation errors).

## Test Plan (TDD — Red → Green → Refactor)

### TestCheckChangelogExclusions

| Test | Scenario | Assert |
|------|----------|--------|
| `test_no_warnings_when_nothing_matches` | Clean subject + bullets | `len(result) == 0` |
| `test_subject_matching_produces_warning` | Subject contains pattern | Warning with `kind == "subject"` |
| `test_bullet_matching_produces_warning` | One bullet matches | Warning with `kind == "bullet"` |
| `test_all_bullets_matching` | All bullets match | Warning count == bullet count |
| `test_subject_and_bullets_both_matching` | Both match | Both kinds present |
| `test_case_insensitive_matching` | Swapped-case pattern | Warning produced |
| `test_empty_exclude_patterns` | Monkeypatch to `[]` | No warnings |
| `test_archtag_lines_not_checked` | ArchTag containing pattern text | No warning for ArchTag |
| `test_each_pattern_triggers` | Parametrize over EXCLUDE_PATTERNS | Each produces a warning |

### TestChangelogWarningCLIIntegration

| Test | Scenario | Assert |
|------|----------|--------|
| `test_filtered_bullet_still_exits_0` | Valid commit with matching bullet | No `SystemExit` |
| `test_clean_commit_no_warning_output` | Valid commit, no matches | No changelog notice in stderr |
| `test_subject_match_still_exits_0` | Subject matches pattern | No `SystemExit` |
| `test_invalid_commit_skips_warning` | Bad subject → exit 1 | Stderr has no changelog notice |

## Verification

```bash
# Run full test suite
uv run pytest tools/tests/test_validate_commit_msg.py -v

# Run with coverage
uv run pytest tools/tests/test_validate_commit_msg.py --cov=tools.scripts.validate_commit_msg --cov-report=term-missing

# Manual smoke test: create a test commit message with CLAUDE.md bullet
echo -e "docs: update project docs\n\n- Updated: CLAUDE.md — added convention\n- Updated: README.md — fixed typo" > /tmp/test_msg
uv run tools/scripts/validate_commit_msg.py /tmp/test_msg

# Sync jupytext for the doc file
uv run jupytext --sync tools/docs/scripts_instructions/validate_commit_msg_py_script.md
```
