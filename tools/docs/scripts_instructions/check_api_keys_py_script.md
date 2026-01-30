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

# Instruction on check_api_keys.py script

+++

---

Owner: Vadim Rudakov, rudakow.wadim@gmail.com  
Version: 0.1.0
Birth: 2026-01-21
Last Modified: 2026-01-21

---

+++

## **1. Architectural Overview: The SVA Principle**

+++

This [script](/tools/scripts/check_api_keys.py) detects real API keys in files using regex patterns while filtering out placeholders and low-entropy strings to minimize false positives.

This tool is designed to serve as a security gate in CI/CD, preventing accidental commits of sensitive credentials.

It adheres to the **Smallest Viable Architecture (SVA)** principle.

:::{hint} **SVA = right tool for the job**
SVA isn't about minimal *code* — it's about **minimal *cognitive and operational overhead***.

* **Zero External Dependencies**: Uses only the Python standard library (`argparse`, `re`, `sys`, `pathlib`) plus internal `paths.py` configuration, ensuring it runs on any system with Python installed.
* **Security-First Design**: No file or directory exclusions by file type—checks all files passed to it.
* **Dual Validation**: Combines regex pattern matching with entropy analysis to reduce false positives.
:::

+++

## **2. Key Capabilities & Logic**

+++

### A. Provider-Specific Pattern Detection

The script identifies API keys from major providers using tailored regex patterns:

| Provider | Pattern | Min Length |
|----------|---------|------------|
| OpenAI | `sk-[a-zA-Z0-9]{48,}` | 51 |
| OpenAI Project | `sk-proj-[a-zA-Z0-9_-]{48,}` | 56 |
| GROQ | `gsk_[a-zA-Z0-9]{48,}` | 52 |
| Google | `AIza[a-zA-Z0-9_-]{35}` | 39 |
| GitHub | `gh[pousr]_[a-zA-Z0-9]{36,}` | 40 |
| Slack | `xox[bpras]-[a-zA-Z0-9-]+` | 32 |
| AWS | `AKIA[A-Z0-9]{16}` | 20 |

+++

### B. False Positive Prevention

The script uses multiple layers to filter out non-real keys:

**Placeholder Indicators** (configured in `paths.py`):
- Bracket notation: `[`, `<`, `${`, `{{`
- Common placeholder words: `example`, `placeholder`, `your_`, `test_`, `fake_`

**Low Entropy Detection**:
- Keys where >80% of characters are the same are rejected (e.g., `sk-xxxxxxxx...`)

**Sequential Pattern Detection**:
- Very long sequential patterns (16+ characters) are rejected
- Short sequences like `123456` or `abcdef` are allowed as they can appear in real keys

+++

## **3. Technical Architecture**

+++

The script is organized into specialized classes to maintain clarity:

| Class | Responsibility |
|-------|----------------|
| `ApiKeyDetector` | Pattern matching using regex; orchestrates detection for a file |
| `ApiKeyValidator` | Filters placeholders, low-entropy, and sequential patterns |
| `FileFinder` | Recursive file discovery for directory scan mode |
| `Reporter` | Output formatting and exit code handling |
| `ApiKeyCheckerCLI` | Argument parsing and main orchestration |
| `ApiKeyMatch` | NamedTuple storing detection results (key, provider, file, line) |

+++

## **4. Operational Guide**

+++

### Configuration Reference

+++

* **Primary Script**: `tools/scripts/check_api_keys.py`
* **Placeholder Config**: Managed via `tools/scripts/paths.py` (`API_KEYS_PLACEHOLDER_INDICATORS`)
* **Pre-commit Config**: `.pre-commit-config.yaml`
* **CI Config**: `.github/workflows/quality.yml`

+++

### Command Line Interface

+++

```bash
check_api_keys.py [files...] [--verbose]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `files` | One or more files to scan | Current directory (recursive) |
| `--verbose` | Shows detailed logs of skipped files and results | `False` |

**Exit Codes:**
- `0` = No API keys found
- `1` = API keys detected

+++

### Manual Execution Commands

+++

Run these from the repository root using `uv` for consistent environment resolution:

| Task | Command |
|------|---------|
| **Check Specific Files** | `uv run tools/scripts/check_api_keys.py file1.md file2.py` |
| **Full Directory Scan** | `uv run tools/scripts/check_api_keys.py --verbose` |
| **Pre-commit Mode** | `uv run tools/scripts/check_api_keys.py path/to/staged/file.py` |

+++

### Examples

```{code-cell}
cd ../../../
ls
```

1. Check specific files:

```{code-cell}
env -u VIRTUAL_ENV uv run tools/scripts/check_api_keys.py tools/docs/scripts_instructions/check_api_keys_py_script.md
```

2. Check with verbose output:

```{code-cell}
env -u VIRTUAL_ENV uv run tools/scripts/check_api_keys.py --verbose RELEASE_NOTES.md
```

## **5. Validation Layers**

+++

### Layer 1: Local Pre-commit Hook

+++

The first line of defense runs automatically during the `git commit` process to prevent credentials from entering version control.

**Pre-commit Configuration:**
```yaml
- id: check-api-keys
  name: Check for API keys
  entry: uv run --active tools/scripts/check_api_keys.py
  language: system
  pass_filenames: true
  exclude: ^(tools/tests/test_check_api_keys\.py|tools/docs/scripts_instructions/check_api_keys_py_script\.md)$
  stages: [pre-commit]
```

* **Scope**: Validates all staged files (no file type restrictions)
* **`pass_filenames: true`**: Receives file list from git, enabling targeted checking
* **Exclusion**: `test_check_api_keys.py` and this documentation file are excluded (see section 6 for rationale)
* **Runtime Exclusion**: The script also has built-in exclusion via `API_KEYS_EXCLUDE_FILES` in `paths.py` for cases when files are passed directly (e.g., CI)

+++

### Layer 2: GitHub Action (Continuous Integration)

+++

The CI pipeline in `quality.yml` runs the test suite when relevant files change:

```yaml
- name: Get changed check_api_keys files
  id: changed-check-api-keys
  uses: tj-actions/changed-files@v45
  with:
    files: |
      tools/scripts/check_api_keys.py
      tools/tests/test_check_api_keys.py

- name: Run API Key Check Tests
  if: steps.changed-check-api-keys.outputs.any_changed == 'true' || steps.changed-paths.outputs.any_changed == 'true'
  run: uv run pytest tools/tests/test_check_api_keys.py
```

*Note: `paths.py` is detected separately because it's a shared dependency across multiple test suites.*

+++

#### Why `test_check_api_keys.py` and Documentation are Excluded from the `check-api-keys` Hook

+++

The test file and its documentation contain **intentional API key patterns** that look real to verify detection works correctly or to provide examples. These are test fixtures or documentation examples, not secrets.

**Example from test file:**
```python
# Real-looking keys SHOULD be detected
("sk-<high_entropy_48_char_string>", True),
```

**The test suite is validated separately via:**
- **Pre-commit**: `test-check-api-keys` hook runs pytest when relevant files change
- **CI**: GitHub Action runs pytest when `check_api_keys.py`, `test_check_api_keys.py`, or `paths.py` change

:::{note}
This is standard practice for security scanning tools—the scanner's own test suite must contain patterns it's designed to detect. Excluding the test file from scanning while ensuring the tests themselves pass provides comprehensive coverage without false positives.
:::

+++

### Layer 3: Logic Tests Pre-commit Hook

+++

A meta-check ensures the detection logic remains sound:

```yaml
- id: test-check-api-keys
  name: Test Check API Keys script
  entry: uv run --active pytest tools/tests/test_check_api_keys.py
  language: python
  files: ^tools/(scripts/check_api_keys\.py|scripts/paths\.py|tests/test_check_api_keys\.py)$
  pass_filenames: false
```

This triggers whenever the script, its tests, or shared configuration change.

+++

## **6. Test Suite Documentation**

+++

The script is accompanied by a comprehensive test suite (`test_check_api_keys.py`) that ensures reliability across different patterns and edge cases.

+++

### Test Classes and Coverage

| Test Class | Purpose |
|------------|---------|
| `TestApiKeyDetector` | Pattern matching for all providers, binary file handling, multiline detection |
| `TestApiKeyValidator` | Placeholder filtering, entropy checks, sequential pattern detection |
| `TestFileFinder` | Recursive file discovery, directory exclusion |
| `TestReporter` | Exit codes, output formatting, verbose mode |
| `TestApiKeyCheckerCLI` | Integration tests for CLI modes and arguments |

+++

### Key Test Scenarios

- **Provider Patterns**: Each provider's regex is tested with valid keys
- **Placeholder Detection**: Brackets, env vars, Jinja templates, common placeholder words
- **Low Entropy**: Keys with >80% same character are rejected
- **Sequential Patterns**: 16+ character sequences rejected, shorter allowed
- **Binary Files**: Gracefully skipped with verbose output
- **Missing Files**: Warning issued, non-blocking
- **Multiline Files**: Correct line number reporting

+++

### Running the Tests

To run the full suite, execute from the repository root:

```{code-cell}
env -u VIRTUAL_ENV uv run pytest tools/tests/test_check_api_keys.py -q
```

```{code-cell}
env -u VIRTUAL_ENV uv run pytest tools/tests/test_check_api_keys.py --cov=. --cov-report=term-missing -q
```
