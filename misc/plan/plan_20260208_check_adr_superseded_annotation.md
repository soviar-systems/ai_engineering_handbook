# Plan: Add superseded_by annotation to check_adr.py fix_index

## Context

The `check_adr.py --fix` pre-commit hook regenerates `adr_index.md` from ADR files. Currently, `fix_index()` generates plain entries like:

```
ADR-26018
: [Title](/path)
```

For superseded ADRs in the "Historical Context" section, we want annotations:

```
ADR-26018
: [Title](/path) — superseded by {term}`ADR-26023`
```

This helps users orient themselves when reading the index. The hook currently strips these annotations on every commit. We need to modify `fix_index()` to generate them from the `superseded_by` frontmatter field.

---

## Files to modify

1. **`tools/tests/test_check_adr.py`** — add tests (TDD: write first)
2. **`tools/scripts/check_adr.py`** — modify `fix_index()` to emit annotations
3. **`tools/docs/scripts_instructions/check_adr_py_script.md`** — update docs (Section 2D, line 131-143)

---

## Step 1: Add test helper support for `superseded_by`

**File:** `tools/tests/test_check_adr.py`

Add `superseded_by` parameter to `create_adr_file_full()` (line 254). Default: `None` (meaning `null` in YAML, same as current behavior). When set to a string (e.g., `"ADR-26023"`), output `superseded_by: ADR-26023` in the frontmatter.

---

## Step 2: Write failing test

**File:** `tools/tests/test_check_adr.py`

Add test in `TestAutoFixIndex` class:

```python
def test_superseded_entry_has_annotation(self, adr_env):
    """Superseded ADRs should include 'superseded by' annotation in index."""
    from tools.scripts.check_adr import fix_index, parse_index

    create_adr_file_full(
        adr_env.adr_dir, 26001, "Old Decision", "old_decision",
        status="superseded", superseded_by="ADR-26002",
    )
    create_adr_file_full(
        adr_env.adr_dir, 26002, "New Decision", "new_decision",
        status="accepted",
    )

    fix_index()

    content = adr_env.index_path.read_text(encoding="utf-8")
    # Superseded entry should have annotation
    assert "superseded by" in content.lower()
    assert "ADR-26002" in content
```

Also add a test that non-superseded entries do NOT get annotations.

---

## Step 3: Modify `fix_index()` in check_adr.py

**File:** `tools/scripts/check_adr.py`, function `fix_index()` (line 935)

In the loop at line 972-978, after building the basic entry line, check `adr.frontmatter` for `superseded_by`. If it's set and not `null`/`None`, append the annotation:

```python
for adr in sorted(section_adrs, key=lambda x: x.number):
    title = adr.title
    link = f"/architecture/adr/{adr.path.name}"

    # Build annotation for superseded ADRs
    annotation = ""
    if adr.frontmatter and adr.frontmatter.get("superseded_by"):
        successor = adr.frontmatter["superseded_by"]
        annotation = f" — superseded by {{term}}`{successor}`"

    lines.append(f"ADR-{adr.number}\n")
    lines.append(f": [{title}]({link}){annotation}\n")
    lines.append("\n")
```

Note: The `INDEX_ENTRY_PATTERN` regex on line 42 only captures `[title](link)` — the annotation text after `)` is ignored by the parser and does NOT need regex changes. This is safe because `parse_index()` captures title and link, and the annotation is decorative.

---

## Step 4: Verify `parse_index()` still works

The `INDEX_ENTRY_PATTERN` (line 41-44):
```python
INDEX_ENTRY_PATTERN = re.compile(
    r"^ADR-(\d+)\s*\n:\s*\[([^\]]+)\]\(([^)]+)\)",
    re.MULTILINE,
)
```

This captures up to the closing `)` of the link. Any text after `)` (the annotation) is not captured. This means `parse_index()` correctly ignores annotations — **no regex change needed**.

---

## Step 5: Update docs

**File:** `tools/docs/scripts_instructions/check_adr_py_script.md`

In Section 2D "Auto-Fix Mode (`--fix`)" (line 131-143), add item after point 3:

> 4. **Annotates superseded entries**: Adds "— superseded by {term}`ADR-XXXXX`" to index entries for ADRs with `superseded_by` set in frontmatter

Also update the reflection block (lines 18-27) to use MyST-aligned frontmatter, and bump version.

Then sync: `uv run jupytext --sync tools/docs/scripts_instructions/check_adr_py_script.md`

---

## Verification

```bash
# Run test suite with coverage (should pass after implementation)
uv run pytest tools/tests/test_check_adr.py --cov=tools.scripts.check_adr --cov-report=term-missing -v

# Run the hook on the actual index
uv run python tools/scripts/check_adr.py --fix

# Verify the annotation appears in the index
grep "superseded by" architecture/adr_index.md

# Re-commit with the hook passing
```
