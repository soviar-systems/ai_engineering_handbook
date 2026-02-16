# Plan: Structured Commit Bodies for Automated CHANGELOG Generation

## Context

Currently CHANGELOG is manually curated and RELEASE_NOTES.md is LLM-composed from a `./diff` file. Commit bodies are inconsistent — some prose, some empty, none structured. The insight: if commit bodies follow a parseable bullet format, a simple Python script can generate the CHANGELOG directly from `git log` — no LLM needed.

### Relationship to existing conventions

The [Production Git Workflow Standards](/tools/docs/git/01_production_git_workflow_standards.md) define a three-tier system:

| Tier | Purpose | Format |
|------|---------|--------|
| 1. SCOPE | Branch prefix + ticket ID | `feat/456-add-metrics-endpoint` |
| 2. INTENT | Commit subject prefix | `feat: implement X interface` |
| 3. JUSTIFICATION | ArchTag (conditional: refactor/perf/BREAKING) | `ArchTag:TECHDEBT-PAYMENT` |

**Structured body bullets extend Tier 2** — they detail *what exactly* changed within the commit. They coexist with Tier 3 (ArchTag) when applicable.

The merge strategy (`--ff-only` / Squash-and-Merge) means each feature branch becomes **one atomic commit** on main. Each commit body therefore represents one complete changelog topic — ideal for automated extraction.

### Foundational architectural decisions

These decisions were evaluated through competing hypothesis analysis (Gemini session, 2026-02-09) and form the non-negotiable foundation of this plan:

**1. `git bisect` is formally deprioritized as a debugging tool.**
- **Motivation**: In ML-heavy systems, regressions are more frequently caused by data/config drift or high-level logic errors, not single-line syntax bugs. Unit/eval tests catch logic bugs faster than history-walking. Maintaining perfect stacked-diff history for `bisect` represents "Process Debt" that violates SVA (Smallest Viable Architecture) principles — especially without specialized wrappers like Graphite or Sapling.
- **Consequence**: We do not need atomic commit history within feature branches. The topic branch is a transient development workspace. Only the squashed commit on trunk matters.

**2. Rich-Body Squash is the merge strategy — 1 PR = 1 Commit = 1 Logical Change.**
- **Motivation**: Squashing moves the system from *Micro-Atomic History* (line-level changes) to *Macro-Atomic History* (intent-level changes). This reduces history noise by 70-90% while preserving 100% of the semantic metadata needed for changelogs. Each squashed commit body contains the structured bullets that describe all sub-tasks — no metadata is lost, it's *relocated* from individual commits into a single rich body.
- **Consequence**: The merge policy must be set to Squash-and-Merge. The Git host must be configured to include the PR description in the squash commit message template. `generate_changelog.py` must use `git log --first-parent` to scan only trunk commits and ignore noise from deleted feature branches.

**3. Release-Time Batch Generation — the "Ingredients-First" pattern.**
- **Motivation**: Running changelog extraction on every commit adds unnecessary latency to the local dev cycle. Generating the changelog only when the release branch is frozen ensures the artifact reflects the final, immutable state of the release candidate. A single generation event is easier to audit. However, batch generation at release time *requires* that input data (commit bodies) was validated continuously — otherwise the generator will fail when needed most.
- **Consequence**: Two decoupled concerns: (a) `validate_commit_msg.py` runs as a hard gate at every commit, ensuring "ingredients" are parseable; (b) `generate_changelog.py` runs once at release time, "cooking" the CHANGELOG from validated ingredients. The validator is the critical path protector.

**4. Debian `dch` (stateful metadata buffer) is rejected.**
- **Motivation**: The `dch` approach introduces a changelog buffer file (`UNRELEASED.md` or `debian/changelog`) as a staging area. While it provides editorial control, it creates "Double-Entry Bookkeeping" — the delta between what was committed and what was recorded in the buffer can drift. The buffer file is notorious for merge conflicts. It requires a manual CLI step (SVA C1 violation) and adds a persistent state-tracking layer (SVA C4 violation). The `--amend` problem is unsolvable without idempotent hash-checking. In modern Git-centric workflows, the Git log itself is the single source of truth.
- **Mitigation adopted**: The "Unreleased Stanza" concept is preserved — `generate_changelog.py` can output commits since the last tag, providing the same "what's pending" visibility without a separate file.

**5. LLM-based generation is superseded.**
- **Motivation**: The existing `ai_system/4_orchestration/workflows/release_notes_generation/` approach uses LLMs to compose RELEASE_NOTES.md from a diff file. This introduces non-determinism and "hallucination" risks in technical documentation. With structured commit bodies, a deterministic regex parser produces identical output every time — traceability from commit to changelog entry is 1:1.

## Competing Hypothesis Analysis

### The Problem Statement

Generate hierarchical changelogs (section → topic → sub-items) automatically from git commit history, across all repos in the ecosystem, without an LLM. The existing CHANGELOG format is richer than what any standard tool produces:

```
release 2.4.0
* ADR Validation Toolchain:                              ← topic (from commit subject)
    - check_adr_index.py renamed to check_adr.py...     ← sub-item (from commit body)
    - Term reference validation added...                 ← sub-item
* Architecture Decisions (ADRs) added:                   ← another topic
    - ADR-26016: Metadata-Driven...                      ← sub-item
```

### Evaluation Criteria

| # | Criterion | Weight | Why it matters |
|---|-----------|--------|----------------|
| 1 | **Output fidelity** | High | Must produce hierarchical CHANGELOG with sub-items, not flat lists |
| 2 | **Python-native** | High | Ecosystem uses Python + uv exclusively (ADR-26001, ADR-26003 rejected Node.js) |
| 3 | **Ecosystem portability** | High | Must work across all ecosystem repos, installable as a package |
| 4 | **Convention compliance** | Medium | How far from Conventional Commits spec? |
| 5 | **Maintenance burden** | Medium | Who maintains the tooling? |
| 6 | **Extensibility** | Medium | Can it adapt as needs evolve (e.g., SemVer hints, RELEASE_NOTES)? |
| 7 | **Adoption friction** | Low-Med | How hard for contributors to learn? |

### Hypothesis A: git-cliff (Rust binary with Python config)

[git-cliff](https://git-cliff.org/) is a Rust-based changelog generator with regex parsers and Tera templates. It can be configured in `pyproject.toml` via `[tool.git-cliff]`.

**Body handling**: `split_commits: true` processes each body line as a separate entry. This would turn each bullet into its own changelog line. But it can't produce hierarchical output (subject as parent, bullets as children) — all lines become flat, same-level entries.

**Scoring:**

| Criterion | Score | Notes |
|-----------|-------|-------|
| Output fidelity | **Partial** | Flat output only. No parent-child hierarchy. Would need post-processing. |
| Python-native | **No** | Rust binary. `pip install git-cliff` exists but wraps a Rust binary. Breaks ADR-26001. |
| Ecosystem portability | **Good** | Configurable in pyproject.toml, pip-installable |
| Convention compliance | **High** | Standard CC, no custom body format needed |
| Maintenance burden | **Low** | Maintained by community (10k+ GitHub stars) |
| Extensibility | **Medium** | Tera templates are powerful but limited to what git-cliff exposes |
| Adoption friction | **Low** | No new commit conventions needed |

**Verdict: REJECTED** — Cannot produce hierarchical output. Rust dependency violates ecosystem Python-only constraint.

### Hypothesis B: git-changelog (Python + Jinja2)

[git-changelog](https://pypi.org/project/git-changelog/) is a Python changelog generator with Jinja2 templates and CC parsing. Supports Angular, Conventional Commits, and basic conventions.

**Body handling**: Parses git trailers. Body included as a block in the template context. No bullet extraction. Jinja2 templates can render the body as-is but cannot decompose it into structured sub-items without custom Python filters.

**Scoring:**

| Criterion | Score | Notes |
|-----------|-------|-------|
| Output fidelity | **Partial** | Body as a block. Jinja2 COULD split on `\n- ` but it's a hack, not a feature. |
| Python-native | **Yes** | Pure Python |
| Ecosystem portability | **Good** | pip-installable, Jinja2 templates |
| Convention compliance | **High** | Standard CC |
| Maintenance burden | **Low** | Community-maintained |
| Extensibility | **Medium** | Jinja2 is flexible but body decomposition requires custom filters |
| Adoption friction | **Low** | No new commit conventions |

**Verdict: POSSIBLE BUT STRAINED** — Could work with Jinja2 hacks but body bullet extraction is not a first-class feature. We'd be fighting the tool.

### Hypothesis C: Commitizen (Python framework)

[Commitizen](https://commitizen-tools.github.io/commitizen/) is a Python framework for guided commits, version bumping, and changelog generation. Supports custom rules via `cz_customize`.

**Body handling**: Has `changelog_message_builder_hook` that can generate multiple changelog entries from a single commit. Custom rules can parse body content. However, [known issues](https://github.com/commitizen-tools/commitizen/issues/524) with multiline body handling in custom configs — each line may appear as a separate entry incorrectly.

**Scoring:**

| Criterion | Score | Notes |
|-----------|-------|-------|
| Output fidelity | **Possible** | With `changelog_message_builder_hook` and custom template, could produce hierarchical output. But fragile. |
| Python-native | **Yes** | Pure Python |
| Ecosystem portability | **Good** | pip-installable, extensive config |
| Convention compliance | **High** | Built on CC, extensible |
| Maintenance burden | **Low-Med** | Community-maintained but custom hooks are our code |
| Extensibility | **High** | Full Python plugin system, custom rules, templates |
| Adoption friction | **Medium** | Commitizen adds guided commit flow — more opinionated than a simple parser |

**Verdict: POSSIBLE** — Most capable existing tool. But commitizen is an opinionated framework (guided commits, version bumping), not just a changelog parser. Adopting it means adopting its workflow model. The `changelog_message_builder_hook` could work but has known multiline issues.

### Hypothesis D: Custom Python parser (spoke package)

A custom Python package (`changelog-generator` or similar) published as a spoke package in the ecosystem. Understands the structured body convention natively.

**Body handling**: First-class bullet extraction. Knows that `- Verb: target — description` lines are changelog sub-items. Ignores prose lines. Excludes ArchTag and trailers.

**Scoring:**

| Criterion | Score | Notes |
|-----------|-------|-------|
| Output fidelity | **Full** | Designed for our exact CHANGELOG format. Hierarchical output is the primary feature. |
| Python-native | **Yes** | Pure Python, follows ADR-26001 |
| Ecosystem portability | **Excellent** | Spoke package, `uv add` in any repo. Follows ADR-26020 hub-spoke model. |
| Convention compliance | **Medium** | Extends CC with structured body. Non-standard but well-documented. |
| Maintenance burden | **Medium** | We own it. But scope is small (~200 lines of parser + tests). |
| Extensibility | **High** | Full control. Can add SemVer detection, RELEASE_NOTES skeleton, Telegram post templates later. |
| Adoption friction | **Medium** | Contributors must learn the body bullet convention. But it's simple: `- Verb: target — description`. |

**Verdict: RECOMMENDED** — Only approach that produces the exact hierarchical output we need. Fits the ecosystem model (spoke package). Small, focused scope. The body convention is a simple extension of CC, not a radical departure.

### Hypothesis E: Hybrid — git-changelog + custom Jinja2 filter

Use git-changelog as the parsing engine (handles git log, CC parsing, version grouping) but add a custom Jinja2 filter that decomposes body text into bullet sub-items.

**Scoring:**

| Criterion | Score | Notes |
|-----------|-------|-------|
| Output fidelity | **Good** | git-changelog handles structure, custom filter handles bullets |
| Python-native | **Yes** | Both are Python |
| Ecosystem portability | **Good** | pip-installable with custom filter package |
| Convention compliance | **High** | Standard CC + body convention |
| Maintenance burden | **Low-Med** | git-changelog maintained by community, only the filter is ours |
| Extensibility | **Medium** | Limited by what git-changelog exposes to templates |
| Adoption friction | **Medium** | Same body convention as Hypothesis D |

**Verdict: VIABLE ALTERNATIVE** — Less code to write than a full custom parser. But adds a dependency on git-changelog's internal data model. If git-changelog changes how it exposes body text, our filter breaks.

### Decision Matrix

| Criterion | A: git-cliff | B: git-changelog | C: commitizen | D: Custom parser | E: Hybrid |
|-----------|:---:|:---:|:---:|:---:|:---:|
| Output fidelity | partial | partial | possible | **full** | good |
| Python-native | **no** | yes | yes | yes | yes |
| Ecosystem portability | good | good | good | **excellent** | good |
| Convention compliance | high | high | high | medium | high |
| Maintenance burden | low | low | low-med | **medium** | low-med |
| Extensibility | medium | medium | high | **high** | medium |
| Adoption friction | low | low | medium | medium | medium |

### Recommendation: Hypothesis D (Custom Python parser as spoke package)

**Rationale:**
1. It's the only approach that can produce the exact hierarchical CHANGELOG format natively — all others require hacks or post-processing.
2. It fits the ecosystem model perfectly: a spoke package (like vadocs) that any repo can install via `uv add`.
3. Full control means it can evolve with the ecosystem — SemVer detection, RELEASE_NOTES skeleton, integration with the release workflow.
4. The maintenance burden is proportional to the scope (~200 lines parser + ~300 lines tests) and follows the established script suite pattern.
5. The body convention (`- Verb: target — description`) is a minor, well-documented extension of Conventional Commits, not a radical departure.

**Key risk to acknowledge in ADR**: This is a project-ecosystem-specific convention, not an industry standard. The parser is portable to any project that adopts the same body format, but the body format itself is bespoke.

## Design

### Commit Body Convention

Every commit MUST have a structured body with at least one bullet:

```
<type>[(<scope>)]: <subject line>

- <Verb>: <target> — <description>
- <Verb>: <target> — <description>

Co-Authored-By: ...
```

**Rules:**
1. Body MUST contain at least one line starting with `- ` (a changelog bullet)
2. Each bullet is a self-contained changelog entry
3. Optional verb prefix before `:` — `Created`, `Updated`, `Deleted`, `Renamed`, `Fixed`, `Moved`, `Added`, `Removed`, `Refactored`, `Configured`
4. Git trailers (after blank line, `Key: Value` format) are excluded from parsing
5. Non-bullet lines in the body (prose context) are ignored by the parser but allowed for human context
6. ArchTag line (`ArchTag:TAG-NAME`) is preserved for Tier 3 validation but excluded from changelog output

**Example — complex commit (docs) — real commit `3e652bc`:**
```
docs: restructure website deployment documentation

- Created: `tools/docs/website/01_github_pages_deployment.(md|ipynb)` — canonical GitHub Pages guide with MyST init, myst.yml config, local testing, Pages enablement, deploy workflow, and troubleshooting (309 lines)
- Renamed: `mystmd_website_deployment_instruction.(md|ipynb)` → `02_self_hosted_deployment.(md|ipynb)` — with `:::{warning}` deprecation notice linking to the new guide
- Refactored: `02_self_hosted_deployment.md` — replaced duplicated MyST init/config/local-testing sections (1.1, 1.2, 4) with cross-references to the GitHub Pages guide; added superseded notice inside deploy.yml dropdown
- Deleted: `tools/docs/git/github_pages_setup.md` — content fully absorbed into `01_github_pages_deployment`
- Updated: `architecture/adr/adr_26022...md` — fixed self-hosted link path, replaced single reference with two entries (GitHub Pages guide + deprecated self-hosted)
- Updated: `architecture/packages/README.md` — GitHub Pages setup link now points to `01_github_pages_deployment.ipynb`
- Updated: `architecture/packages/creating_spoke_packages.md` — same link fix in Next Steps section
- Fixed: `configs/mutli-site/` → `configs/multi-site/` directory typo (nginx.conf + play_nginx.yml)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

**Example — simple commit (fix):**
```
fix: correct broken MyST term reference in ADR-26019

- Fixed: `{term}`ADR 26001`` → `{term}`ADR-26001`` across 11 ADR files

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

**Example — refactor with ArchTag (Tier 3 + structured body coexist):**
```
refactor: simplify model loading logic

ArchTag:TECHDEBT-PAYMENT
- Updated: `model_loader.py` — reduced cyclomatic complexity from 15 to 8
- Deleted: `legacy_loader.py` — consolidated into main loader

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

### Parser Output (CHANGELOG format)

The script groups commits by conventional commit type and maps them to CHANGELOG sections:

| Commit type | CHANGELOG section |
|-------------|-------------------|
| `feat:` | New Features |
| `fix:` | Bug Fixes |
| `docs:` | Documentation |
| `ci:` | CI/CD & Quality |
| `chore:` | Maintenance |
| `refactor:` | Refactoring |
| `adr:` | Architecture Decisions |
| `pr:` | Public Relations |
| `perf:` | Performance |

Output format matches existing CHANGELOG:
```
release X.Y.Z
* Documentation:
    - Restructure website deployment documentation
        - Created: `tools/docs/website/01_github_pages_deployment.(md|ipynb)` — canonical GitHub Pages guide with MyST init, myst.yml config, local testing, Pages enablement, deploy workflow, and troubleshooting (309 lines)
        - Renamed: `mystmd_website_deployment_instruction.(md|ipynb)` → `02_self_hosted_deployment.(md|ipynb)` — with deprecation notice
        - Refactored: `02_self_hosted_deployment.md` — replaced duplicated sections with cross-references; added superseded notice
        - Deleted: `tools/docs/git/github_pages_setup.md` — content fully absorbed into `01_github_pages_deployment`
        - Updated: `architecture/adr/adr_26022...md` — fixed link path, split into two reference entries
        - Updated: `architecture/packages/README.md` — link fix
        - Updated: `architecture/packages/creating_spoke_packages.md` — link fix
        - Fixed: `configs/mutli-site/` → `configs/multi-site/` directory typo
* Bug Fixes:
    - Correct broken MyST term reference in ADR-26019
        - Fixed: `{term}`ADR 26001`` → `{term}`ADR-26001`` across 11 ADR files
```

## Where the alternatives analysis lives

The detailed alternatives analysis (5 hypotheses with WRC scoring, Debian `dch` evaluation, Stacked Diffs vs Rich-Body Squash evaluation) is substantial — too large for an ADR alternatives section, but too decision-focused for a standalone RFC.

**Decision: Split into two artifacts:**

1. **Primary source**: `misc/plan/gemini_20260209_changelog_alternatives_analysis.md` — the full Gemini conversation transcript with WRC calculations, methodology comparisons, assumption interrogation, and validation gap analysis. This is the analytical record that future readers can audit.
2. **ADR-26024 alternatives section**: A condensed summary referencing the primary source. Each rejected alternative gets 2-3 sentences of rationale + the WRC score, with a pointer to the full analysis. This keeps the ADR readable while preserving traceability.

**Why not a separate RFC?** The RFC→ADR workflow makes sense when a proposal needs cross-team review before a decision is made. Here, the decision is already made — the analytical work *justifies* the ADR, it doesn't precede it as a separate governance stage. The Gemini transcript *is* the RFC equivalent, and the ADR is the ratified decision.

---

## Steps — Phase A: Analytical Foundation (must complete before any implementation)

This is a large analytical task. The git workflow standards, the ADR, and the commit convention need to be theoretically sound and internally consistent *before* any script is written. A script suite built on a shaky doctrinal foundation will need to be rewritten when the conventions change.

### A1. Revise `01_production_git_workflow_standards.md`

**File**: `tools/docs/git/01_production_git_workflow_standards.md`

The current document contains several contradictions with the decisions formalized above. These must be resolved first because the ADR and all tooling reference this document as the authoritative source.

**Contradictions to resolve:**

| Section | Current state | Required change | Motivation |
|---------|--------------|-----------------|------------|
| "WIP" Commits: Interactive Rebase | Recommends `git rebase -i` to squash WIPs before PR | Remove or downgrade to "optional local hygiene". The Git host handles squashing at merge time. | Rich-Body Squash makes developer-side rebase unnecessary — the squash happens at merge, not before. |
| PR System Guardrails | Recommends both `--ff-only` (line 223) and "Squash and Merge" (line 215) | Remove `--ff-only` — it's incompatible with Squash-and-Merge. Squash creates a new commit, not a fast-forward. | These are mutually exclusive merge strategies. The document currently contradicts itself. |
| PR System Guardrails | Developer rebase workflow code block (lines 226-236) | Remove. Developers don't manually squash — the Git host UI does it. | Obsolete with Rich-Body Squash. |
| Atomic Commits: Guiding Principle | Rule 2: "mandatory for `git bisect`" (line 271) | Reframe: "The final squashed commit on trunk must be buildable. Intermediate feature branch commits are transient." | `git bisect` is formally deprioritized. Atomicity applies to the squashed commit, not feature branch WIPs. |
| The "Commit by Logic" Workflow | Promotes granular atomic commits on feature branches | Reframe as "recommended for PR reviewability" but explicitly state: only the squashed commit matters for history and changelog extraction. | Internal feature branch history is invisible to trunk — it's a development aid, not a historical record. |
| Merge Strategy: Enforcement | "enforce 'Merge --ff-only'" (line 354) | Replace with: "enforce Squash-and-Merge. The Git host must populate the squash commit message from the PR description." | `--ff-only` contradicts squash. The merge policy must guarantee that PR descriptions flow into commit bodies. |
| Debugging Without "git bisect" Granularity | States bisect is not primary — already partially aligned | Strengthen language: formally deprioritize `git bisect`. In ML-heavy systems, regressions stem from data/config drift, caught by unit/eval tests, not line-level history-walking. | Makes the existing section match the formal decision. |
| Stacked Diff Exception | Allows multiple commits to preserve bisect utility | Mark as "Not Recommended" or remove. If kept: clarify that each diff = separate PR, each PR still gets squashed. | Stacked Diffs rejected (WRC 0.68) due to rebase toil and tooling requirements (Graphite/Sapling). |

**New sections to add:**

1. **Structured Commit Body Format** — The `- Verb: target — description` convention, with examples. This is the Tier 2 extension that makes automated CHANGELOG extraction possible.
2. **Release-Time CHANGELOG Generation** — When and how the CHANGELOG is produced: batch extraction on a frozen release branch using `generate_changelog.py` with `git log --first-parent`. References the "Ingredients-First" pattern.

**Frontmatter**: Update from old `Owner/Version` format to ADR-26023 standard. Version bumps to `1.0.0` (production document).

### A2. Revise `02_pre_commit_hooks_and_staging_instruction_for_developers.md`

**File**: `tools/docs/git/02_pre_commit_hooks_and_staging_instruction_for_devel.md`

**Changes:**
- **Frontmatter**: Update from old format (`lefthand67@gmail.com`, Version 0.2.2) to ADR-26023 standard. Version `1.0.0`.
- **New section**: "Commit Message Validation" — explain how `validate_commit_msg.py` (the `commit-msg` stage hook) enforces Tier 2 (Conventional Commits subject) and structured body bullets. Reference ADR-26003 and ADR-26024. Note that with Squash-and-Merge, intermediate commit messages during development are less critical — the squash commit message (derived from the PR description) is the one that must pass validation.

### A3. Write ADR-26024

**File**: `architecture/adr/adr_26024_structured_commit_bodies_for_automated_changelog.md`

This ADR codifies the decisions made in the Gemini analysis session. It is the ratified decision document; the full analysis lives in `misc/plan/gemini_20260209_changelog_alternatives_analysis.md`.

Content:
- **Context**: Manual CHANGELOG curation doesn't scale; LLM-based generation (see `ai_system/4_orchestration/workflows/release_notes_generation/`) adds non-determinism. Conventional commits already provide type classification — extending this with structured bodies enables fully automated, deterministic CHANGELOG generation. The CHANGELOG transitions from a narrative/descriptive artifact to a computational/traceable artifact [ISO 29148: Traceability].
- **Decision**: Mandate structured bullet bodies in all commits. Build a custom Python parser as a spoke package (per ADR-26020) to extract them into hierarchical CHANGELOG format. This extends the Three-Tier Naming Structure from the Production Git Workflow Standards by adding detailed change manifests to Tier 2.
- **Architectural pillars** (reference the foundational decisions from this plan):
  1. `git bisect` deprioritized — tests over history-walking
  2. Rich-Body Squash — 1 PR = 1 Commit = 1 Logical Change
  3. Release-Time Batch Generation — "Ingredients-First" pattern
  4. Git log as single source of truth — no stateful buffers
- **Alternatives section** (condensed, with WRC scores and pointers to full analysis):
  - git-cliff (WRC n/a — Rust, rejected: non-Python, flat output)
  - git-changelog (WRC n/a — Python, but body bullet extraction is not first-class)
  - Commitizen (WRC n/a — opinionated framework, fragile multiline `changelog_message_builder_hook`)
  - Hybrid git-changelog + custom Jinja2 filter (viable but creates dependency on third-party data model)
  - Debian `dch` stateful buffer (WRC 0.70 — rejected: SVA violations C1/C4, merge conflict risk, double-entry bookkeeping)
  - Stacked Diffs (WRC 0.68 — rejected: rebase toil, requires Graphite/Sapling, bisect deprioritized)
  - LLM-Based Generation (WRC 0.62 — rejected: non-deterministic, no audit trail)
  - Custom Python parser (WRC 0.91 — **selected**: only approach achieving full hierarchical output fidelity within Python-only ecosystem constraints)
  - Full analysis: `misc/plan/gemini_20260209_changelog_alternatives_analysis.md`
- **Key risk**: The body convention (`- Verb: target — description`) is an ecosystem-specific extension of Conventional Commits, not an industry standard. The parser is portable to any project adopting the same format, but the format itself is bespoke.
- **References**: ADR-26003 (gitlint), ADR-26020 (hub-spoke ecosystem), Production Git Workflow Standards, existing CHANGELOG/RELEASE_NOTES patterns, Gemini analysis transcript.

### A4. Update CLAUDE.md

Add to "Commit Conventions" section:
- Commit bodies MUST contain structured bullets (per ADR-26024)
- Format: `- <Verb>: <target> — <description>`
- CHANGELOG is generated from commit history, not manually curated
- Merge policy: Squash-and-Merge (1 PR = 1 Commit on trunk)

### A5. Review internal consistency

Before proceeding to implementation, verify that all four documents (01_production, 02_pre_commit, ADR-26024, CLAUDE.md) are internally consistent:
- No contradictions between merge strategy references
- The structured body convention is described identically everywhere
- Cross-references between documents are correct
- Frontmatter on all revised docs follows ADR-26023

---

## Steps — Phase B: Implementation (only after Phase A is complete and reviewed)

Phase B implements the tooling that *operationalizes* the standards established in Phase A. No script should be written until the conventions it enforces are finalized and documented.

### B1. Write tests for the changelog generator (TDD — tests first)

**File**: `tools/tests/test_generate_changelog.py`

Test contracts:
- **Parsing**: Extract type, scope, subject, body bullets, trailers from raw commit text
- **Grouping**: Commits grouped by type into correct CHANGELOG sections
- **Ordering**: Sections appear in a consistent order (feat → fix → docs → ci → ...)
- **Trailer exclusion**: `Co-Authored-By` and other trailers not included in bullets
- **Body-less commits**: Handled gracefully (the validator prevents these, but the generator should not crash)
- **Non-bullet body lines**: Prose context lines are ignored, only `- ` lines extracted
- **ArchTag exclusion**: `ArchTag:TAG-NAME` lines excluded from changelog output
- **Edge cases**: Empty ref range, single commit, scope in subject `feat(auth):`
- **Output format**: Matches existing CHANGELOG indentation (4-space sub-items)
- **`--first-parent` behavior**: Only trunk commits are processed, not feature branch noise
- **Legacy handling**: Commits before the standard (no body bullets) are included with subject only, no sub-items

### B2. Write the changelog generator script

**File**: `tools/scripts/generate_changelog.py`

Interface:
```bash
# Generate changelog between two refs
uv run tools/scripts/generate_changelog.py v2.4.0..HEAD

# Generate with version label
uv run tools/scripts/generate_changelog.py v2.4.0..HEAD --version 2.5.0

# Append directly to CHANGELOG
uv run tools/scripts/generate_changelog.py v2.4.0..HEAD --version 2.5.0 --prepend CHANGELOG
```

Implementation (top-down design per CLAUDE.md):
1. `main()` — argparse, call generate, output
2. `generate_changelog(ref_range, version)` → str
3. `parse_commits(ref_range)` → list[Commit] — runs `git log --first-parent`, parses output
4. `parse_single_commit(raw)` → Commit dataclass (type, scope, subject, bullets, hash)
5. `group_by_type(commits)` → dict[str, list[Commit]]
6. `format_changelog(groups, version)` → str

Key details:
- **MUST use `git log --first-parent`** to scan only squashed trunk commits and ignore noise from deleted feature branches
- Uses `subprocess.run` for `git log` with format `%H%n%s%n%b%nEND_COMMIT_MARKER`
- Trailer detection: lines matching `^[\w-]+: .+` after a blank line
- Bullet detection: lines matching `^\s*- .+`
- ArchTag detection: lines matching `^ArchTag:.+` — preserved for Tier 3 but excluded from changelog
- Uses `pathlib.Path` throughout
- **Legacy commits** (pre-standard, no body bullets): included with subject line only, no sub-items — graceful degradation, not failure
- **Clean state check**: warn (not fail) if `git status` is not clean when running

### B3. Write tests for the commit-msg validator (TDD)

**File**: `tools/tests/test_validate_commit_msg.py`

### B4. Write the commit-msg validation hook

**File**: `tools/scripts/validate_commit_msg.py`

A pre-commit hook (stage: `commit-msg`) that:
1. Reads the commit message file (passed as arg)
2. Validates Conventional Commits format on subject line (Tier 2)
3. Checks body has at least one `- ` bullet line (structured changelog entry)
4. For `refactor:`, `perf:`, `BREAKING CHANGE` — also validates ArchTag presence (Tier 3, per Production Git Workflow Standards)
5. Exits 1 with clear error message if validation fails
6. Skips merge commits and fixup commits

This implements the commit-msg validation envisioned in ADR-26003 without the external gitlint dependency — a single-purpose Python script following ADR-26001 (Python + OOP for hooks).

### B5. Write script documentation

**Files**:
- `tools/docs/scripts_instructions/generate_changelog_py_script.md` (+ `.ipynb` via jupytext)
- `tools/docs/scripts_instructions/validate_commit_msg_py_script.md` (+ `.ipynb` via jupytext)

Following existing doc pattern: purpose, usage, examples, contract.

### B6. Register in pre-commit config

Add to `.pre-commit-config.yaml`:
```yaml
  - id: validate-commit-msg
    name: Validate Commit Body
    entry: uv run --active tools/scripts/validate_commit_msg.py
    language: python
    stages: [commit-msg]
    pass_filenames: true
```

Also add the test hook:
```yaml
  - id: test-validate-commit-msg
    name: Test Validate Commit Msg script
    entry: uv run --active pytest tools/tests/test_validate_commit_msg.py
    language: python
    files: ^tools/(scripts/validate_commit_msg\.py|tests/test_validate_commit_msg\.py)$
    pass_filenames: false
```

---

## Files involved

### Phase A — Analytical Foundation

| Action | File |
|--------|------|
| **Created** | `misc/plan/gemini_20260209_changelog_alternatives_analysis.md` — full Gemini analysis transcript |
| **Edit** | `tools/docs/git/01_production_git_workflow_standards.md` — resolve contradictions, add structured body & release-time sections, frontmatter |
| **Edit** | `tools/docs/git/02_pre_commit_hooks_and_staging_instruction_for_devel.md` — add commit-msg validation section, frontmatter |
| **Create** | `architecture/adr/adr_26024_structured_commit_bodies_for_automated_changelog.md` |
| **Edit** | `CLAUDE.md` — update commit conventions |

### Phase B — Implementation

| Action | File |
|--------|------|
| **Create** | `tools/tests/test_generate_changelog.py` |
| **Create** | `tools/scripts/generate_changelog.py` |
| **Create** | `tools/tests/test_validate_commit_msg.py` |
| **Create** | `tools/scripts/validate_commit_msg.py` |
| **Create** | `tools/docs/scripts_instructions/generate_changelog_py_script.md` |
| **Create** | `tools/docs/scripts_instructions/validate_commit_msg_py_script.md` |
| **Edit** | `.pre-commit-config.yaml` — add commit-msg hook + test hook |

## Verification

### Phase A
1. All four documents (01_production, 02_pre_commit, ADR-26024, CLAUDE.md) reference the same merge strategy, body convention, and generation timing — no contradictions
2. Cross-references between documents resolve correctly
3. Frontmatter on all revised docs follows ADR-26023

### Phase B
1. `uv run pytest tools/tests/test_generate_changelog.py` — all tests pass
2. `uv run pytest tools/tests/test_validate_commit_msg.py` — all tests pass
3. `uv run tools/scripts/generate_changelog.py HEAD~5..HEAD` — generates output from recent commits
4. Manual: make a commit without body bullets → hook rejects it
5. Manual: make a commit with body bullets → hook passes, `generate_changelog.py` extracts them
6. `uv run tools/scripts/check_script_suite.py` — validates script+test+doc triplet
