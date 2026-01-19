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
uv run pytest tools/tests/test_check_broken_links.py

# Check broken links in markdown files
uv run tools/scripts/check_broken_links.py --pattern "*.md"

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

**MyST Notebooks:**
- Never convert `{code-cell}` blocks to standard markdown code blocks
- Always preserve MyST directive syntax exactly
- Notebooks (.ipynb) and markdown (.md) files are paired via Jupytext - editing one requires syncing

**Python:**
- Use `pathlib.Path`, never `os` library
- Follow top-down design: main function at the top

**Configuration:**
- Use placeholders like `[IP_ADDRESS]` or `[DOMAIN]` instead of real values

## CI/CD Pipeline

Two GitHub Actions workflows:

1. **quality.yml** - Runs on all pushes: pytest for link checker, validates changed .md files
2. **deploy.yml** - Validates notebook sync on all branches, deploys to server on main only

The pipeline verifies that .md and .ipynb pairs are synchronized before allowing deployment.

## Development Workflow

This project uses Aider as the primary AI editor with Jupytext sync as a lint step. The `.aider.conf.yml` configures auto-linting to run `uv run jupytext --sync` after edits.

Python version: 3.13+ (locked in `.python-version`)
Package manager: `uv` (never use pip directly)
