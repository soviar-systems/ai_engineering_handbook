# Plan: Remove Backtick Requirement from Commit Body File Paths

## Context

ADR-26024 requires file paths in commit body bullets to be wrapped in backticks: `` - Verb: `file-path` — description ``. Analysis shows neither `generate_changelog.py` nor `validate_commit_msg.py` parse or validate backticks — both use `^\s*- .+` regex. Backticks are purely cosmetic (markdown rendering in GitHub PR views) but cause a concrete recurring problem: bash interprets backticks inside double-quoted strings as command substitution, making `git commit -m "..."` unsafe. This forces heredoc syntax for every commit, creates silent data corruption when forgotten, and causes repeated AI agent errors (observed this session).

**Decision:** Remove the backtick requirement. The `Verb:` prefix and ` — ` separator already delimit file paths unambiguously. The new format:
```
- Created: tools/scripts/check_adr.py — description
```

## Pre-task: Move Old Plan File

The plan file at `/home/commi/.claude/plans/flickering-wandering-wind.md` previously contained the Gherkin roadmap. That content was already saved to `misc/plan/implemented/plan_20260218_gherkin-adoption-debian-fork.md` and committed. No action needed — the old plan content is already archived.

## Files to Modify (5 mandatory + 2 optional)

### Mandatory

1. **`architecture/adr/adr_26024_structured_commit_bodies_for_automated_changelog.md`**
   - Line 56: Remove backticks from format template
   - Lines 61–67: Rewrite "Target Rules" — remove "wrapped in backticks", update all 5 examples
   - Line 118: Update adoption friction note
   - Line 212: Update Alternative 8 format reference

2. **`tools/docs/git/01_production_git_workflow_standards.md`**
   - Lines 211–212: Remove backticks from Body Convention code block
   - Line 224: Rewrite Rule 4 — remove "wrapped in backticks", update examples
   - Lines 239–246: Update Complex commit example (remove backticks from all 8 bullets)
   - Lines 256: Update Simple commit example
   - Lines 267–268: Update Refactor example

3. **`CLAUDE.md`**
   - Line 123: Update format template
   - Line 124: Remove "in backticks" phrasing, update example

4. **`CONVENTIONS.md`**
   - Line 24: Update format template
   - Line 25: Remove "in backticks" phrasing

5. **`tools/scripts/validate_commit_msg.py`**
   - Line 119: Update error message from `` (- Verb: `target` — description) `` to `(- Verb: target — description)`

### Optional (test data — update for consistency)

6. **`tools/tests/test_validate_commit_msg.py`** — Remove backticks from test input strings (~20 locations). No assertions break without this; it's a consistency update.

7. **`tools/tests/test_generate_changelog.py`** — Same: remove backticks from fixture data (~15 locations). No assertions break.

### Not Modified

- `generate_changelog.py` — parser regex unchanged, no backtick logic
- `misc/plan/implemented/` — historical records, not updated
- `pyproject.toml` — no backtick references

## Execution Order

1. Update ADR-26024 (the authoritative spec)
2. Update git workflow standards doc (developer-facing reference)
3. Update CLAUDE.md and CONVENTIONS.md (agent + editor instructions)
4. Update validate_commit_msg.py error message
5. Update test files for consistency
6. Run tests to verify nothing breaks:
   ```bash
   uv run pytest tools/tests/test_validate_commit_msg.py -v
   uv run pytest tools/tests/test_generate_changelog.py -v
   ```

## Verification

1. `uv run pytest tools/tests/test_validate_commit_msg.py -v` — all pass (regex unchanged)
2. `uv run pytest tools/tests/test_generate_changelog.py -v` — all pass (regex unchanged)
3. Manual: write a test commit with `git commit -m "..."` using plain file paths — no shell escaping issues
4. Grep the repo for remaining backtick-in-commit-body references: `grep -rn "wrapped in backtick" .` should return zero hits
