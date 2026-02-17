# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Engineering Book - a knowledge base for building production-grade AI systems using hybrid LLM+SLM methodology. Content is authored as MyST Markdown notebooks paired with Jupyter notebooks via Jupytext.

## Common Commands

```bash
# Restore environment from lock file
uv sync --frozen

# Sync notebooks after editing .md or .ipynb files
uv run jupytext --sync

# Run link validation tests
uv run pytest tools/tests/test_file.py --cov=tools.tests.test_file --cov-report=term-missing

# Check broken links in markdown files
uv run tools/scripts/check_broken_links.py --pattern "*.md"

# Validate all ADRs and auto-fix index
uv run tools/scripts/check_adr.py --fix

# Validate a commit message (used by commit-msg hook)
uv run tools/scripts/validate_commit_msg.py .git/COMMIT_EDITMSG

# Generate CHANGELOG from git history
uv run tools/scripts/generate_changelog.py

# Build documentation site
npm install -g mystmd && myst build --html
```

## Architecture

The repository is organized around a six-layer AI system architecture:

- `0_intro/` - Onboarding and foundational concepts (start with `00_onboarding.ipynb`)
- `ai_system/` - Core content organized by layer:
  - `1_execution/` - CPU/GPU optimization, VRAM/RAM management
  - `2_model/` - SLM selection, tokenization, embeddings
  - `3_prompts/` - Prompts-as-Infrastructure, includes JSON prompt files in `consultants/`
  - `4_orchestration/` - RAG, agent workflows, structured output
  - `5_context/` - Vector stores, hybrid retrieval
- `architecture/` - Architectural Decision Records (ADRs) and post-mortems
- `security/` - Centralized security policy hub
- `mlops/` - CI/CD and security tooling
- `tools/` - Scripts, tests, and configuration files

## Critical Conventions

When you implemented a plan in /plan mode, save it to misc/plan/plan_<YYYYMMDD>_<descriptive_slug>.md, ONLY then start implementation. After the plan is fully implemented, move it to misc/plan/implemented/. This is needed to save the history of the decisions made between context switches.

**MyST Notebooks:**
- Never convert `{code-cell}` blocks to standard markdown code blocks
- Always preserve MyST directive syntax exactly
- Notebooks (.ipynb) and markdown (.md) files are paired via Jupytext - editing one requires syncing
- **Always read `.md` files, never `.ipynb`** — `.ipynb` is JSON and expensive to parse; the `.md` Jupytext pair contains the same content

**Python:**
- Use `pathlib.Path`, never `os` library
- Follow top-down design: main function at the top

**Content Frontmatter (ADR-26023):**
- Use MyST-native fields: `title`, `author`, `date`, `options.version`, `options.birth`
- Author email: `rudakow.wadim@gmail.com` (not `lefthand67@gmail.com`)
- Docs already in production use version `1.0.0`+, not `0.x`

**Tool Configuration (ADR-26029):**
- Machine-readable tool config goes in `pyproject.toml [tool.X]` sections, loaded via `tomllib` (stdlib)
- Path constants stay in `tools/scripts/paths.py`; ADR validation rules stay in `adr_config.yaml`

**ADRs:**
- Never manually edit `architecture/adr_index.md` — run `uv run tools/scripts/check_adr.py --fix` to auto-update it
- `check_adr.py` operates on all ADRs at once (no file arguments)
- ADR frontmatter `status` determines index section placement (see `adr_config.yaml`)

**Configuration:**
- Use placeholders like `[IP_ADDRESS]` or `[DOMAIN]` instead of real values

## CI/CD Pipeline

Two GitHub Actions workflows:

1. **quality.yml** - Runs on all pushes/PRs:
   - Runs check_broken_links tests when script, tests, or `paths.py` change
   - Runs jupytext tests when sync/verify scripts, tests, or `paths.py` change
   - Validates links in changed `.md` files
2. **deploy.yml** - Validates notebook sync on all branches, deploys to GitHub Pages on main only

The pipeline verifies that .md and .ipynb pairs are synchronized before allowing deployment.

## Development Workflow

Jupytext sync runs as a pre-commit lint step. The `.aider.conf.yml` also configures auto-linting for Aider sessions.

Python version: 3.13+ (locked in `.python-version`)
Package manager: `uv` (never use pip directly)

**TDD Approach (Tests First):**
- **IMPORTANT: Always write tests FIRST, then implement the functionality to make them pass (Red → Green → Refactor)**
- For new features or refactoring: write failing tests first, then implement until tests pass
- Scripts require comprehensive test suites (e.g., prepare_prompt.py has 96 tests)
- Tests live in `tools/tests/` with `test_<script_name>.py` naming
- Run tests with `uv run pytest tools/tests/test_<script_name>.py`
- Pre-commit hooks automatically run relevant tests on commit

**Test Quality Standards (Non-Brittle Tests):**
- **Test contracts, not implementation**: Verify exit codes, return types, and side effects—not exact message strings or output formatting
- **Avoid asserting on specific wording**: Use `assert exit_code == 1` instead of `assert "specific error text" in output`
- **Test behavior boundaries**: One broken ref → exit 1, zero broken refs → exit 0. Don't test message content
- **Use semantic assertions**: `assert len(errors) > 0` or `assert adr_number in {found_numbers}` instead of exact counts when the exact count isn't the contract
- **Parameterize inputs**: Test varied scenarios (edge cases, empty inputs, multiple items) without duplicating test logic
- **Document the contract**: Each test class should have a docstring explaining what contract it verifies

**Commit Conventions (ADR-26024):**
- Use conventional commits with prefixes: `feat:`, `fix:`, `docs:`, `ci:`, `chore:`, `pr:`, `refactor:`, `perf:`, `test:`
- `pr:` prefix is for promotional/announcement posts
- Keep commit subjects concise (50 chars max), focusing on the "why"
- Commit bodies **MUST** contain structured bullets: `- <Verb>: \`<file-path>\` — <what/why>`
- `<file-path>` is relative to repo root, in backticks (e.g., `` `tools/scripts/check_adr.py` ``). No abstract targets — every change lives in a file
- One bullet = one line, no line length limit
- Verbs: `Created`, `Updated`, `Deleted`, `Renamed`, `Fixed`, `Moved`, `Added`, `Removed`, `Refactored`, `Configured`
- CHANGELOG is generated from commit history, not manually curated
- Merge policy: Squash-and-Merge (1 PR = 1 Commit on trunk)

**Pre-commit Hooks:**
- Extensive validation runs before each commit (see `.pre-commit-config.yaml`)
- Includes: broken links check, link format check, jupytext sync/verify, API key detection, JSON validation, script tests
- All hooks use `uv run` for Python execution

Script suite:
- Use architecture/adr/adr_26011_formalization_of_mandatory_script_suite.md convention when developing Python scripts.

## Telegram Channel Posts

Posts for the `@ai_learning` Telegram channel are stored in `misc/pr/tg_channel_ai_learning/`.

**Naming convention:** `YYYY_MM_DD_<topic_slug>.md`

**Language:** Russian

**Post structure:**
1. Bold headline
2. Problem statement (with 💡 icon)
3. Technical explanation (with 🧠 icon if applicable)
4. Solution description (with ⚙️ icon)
5. Key features list (with ✅ checkmarks)
6. Usage examples in code blocks
7. Documentation link
8. Hashtags (e.g., #Python #LLM #ai_engineering_handbook)
