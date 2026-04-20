# Plan: State-Based Sync for External Repositories

**Date:** 2026-04-19
**Status:** Proposed
**Slug:** external-repos-sync

## 1. Full Context & Analysis

### Current State
The project uses `tools/scripts/manage_external_repos.py` to handle external research repositories. Currently, it operates as a set of imperative CLI utilities:
- `setup`: Clones a repo into a registered directory.
- `register`: Adds a directory to `.vadocs/validation/external-repos.conf.json`.
- `update`: Pulls latest changes.
- `relocate`: Moves a directory and updates consumer files (`.gitignore`, `myst.yml`).

The "State" is split across three locations:
1. **Registry:** `.vadocs/validation/external-repos.conf.json` (What is excluded).
2. **Filesystem:** Actual folders in `ai_agents/research/`.
3. **Memory:** The user knows which repos *should* be there.

### Problem Statement
There is no Single Source of Truth (SSoT) for the *intended* set of repositories. Adding new repos requires multiple manual CLI calls. Moving repositories or pruning old ones is manual and error-prone, leading to broken symlinks or stale `.gitignore` entries.

### Proposed Solution
Implement a **State-Based Sync** system. The user defines the desired state in a manifest file, and the script reconciles the actual state to match it.

---

## 2. Technical Specification

### 2.1 The Manifest (SSoT)
**File Path:** `.vadocs/inventory/manage_external_repos.json`
**Structure:**
```json
{
  "directories": {
    "rel/path/to/dir": {
      "description": "Dir description",
      "repos": {
        "repo_name": {
          "url": "https://github.com/... ",
          "description": "Repo description"
        }
      }
    }
  }
}
```

### 2.2 Reconciliation Workflow

#### Phase 1: Discovery & Delta Calculation
The script will map:
- `Desired`: Entries in `manage_external_repos.json`.
- `Registered`: Entries in `external-repos.conf.json`.
- `Actual`: Directories existing on disk in the registered paths.

**Deltas calculated:**
- **Orphans:** Folder on disk $\rightarrow$ Not in Manifest.
- **Ghost Dirs:** Registered in config $\rightarrow$ Not in Manifest.
- **Missing:** In Manifest $\rightarrow$ Not on disk.
- **Relocated:** In Manifest path A $\rightarrow$ On disk path B (detected via URL match).

#### Phase 2: Interactive Guard (Step 0)
Before any modifications, the script presents the delta and asks for resolution:

1. **For Orphans:**
   - `Remove`: Delete the directory.
   - `Move`: If the orphan's URL matches a "Missing" repo in the manifest, move it to the desired path.
   - `Ignore`: Leave as is.
   - `Cancel`: Abort script.

2. **For Ghost Dirs:**
   - `Unregister`: Remove from registry and consumers.
   - `Keep`: Leave in registry.
   - `Cancel`: Abort script.

#### Phase 3: Execution
Once resolutions are decided:
1. **Relocate** directories/repos to match manifest paths.
2. **Delete** approved orphans.
3. **Register** missing directories via `register_command()`.
4. **Clone** missing repos via `setup_command()`.
5. **Update** remote URLs if they differ from the manifest.

#### Phase 4: Optional Update
If `--update` is passed, the script runs `git pull --rebase` on all repos defined in the manifest.

---

## 3. Implementation Steps

### Step 1: Infrastructure Setup
- Create `.vadocs/inventory/` directory.
- Create the initial `manage_external_repos.json` with current `ai_skills_plugins` data.

### Step 2: Enhance `manage_external_repos.py`
- **Add `sync` command** to `argparse`.
- **Add `--update` flag** to the `sync` command.
- **Implement `SyncManager` class**:
    - `load_manifest()`: Reads `.vadocs/inventory/manage_external_repos.json`.
    - `calculate_delta()`: Compares manifest, registry, and disk.
    - `interactive_resolve()`: Handles the user prompts for Orphans and Ghost Dirs.
    - `apply_reconciliation()`: Executes the changes using existing primitives (`register_command`, `setup_command`, etc.).
    - `perform_updates()`: Logic for `git pull --rebase`.

### Step 3: Refactor existing primitives
- Ensure `register_command` and `setup_command` handle "already exists" cases gracefully (returning 0 or a specific "already present" code) to support idempotency.

---

## 4. Verification Plan

### Test Scenarios
1. **Clean Sync:** Run `sync` on a system that already matches the manifest $\rightarrow$ Expect "System up to date".
2. **New Repo:** Add a repo to manifest $\rightarrow$ Run `sync` $\rightarrow$ Expect clone and registration.
3. **Relocation:** Change a directory path in manifest $\rightarrow$ Run `sync` $\rightarrow$ Expect `relocate_command` to move the dir and update `.gitignore`.
4. **Orphan Handling:** Create a dummy folder in a research dir $\rightarrow$ Run `sync` $\rightarrow$ Expect prompt to remove/ignore.
5. **Ghost Handling:** Manually add a dir to `external-repos.conf.json` $\rightarrow$ Run `sync` $\rightarrow$ Expect prompt to unregister.
6. **Update Flag:** Run `sync --update` $\rightarrow$ Expect `git pull` for all managed repos.

### Verification Commands
- `uv run tools/scripts/manage_external_repos.py sync`
- `uv run tools/scripts/manage_external_repos.py sync --update`
- `cat .vadocs/validation/external-repos.conf.json`
- `git status` (to verify `.gitignore` updates)
