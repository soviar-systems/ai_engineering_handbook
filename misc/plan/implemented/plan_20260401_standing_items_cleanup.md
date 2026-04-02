# Plan: Standing Items Cleanup (5 Items)

## Context

Five standing work items have accumulated with no active plan: two tech-debt entries (TD-004, TD-005), two todo.md items (pre-commit dedup, prepare_prompt serializer), and one roadmap blocker (Phase 2.0 CLI agents source conversion). This plan sequences all five for implementation.

During Item 3 implementation, a governance gap was discovered: the contract docstring convention existed only in `AGENTS.md`, not as a governed ADR. This required inserting ADR-26045 (AI-Native Development) and A-26020 (analysis) before the dyad ADR could be written.

**Note:** ADR-26045 ("AI-Native Development — Code as Primary Documentation") serves as the dyad ADR — no separate ADR-26046 needed. It supersedes ADR-26011 and establishes contract docstrings as the ecosystem-wide documentation standard.

## Progress

- [x] Item 1: Pre-commit hook stage deduplication — `.pre-commit-config.yaml` updated, todo.md cleaned
- [x] Item 2: Close prepare_prompt.py serializer todo — todo.md entry removed (N/A — custom serializer)
- [x] Item 3: TD-004 — Supersede ADR-26011 (triad → dyad)
  - [x] A-26020 written (AI-Native Development analysis)
  - [x] ADR-26045 written (accepted — contract docstrings ecosystem-wide, supersedes ADR-26011)
  - [x] `development` tag added to `.vadocs/conf.json`
  - [x] Version semantics convention added to `architecture/architecture_decision_workflow_guide.md`
  - [x] Roadmap updated: ADR-26045 marked done, follow-up items (a-d) added
  - [x] `check_script_suite.py` updated — removed doc checks (check_doc_staged, check_doc_rename), DOCS_DIR/CONFIG_FILES constants
  - [x] `test_check_script_suite.py` updated — removed TestCheckDocStaged/TestCheckDocRename, updated for dyad convention
  - [x] `.pre-commit-config.yaml` updated — hook name and files regex for dyad pattern
  - [x] ADR-26011 marked as superseded (superseded_by: ADR-26045, added ## Supersession Rationale)
  - [x] TD-004 moved to Resolved in `techdebt.md`
- [ ] Item 4: Phase 2.0 CLI agents source conversion — **deferred by user**
- [x] Item 5: TD-005 — check_frontmatter.py sub-type spoke resolution
  - [x] Added `SUBTYPE_PARENT_MAP` to `tools/scripts/paths.py` — maps analysis/retrospective/source → evidence
  - [x] Updated `get_config_path()` — resolves sub-types to parent config before building path
  - [x] Added `_resolve_subtype_rules()` to `tools/scripts/check_frontmatter.py` — merges common + sub-type required_fields
  - [x] Updated `load_config_chain()` — calls `_resolve_subtype_rules()` for sub-types, returns merged child_config
  - [x] Added 4 tests to `TestLoadConfigChain` — test_subtype_resolves_to_parent_config, test_subtype_merges_required_fields, test_retrospective_subtype_resolves_correctly, test_source_subtype_resolves_correctly
  - [x] Updated `.vadocs/types/evidence.conf.json` — added TD-005 sub-type resolution comment
  - [x] Updated `.vadocs/conf.json` — changed "spoke configs" to "child configs" in directory layout comment
  - [x] Updated `.vadocs/README.md` — changed "Spoke configs" to "Child configs" terminology
  - [x] Tests pass: 70 passed, 1 skipped, 97% coverage

## Dependency graph (current)

```
Done:           Item 1 ✅, Item 2 ✅, Item 3 ✅
Deferred:       Item 4 (user will return to source conversion later)
Pending:        Item 5 (unblocked — needs dedicated plan or task)
```

---

## Item 3: TD-004 — Supersede ADR-26011 (triad → dyad)

### Remaining work

**New ADR**: `adr_26046_script_suite_dyad_convention.md` (next available number after 26045)

Decision: relax script+test+doc triad to script+test dyad. Contract docstrings (ADR-26045) + test suites provide sufficient documentation. References A-26020, A-26014.

**Script changes** (`tools/scripts/check_script_suite.py`):
- Remove `check_doc_staged()` function
- Remove `check_doc_rename()` function
- Remove doc check from `check_naming_convention()`
- Remove `DOCS_DIR`, `CONFIG_FILES` constants
- Update module docstring

**Test changes** (`tools/tests/test_check_script_suite.py`):
- Remove `TestCheckDocStaged`, `TestCheckDocRename` classes
- Update `TestCheckNamingConvention` — no doc assertions
- Update `TestMain` — no doc setup

**Config changes**:
- `.pre-commit-config.yaml` — update hook name to `(script + test)`, remove doc pattern from `files:` regex
- `architecture/adr/adr_26011*.md` — set `status: superseded`, `superseded_by: 26046`

**Techdebt**: Move TD-004 to Resolved in `misc/plan/techdebt.md`

**TDD order**: Update tests first (expect no doc requirement) → update script → green.

**Verify**:
- `uv run pytest tools/tests/test_check_script_suite.py`
- `pre-commit run check-script-suite --all-files`
- `uv run tools/scripts/check_adr.py --fix`

---

## Item 5: TD-005 — check_frontmatter.py sub-type spoke resolution

Unchanged from original plan. Blocked on Item 3 completion.

**Approach**: Sub-type → parent spoke mapping.

**Changes to `tools/scripts/paths.py`**:
- Add `SUBTYPE_SPOKE_MAP = {"analysis": "evidence", "retrospective": "evidence", "source": "evidence"}`
- Update `get_config_path()`: resolve sub-types to parent spoke file

**Changes to `tools/scripts/check_frontmatter.py`**:
- Add `_resolve_subtype_spoke()` — extracts nested `artifact_types.<type>` from parent spoke
- Update `load_config_chain()` to use it
- Remove `# pragma: no cover` from severity validation (now reachable via retrospective)

**Tests** (`tools/tests/test_check_frontmatter.py`):
- `TestSubTypeSpokeResolution` — analysis/retrospective/source load correct spoke rules
- Severity validation now covered for retrospective type

**Techdebt**: Move TD-005 to Resolved.

**TDD order**: Write failing tests → implement mapping → green.

**Verify**:
- `uv run pytest tools/tests/test_check_frontmatter.py`
- `uv run python -m tools.scripts.check_frontmatter architecture/evidence/analyses/`
- `pre-commit run check-frontmatter --all-files`
