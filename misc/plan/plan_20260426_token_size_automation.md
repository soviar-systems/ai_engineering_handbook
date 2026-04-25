# Token Size Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automate the calculation of `token_size` in YAML frontmatter to eliminate manual entry and pre-commit hook failures.

**Architecture:** 
1. A new utility script `tools/scripts/update_token_counts.py` that scans governed files, calculates tokens using `tiktoken`, and updates the `options.token_size` field.
2. Enhancements to `tools/scripts/check_frontmatter.py` to validate the accuracy of the `token_size` field and provide actionable error messages.
3. **Code-as-Doc**: All motivation, design rationale, and constraints (e.g., why `cl100k_base` is used, why a margin is allowed) must be documented within the code via comprehensive module-level docstrings and internal "contracts" (inline explanations of the *why*).

**Tech Stack:** Python 3.13, `tiktoken` (cl100k_base), `PyYAML`.

---

## File Structure

- Create: `tools/scripts/update_token_counts.py` — Responsible for discovering governed files and updating their `token_size` field.
- Create: `tools/tests/test_update_token_counts.py` — Unit and integration tests for the update script.
- Modify: `tools/scripts/check_frontmatter.py` — Add accuracy validation for the `token_size` field.
- Modify: `tools/tests/test_check_frontmatter.py` — Add tests to verify that incorrect token counts trigger validation errors.

---

## Tasks

### Task 1: TDD for `update_token_counts.py`

**Files:**
- Create: `tools/tests/test_update_token_counts.py`

- [ ] **Step 1: Write test for basic token calculation and update**

```python
import pytest
from pathlib import Path
from tools.scripts.update_token_counts import update_token_counts

def test_update_token_counts_basic(tmp_path):
    # Create a mock governed file
    file = tmp_path / "test.md"
    content = "---\\ntitle: Test\\noptions:\\n  token_size: 0\\n---\\n\\nHello world!"
    file.write_text(content)
    
    # Run update (mocking repo root to tmp_path)
    # Note: update_token_counts should accept a root path for testing
    update_token_counts(root=tmp_path, paths=[file])
    
    updated_content = file.read_text()
    assert "token_size: " in updated_content
    # "Hello world!" + frontmatter should be > 0
    # We'll verify the exact number in the implementation, but it must be > 0
    assert "token_size: 0" not in updated_content
```

- [ ] **Step 2: Write test for updating missing `token_size`**

```python
def test_update_token_counts_missing_field(tmp_path):
    file = tmp_path / "test.md"
    content = "---\\ntitle: Test\\noptions: {}\\n---\\n\\nHello world!"
    file.write_text(content)
    
    update_token_counts(root=tmp_path, paths=[file])
    
    assert "token_size:" in file.read_text()
```

- [ ] **Step 3: Write test for preserving file content**

```python
def test_update_token_counts_preserves_content(tmp_path):
    file = tmp_path / "test.md"
    body = "This is the important body content that must not change."
    content = f"---\\ntitle: Test\\noptions:\\n  token_size: 0\\n---\\n\\n{body}"
    file.write_text(content)
    
    update_token_counts(root=tmp_path, paths=[file])
    
    updated = file.read_text()
    assert body in updated
    assert updated.count("---") == 2
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `uv run pytest tools/tests/test_update_token_counts.py`
Expected: FAIL (Module not found or function not defined)

- [ ] **Step 5: Commit**

```bash
git add tools/tests/test_update_token_counts.py
git commit -m "test: add failing tests for update_token_counts"
```

### Task 2: Implement `update_token_counts.py`

**Files:**
- Create: `tools/scripts/update_token_counts.py`

- [ ] **Step 1: Write comprehensive module docstring (Code-as-Doc)**

Include:
- Purpose: Automate `token_size` updates to eliminate manual entry and pre-commit failures.
- Rationale: Why `tiktoken` and `cl100k_base` were chosen (industry standard for OpenAI/modern LLMs).
- Contract: The tool updates the `options.token_size` field based on the full file content (including frontmatter).

- [ ] **Step 2: Implement token counting logic using `tiktoken`**

```python
import tiktoken

def calculate_tokens(text: str) -> int:
    # Use cl100k_base as the standard for current production-grade LLMs
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))
```

- [ ] **Step 3: Implement frontmatter update logic with internal contracts**

The implementation should:
1. Read file content.
2. Use `FRONTMATTER_PATTERN` from `check_frontmatter.py` (or re-implement) to split frontmatter and body.
3. Parse frontmatter with `yaml.safe_load`.
4. Update `options['token_size']`.
5. Dump YAML and reconstruct the file.

Add inline contracts explaining:
- Why `default_flow_style=False` is used (to maintain readability and avoid serializer variance).
- Why the full content is used for counting rather than just the body.

```python
import yaml
import re
from pathlib import Path

FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

def update_file_tokens(file_path: Path):
    content = file_path.read_text(encoding="utf-8")
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        return False
    
    fm_text = match.group(1)
    body = content[match.end():]
    
    fm = yaml.safe_load(fm_text) or {}
    if "options" not in fm:
        fm["options"] = {}
    
    # Calculate tokens of the WHOLE file (standard for token_size)
    # This ensures the value represents the actual cost of loading the file into context
    fm["options"]["token_size"] = calculate_tokens(content)
    
    # Dump YAML - use default_flow_style=False to keep it readable
    # This prevents the serializer from converting lists/dicts to flow style [a, b], 
    # which would change the visual structure of the frontmatter.
    new_fm_text = yaml.dump(fm, default_flow_style=False, sort_keys=False)
    file_path.write_text(f"---\\n{new_fm_text}---\\n\\n{body}", encoding="utf-8")
    return True
```

- [ ] **Step 4: Implement CLI and Discovery**

Use `scan_paths` logic from `check_frontmatter.py` to find governed files.

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tools/tests/test_update_token_counts.py`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add tools/scripts/update_token_counts.py
git commit -m "feat: implement token count automation script"
```

### Task 3: Enhance `check_frontmatter.py` Validation

**Files:**
- Modify: `tools/scripts/check_frontmatter.py`

- [ ] **Step 1: Add `tiktoken` import and helper**

```python
import tiktoken

def _calculate_tokens(text: str) -> int:
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))
```

- [ ] **Step 2: Modify `validate_parsed_frontmatter` to pass content**

Change signature of `validate_parsed_frontmatter` or create a wrapper to ensure the full file content is available for the token check.

```python
# Update the call in main():
# errors = validate_parsed_frontmatter(frontmatter, file_path, REPO_ROOT, content=content)

def validate_parsed_frontmatter(
    frontmatter: dict, file_path: Path, repo_root: Path, content: str | None = None
) -> list[FrontmatterError]:
    # ... existing logic ...
    # Pass content to _validate_field_value
    for field in required:
        value = _get_field_value(frontmatter, field)
        if value is None:
            continue
        error = _validate_field_value(field, value, file_path, hub, spoke, content=content)
        if error is not None:
            errors.append(error)
```

- [ ] **Step 3: Implement `token_size` accuracy check in `_validate_field_value` with internal contracts**

```python
def _validate_field_value(
    field: str,
    value: Any,
    file_path: Path,
    hub_config: dict,
    spoke_config: dict | None,
    content: str | None = None, # Added parameter
) -> FrontmatterError | None:
    # ... existing checks ...
    
    if field == "token_size":
        if content is None:
            return None # Cannot validate accuracy without content
        
        actual_count = _calculate_tokens(content)
        
        # Contract: We allow a small margin (10 tokens) to account for minor 
        # tokenizer version differences or insignificant whitespace changes 
        # that don't impact context budgeting, while still catching 
        # outdated values that need synchronization.
        if abs(int(value) - actual_count) > 10: 
            return FrontmatterError(
                file_path=file_path,
                error_type="invalid_value",
                field="token_size",
                message=f"declared token_size '{value}' differs from actual count '{actual_count}' — run 'uv run tools/scripts/update_token_counts.py' to fix",
                config_source=".vadocs/conf.json → field_registry.token_size",
            )
```

- [ ] **Step 4: Write failing test in `tools/tests/test_check_frontmatter.py`**

```python
def test_token_size_accuracy(tmp_path):
    file = tmp_path / "test.md"
    content = "---\\ntitle: Test\\noptions:\\n  token_size: 1\\n---\\n\\nThis is a long text."
    file.write_text(content)
    
    # Mock REPO_ROOT and HUB_CONFIG to allow the script to run
    # ...
    errors = validate_frontmatter(file, tmp_path)
    assert any(e.field == "token_size" and "differs" in e.message for e in errors)
```

- [ ] **Step 5: Run tests and verify fix**

Run: `uv run pytest tools/tests/test_check_frontmatter.py`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add tools/scripts/check_frontmatter.py tools/tests/test_check_frontmatter.py
git commit -m "fix: validate token_size accuracy in frontmatter"
```

### Task 4: Final Repository Sync

- [ ] **Step 1: Run update script on whole repo**

Run: `uv run tools/scripts/update_token_counts.py .`

- [ ] **Step 2: Run validator to confirm all pass**

Run: `uv run tools/scripts/check_frontmatter.py .`
Expected: Exit 0

- [ ] **Step 3: Commit updated files**

```bash
git add .
git commit -m "chore: synchronize token_size across all governed files"
```
