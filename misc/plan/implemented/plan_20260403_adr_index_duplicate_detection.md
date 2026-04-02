# ADR Index Duplicate Detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add explicit duplicate detection to check_adr.py's fix_index() function that reports exactly where duplicate ADR entries appear in the index.

**Architecture:** Add duplicate detection logic before index regeneration that tracks ADR numbers by their index location (status/primary_tag combination), then prints warnings with exact locations for any duplicates found.

**Tech Stack:** Python 3.13+, existing check_adr.py infrastructure (AdrFile, get_adr_files(), _get_primary_tag())

---

## File Structure

**Modify:**
- `tools/scripts/check_adr.py:1442-1520` — fix_index() function, add duplicate detection logic
- `tools/tests/test_check_adr.py` — add tests for duplicate detection

**Files to understand (read-only):**
- `tools/scripts/check_adr.py:931-980` — parse_index() function
- `tools/scripts/check_adr.py:1410-1440` — _format_entry() function
- `tools/scripts/check_adr.py:180-200` — _get_primary_tag() function

---

### Task 1: Add duplicate detection to fix_index()

**Files:**
- Modify: `tools/scripts/check_adr.py:1442-1520`

- [ ] **Step 1: Add duplicate detection before index building**

Add this code after the "Group ADRs by section" block and before "Build new index content":

```python
# Check for duplicate ADR numbers before building index
seen_numbers: dict[int, list[str]] = {}
for adr in adr_files:
    status = adr.status if adr.status else DEFAULT_STATUS
    tag = _get_primary_tag(adr)
    location = f"{status}/{tag}"
    if adr.number not in seen_numbers:
        seen_numbers[adr.number] = []
    seen_numbers[adr.number].append(location)

for number, locations in seen_numbers.items():
    if len(locations) > 1:
        print(f"WARNING: ADR-{number} appears in multiple index locations: {', '.join(locations)}", file=sys.stderr)
```

- [ ] **Step 2: Import sys at module top if not present**

Check line ~1-30 of check_adr.py. If `import sys` is missing, add it:

```python
import sys
```

- [ ] **Step 3: Run check_adr.py --fix to test**

Run: `uv run tools/scripts/check_adr.py --fix`
Expected: If duplicates exist, warning printed to stderr showing exact locations

- [ ] **Step 4: Commit**

```bash
git add tools/scripts/check_adr.py
git commit -m "feat: Add duplicate detection to fix_index() with location reporting"
```

---

### Task 2: Write tests for duplicate detection

**Files:**
- Modify: `tools/tests/test_check_adr.py`
- Create test class: `TestFixIndexDuplicateDetection`

- [ ] **Step 1: Add test for duplicate detection warning**

Add to `tools/tests/test_check_adr.py`:

```python
class TestFixIndexDuplicateDetection:
    """Contract: fix_index() warns when ADR appears in multiple locations."""

    def test_duplicate_adr_prints_warning(self, tmp_path, capsys):
        """ADR appearing in multiple status/tag combinations produces warning."""
        # Create two ADR files with same number but different status
        adr1 = tmp_path / "architecture" / "adr" / "adr_26001_test1.md"
        adr1.parent.mkdir(parents=True)
        adr1.write_text(
            "---\nid: 26001\ntitle: Test ADR\nstatus: accepted\ntags: [governance]\ndate: 2026-01-01\n---\n\n# Test\n"
        )
        
        adr2 = tmp_path / "architecture" / "adr" / "adr_26001_test2.md"
        adr2.write_text(
            "---\nid: 26001\ntitle: Test ADR Duplicate\nstatus: rejected\ntags: [governance]\ndate: 2026-01-01\n---\n\n# Test\n"
        )
        
        # Mock get_adr_files to return both files
        with patch("tools.scripts.check_adr.get_adr_files") as mock_get:
            from tools.scripts.check_adr import AdrFile
            mock_get.return_value = [
                AdrFile(
                    path=adr1,
                    number=26001,
                    title="Test ADR",
                    status="accepted",
                    frontmatter={"id": 26001, "title": "Test ADR", "status": "accepted", "tags": ["governance"], "date": "2026-01-01"}
                ),
                AdrFile(
                    path=adr2,
                    number=26001,
                    title="Test ADR Duplicate",
                    status="rejected",
                    frontmatter={"id": 26001, "title": "Test ADR Duplicate", "status": "rejected", "tags": ["governance"], "date": "2026-01-01"}
                )
            ]
            
            # Call fix_index
            from tools.scripts.check_adr import fix_index
            fix_index()
        
        # Check warning was printed
        captured = capsys.readouterr()
        assert "ADR-26001 appears in multiple index locations" in captured.err
        assert "accepted/governance" in captured.err
        assert "rejected/governance" in captured.err
```

- [ ] **Step 2: Run test to verify it passes**

Run: `uv run pytest tools/tests/test_check_adr.py::TestFixIndexDuplicateDetection::test_duplicate_adr_prints_warning -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tools/tests/test_check_adr.py
git commit -m "test: Add duplicate detection test for fix_index()"
```

---

### Task 3: Verify end-to-end with actual duplicate

**Files:**
- None (verification only)

- [ ] **Step 1: Check current index for duplicates**

Run: `grep -n "ADR-26045" architecture/adr_index.md`
Expected: Show line numbers where ADR-26045 appears

- [ ] **Step 2: Run fix_index and check warning**

Run: `uv run tools/scripts/check_adr.py --fix 2>&1 | grep -i "warning\|duplicate"`
Expected: Warning showing ADR-26045 appears in multiple locations

- [ ] **Step 3: Verify index is correct after fix**

Run: `grep -c "ADR-26045" architecture/adr_index.md`
Expected: 1 (single entry after fix)

---

## Self-Review

**Spec coverage:**
- ✅ Duplicate detection added to fix_index()
- ✅ Warning messages show exact locations (status/primary_tag)
- ✅ Tests verify warning output
- ✅ End-to-end verification with actual duplicate

**Placeholder scan:**
- ✅ No TBD/TODO
- ✅ All code shown explicitly
- ✅ All commands with expected output

**Type consistency:**
- ✅ AdrFile used consistently
- ✅ _get_primary_tag() called correctly
- ✅ seen_numbers dict type matches usage

---

## Execution Handoff

**Plan complete and saved to `misc/plan/plan_20260403_adr_index_duplicate_detection.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
