# Plan: ADR Status-Conditional Validation Gaps

## Context

While superseding ADR-26011 with ADR-26045, we discovered that `check_adr.py` validates section *presence* but not the inverse: when a status *requires* a conditional section, its absence is not caught. The `superseded_by` field is also not validated. This is a systematic gap — rejected ADRs can also lack `## Rejection Rationale` today.

Root cause: `validate_sections()` checks "section X is only allowed for status Y" but never checks "status Y requires section X."

## What to fix now (P1–P4)

### P1+P3: Enforce missing conditional sections

`validate_sections()` needs the inverse check. ~10 lines of code.

Config change in `adr.conf.json`:
- `conditional_sections`: add `"superseded": ["Supersession Rationale"]`, `"deprecated": ["Deprecation Rationale"]`
- `allowed_sections`: add `"Supersession Rationale"`, `"Deprecation Rationale"`

This is config-driven — `validate_sections()` will enforce all three statuses from the same dict.

### P2: Validate `superseded_by` field

New `validate_conditional_fields()` function:
- When `status: superseded`, `superseded_by` must be non-null integer
- `superseded_by` must reference an existing ADR number
- Config: add `conditional_fields` key to `adr.conf.json`

Wire into `validate_sync()` after `validate_tags()`.

### P4: Non-empty conditional section content

New `validate_conditional_section_content()` function:
- Uses existing `_extract_section_body()` to get body text
- Minimum 3 words (config: `min_conditional_section_words`)
- Catches empty or "TBD" placeholders

### Fix ADR-26011

Move supersession rationale from `## Status` body into new `## Supersession Rationale` section. This becomes the integration test — ADR-26011 should fail *before* the fix, pass *after*.

## What to defer

| Gap | Why defer |
|---|---|
| Status body text vs frontmatter mismatch | Cosmetic; frontmatter is authoritative |
| Status transitions enforcement | Requires git history, infeasible in current-state validator |
| Bidirectional integrity (superseding ADR acknowledges) | Cross-file validation, different architecture |

## Implementation order (TDD)

1. Config: update `adr.conf.json` (conditional_sections, allowed_sections, conditional_fields, min_conditional_section_words)
2. Tests RED: `TestConditionalSectionsMissing` (5 tests), `TestValidateConditionalFields` (5 tests), `TestConditionalSectionContent` (5 tests)
3. Code GREEN: inverse check in `validate_sections()`, new `validate_conditional_fields()`, new `validate_conditional_section_content()`, wire into `validate_sync()`
4. Fix ADR-26011: move rationale to `## Supersession Rationale`
5. Verify: `uv run pytest tools/tests/test_check_adr.py`, `uv run tools/scripts/check_adr.py --fix`

## Files to modify

- `.vadocs/types/adr.conf.json` — config additions
- `tools/scripts/check_adr.py` — ~40 lines new code, 2 new functions + inverse check
- `tools/tests/test_check_adr.py` — ~15 new tests in 3 classes
- `architecture/adr/adr_26011_formalization_of_mandatory_script_suite.md` — section restructure

## Verification

- `uv run pytest tools/tests/test_check_adr.py -v`
- `uv run tools/scripts/check_adr.py --fix` (ADR-26011 should fail before fix, pass after)
- `uv run pre-commit run check-adr-index --all-files`
- `uv run pre-commit run test-check-adr --all-files`
