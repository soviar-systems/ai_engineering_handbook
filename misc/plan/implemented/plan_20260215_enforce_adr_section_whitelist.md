# Future Plan: Enforce ADR Section Whitelist in `check_adr.py`

## Context

During the ADR-26004..26008 triage, we introduced a `## Rejection Rationale` section for rejected ADRs and updated the template accordingly. This revealed a gap: `check_adr.py` only validates that **required** sections exist — it does **not** flag unexpected/extra sections. Any arbitrary `## Foo` section silently passes validation.

The template (`adr_template.md`) should be the Single Source of Truth for allowed sections, and `check_adr.py` should enforce this.

## Current State (as of 2026-02-15)

- **`adr_config.yaml`** defines `required_sections` (8 items: Date, Status, Context, Decision, Consequences, Alternatives, References, Participants) and `recommended_subsections` (Positive, Negative / Risks under Consequences)
- **`validate_sections()`** in `check_adr.py` only checks: (1) required sections present, (2) no duplicate sections
- **No validation** for unexpected sections — extra `## Foo` sections pass silently
- **Template** now includes conditional `## Rejection Rationale` (for rejected status) and `## Title` — neither is in `required_sections`

## Proposed Changes

### 1. Add `allowed_sections` to `adr_config.yaml`

```yaml
# Sections allowed in ADR documents (superset of required_sections)
allowed_sections:
  - Title
  - Date
  - Status
  - Rejection Rationale  # conditional: only for rejected ADRs
  - Context
  - Decision
  - Consequences
  - Alternatives
  - References
  - Participants
```

Alternatively: derive allowed sections as `required_sections + optional_sections` to avoid duplication.

### 2. Update `validate_sections()` in `check_adr.py`

Add a check after finding all sections:

```python
ALLOWED_SECTIONS = set(config.get("allowed_sections", []))

# After finding all section headers...
if ALLOWED_SECTIONS:
    unexpected = found_sections - ALLOWED_SECTIONS
    for section in unexpected:
        errors.append(ValidationError(
            number=adr_file.number,
            error_type="unexpected_section",
            message=f"ADR {adr_file.number} has unexpected section: '## {section}' (not in allowed_sections)",
        ))
```

### 3. Conditional section validation

`## Rejection Rationale` should only appear in ADRs with `status: rejected`. Add status-aware validation:

```yaml
conditional_sections:
  rejected:
    - Rejection Rationale
```

### 4. Update tests (TDD)

**Write tests FIRST** per CLAUDE.md convention:

- `test_unexpected_section_produces_error` — ADR with `## CustomSection` should fail
- `test_allowed_extra_section_passes` — ADR with `## Title` (in allowed list) should pass
- `test_rejection_rationale_only_for_rejected` — `## Rejection Rationale` in a `proposed` ADR should fail
- `test_rejection_rationale_in_rejected_adr_passes` — same section in `rejected` ADR should pass

## Files to Modify

| File | Change |
|------|--------|
| `architecture/adr/adr_config.yaml` | Add `allowed_sections` and `conditional_sections` |
| `tools/scripts/check_adr.py` | Extend `validate_sections()` with whitelist check |
| `tools/tests/test_check_adr.py` | Add tests for unexpected/conditional sections |
| `architecture/adr/adr_template.md` | Verify alignment (already updated) |

## Discovery: `##` Headers Inside Code Blocks (Pre-existing Bug)

The `SECTION_HEADER_PATTERN` regex (`^##\s+(.+?)$` with `re.MULTILINE`) matches `##` headers inside fenced code blocks (e.g. `` ```markdown ``). The `re.MULTILINE` flag makes `^` match any line start, not just the document start, so a line like `## Governing ADRs (in hub)` inside a code fence is treated as a real section header.

**Impact:** ADR-26020 contains an example `ARCHITECTURE.md` snippet inside a `` ```markdown `` fence with `## Governing ADRs (in hub)` and `## Implementation ADRs (in this repo)`. These are parsed as real sections today (silently passing) but would be flagged as unexpected by the new whitelist.

**Fix:** Strip fenced code blocks from content before extracting section headers. A preprocessing step with `re.sub(r'```.*?```', '', content, flags=re.DOTALL)` removes all fenced blocks before the section regex runs.

## Verification

1. `uv run pytest tools/tests/test_check_adr.py -v` — all tests pass
2. `uv run tools/scripts/check_adr.py` — no false positives on existing ADRs
3. Manually add a `## Bogus` section to an ADR and verify it's flagged
