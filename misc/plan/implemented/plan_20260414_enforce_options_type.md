# Enforce `options.type` for All Frontmatter Files

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `options.type` a mandatory field for any markdown file with YAML frontmatter — files without it should fail validation (exit 1), not warn-and-skip.

**Architecture:** Currently `check_frontmatter.py` emits a WARNING to stderr and silently skips validation when a file has frontmatter but no `options.type` (line 190-196). This means ungoverned files bypass all schema validation. The fix changes this behavior to emit a blocking `FrontmatterError` with `error_type="missing_type"`, causing exit 1. Tests must verify the new error behavior and ensure main() still exits 0 when no errors exist.

**Tech Stack:** Python 3.13+, pathlib, pytest, yaml

---

## Problem Analysis

### Current Behavior (lines 190-196 in `check_frontmatter.py`):
```python
doc_type = resolve_type(frontmatter)
if doc_type is None:
    print(
        f"WARNING: {file_path} — has frontmatter but no options.type, skipping type-specific validation",
        file=sys.stderr,
    )
    continue  # ← SKIPS validation entirely
```

### Desired Behavior:
Files with frontmatter but no `options.type` should produce a `FrontmatterError` with `error_type="missing_type"`. This is a **blocking error** — main() returns exit 1.

### Why This Matters:
- **Design principle:** All governed files MUST declare their type to be governed. No silent bypasses.
- **Current gap:** Any `.md` file with a YAML block bypasses schema validation if it lacks `options.type` — this is a validation hole.
- **Consistency:** `namespace_warning` already exists as a non-blocking warning; `missing_type` should be treated the same way initially (warning) then promoted to error after migration. However, the todo explicitly states: "files without a type should **fail**, not warn-and-skip."

### Impact Analysis:
1. **`main()` loop:** Change the `if doc_type is None:` branch from `print(WARNING) + continue` to `errors.append(FrontmatterError) + continue`
2. **`validate_parsed_frontmatter()`:** Currently returns `[]` for `doc_type is None`. Should return `[FrontmatterError(...)]` instead.
3. **Tests:** `TestWarningNoType` tests will need updating — warning becomes error. New test class needed for error behavior.
4. **Existing files:** Any real `.md` files in the repo with frontmatter but no `options.type` will now fail validation. These need to be identified and fixed.

---

## File Structure

### Files to Modify:
- **`tools/scripts/check_frontmatter.py`** (lines 190-196, 275-296)
  - Change `main()`: replace warning+skip with error collection
  - Change `validate_parsed_frontmatter()`: return error instead of `[]` for missing type

- **`tools/tests/test_check_frontmatter.py`**
  - Update `TestWarningNoType` → `TestMissingType`: test error behavior, not warning
  - Add test for `validate_parsed_frontmatter()` returning error for missing type
  - Ensure existing tests still pass (valid files with type still work)

### Files to Check (no changes expected, but verify):
- `.vadocs/conf.json` — already has `type` in field_registry with `myst_native: false`
- `.vadocs/types/*.conf.json` — no changes needed, type is a hub-level concept

---

## Task Decomposition

### Task 1: Add `missing_type` to FrontmatterError taxonomy and update `validate_parsed_frontmatter()`

**Files:**
- Modify: `tools/scripts/check_frontmatter.py:56-67` (FrontmatterError docstring)
- Modify: `tools/scripts/check_frontmatter.py:275-296` (validate_parsed_frontmatter)
- Test: `tools/tests/test_check_frontmatter.py` (new test class)

- [ ] **Step 1: Document the new error_type in FrontmatterError docstring**

Add `"missing_type"` to the error_type taxonomy in the docstring:

```python
    """Represents a frontmatter validation error or warning.

    error_type taxonomy (used by main() to separate blocking vs non-blocking):
        "missing_field"      — required field absent (blocking)
        "invalid_format"     — field present but wrong format, e.g. bad date (blocking)
        "invalid_value"      — field value not in allowed set, e.g. unknown tag (blocking)
        "unknown_type"       — options.type not in conf.json types registry (blocking)
        "missing_type"       — frontmatter present but options.type absent (blocking)
        "namespace_warning"  — non-myst_native field at top level instead of options.* (non-blocking)

    main() treats "namespace_warning" as stderr-only; all others cause exit 1.
    """
```

- [ ] **Step 2: Write test for `validate_parsed_frontmatter()` returning error for missing type**

```python
class TestValidateMissingType:
    """Contract: files with frontmatter but no options.type produce blocking error."""

    def test_validate_parsed_frontmatter_returns_error_for_missing_type(self, frontmatter_env):
        """Frontmatter without options.type → returns [FrontmatterError]."""
        fm = {"title": "Test", "date": "2026-01-01"}  # no options.type
        md_file = frontmatter_env / "test.md"
        errors = _module.validate_parsed_frontmatter(fm, md_file, frontmatter_env)
        missing_type = [e for e in errors if e.error_type == "missing_type"]
        assert len(missing_type) == 1
        assert missing_type[0].field == "options.type"
        assert "options.type" in missing_type[0].message

    def test_validate_parsed_frontmatter_no_error_when_type_present(self, frontmatter_env):
        """Frontmatter with options.type → no missing_type error."""
        fm = {"title": "Test", "options": {"type": "adr"}}
        md_file = frontmatter_env / "test.md"
        errors = _module.validate_parsed_frontmatter(fm, md_file, frontmatter_env)
        missing_type = [e for e in errors if e.error_type == "missing_type"]
        assert len(missing_type) == 0
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tools/tests/test_check_frontmatter.py::TestValidateMissingType -v`
Expected: FAIL — `validate_parsed_frontmatter()` currently returns `[]` for missing type.

- [ ] **Step 4: Implement the change in `validate_parsed_frontmatter()`**

Replace lines 289-296:
```python
    # Step 1: Determine document type from options.type field.
    # Files without options.type are not governed — this is now a blocking error.
    doc_type = resolve_type(frontmatter)
    if doc_type is None:
        return [
            FrontmatterError(
                file_path=file_path,
                error_type="missing_type",
                field="options.type",
                message="frontmatter present but missing required 'options.type' — all governed files must declare their type",
                config_source=".vadocs/conf.json → field_registry.type",
            )
        ]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tools/tests/test_check_frontmatter.py::TestValidateMissingType -v`
Expected: PASS

---

### Task 2: Update `main()` to collect errors instead of printing warnings

**Files:**
- Modify: `tools/scripts/check_frontmatter.py:186-196` (main loop)
- Test: `tools/tests/test_check_frontmatter.py` (update TestWarningNoType)

- [ ] **Step 1: Write test for `main()` exit code 1 when type is missing**

```python
class TestMissingTypeError:
    """Contract: files with frontmatter but no options.type cause exit 1."""

    def test_main_exits_1_for_missing_type(self, frontmatter_env, capsys):
        """File without options.type → exit code 1, error on stdout."""
        content = "---\ntitle: Untyped Document\ndate: 2026-01-01\n---\n\n# Body\n"
        md_file = frontmatter_env / "untyped.md"
        md_file.write_text(content, encoding="utf-8")
        exit_code = _module.main([str(md_file)])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "options.type" in captured.out
        assert "missing" in captured.out.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tools/tests/test_check_frontmatter.py::TestMissingTypeError -v`
Expected: FAIL — `main()` currently exits 0 and prints to stderr.

- [ ] **Step 3: Update `main()` to collect errors instead of warning**

Replace lines 190-196:
```python
        doc_type = resolve_type(frontmatter)
        if doc_type is None:
            all_errors.append(
                FrontmatterError(
                    file_path=file_path,
                    error_type="missing_type",
                    field="options.type",
                    message="frontmatter present but missing required 'options.type' — all governed files must declare their type",
                    config_source=".vadocs/conf.json → field_registry.type",
                )
            )
            continue
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tools/tests/test_check_frontmatter.py::TestMissingTypeError -v`
Expected: PASS

- [ ] **Step 5: Remove the old warning test class or convert to error test**

The existing `TestWarningNoType` class tests for warning behavior that no longer exists. Replace it:

```python
class TestMissingTypeError:
    """Contract: files with frontmatter but no options.type cause exit 1."""

    def test_error_printed_for_missing_type(self, frontmatter_env, capsys):
        """File with frontmatter but no options.type → error on stdout, exit 1."""
        content = "---\ntitle: Untyped Document\ndate: 2026-01-01\n---\n\n# Body\n"
        md_file = frontmatter_env / "untyped.md"
        md_file.write_text(content, encoding="utf-8")
        exit_code = _module.main([str(md_file)])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "options.type" in captured.out
```

Delete the old `TestWarningNoType` class entirely.

- [ ] **Step 6: Run full test suite to ensure no regressions**

Run: `uv run pytest tools/tests/test_check_frontmatter.py -v`
Expected: All tests PASS

---

### Task 3: Find and fix existing files in the repo that lack `options.type`

**Files:**
- Scan: All `.md` files in the repository with frontmatter
- Fix: Each file found without `options.type`

- [ ] **Step 1: Run the validator on the full repo to find offending files**

Run: `uv run tools/scripts/check_frontmatter.py`
Expected: Exit 1, with a list of files missing `options.type`.

- [ ] **Step 2: For each file, add `options.type` based on file context**

Files will need their type determined by context:
- ADRs → `options.type: adr`
- Evidence sources → `options.type: source`
- Evidence analyses → `options.type: analysis`
- Tutorials/guides → appropriate type from `.vadocs/conf.json` types registry

Example addition to frontmatter:
```yaml
---
title: Existing Title
date: 2026-01-01
options:
  type: adr
---
```

- [ ] **Step 3: Re-run validator to confirm all files pass**

Run: `uv run tools/scripts/check_frontmatter.py`
Expected: Exit 0

---

### Task 4: Update docstring in `validate_parsed_frontmatter()` to reflect new behavior

**Files:**
- Modify: `tools/scripts/check_frontmatter.py:278-288` (docstring)

- [ ] **Step 1: Update the docstring**

Replace:
```python
    """Validate already-parsed frontmatter dict against hub + spoke rules.

    For use by domain scripts (check_adr.py, check_evidence.py) that have
    already parsed frontmatter for their own structural validation. This
    avoids double-parsing during the migration period where both the domain
    script and check_frontmatter.py run on the same files.

    Returns [] for files with no options.type — caller is responsible for
    deciding whether to warn (main() does, domain scripts may not).
    """
```

With:
```python
    """Validate already-parsed frontmatter dict against hub + spoke rules.

    For use by domain scripts (check_adr.py, check_evidence.py) that have
    already parsed frontmatter for their own structural validation. This
    avoids double-parsing during the migration period where both the domain
    script and check_frontmatter.py run on the same files.

    Returns [FrontmatterError] for files with frontmatter but no options.type —
    all governed files must declare their type to be validated.
    """
```

- [ ] **Step 2: Run full test suite to verify no regressions**

Run: `uv run pytest tools/tests/test_check_frontmatter.py -v`
Expected: All tests PASS

---

### Task 5: Sync Jupytext pairs and commit

**Files:**
- All modified `.md` files that have `.ipynb` pairs

- [ ] **Step 1: Sync all edited files with Jupytext**

Run: `uv run jupytext --sync`

- [ ] **Step 2: Verify sync succeeded**

Run: `uv run jupytext --verify`

- [ ] **Step 3: Stage all changes**

```bash
git add tools/scripts/check_frontmatter.py tools/tests/test_check_frontmatter.py
# Add any .md files fixed in Task 3
git add <specific-paths>
```

- [ ] **Step 4: Commit**

```bash
git commit -m "fix: enforce options.type for all frontmatter files

- check_frontmatter.py: emit blocking error when frontmatter present but options.type absent
- validate_parsed_frontmatter(): return FrontmatterError instead of [] for missing type
- main(): collect missing_type errors instead of printing warnings to stderr
- test_check_frontmatter.py: replace TestWarningNoType with TestMissingTypeError
- Fix N existing .md files by adding options.type based on file context

All governed files must now declare their type to pass validation.
Closes todo: Require options.type for all markdown files with frontmatter"
```

---

## Risk Mitigation

1. **Existing files without type:** Task 3 will identify them. Each needs manual review to determine the correct type. If uncertain, check the file's directory structure and content.
2. **Test brittleness:** Tests assert on `error_type == "missing_type"` and field presence, not exact message strings — follows non-brittle test design from AGENTS.md.
3. **Domain script callers:** `validate_parsed_frontmatter()` is called by `check_adr.py` and `check_evidence.py`. These scripts call it with files that already have a known type, so the new error path won't trigger. Verify by reading their call sites.

## Self-Review

### 1. Spec coverage
- ✅ `options.type` mandatory for all frontmatter files — enforced via `missing_type` error
- ✅ Files without type should fail, not warn-and-skip — `main()` exits 1, errors on stdout
- ✅ Tests updated — `TestWarningNoType` replaced with `TestMissingTypeError`, new `TestValidateMissingType` class
- ✅ Docstrings updated to reflect new behavior
- ✅ Existing files in repo identified and fixed

### 2. Placeholder scan
No TBD, TODO, or placeholder code in the plan. All steps contain actual code.

### 3. Type consistency
- `FrontmatterError` dataclass usage consistent across all steps
- `error_type="missing_type"` used consistently in main() and validate_parsed_frontmatter()
- Test assertions use semantic checks (`error_type ==`, `field ==`, `exit_code ==`) not exact message matching
