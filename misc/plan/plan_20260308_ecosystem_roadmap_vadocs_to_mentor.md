---
title: "Ecosystem Roadmap: From vadocs Governance to Production Mentor Agent"
date: 2026-03-08
---

# Ecosystem Roadmap: vadocs to Production Mentor Agent

## Goal

A general-purpose local agent that runs skills for different tasks. The first complete application: a personalized AI learning mentor with RAG-backed knowledge, web research, and session continuity. Deployable from repo with `podman play kube` + API key.

## Dependency Chain

```
vadocs + vadocs-git (ecosystem governance)
  | validates docs in
ai_engineering_book (hub — ADRs, evidence, standards)
  | defines standards consumed by
mentor_generator (first OS application)
  | runs on
agent runtime (skill dispatcher + shared RAG)
  | uses
pgvector in Postgres (shared semantic memory, Podman pod via Kube YAML)
```

## Phase 1: Foundation (Governance Automation)

Order: Decide (ADRs) -> Implement (scripts in hub) -> Extract (ecosystem packages)

### 1.0 Compass Source Artifact ✅

Formalized as A-26009 in architecture/evidence/analyses/ (promoted from S-26007).
Also created S-26008 (LangChain vs production agents), S-26009 (pgvector RAG), S-26010 (stateless JIT), and analysis A-26006 extracting insights from all three.

### 1.05 Review ADRs 26031-26034 ✅

Proposed ADRs from the initial Agentic OS brainstorm. Valid concepts absorbed into ADR-26038 and subsequent ADRs.

| ADR | Action | Status |
|---|---|---|
| 26031 (namespaces) | Rejected | Problem real but string prefixes weaker than A-26005 Postgres namespace model |
| 26032 (tiered memory) | Kept proposed | Procedural vs declarative split orthogonal to ADR-26038; needs completion |
| 26033 (virtual monorepo) | Kept proposed | Valid independent problem (ecosystem repo interaction); needs completion |
| 26034 (skills as apps) | Rejected | Grand OS framing replaced by context engineering (ADR-26038); valid concepts acknowledged |

Also defined status transition rules in adr_config.yaml (proposed can only go to accepted/rejected, never superseded). Guide updated to reference config as SSoT. Script enforcement pending (see 1.2).

### 1.1 Strategic ADRs

In dependency order:

1. ADR-26038: Context Engineering as Core Principle ✅
   - Single-agent + skill dispatch
   - Context management is the product, not orchestration
   - Grounded in A-26009 (compass analysis)

2. ADR-26039: pgvector as Ecosystem Database Standard ✅
   - One Postgres for structured + vector data
   - Schema-per-project isolation
   - Deployment-agnostic (container or local package)
   - Shared across all ecosystem projects
   - Also created S-26011 (pgvector viability + logic locality) and A-26007 extracting insights

3. ADR-26040: Podman Kube YAML as Deployment Standard ✅
   - Kube YAML manifests as single deployment artifact
   - `podman-kube@.service` systemd template for lifecycle management
   - Rootless by default, orchestrator-independent (ADR-26009)

4. ADR-26041: Client-Side Logic with Server-Side Retrieval ✅
   - Logic-in-View pattern: Python owns orchestration, SQL functions own retrieval
   - LLM inference dominates latency — server-side logic advantage is negligible
   - Grounded in A-26007 (logic locality analysis) and existing postgres_connector module

5. ADR-26042: ← NEXT Common Frontmatter Standard
   - Composable block schema: identity (title, type), discovery (description, tags, token_size), lifecycle (date, birth, version)
   - Types compose blocks additively (DITA specialization principle) — no exclusions
   - 11 types registered: 10 content + 1 service. Sources skip lifecycle (ephemeral), service skips discovery+lifecycle
   - Auto-maintenance: date, birth, token_size by pre-commit hooks. version auto-validated
   - Jupytext two-block parsing: dual-block parser required for tutorial files
   - Grounded in A-26008 (taxonomy audit and composable block design) and A-26005 (VFS/inode model)
   - Resolves TD-001, supersedes ADR-26023 field placement

6. ADR-26043: Ecosystem Package Boundary
   - vadocs = doc content validation (frontmatter, sections, cross-refs, type registry)
   - vadocs-git = git policy governance (commit messages, branch naming, changelog)
   - vadocs init for repo scaffolding
   - Org-agnostic, configurable prefixes (no hardcoded values)

7. ADR-26044: Skills as Progressive Disclosure Units
   - Revise ADR-26034 with compass findings on SKILL.md convergence
   - MCP integration for tool connectivity
   - Single-agent emphasis

8. ADR-26045: Ephemeral File Lifecycle
   - Cleanup policy for sources, implemented plans, insights
   - check_ephemeral_files.py script
   - Maps to A-26005 RUNTIME doc types (/proc/, /var/spool/)

9. ADR-26046: Tech Debt Governance
   - Formalize tracking format, ownership, review cadence
   - Resolves TD-002

### 1.2 Implement Validation Scripts in Hub

Based on the ADRs:
- Common frontmatter validation (ADR-26040) in hub scripts
- Evidence type validators for new types from A-26005 taxonomy
- Git policy validators (commit msg, branch naming) — separate from doc validators
- Fix check_adr.py interactive input bug
- Fix generate_changelog.py excluded commits bug
- check_adr.py: enforce status transitions per adr_config.yaml status_transitions (proposed -> accepted/rejected only, no supersession of proposals)

### 1.3 Extract vadocs v0.2.0

Extract shared primitives from hub tools/scripts/ into vadocs:

Syscalls (kernel):
- parse_frontmatter(), extract_sections(), find_files()
- load_config(), ValidationError, report_errors()
- Common patterns across check_adr.py, check_evidence.py, check_broken_links.py

VFS (registry):
- DocumentTypeRegistry, common frontmatter schema, type resolution
- Based on ADR-26040

Validators (user space):
- ADR validator, Evidence validator, generic Frontmatter validator
- Existing vadocs v0.1.0 + check_evidence.py logic

Hub scripts become thin wrappers calling vadocs.

### 1.4 Extract vadocs-git v0.1.0

- validate_commit_msg.py -> vadocs-git
- generate_changelog.py -> vadocs-git
- check_script_suite.py -> vadocs-git
- Pre-commit hooks orchestrate both vadocs and vadocs-git

### 1.5 Install in Ecosystem

- mentor_generator installs vadocs + vadocs-git
- All three repos get pre-commit hooks using ecosystem packages

## Phase 2: Runtime (Agent + Infrastructure)

### 2.0 Research: Frontier CLI Agents

Analyze internals of aider, gemini-cli, qwen-code, claude-code:
- Architecture patterns
- Context management strategies
- Tool integration approaches
- What to leverage (like litellm from aider)

### 2.1 ADR: Skill Dispatcher Architecture

In mentor_generator, informed by 2.0 research:
- Skill registration and dispatch
- Shared context management (the "kernel")
- Tool integration via litellm tool_call / MCP

### 2.2 ADR: Context Window Management

Three scenarios the mentor must handle:
- (a) Context almost full -> summarize and continue (page fault -> swap)
- (b) User explicitly stops -> graceful save (SIGTERM)
- (c) Session goals complete -> fill session log template (exit(0))
Token counting via litellm.token_counter() per provider.

### 2.3 pgvector + Podman Pod

- Kube YAML manifest for Postgres + pgvector
- podman play kube for local deployment
- Schema for structured data + vector embeddings

### 2.4 RAG Indexer + Hybrid Retriever

- CLI command to index books/articles (PDF, EPUB, markdown)
- Hybrid search: pgvector similarity + tsvector keyword
- Exposed as a tool to the agent
- Embedding model configurable (local sentence-transformers or API)

### 2.5 Tool Integration

- litellm tool_call for LLM-native tool use
- MCP where appropriate for external services
- Web search tool

## Phase 3: Application (The Mentor)

### 3.1 Refactor Pipeline into Skills

Current mentor_generator pipeline becomes skills:
- collector.py -> Interview skill (questions as data, logic generic)
- creative_engine.py -> Generation skill (template + context -> filled output)
- validator.py + template_engine.py stay as pipeline infrastructure

### 3.2 Research Skill

- Web search + source analysis
- Reference list creation (10-15 foundational sources)
- Index sources to RAG (pgvector)
- Output: JSON with strict structure per template

### 3.3 Mentor Skill

- Dynamic config loaded as system prompt
- RAG-backed knowledge retrieval during learning sessions
- Course_history managed automatically (episodic memory)
- Context window management (three scenarios from 2.2)

### 3.4 End-to-End Flow

```
uv run python -m agent.main /start
  -> Interview skill (collect answers)
  -> Research skill (web search, build references, index to RAG)
  -> Generate skill (create mentor config)
  -> "Your mentor is ready. Start learning? [Y/n]"
  -> Mentor skill loads (dynamic config as system prompt)
  -> Learning session begins (RAG-backed, course_history managed)
```

## Key Technical Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Container runtime | Podman with Kube YAML manifests | Native tooling, rootless, no daemon |
| LLM connectivity | litellm | Any provider, single API (leveraged from aider) |
| Vector store | pgvector in Postgres | Ecosystem standard, one DB for structured + vector |
| Token counting | litellm.token_counter() | Provider-aware, already a dependency |
| Doc governance | vadocs + vadocs-git | UNIX philosophy, separate concerns, ecosystem plugins |
| Agent architecture | Single agent + skill dispatch | Compass evidence: single > multi-agent |
| Context strategy | Proactive management, three exit scenarios | OS process model (page fault, SIGTERM, exit(0)) |
