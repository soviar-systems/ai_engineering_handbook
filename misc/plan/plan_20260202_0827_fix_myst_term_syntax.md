# Plan: Fix Broken MyST Term Syntax in check_adr.py

## Problem Statement

MyST term references are broken because of a format mismatch:
- **Glossary defines**: `ADR-26001` (hyphen separator)
- **References use**: `{term}`ADR-26001`` (space separator)
- **Error**: "Cross reference target was not found: term-adr 26006"

Found 60+ broken references across 15+ files in the codebase.

## Solution

Extend `check_adr.py` to validate MyST term references and optionally fix them.

## Implementation Steps

### 1. Add Term Reference Validation (TDD: Tests First)

**File**: `tools/tests/test_check_adr.py`

Add tests for:
- Detecting broken `{term}`ADR-26001`` patterns (space instead of hyphen)
- Detecting valid `{term}`ADR-26001`` patterns
- Reporting errors for unresolved term references
- Fix mode correcting broken references

### 2. Implement Validation Logic

**File**: `tools/scripts/check_adr.py`

Add new functionality:

```python
# New regex pattern
TERM_REFERENCE_PATTERN = re.compile(r"\{term\}`ADR[ -](\d+)`")

# New validation function
def validate_term_references(files: list[Path], index_entries: list[IndexEntry]) -> list[ValidationError]:
    """Check all {term}`ADR ...` references use hyphen format."""
    # 1. Build set of valid ADR numbers from glossary
    # 2. Scan files for {term}`ADR ...` patterns
    # 3. Report errors for:
    #    - Space format: {term}`ADR-26001` should be {term}`ADR-26001`
    #    - Missing ADRs: referencing non-existent ADR numbers
```

### 3. Add --check-terms CLI Flag

Extend argument parser:
```python
parser.add_argument(
    "--check-terms",
    action="store_true",
    help="Validate {term}`ADR...` references in all .md files",
)
```

### 4. Add --fix-terms Mode

Auto-correct broken references:
- Replace `{term}`ADR-26001`` with `{term}`ADR-26001``
- Report files modified

### 5. Integrate with Existing Validation

Add term validation to `validate_sync()` or as a separate check in `main()`.

## Files to Modify

1. `tools/scripts/check_adr.py` - Add validation logic
2. `tools/tests/test_check_adr.py` - Add tests (write first per TDD)

## Files to Scan for Broken References

Based on grep results, these files have broken term references:
- `architecture/adr/adr_26002*.md` through `adr_26012*.md`
- `ai_system/2_model/selection/general_purpose_vs_agentic_models.md`
- `ai_system/4_orchestration/workflows/aidx_industrial_ai_orchestration_framework.md`
- `tools/docs/scripts_instructions/docs_validation_engine_development_plan.md`
- Paired `.ipynb` files (will be synced via jupytext)

## Verification

1. Run new tests: `uv run pytest tools/tests/test_check_adr.py -v`
2. Run check: `uv run python tools/scripts/check_adr.py --check-terms --verbose`
3. Run fix: `uv run python tools/scripts/check_adr.py --fix-terms`
4. Sync notebooks: `uv run jupytext --sync`
5. Build docs to verify no MyST errors: `myst build --html`

## Technical Notes

- Pattern `{term}`ADR-26001`` must match glossary entry `ADR-26001` exactly
- Scan should include all `.md` files, not just ADRs
- Only modify `.md` files; `.ipynb` files will be synced by jupytext
