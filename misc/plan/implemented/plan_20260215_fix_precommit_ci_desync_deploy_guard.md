# Fix: Pre-commit / CI Desync + Deploy Workflow Branch Guard

## Context

Two related CI issues on the `tmp` branch:

1. **Promotion gate desync:** `check_adr.py --fix` (pre-commit) exits at line 1313 before reaching promotion gate validation (line 1357). CI runs `--verbose` which hits the gate → fails on ADR 26026's duplicate empty `## Participants` header.

2. **Duplicate section headers undetected:** ADR 26026 has two `## Participants` headers. `_extract_section_body()` (line 396) uses `re.search()` — grabs the first (empty) one, ignoring the populated second. `validate_sections()` (line 353) uses a `set`, silently collapsing duplicates. Neither detection nor auto-fix exists.

3. **Deploy on non-main branches:** `deploy.yml` triggers `build-deploy` on all branches. It declares `environment: github-pages` (line 53), so environment protection rules reject the job on non-main branches.

## Changes

### 1. Add duplicate section detection to `validate_sections()`

**File:** `tools/scripts/check_adr.py` — `validate_sections()` (line 353)

Currently uses `found_sections = set()` which silently eats duplicates. Change to count occurrences and report an error for any section name appearing more than once.

```python
section_counts: dict[str, int] = {}
for match in SECTION_HEADER_PATTERN.finditer(adr_file.content):
    name = match.group(1)
    section_counts[name] = section_counts.get(name, 0) + 1

for name, count in section_counts.items():
    if count > 1:
        errors.append(ValidationError(
            number=adr_file.number,
            error_type="duplicate_section",
            message=f"ADR {adr_file.number} has duplicate section: '## {name}' ({count} occurrences)",
        ))

found_sections = set(section_counts)
```

### 2. Add duplicate section auto-fix to `--fix` mode

**File:** `tools/scripts/check_adr.py` — new function `fix_duplicate_sections()`

For each ADR with duplicate `##` headers: merge duplicates by keeping the first header and concatenating all bodies. Write the result back. Called in `--fix` mode (around line 1265) alongside existing status/title fixes.

### 3. Add promotion gate validation to `--fix` mode

**File:** `tools/scripts/check_adr.py` (after line 1312, before `return 0`)

After `--fix` mode verifies sync is clean, run `validate_promotion_gate()` on all ADR files — same logic as lines 1357-1374. This closes the gap so `--fix` mode catches the same errors CI does.

### 4. Add tests (TDD — write first)

**File:** `tools/tests/test_check_adr.py`

- Test: `validate_sections()` returns `duplicate_section` error for ADR with two `## Participants` headers
- Test: `fix_duplicate_sections()` merges two `## Participants` into one with combined body
- Test: `main(["--fix"])` returns exit code 1 when an accepted ADR has empty `## Participants` (promotion gate in fix mode)

### 5. Update script documentation

**File:** `tools/docs/scripts_instructions/check_adr_py_script.md`

Per ADR-26011 (script suite convention), update the doc to reflect new capabilities:

- **Section 1 (line 44):** Add "Duplicate Sections" to the "ensures" list
- **Section 2C (line 103):** Add `duplicate_section` error type to the Format Validation Errors table
- **Section 2D (line 131):** Add step for fixing duplicate sections in Auto-Fix Mode list
- **Section 2D:** Add note that `--fix` mode also runs promotion gate validation
- **Section 5 (line 278):** Add `TestDuplicateSections` and `TestPromotionGateInFixMode` test classes to the test suite table
- **Section 6:** Add new Scenario for fixing duplicate sections
- Bump version from `0.4.0` to `0.5.0`

### 6. Gate `build-deploy` job to main branch only

**File:** `.github/workflows/deploy.yml` (line 50)

Add `if: github.ref == 'refs/heads/main'` to the `build-deploy` job.

```yaml
  build-deploy:
    needs: validate
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
```

### 7. Document the environment protection pitfall

**File:** `tools/docs/website/01_github_pages_deployment.md` — Common Pitfalls table (line 304)

Add a new row:

| `deployment was rejected` on non-main branches | `environment: github-pages` enforces protection rules at *job* level, not step level | Add `if: github.ref == 'refs/heads/main'` to the entire `build-deploy` job, not just the deploy step |

## Verification

```bash
# 1. Test suite (TDD — write tests first, then implement)
uv run pytest tools/tests/test_check_adr.py -v

# 2. Both modes should pass after all fixes
uv run tools/scripts/check_adr.py --verbose
uv run tools/scripts/check_adr.py --fix

# 3. Pre-commit hook
uv run pre-commit run check-adr-index --all-files

# 4. Verify deploy.yml — push to tmp branch, confirm build-deploy job is skipped
```
