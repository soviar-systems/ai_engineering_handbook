# Plan: Refactor paths.py Exclusion Variables

## Problem Statement

The `tools/scripts/paths.py` module has grown organically and now contains exclusion patterns used by multiple validation scripts:
- `check_broken_links.py`
- `jupytext_sync_verify.py`
- `check_api_keys.py`
- `check_adr.py` (new)

The variable naming is misleading:
- `BROKEN_LINKS_EXCLUDE_DIRS` is now reused by `check_adr.py` for term reference scanning
- `JUPYTEXT_EXCLUDE_DIRS` is just an alias to `BROKEN_LINKS_EXCLUDE_DIRS`
- The names suggest script-specific usage but they're actually shared

## Proposed Solution

Rename to reflect shared/general purpose:

```python
# Before
BROKEN_LINKS_EXCLUDE_DIRS = {...}
JUPYTEXT_EXCLUDE_DIRS = BROKEN_LINKS_EXCLUDE_DIRS

# After
VALIDATION_EXCLUDE_DIRS = {
    ".git",
    ".ipynb_checkpoints",
    ".pytest_cache",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "build",
    "_build",
    "dist",
    "misc",
}

# Backward compatibility aliases (deprecate in future)
BROKEN_LINKS_EXCLUDE_DIRS = VALIDATION_EXCLUDE_DIRS
JUPYTEXT_EXCLUDE_DIRS = VALIDATION_EXCLUDE_DIRS
```

## Files to Update

1. `tools/scripts/paths.py` - Rename variables, add aliases for backward compat
2. `tools/scripts/check_broken_links.py` - Update import
3. `tools/scripts/jupytext_sync_verify.py` - Update import
4. `tools/scripts/check_adr.py` - Update import
5. `tools/tests/test_*.py` - Update any tests that reference these variables

## Acceptance Criteria

- [ ] All validation scripts use `VALIDATION_EXCLUDE_DIRS`
- [ ] Old variable names work as aliases (no breaking changes)
- [ ] Tests pass
- [ ] Add deprecation warning for old names (optional)

## Priority

Low - Current code works, this is just naming clarity for maintainability.
