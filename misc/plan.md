# Refactoring Plan for Quality Assurance Workflow

This plan outlines the refactoring of `.github/workflows/quality.yml` to separate quality checks into independent jobs and improve security/validation logic.

## 1. Architectural Changes
- Split the single `validate_broken_links` job into four specialized jobs:
    - `broken-links`: Logic tests and link validation for `.md` files.
    - `jupytext`: Logic tests for Jupytext synchronization and verification.
    - `api-keys`: Logic tests and secret scanning for all changed files.
    - `json-validation`: Logic tests and syntax validation for `.json` files.
- Each job will independently manage its own checkout, environment setup (uv), and change detection.

## 2. Shared Dependency Handling
- `tools/scripts/paths.py` is a shared module. Any change to this file must trigger logic tests in **all** jobs.

## 3. Job-Specific Logic

### A. Broken Links Job
- **Triggers**: Changes to `check_broken_links.py`, `test_check_broken_links.py`, `paths.py`, or any `**/*.md`.
- **Steps**:
    1. Run logic tests (pytest) if script/tests/paths changed.
    2. Run `check_broken_links.py` on changed `.md` files.

### B. Jupytext Job
- **Triggers**: Changes to `jupytext_sync.py`, `jupytext_verify_pair.py`, `test_jupytext_sync.py`, `test_jupytext_verify_pair.py`, or `paths.py`.
- **Steps**:
    1. Run Jupytext logic tests (pytest).

### C. API Keys Job
- **Triggers**: Changes to `check_api_keys.py`, `test_check_api_keys.py`, `paths.py`, or **any** file change.
- **Steps**:
    1. Run logic tests (pytest) if script/tests/paths changed.
    2. Run `check_api_keys.py` on all changed files **EXCEPT** `tools/tests/test_check_api_keys.py` and `tools/docs/scripts_instructions/check_api_keys_py_script.md`.

### D. JSON Validation Job
- **Triggers**: Changes to `check_json_files.py`, `test_check_json_files.py`, `paths.py`, or any `**/*.json`.
- **Steps**:
    1. Run logic tests (pytest) if script/tests/paths changed.
    2. Run `check_json_files.py` on changed `.json` files.

## 4. Implementation Details
- Use `tj-actions/changed-files` within each job to determine execution paths.
- Use `files_ignore` in `tj-actions/changed-files` for the API key scan to exclude the test fixture file and its documentation.
- **Security**: Ensure test keys in `tools/tests/test_check_api_keys.py` do not trigger GitHub Push Protection (e.g., avoid `xoxb-[digits]-` patterns for Slack).

## 5. Coverage Improvements
- **`check_api_keys.py`**: Add tests for verbose output of skipped keys, empty string entropy, and directory handling in CLI.
    - **Fix**: Updated `test_verbose_skips` and `test_edge_cases` in `test_api_keys.py` and `test_check_api_keys.py` to use test strings that correctly match provider regex patterns (e.g., OpenAI keys must be at least 51 characters).
- **`check_broken_links.py`**: Add tests for relative path resolution, multiple input paths, target outside root in verbose mode, and multi-segment directory exclusions.
    - **Fix**: Updated `test_validate_link_target_outside_root_verbose` in `test_check_broken_links.py` to use `walk_up=True` in `relative_to()` for Python 3.13 compatibility.
    - **Fix**: Changed default value of `--paths` to `None` in `check_broken_links.py` to correctly exercise default path logic.
    - **Fix**: Added `test_run_no_git_root_warning` to cover the warning message when not in a Git repository.
- **`check_json_files.py`**: Add tests for directory handling in CLI and file discovery edge cases.
- **`jupytext_verify_pair.py`**: Add tests for empty file lists and asymmetric staging (pair staged, file not).
- **General**: Use `runpy` to cover `if __name__ == "__main__":` blocks in all scripts.
