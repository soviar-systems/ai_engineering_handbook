# Mandatory Frontmatter Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enforce that all files with extensions defined in the hub configuration must have YAML frontmatter, while providing a configurable exclusion list for exempt files and directories.

**Architecture:**
1. **Configuration**: 
    - Add `governed_extensions: [".md", ".ipynb"]` to `.vadocs/conf.json`.
    - Add `governance_excludes` to `.vadocs/conf.json` (or a dedicated validation config), supporting both directory segments and specific file patterns.
2. **Validation Logic**: Update `check_frontmatter.py` to:
    - Load `governed_extensions` and `governance_excludes` from the hub config.
    - Update the scanning/validation loop to first check if a file matches any exclusion pattern.
    - For non-excluded files with a governed extension, emit a blocking `FrontmatterError` (`error_type="missing_frontmatter"`) if no frontmatter is present.
3. **Verification**: Use TDD to verify that governed files fail, excluded files are skipped, and non-governed extensions are ignored.

**Tech Stack:** Python, Pytest, JSON, YAML.

---

### Task 1: Update Governance Configuration

**Files:**
- Modify: `.vadocs/conf.json`

- [ ] **Step 1: Add governance scope and excludes to hub config**
  Add the following to `.vadocs/conf.json`:
  ```json
  "governed_extensions": [".md", ".ipynb"],
  "governance_excludes": {
    "dirs": ["misc", ".github", "tests"],
    "files": ["README.md", "CONTRIBUTING.md"]
  }
  ```

- [ ] **Step 2: Commit config change**
  ```bash
  git add .vadocs/conf.json
  git commit -m "chore(governance): define governed extensions and exclusions in hub config"
  ```

---

### Task 2: Update Frontmatter Error Taxonomy

**Files:**
- Modify: `tools/scripts/check_frontmatter.py`

- [ ] **Step 1: Add `missing_frontmatter` to `FrontmatterError` docstring**
  Update the `error_type` taxonomy in the `FrontmatterError` dataclass to include:
  `"missing_frontmatter" — file has governed extension but no YAML frontmatter present (blocking)`

- [ ] **Step 2: Commit taxonomy update**
  ```bash
  git add tools/scripts/check_frontmatter.py
  git commit -m "chore(governance): add missing_frontmatter to error taxonomy"
  ```

---

### Task 3: Implement Mandatory Governance & Exclusion Logic

**Files:**
- Modify: `tools/scripts/check_frontmatter.py`

- [ ] **Step 1: Load scope and excludes in `main()`**
  Extract `governed_exts` and `governance_excludes` from `HUB_CONFIG`.
  ```python
  governed_exts = HUB_CONFIG.get("governed_extensions", [])
  excludes = HUB_CONFIG.get("governance_excludes", {})
  exclude_dirs = excludes.get("dirs", [])
  exclude_files = excludes.get("files", [])
  ```

- [ ] **Step 2: Implement the exclusion check**
  Before the frontmatter parsing logic in the `for file_path in files:` loop, add a check to skip excluded files.
  ```python
  # Skip explicitly excluded files or directories
  if any(part in exclude_dirs for part in file_path.parts) or file_path.name in exclude_files:
      continue
  ```

- [ ] **Step 3: Replace "opt-in" skip logic with mandatory check**
  Locate the `if frontmatter is None: continue` block and replace it with:
  ```python
  if frontmatter is None:
      if file_path.suffix in governed_exts:
          all_errors.append(
              FrontmatterError(
                  file_path=file_path,
                  error_type="missing_frontmatter",
                  field=None,
                  message="file has governed extension but no YAML frontmatter present — all governed files must have frontmatter to be subject to validation",
                  config_source=".vadocs/conf.json → governed_extensions",
              )
          )
      continue
  ```

- [ ] **Step 4: Commit implementation**
  ```bash
  git add tools/scripts/check_frontmatter.py
  git commit -m "feat(governance): enforce mandatory frontmatter with configurable exclusions"
  ```

---

### Task 4: TDD Verification

**Files:**
- Modify: `tools/tests/test_check_frontmatter.py`

- [ ] **Step 1: Add test for mandatory frontmatter failure**
  Create a file with `.md` extension and no frontmatter $\rightarrow$ assert exit 1 and `missing_frontmatter` error.

- [ ] **Step 2: Add test for exclusion (directory)**
  Create a file in a directory listed in `governance_excludes["dirs"]` (e.g., `misc/test.md`) $\rightarrow$ assert exit 0.

- [ ] **Step 3: Add test for exclusion (filename)**
  Create a file named `README.md` with no frontmatter $\rightarrow$ assert exit 0.

- [ ] **Step 4: Add test for non-governed extension**
  Create a `.txt` file with no frontmatter $\rightarrow$ assert exit 0.

- [ ] **Step 5: Run the full test suite**
  Run: `uv run pytest tools/tests/test_check_frontmatter.py -v`
  Expected: PASS

- [ ] **Step 6: Commit tests**
  ```bash
  git add tools/tests/test_check_frontmatter.py
  git commit -m "test(governance): verify mandatory frontmatter, exclusions, and extension filtering"
  ```
