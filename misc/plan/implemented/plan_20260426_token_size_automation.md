# Token Size Automation Implementation Plan (Implemented)

**Goal:** Automate the calculation of `token_size` in YAML frontmatter to eliminate manual entry and pre-commit hook failures using a Fixer/Gate pattern.

## 1. Architecture: Fixer/Gate Pattern

To ensure a predictable development workflow, the solution separates validation from modification.

### The Gate (`tools/scripts/check_frontmatter.py`)
- **Role:** Quality Assurance / Blocking Validator.
- **Behavior:** Read-only. It scans files and compares the declared `token_size` against the actual count using `tiktoken`.
- **Enforcement:** Integrated into the `pre-commit` hook and GitHub Actions.
- **Recovery Loop:** If an inaccurate `token_size` is detected, the commit is blocked, and the user is presented with a 3-step recovery guide:
  1. Run the fixer: `uv run tools/scripts/update_token_counts.py`
  2. Stage changes: `git add <file>`
  3. Commit again.

### The Fixer (`tools/scripts/update_token_counts.py`)
- **Role:** Developer Utility / Automation Tool.
- **Behavior:** Read-Write. It calculates actual token counts and updates the `options.token_size` field.
- **Usage:** Run manually by developers to synchronize metadata.

## 2. Technical Specifications
- **Tokenizer:** `tiktoken` using `cl100k_base` encoding (OpenAI standard).
- **Validation Margin:** $\pm 10$ tokens allowed to account for minor tokenizer differences/whitespace.
- **Robustness:** Implemented safe integer casting to handle malformed values (e.g., `~800`) as `invalid_format` errors instead of crashing.
- **Documentation:** Added explicit notes in `check_frontmatter.py` docstring confirming its read-only nature.

---

## Implemented Tasks

### Task 1: Implement `update_token_counts.py` and Tests
- [x] Created `tools/scripts/update_token_counts.py` to handle discovery of governed files and token updates.
- [x] Created `tools/tests/test_update_token_counts.py` to verify:
    - Basic token calculation and update.
    - Handling of missing `token_size` fields.
    - Preservation of non-frontmatter content.
- [x] Verified that the script maintains YAML readability using `default_flow_style=False`.

### Task 2: Enhance `check_frontmatter.py` Validation
- [x] Integrated `tiktoken` for real-time accuracy checks.
- [x] Implemented `token_size` validation in `_validate_field_value` with a 10-token margin.
- [x] Added robust integer casting to prevent crashes on non-numeric values.
- [x] Refined error messages to include the full 3-step recovery loop.
- [x] Updated `tools/tests/test_check_frontmatter.py` to cover accuracy, margins, and malformed values.

### Task 3: Repository Synchronization
- [x] Ran `update_token_counts.py` across the entire repository to synchronize all governed files.
- [x] Verified that `check_frontmatter.py` passes on the full repository.

### Task 4: CI/CD Integration & Adversary Testing
- [x] Added a dedicated `update-token-counts` job to `.github/workflows/quality.yml` to run fixer tests on any logic changes.
- [x] Performed "Adversary Testing" by creating a file with an intentionally wrong `token_size` and verifying that the pre-commit hook successfully blocks the commit.

---

## Final Verification
- **Fixer Logic:** Verified via `pytest tools/tests/test_update_token_counts.py`.
- **Gate Logic:** Verified via `pytest tools/tests/test_check_frontmatter.py` and adversary test file.
- **Developer UX:** Verified that the failed hook provides clear, actionable instructions.
- **Pipeline:** Verified that the CI workflow now guards the automation logic.
