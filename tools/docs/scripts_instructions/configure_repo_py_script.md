---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.0
kernelspec:
  name: bash
  display_name: Bash
  language: bash
---

---
title: "Instruction on configure_repo.py script"
author: rudakow.wadim@gmail.com
date: 2026-03-01
options:
  version: 0.3.0
  birth: 2026-01-27
---

# Instruction on configure_repo.py script

+++

## **1. Architectural Overview: The SVA Principle**

+++

This [script](/tools/scripts/configure_repo.py) automates repository setup for development by running dependency installation, configuring git hooks, setting permissions, and creating convenience symlinks.

It replaces the legacy `configure_repo.sh` bash script with a Python implementation that provides better error handling, dry-run support, and testability.

It adheres to the **Smallest Viable Architecture (SVA)** principle.

:::{hint} **SVA = right tool for the job**
:class: dropdown
SVA isn't about minimal *code* — it's about **minimal *cognitive and operational overhead***.

* **Zero External Dependencies**: Uses only the Python standard library (`argparse`, `subprocess`, `shutil`, `pathlib`), ensuring it runs on any system with Python installed.
* **Idempotent Operations**: Running the script multiple times produces the same result - safe to re-run after partial failures.
* **Dry-run Support**: Preview all operations before execution with `--dry-run` flag.
:::

+++

## **2. Key Capabilities & Logic**

+++

### A. Setup Operations

The script performs five sequential operations:

| Operation | Description |
|-----------|-------------|
| **UV Sync** | Runs `uv sync` to install/update dependencies from lockfile |
| **Pre-commit Install** | Runs `uv run pre-commit install` to configure pre-commit hooks |
| **Commit-msg Hook** | Runs `uv run pre-commit install --hook-type commit-msg` to enable commit message validation |
| **Post-commit Hook** | Runs `uv run pre-commit install --hook-type post-commit` to enable changelog preview |
| **Aider Config** | Copies `tools/configs/aider.conf.yml` to `.aider.conf.yml` if target missing |
| **Script Permissions** | Makes all `.sh` and `.py` files executable recursively |
| **Symlinks** | Creates symlinks in `~/bin` for all files in `tools/scripts/` |

+++

### B. Skip Flags

Operations can be selectively skipped:

| Flag | Effect |
|------|--------|
| `--skip-uv-sync` | Skips both `uv sync` and `pre-commit install` |
| `--skip-symlinks` | Skips symlink creation in `~/bin` |

+++

## **3. Technical Architecture**

+++

The script is organized into specialized classes to maintain clarity:

| Class | Responsibility |
|-------|----------------|
| `UvSyncRunner` | Execute `uv sync`, `pre-commit install`, `commit-msg` and `post-commit` hook installs |
| `AiderConfigCopier` | Copy aider configuration file with existence checks |
| `ScriptPermissions` | Find and make `.sh`/`.py` files executable |
| `SymlinkCreator` | Create symlinks in target bin directory |
| `Reporter` | Output formatting and exit code handling |
| `ConfigureRepoCLI` | Argument parsing and main orchestration |

+++

## **4. Operational Guide**

+++

### Configuration Reference

+++

* **Primary Script**: `tools/scripts/configure_repo.py`
* **Legacy Script**: `tools/scripts/configure_repo.sh` (deprecated)
* **Aider Source**: `tools/configs/aider.conf.yml`
* **Aider Target**: `.aider.conf.yml` (repository root)

+++

### Command Line Interface

+++

```bash
configure_repo.py [--skip-uv-sync] [--skip-symlinks] [--verbose] [--dry-run] [--bin-dir DIR]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `--skip-uv-sync` | Skip dependency and hook installation | `False` |
| `--skip-symlinks` | Skip symlink creation | `False` |
| `--verbose` | Show detailed progress | `False` |
| `--dry-run` | Preview operations without execution | `False` |
| `--bin-dir` | Target directory for symlinks | `~/bin` |

**Exit Codes:**
- `0` = Setup completed successfully
- `1` = Setup failed (e.g., uv sync error)

+++

### Manual Execution Commands

+++

Run these from the repository root using `uv` for consistent environment resolution:

| Task | Command |
|------|---------|
| **Full Setup** | `uv run tools/scripts/configure_repo.py` |
| **With Verbose Output** | `uv run tools/scripts/configure_repo.py --verbose` |
| **Dry Run Preview** | `uv run tools/scripts/configure_repo.py --dry-run --verbose` |
| **Skip UV Sync** | `uv run tools/scripts/configure_repo.py --skip-uv-sync` |
| **Custom Bin Dir** | `uv run tools/scripts/configure_repo.py --bin-dir=/usr/local/bin` |

+++

### Examples

```{code-cell}
cd ../../../
```

#### Preview what would be done:

```bash
uv run tools/scripts/configure_repo.py --dry-run --verbose
```

```{code-cell}
env -u VIRTUAL_ENV uv run tools/scripts/configure_repo.py --dry-run
```

#### Run setup skipping symlinks:

+++

```bash
uv run tools/scripts/configure_repo.py --skip-symlinks --skip-uv-sync --verbose
```

+++

## **5. Test Suite Documentation**

+++

The script is accompanied by a comprehensive test suite (`test_configure_repo.py`) that ensures reliability across different patterns and edge cases.

+++

### Test Classes and Coverage

| Test Class | Purpose |
|------------|---------|
| `TestUvSyncRunner` | Command execution, failure handling, dry-run mode |
| `TestAiderConfigCopier` | Source/target existence checks, copy operations |
| `TestScriptPermissions` | Permission changes, file type filtering, nested dirs |
| `TestSymlinkCreator` | Symlink creation/update, directory handling |
| `TestReporter` | Exit codes, verbose/quiet output |
| `TestConfigureRepoCLI` | Integration tests for CLI flags and full runs |

+++

### Key Test Scenarios

- **UvSyncRunner**: Command success/failure, dry-run skips execution
- **AiderConfigCopier**: Source exists/missing, target exists/missing, dry-run
- **ScriptPermissions**: .py/.sh files made executable, directories skipped
- **SymlinkCreator**: New symlinks, existing symlinks updated, missing bin dir created
- **ConfigureRepoCLI**: All flag combinations, full setup integration

+++

### Running the Tests

To run the full suite, execute from the repository root:

```bash
$ uv run pytest tools/tests/test_configure_repo.py
```

```{code-cell}
env -u VIRTUAL_ENV uv run pytest tools/tests/test_configure_repo.py -q
```

```{code-cell}
env -u VIRTUAL_ENV uv run pytest tools/tests/test_configure_repo.py --cov=tools.scripts.configure_repo --cov-report=term-missing -q
```
