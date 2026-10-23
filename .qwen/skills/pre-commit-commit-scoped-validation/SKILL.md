---
name: pre-commit-commit-scoped-validation
description: Implementing commit-scoped validation in pre-commit hooks to avoid blocking noise from unrelated files.
source: auto-skill
extracted_at: '2026-05-30T14:00:00.000Z'
---

# Pre-commit Commit-Scoped Validation

When implementing validation scripts for `pre-commit` hooks, a common pitfall is performing a global scan of the repository (e.g., using `glob` on a directory) instead of validating only the files being changed in the current commit. This leads to "blocking noise," where unrelated existing errors prevent a developer from committing a small, correct change.

## The Principle: Commit-Scoped Validation
A hook should only validate files passed to it by the `pre-commit` framework. If a file is not part of the current commit, its existing state should not block the commit process.

### Refinement: Dual-Mode Validation (Strict vs Warning)
To avoid the "blind spot" where legacy technical debt is completely ignored and forgotten, implement **Dual-Mode Validation**. Instead of silently skipping non-staged files, the script validates everything but differentiates the impact:

- **Strict Mode (Blocking)**: Applied to staged files and "Blueprints". Any violation results in `Exit 1`.
- **Audit Mode (Warning)**: Applied to all other files in the repository. Violations are reported as warnings in the logs but result in `Exit 0`.

This ensures that new code is 100% compliant while maintaining a visible "shame list" of legacy errors to be cleaned up incrementally.


## Implementation Strategy

### 1. Pre-commit Configuration
In `.pre-commit-config.yaml`, ensure the hook is configured to target only the current commit. There are two primary patterns:

#### Pattern A: Pre-commit Driven (Recommended)
The framework sends the list of changed filenames as positional arguments.

```yaml
- repo: local
  hooks:
    - id: check-script-suite
      name: Check Script Suite
      entry: uv run tools/scripts/check_script_suite.py
      language: python
      pass_filenames: true  # CRITICAL: Sends changed files as positional arguments
      files: ^tools/scripts/
```

#### Pattern B: Script Driven (Internal Git Check)
The script handles its own discovery of staged files (e.g., via `git diff --cached`). Use this when the script needs full context of the index or performs complex cross-file validation that `pass_filenames` cannot easily support.

```yaml
- repo: local
  hooks:
    - id: check-adr-index
      name: Check ADR Index
      entry: uv run tools/scripts/check_adr.py --fix --check-staged # Activate scoped mode via flag
      language: python
      pass_filenames: false # Script manages its own file discovery
      files: ^architecture/adr/
```

### 2. Script Logic Update
Depending on the chosen pattern, the script must be updated accordingly.

**Pattern A (Scoped via `sys.argv`):**
```python
import sys
from pathlib import Path

def main():
    # 1. Extract files passed by pre-commit as the "blocking" set
    staged_files = {Path(f).resolve() for f in sys.argv[1:]}

    # 2. Resolve the full set of files to validate (e.g., global scan for audit)
    # If staged_files is empty, this might be a manual run.
    input_paths = [Path(p) for p in sys.argv[1:]] if sys.argv[1:] else [REPO_ROOT]
    files_to_validate = [f.resolve() for f in scan_paths(input_paths, REPO_ROOT)]
    
    blocking_errors = []
    warning_errors = []

    for file in files_to_validate:
        errors = validate_file(file)
        if errors:
            if file in staged_files:
                blocking_errors.extend(errors)
            else:
                warning_errors.extend(errors)
    
    # Report all, but only block on staged violations
    report_errors(blocking_errors, warning_errors)
    return 1 if blocking_errors else 0
```

### 2. Script Logic Update
Depending on the chosen pattern, the script must be updated accordingly.

**Pattern A (Scoped via `sys.argv`):**
```python
import sys
from pathlib import Path

def main():
    # 1. Extract files passed by pre-commit as the "blocking" set
    staged_files = {Path(f).resolve() for f in sys.argv[1:]}

    # 2. Resolve the full set of files to validate (e.g., global scan for audit)
    # If staged_files is empty, this might be a manual run.
    input_paths = [Path(p) for p in sys.argv[1:]] if sys.argv[1:] else [REPO_ROOT]
    files_to_validate = [f.resolve() for f in scan_paths(input_paths, REPO_ROOT)]

    blocking_errors = []
    warning_errors = []

    for file in files_to_validate:
        errors = validate_file(file)
        if errors:
            if file in staged_files:
                blocking_errors.extend(errors)
            else:
                warning_errors.extend(errors)

    # Report all, but only block on staged violations
    report_errors(blocking_errors, warning_errors)
    return 1 if blocking_errors else 0
```

**Pattern B (Scoped via Internal Git Query):**
The script should implement a flag (e.g., `--check-staged`) that filters the target list using `git` commands before proceeding with validation.


#### Reporting and UX: Distinguishing Debt from Blockers
To prevent developers (and AI agents) from becoming overwhelmed by legacy warnings, use clear visual prefixes in the logs.

- **`[BLOCKING]`**: Indicates a violation in a staged file that must be resolved before the commit can proceed.
- **`[LEGACY]`**: Indicates existing technical debt in the repository. These are reported for visibility but do not block the commit.

This labeling allows for easy filtering (e.g., `grep "[BLOCKING]"` ) to identify the immediate action items.


#### Operational Note: Handling Paired Files (e.g., Jupytext)
In projects where files exist in pairs (like `.md` and `.ipynb` via Jupytext), a validation error in one file typically requires staging *both* files to maintain synchronization.

**Correct Fix Workflow**:
1.  Identify the error in `File.md`.
2.  Apply the fix to `File.md`.
3.  Sync to `File.ipynb` (e.g., `uv run jupytext --sync`).
4.  Stage **both**: `git add File.md File.ipynb`.

Failure to stage the pair will lead to "sync errors" in the CI/CD pipeline, even if the structural validation passes.

#### The "Blueprint Exception": Ensuring Global Invariants
In advanced governance systems, some files are designated as "Blueprints" (gold-standard templates). These files MUST be validated on every run, regardless of whether they were staged in the current commit. This prevents "blueprint drift" where the SSoT config changes but the templates are not updated.


**Implementation for Blueprint Exception:**
```python
# Example integration into the validation loop
blueprints = HUB_CONFIG.get("blueprints", [])
for bp_rel_path in blueprints:
    bp_path = REPO_ROOT / bp_rel_path
    if bp_path.exists() and bp_path not in files_to_validate:
        files_to_validate.append(bp_path)
```



## Verification via TDD (Red $\rightarrow$ Green $\rightarrow$ Refactor)

To ensure the fix works without introducing regressions:

1.  **Red Phase**: Create two test cases:
    -   **Staged Violation**: Mock the staged file list with a "broken" file. Assert that `main()` returns `1`.
    -   **Legacy Violation**: Mock the staged file list with a "correct" file, while a "broken" file exists in the directory. Assert that `main()` returns `0` but the broken file is still present in `caplog`.
2.  **Green Phase**: Update the script to implement the Dual-Mode logic.
3.  **Refactor Phase**: Ensure that the "global scan" fallback still works for manual execution.


### Technical Note: Verifying Logs in Pytest
When verifying that specific files are (or are not) flagged in the output, avoid using `contextlib.redirect_stdout` or `redirect_stderr`. If the script uses the Python `logging` module, `pytest` intercepts these logs internally.

**Correct Approach**: Use the `caplog` fixture to inspect captured logs.

```python
def test_scoped_validation(frontmatter_env, monkeypatch, caplog):
    # ... setup files ...
    
    # Run the script
    exit_code = _module.main(argv=["--check-staged"])
    
    # Assert using caplog.text instead of redirected streams
    assert "staged_invalid.md" in caplog.text
    assert "unstaged_invalid.md" not in caplog.text
```

### Technical Note: Path Normalization
When comparing files from the filesystem (`pathlib.Path`) with files from the Git index (`git diff --cached`), always normalize paths to posix strings to avoid OS-specific separator mismatches (e.g., `\` vs `/`).

```python
# Consistent comparison between filesystem and git index
rel_path = file_path.relative_to(REPO_ROOT).as_posix()
if rel_path in staged_files:
    # ... process file ...
```

## Key Benefits
- **Atomic Commits**: Developers can fix one issue at a time without being forced to fix the entire repository.
- **Faster Feedback**: Reducing the number of files checked per commit speeds up the pre-commit pipeline.
- **Reduced Friction**: Eliminates "blocking noise" that leads developers to use `--no-verify` (which should be strictly prohibited).
