# Plan: Hub-Spoke Ecosystem Development Workflow

## Context

vadocs has been extracted to a dedicated repo. The goal is to migrate all validation functionality from `tools/scripts/` into vadocs, which will provide complete features: CLI, pre-commit hooks, and GH CI.

**Repos:**
- **Hub**: `/home/commi/Yandex.Disk/it_working/projects/ai/ai_engineering_book`
- **Spoke**: `/home/commi/Yandex.Disk/it_working/projects/ai/vadocs`

## Migration Strategy (Agile)

vadocs will **replace** tools/scripts validators, NOT import into them.

**Migration approach:**
1. Finalize vadocs to deliver ONE complete feature with full stack: tests, CLI, docs, pre-commit hook, GH CI
2. Consumer repos (hub) use vadocs via pre-commit hook source and `uv add vadocs`
3. Once a feature is complete in vadocs, remove corresponding script from hub's `tools/scripts/`
4. Repeat for each feature until tools/scripts contains only hub-specific scripts

**What vadocs delivers per feature:**
- Validator class (library)
- CLI command (`vadocs check-adr`)
- Pre-commit hook (`.pre-commit-hooks.yaml`)
- GH Actions workflow (reusable)
- Tests (pytest suite)
- Documentation

## Current Session Tasks

### Completed
1. [x] Create `tools/docs/packages/` directory
2. [x] Write `ecosystem_package_development_workflow.md` (generic spoke dev guide)
3. [x] Verify vadocs imports work: `uv run python -c "import vadocs; print(vadocs.__version__)"` → 0.1.0
4. [x] Save plan to `misc/plan/plan_20260204_hub_spoke_ecosystem_workflow.md` for history (per CLAUDE.md convention)

### Next Session (vadocs v0.2.0)
Focus: Deliver first complete feature (ADR frontmatter validation) with full stack

5. [ ] Add CLI to vadocs (`vadocs check-adr`)
6. [ ] Add `.pre-commit-hooks.yaml` to vadocs
7. [ ] Add reusable GH Actions workflow to vadocs
8. [ ] Test: Hub uses vadocs pre-commit hook instead of check_adr.py
9. [ ] Deprecate/remove hub's check_adr.py frontmatter validation (keep index sync for now)

## How Consumer Repos Use vadocs

### Pre-commit Integration (Target State)

Consumer's `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/lefthand67/vadocs
    rev: v0.2.0
    hooks:
      - id: check-adr-frontmatter
      - id: check-adr-terms
```

### Direct CLI Usage
```bash
uv add vadocs
vadocs check-adr architecture/adr/ --config architecture/adr/adr_config.yaml
```

### GH Actions Integration
```yaml
jobs:
  validate-docs:
    uses: lefthand67/vadocs/.github/workflows/validate-adr.yml@v0.2.0
    with:
      adr_dir: architecture/adr/
      config_path: architecture/adr/adr_config.yaml
```

## Development Workflow (Editable Install)

For development, hub uses editable install:

```toml
# hub's pyproject.toml
[tool.uv.sources]
vadocs = { path = "../vadocs", editable = true }
```

**Key benefit:** Edit vadocs → test in hub → changes reflected instantly (symlink).

## Claude Code Workflow

Single session accesses both repos via absolute paths:

| Task | Path |
|------|------|
| Edit hub files | `/home/commi/Yandex.Disk/it_working/projects/ai/ai_engineering_book/...` |
| Edit vadocs files | `/home/commi/Yandex.Disk/it_working/projects/ai/vadocs/...` |
| Run hub tests | `uv run pytest tools/tests/` (from hub CWD) |
| Run vadocs tests | `uv run pytest ../vadocs/tests/` |

## File Paths Reference

**vadocs (spoke):**
- `/home/commi/Yandex.Disk/it_working/projects/ai/vadocs/src/vadocs/`
- `/home/commi/Yandex.Disk/it_working/projects/ai/vadocs/tests/`

**Hub integration points:**
- `pyproject.toml` - editable install for development
- `.pre-commit-config.yaml` - will use vadocs hooks (after v0.2.0)
- `architecture/adr/adr_config.yaml` - config consumed by vadocs

**Created this session:**
- `tools/docs/packages/ecosystem_package_development_workflow.md`

## Governing ADRs

| ADR | Purpose |
|-----|---------|
| ADR-26012 | Extraction of Documentation Validation Engine (founding document) |
| ADR-26020 | Hub-and-Spoke Ecosystem Documentation Architecture |
| ADR-26011 | Mandatory Script Suite Workflow (testing standards) |
