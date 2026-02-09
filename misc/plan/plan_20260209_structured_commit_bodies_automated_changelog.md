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

## Steps

### 1. Write ADR-26024

**File**: `architecture/adr/adr_26024_structured_commit_bodies_for_automated_changelog.md`

Content:
- **Context**: Manual CHANGELOG curation doesn't scale; LLM-based generation adds complexity and non-determinism (see `ai_system/4_orchestration/workflows/release_notes_generation/`). Conventional commits already provide type classification — extending this with structured bodies enables fully automated CHANGELOG generation. Existing tools (git-cliff, git-changelog, commitizen) cannot produce hierarchical changelogs (section → topic → sub-items) without hacks or post-processing.
- **Decision**: Mandate structured bullet bodies in all commits. Build a parser as a spoke package (per ADR-26020) to extract them into CHANGELOG format. This extends the Three-Tier Naming Structure from the Production Git Workflow Standards by adding detailed change manifests to Tier 2.
- **Alternatives section**: Must include the competing hypothesis analysis — git-cliff (Rust, rejected: non-Python, flat output), git-changelog (Python, strained body handling), commitizen (opinionated framework, fragile multiline), hybrid (dependency on third-party data model). Document that the body convention is an ecosystem-specific extension of Conventional Commits.
- **References**: ADR-26003 (gitlint, Tier 2/3 enforcement), ADR-26020 (hub-spoke ecosystem), Production Git Workflow Standards (`tools/docs/git/01_production_git_workflow_standards.md`), existing CHANGELOG/RELEASE_NOTES patterns.

### 2. Write tests (TDD — tests first)

**File**: `tools/tests/test_generate_changelog.py`

Test contracts:
- **Parsing**: Extract type, scope, subject, body bullets, trailers from raw commit text
- **Grouping**: Commits grouped by type into correct CHANGELOG sections
- **Ordering**: Sections appear in a consistent order (feat → fix → docs → ci → ...)
- **Trailer exclusion**: `Co-Authored-By` and other trailers not included in bullets
- **Body-less commits**: Rejected (the validator, not the generator, handles this)
- **Non-bullet body lines**: Prose context lines are ignored, only `- ` lines extracted
- **Edge cases**: Empty ref range, single commit, scope in subject `feat(auth):`
- **Output format**: Matches existing CHANGELOG indentation (4-space sub-items)

### 3. Write the parser script

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
3. `parse_commits(ref_range)` → list[Commit] — runs `git log`, parses output
4. `parse_single_commit(raw)` → Commit dataclass (type, scope, subject, bullets, hash)
5. `group_by_type(commits)` → dict[str, list[Commit]]
6. `format_changelog(groups, version)` → str

Key details:
- Uses `subprocess.run` for `git log` with format `%H%n%s%n%b%nEND_COMMIT_MARKER`
- Trailer detection: lines matching `^[\w-]+: .+` after a blank line
- Bullet detection: lines matching `^\s*- .+`
- Uses `pathlib.Path` throughout

### 4. Write the commit-msg validation hook

**File**: `tools/scripts/validate_commit_msg.py`

A pre-commit hook (stage: `commit-msg`) that:
1. Reads the commit message file (passed as arg)
2. Validates Conventional Commits format on subject line (Tier 2)
3. Checks body has at least one `- ` bullet line (structured changelog entry)
4. For `refactor:`, `perf:`, `BREAKING CHANGE` — also validates ArchTag presence (Tier 3, per Production Git Workflow Standards)
5. Exits 1 with clear error message if validation fails
6. Skips merge commits and fixup commits

This implements the commit-msg validation envisioned in ADR-26003 without the external gitlint dependency — a single-purpose Python script following ADR-26001 (Python + OOP for hooks).

### 5. Write script documentation

**Files**:
- `tools/docs/scripts_instructions/generate_changelog_py_script.md` (+ `.ipynb` via jupytext)
- `tools/docs/scripts_instructions/validate_commit_msg_py_script.md` (+ `.ipynb` via jupytext)

Following existing doc pattern: purpose, usage, examples, contract.

### 6. Register in pre-commit config

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

### 7. Update CLAUDE.md

Add to "Commit Conventions" section:
- Commit bodies MUST contain structured bullets (per ADR-26024)
- Format: `- <Verb>: <target> — <description>`
- CHANGELOG is generated from commit history, not manually curated

## Files involved

| Action | File |
|--------|------|
| **Create** | `architecture/adr/adr_26024_structured_commit_bodies_for_automated_changelog.md` |
| **Create** | `tools/tests/test_generate_changelog.py` |
| **Create** | `tools/scripts/generate_changelog.py` |
| **Create** | `tools/tests/test_validate_commit_msg.py` |
| **Create** | `tools/scripts/validate_commit_msg.py` |
| **Create** | `tools/docs/scripts_instructions/generate_changelog_py_script.md` |
| **Create** | `tools/docs/scripts_instructions/validate_commit_msg_py_script.md` |
| **Edit** | `.pre-commit-config.yaml` — add commit-msg hook + test hook |
| **Edit** | `CLAUDE.md` — update commit conventions |

## Verification

1. `uv run pytest tools/tests/test_generate_changelog.py` — all tests pass
2. `uv run pytest tools/tests/test_validate_commit_msg.py` — all tests pass
3. `uv run tools/scripts/generate_changelog.py HEAD~5..HEAD` — generates output from recent commits
4. Manual: make a commit without body bullets → hook rejects it
5. Manual: make a commit with body bullets → hook passes, `generate_changelog.py` extracts them
6. `uv run tools/scripts/check_script_suite.py` — validates script+test+doc triplet
