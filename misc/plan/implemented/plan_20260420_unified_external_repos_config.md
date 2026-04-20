# Plan: Unify External Repository Configuration SSoT
Date: 2026-04-20
Status: In-Progress

## Problem Statement
Currently, external repository management is split between a Manifest (`.vadocs/inventory/manage_external_repos.json`) for synchronization and a Registry (`.vadocs/validation/external-repos.conf.json`) for validation exclusions. This creates a "split brain" scenario and redundancy.

## Goal
Merge both configurations into a single SSoT manifest in `.vadocs/inventory/manage_external_repos.json`.

## Implementation Steps

### 1. Configuration Merge (Completed)
- Merge `default_consumers` and `managed_by` into a `settings` block in the manifest.
- Merge directory-level registration metadata (`product_type`, `consumers`) into each directory entry in the manifest.
- Delete `.vadocs/validation/external-repos.conf.json`.

### 2. Update `tools/scripts/paths.py` (Completed)
- Replace `_EXTERNAL_REPOS_CONFIG` with `_EXTERNAL_REPOS_MANIFEST`.
- Replace `_VALIDATION_DIR` with `_INVENTORY_DIR` for the manifest path.
- Update `get_external_repo_paths()` to extract keys from the `directories` object instead of iterating over an `entries` list.

### 3. TDD Refactor Cycle
Follow a strict Red $\rightarrow$ Green $\rightarrow$ Refactor workflow:

#### Cycle 1: Register/Unregister (In-Progress)
- Update tests in `tools/tests/test_manage_external_repos.py` to use a temporary Unified Manifest instead of a Registry.
- Verify `register_command` and `unregister_command` modify the manifest correctly.
- Verify `reload_registry()` refreshes `EXTERNAL_REPO_DIRS` from the manifest.

#### Cycle 2: Relocate
- Write tests for `relocate_command` that verify the path change in the manifest.
- Refactor `relocate_command` to operate on the manifest `directories` object.
- Verify consumer files are still updated atomically.

#### Cycle 3: Sync Consumers
- Write tests for `sync_consumers_command` using the Unified Manifest.
- Refactor `sync_consumers_command` to extract paths from the manifest.
- Verify stale entries are removed and missing ones added.

#### Cycle 4: Sync Manager
- Verify the full `sync` reconciliation loop (Discovery $\rightarrow$ Delta $\rightarrow$ Execution) using the new SSoT.
- Ensure `calculate_delta` correctly identifies Missing, Orphans, and Ghost Dirs from the manifest.

### 4. Final Verification
- Run the complete test suite in `tools/tests/test_manage_external_repos.py`.
- Verify that `VALIDATION_EXCLUDE_DIRS` in `tools/scripts/paths.py` remains correct.
