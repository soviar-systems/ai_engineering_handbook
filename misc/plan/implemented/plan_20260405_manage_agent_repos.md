# Plan: Agent Source Code Repository Manager

**Date:** 2026-04-05
**Status:** Approved & In Progress

## Overview
Create a Python script (`tools/scripts/manage_agent_repos.py`) with two commands:
1. **`setup`** - Configure a new agent repository (clone + update myst.yml/.gitignore/paths.py)
2. **`update`** - Pull updates for all configured repositories (pre-session refresh)

## Implementation Details

### Script: `tools/scripts/manage_agent_repos.py`

#### Command 1: `setup`
- Input: Repository URL, optional branch name
- Actions:
  1. Clone repo into `ai_system/6_agents/agents_source_code/<repo-name>/`
  2. Add exclusion path to `myst.yml` (under `site.exclude`)
  3. Verify `.gitignore` already has the parent directory (already exists)
  4. Update `paths.py` VALIDATION_EXCLUDE_DIRS if needed
  5. Output: Success message with repo location

#### Command 2: `update`
- Input: Optional `--parallel` flag, optional specific repo names
- Actions:
  1. Discover all git repos in `agents_source_code/`
  2. For each repo: `git pull --rebase` (or `git pull` if no local changes)
  3. Report status (updated, already current, errors)
  4. Exit code 0 if all succeed, 1 if any fail

#### Command 3: `list` (bonus utility)
- List all configured repos with their current status (branch, last commit date)

### Architecture (following project conventions)
- **Data classes**: `AgentRepo` (name, path, url, branch, status)
- **Configuration**: Constants for `AGENTS_SOURCE_CODE_DIR = Path("ai_system/6_agents/agents_source_code")`
- **Main function**: CLI dispatcher at top
- **Validation functions**: Check if repo exists, if directory is git repo, etc.
- **Discovery functions**: Find all git repos in agents_source_code
- **Helper functions**: Git operations, YAML editing, file I/O
- Structure: data classes → configuration → main → validation → discovery → helpers → `if __name__`

### Key Design Decisions
1. **YAML editing**: Use `ruamel.yaml` (if available) or careful string manipulation to preserve myst.yml formatting
2. **Git operations**: Use `subprocess.run()` with proper error handling
3. **Parallel updates**: Use `concurrent.futures.ThreadPoolExecutor` for `--parallel` flag
4. **Idempotent**: Running `setup` on existing repo updates remote instead of failing
5. **Path handling**: Use `pathlib.Path` exclusively (per conventions)
6. **Validation exclusion**: The parent dir is already in `paths.py` VALIDATION_EXCLUDE_DIRS, so individual repos don't need adding

### Files to Create/Modify
1. **Create**: `tools/scripts/manage_agent_repos.py` (new script)
2. **Create**: `tools/tests/test_manage_agent_repos.py` (test suite)
3. **No modifications needed**: `.gitignore` (already has exclusion), `myst.yml` (will be modified by script at runtime, not in repo)

### Usage Examples
```bash
# Setup a new agent repo
uv run tools/scripts/manage_agent_repos.py setup https://github.com/langchain-ai/langgraph

# Update all repos before starting work
uv run tools/scripts/manage_agent_repos.py update

# Update specific repos only
uv run tools/scripts/manage_agent_repos.py update langgraph autogen

# Update in parallel for speed
uv run tools/scripts/manage_agent_repos.py update --parallel

# List all repos and status
uv run tools/scripts/manage_agent_repos.py list
```
