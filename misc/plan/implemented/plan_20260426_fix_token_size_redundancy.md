---
title: Fix Token Size Redundancy in Frontmatter Automation
authors:
- name: Qwen Code
date: 2026-04-26
description: Fix a bug where update_token_counts.py leaves redundant top-level token_size fields, causing pre-commit validation failures.
tags: [tooling, bugfix, frontmatter]
options:
  type: plan
  birth: 2026-04-26
  version: 1.0.0
---

# Plan: Fix Token Size Redundancy in Frontmatter Automation

## Context Analysis

### Current State
The repository is transitioning to a governed frontmatter system (ADR-26042). 
- **The Gate**: `tools/scripts/check_frontmatter.py` validates that all frontmatter fields are correct. It requires `token_size` to be an integer.
- **The Fixer**: `tools/scripts/update_token_counts.py` calculates the actual token count and updates the field.
- **The Bug**: Many files contain both a top-level `token_size: ~N` (legacy) and an `options.token_size: N` (governed). The fixer updates the latter but ignores the former. The gate sees the top-level `~N` and triggers a blocking error.

### Target State
`update_token_counts.py` should act as a complete migration tool:
1. Calculate the correct token count.
2. Set/Update `options.token_size`.
3. **Explicitly remove** any top-level `token_size` key to ensure no redundant or malformed metadata remains.

## Implementation Steps

### 1. Tooling Modification
**File**: `tools/scripts/update_token_counts.py`

**Operation**: Modify the YAML update logic to delete the top-level `token_size` key.
- **Logic**: After loading the YAML and before writing it back, check if `token_size` exists in the root dictionary. If so, `pop` it.

### 2. Adversary Testing
**File**: `tools/tests/test_update_token_counts.py`

**Operation**: Add a new test case `test_removes_top_level_token_size`.
- **Scenario**: Provide a file with both top-level `token_size: ~100` and `options.token_size: 50`.
- **Expected Result**: The resulting file contains ONLY `options.token_size` with the correct calculated value.

### 3. Repository Cleanup
**Action**: Run the fixed `update_token_counts.py` on the entire project root.
- **Command**: `uv run tools/scripts/update_token_counts.py .`

### 4. Verification
**Action**: Run the validation gate to ensure all files now pass.
- **Command**: `uv run tools/scripts/check_frontmatter.py .`

## Cross-Reference Map

| File | Change | Rationale |
| :--- | :--- | :--- |
| `tools/scripts/update_token_counts.py` | Add `pop('token_size', None)` to root YAML | Eliminate redundancy and fix validation errors |
| `tools/tests/test_update_token_counts.py` | Add redundancy removal test | Prevent regression of the "dual token_size" bug |

## Expected Output

1. `pytest tools/tests/test_update_token_counts.py` $\rightarrow$ **PASS**
2. `uv run tools/scripts/check_frontmatter.py .` $\rightarrow$ **Exit 0** (No more `token_size must be an integer` errors)
