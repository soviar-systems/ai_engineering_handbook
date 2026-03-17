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

5. ADR-26042: Common Frontmatter Standard ✅
   - Composable block schema: identity (title, type, author), discovery (description, tags, token_size), lifecycle (date, birth, version)
   - MyST-native fields top-level, ecosystem fields under options.*
   - Types compose blocks additively (DITA specialization) — 10 types: 9 content + 1 service (manifesto absorbed into policy)
   - Hub-and-spoke config: frontmatter.config.yaml (hub) + domain configs (spokes) with strict additive inheritance
   - Will supersede ADR-26023 upon acceptance
   - Grounded in A-26008 (taxonomy audit and composable block design)

6. ADR-26043: Ecosystem Package Boundary ✅
   - vadocs as installable package organized by concern: core/, docs/, git/, init/, cli.py
   - All governance scripts inside vadocs (15 scripts), only prepare_prompt.py stays outside
   - CLI mirrors concern structure: `vadocs docs check-broken-links`, `vadocs git generate-changelog`
   - Hub-and-spoke config from ADR-26042, org-agnostic design (no hardcoded values)

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

10. ADR-26047: Git Three-Tier Validation Mechanics
    - Document adopted three-tier git validation (branch naming, commit format, ArchTag)
    - Branch naming (Tier 1) is the unimplemented gap
    - Target: vadocs-git plugin

11. ADR-26048: AI-Native Development Methodology — Code as Primary Documentation
    - Core thesis: in AI-native ecosystems, code structure IS the documentation layer — agents read code faster than prose
    - **Contract-in-code**: class docstrings capture guarantees and boundaries, not implementation steps. Method names are self-documenting. Pipeline-aware docs rot on refactor
    - **Test diagnostics for agents**: parametrize multi-case tests (pytest shows which input failed) instead of custom assertion messages. Assertion messages are documentation-in-implementation anti-pattern — they couple to intent the test name should convey
    - **Diagnostics hierarchy**: test name → pytest introspection → contract docstring. Custom messages only where failure mode is genuinely ambiguous
    - **Broader scope**: this shapes the entire ecosystem development workflow — how we write tests, document functions, structure modules so that agents can navigate and modify code with minimal context injection
    - Research questions: Do agents benefit from structured error codes in test output? Should test suites export machine-readable contract schemas? How does this interact with ADR-26042 (frontmatter as machine-readable metadata)?
    - Key insight: this is TDD optimized for agent consumers, not just TDD for humans. Three emerging principles:
      1. Names over messages — test method names are the primary diagnostic channel
      2. Parametrize over multiply-assert — pytest infrastructure provides the diagnostics, not hand-written strings
      3. Contracts over pipelines — docstrings describe what survives refactoring, not what breaks on refactoring
    - Connects to ADR-26038 (context engineering): if code structure is the documentation, context window budget is spent on code, not on redundant prose that paraphrases the code

### 1.12 DB Layer and Ecosystem Context ADRs

These ADRs formalise conventions that exist informally today. They were identified during
the un_votes/postgres_connector migration into soviar-systems (session 2026-03-18;
integration plan in `misc/plan/` or `misc/plan/implemented/` — plans are ephemeral).
ADR writing is deferred here to avoid number conflicts with 26044–26048 above.

**Prerequisites:** ADR-26039 (pgvector, schema-per-project) ✅

**Already completed (session 2026-03-18):**
- S-26012 created: adr_001 content preserved as evidence source. Title rule applied:
  no document-type keywords (ADR, RFC) in S-YYNNN titles — risk of confusing future
  tooling and search. Good: "Database Ecosystem Design Principles". Bad: "ADR-001: ...".
- `architecture_decision_workflow_guide.md` updated: Rule 4 added under Decision guidance —
  "Decide at capability level, not tool level. The tool is the current implementation of
  the requirement; it belongs in the Decision body, not as the decision itself."
- CLAUDE.md files for un_votes, postgres_connector, and root soviar-systems refactored
  ahead of ADR-26049 (principle is clear enough to act; see integration plan for content).
- `soviar-systems/adr_001_database_ecosystem_design_principles.md` deleted (preserved as S-26012).

**Cross-cutting rule established in session 2026-03-18:**
S-YYNNN sources MUST be cited by ID in prose only ("...captured in source S-26012"),
never as markdown links. After the three-commit deletion, the link would fail
`check_broken_links.py`.

In dependency order:

12. ADR-26049: Ecosystem Context Distribution
    - **Core decision:** two-tier CLAUDE.md architecture.
    - Tier 1 — Project CLAUDE.md (self-sufficient): must work when cloned standalone with
      no `soviar-systems/` parent. Mandatory sections:
      - `## Governing Ecosystem Rules` (immediately after `## Project Overview`): inline
        rule summaries, never links. Categories: commit format (ADR-26024), package manager
        (uv only), containers (ADR-26040), safe git commands, plan management, contract
        docstrings, TDD + non-brittle tests, SVA check (ADR-26037). DB projects additionally
        include: psycopg/postgres_connector mandate, schema namespacing, logging, secrets.
      - `## Ecosystem ADR Index`: stable hub URL (GitHub Pages via ADR-26022) for deep
        architectural lookup only.
    - Tier 2 — Root `soviar-systems/CLAUDE.md` (local convenience only): universal rules
      that appear in every project file anyway. Header:
      `<!-- Local convenience layer — NOT authoritative per ADR-26049. Each repo's CLAUDE.md is the canonical source. -->`
    - Propagation: when a hub ADR is accepted and changes an agent-operational rule, the
      ADR author updates all affected project CLAUDE.md files in the same PR. Structured
      commit body (ADR-26024) lists every CLAUDE.md touched — this is the audit trail.
    - References: ADR-26020, ADR-26033, ADR-26038, ADR-26037, ADR-26043, ADR-26024, ADR-26040.

13. ADR-26050: Safe Database Communication from Python
    - **Framing (critical):** the decision is the PRINCIPLE — safe parameterised query
      construction — not the specific driver. psycopg 3 + postgres_connector are the
      current implementation of that principle. A reader 3 years from now should be able
      to judge whether the principle still holds even if the tools changed.
    - Current driver: psycopg 3; shared access layer: `postgres_connector` (PyPI dep).
    - Why combined in one ADR: postgres_connector is the mechanism that enforces the
      driver's safety discipline uniformly across projects. The driver rule is meaningless
      without the shared library; the shared library is meaningless without knowing which
      driver discipline it enforces. They can still be independently superseded.
    - **asyncpg:** satisfies the same safety principle (parameterised by design, not
      bolt-on). Currently constrained by lack of sync API for sync pipeline workloads.
      NOT rejected — requires A-260NN trade study comparing asyncpg vs psycopg 3 across
      actual workload mix. This is the promotion gate for proposed → accepted.
    - **Mandatory alternatives section:** asyncpg (open, needs trade study), direct psycopg
      without shared library (rejected: inconsistent discipline), Django ORM (rejected:
      SVA disproportionality), ODBC (rejected: PostgreSQL-only ecosystem).
    - Supersedes: source S-26012.

14. ADR-26051: PostgreSQL Schema Namespacing
    - Each project stores data in its own PostgreSQL schema (not `public`).
    - Schema name via `DB_SCHEMA` env var in `info.py`; project-specific default.
    - All SQL uses two-part `sql.Identifier(schema, table)` — never bare identifiers.
    - `ensure_schema()` creates schema before any table DDL.
    - Complements ADR-26039 (schema-per-project already established for pgvector context).

15. ADR-26052: Python Logging Standard
    - `logging.getLogger(__name__)` in all modules; `print()` prohibited in production code.
    - Scope: ALL ecosystem Python projects, not DB-only.
    - Log level conventions: DEBUG (per-row/trace), INFO (milestones), WARNING (recoverable
      unexpected state), ERROR (failures requiring attention).

16. ADR-26053: Secrets Management Standard
    - Production secrets MUST be managed via a dedicated secrets management tool.
    - Current tool: Ansible Vault (docs at `misc/in_progress/security/password_management/`).
    - `pexpect` is a symptom of missing secrets management — prohibition follows from this ADR.
    - No credentials in committed env files; CLI tools receive secrets via env vars injected
      by the secrets manager at runtime.
    - **Promotion gate:** `misc/in_progress/security/password_management/` docs must be
      finalised and promoted to governed content before this ADR can be accepted.

**postgres_connector current state (relevant for ADR authoring):**
- No `CLAUDE.md` — created in session 2026-03-18 per ADR-26049 principle.
- No `architecture/` directory — create `architecture/adr/` when writing spoke ADRs.
- Spoke ADR for schema definition format (`_is_constraint()`, tuple format,
  `create_attributes_dict()`) goes in `postgres_connector/architecture/adr/`. Number
  within the package's own namespace (e.g. `adr_001_schema_definition_format.md`).
- Source S-26012 contains the full original content for reference during ADR authoring.

### 1.15 ADR-26042 Migration

Two-phase automated migration implementing ADR-26042:

**Phase A — ADR semantic fix (one-shot script):**
- For each of 41 ADRs: copy current `date` to `options.birth`, set `date` to git last-modified date
- Add `options.type: adr`, `options.token_size` (computed from content)
- Set `description` to `TODO` placeholder for human review
- Priority: `date` semantics are wrong until this runs

**Phase B — All other governed files (auto-fix script):**
- Analogous to `check_adr.py --fix` maintaining `adr_index.md`
- Scan governed directories, detect missing fields per `frontmatter.config.yaml` type registry
- Auto-add: `options.type` (inferred from directory), `options.token_size` (computed), `options.birth` (git log), `date` (git log)
- Human fields (`description`, `tags`): set `TODO` placeholders
- Rename `adr_config.yaml` → `adr.config.yaml` (dot-separated naming consistency)
- Create `frontmatter.config.yaml` hub config referenced from `pyproject.toml [tool.frontmatter]`
- Migrate `common_required_fields` from `evidence.config.yaml` to hub (resolves TD-001)

### 1.2 Implement Validation Scripts in Hub

Based on the ADRs:
- Common frontmatter validation (ADR-26042) in hub scripts
- Evidence type validators for new types from A-26005 taxonomy
- Git policy validators (commit msg, branch naming) — separate from doc validators
- Fix check_adr.py interactive input bug
- Fix generate_changelog.py excluded commits bug
- check_adr.py: enforce status transitions per adr.config.yaml status_transitions (proposed -> accepted/rejected only, no supersession of proposals)

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

### 2.05 Research: Skills vs Subagents — Architectural Boundary

**Problem**: ADR-26038 defines skills as "injected instructions, not sub-agents." But production tools (Claude Code, aider) use subagent patterns — child processes with their own LLM calls forked from the parent agent. This creates an unresolved tension:

- **Injected instructions** (ADR-26038 position): skill loads into the main conversation as context, one LLM loop, no context isolation. Progressive disclosure controls token budget
- **Forked subagents** (Claude Code pattern): parent spawns a child process with a subset of context, child returns a result, parent integrates. Multiple LLM loops, but orchestrated by a single parent — NOT a multi-agent swarm
- **Multi-agent swarms** (AutoGen, CrewAI): independent agents negotiating with each other, context isolation between them, 25% correctness floor (UC Berkeley MAST)

**Key questions**:
- Is the Claude Code subagent pattern a controlled fork-and-join within single-agent architecture, or a multi-agent system?
- When should a skill be injected instructions vs a forked subagent? What's the decision boundary?
- Agent swarms are gaining popularity (2026 hype cycle) — is there a real use case beyond the hype, or does the evidence consistently show single-agent superiority?
- How does this interact with MCP tool servers — is an MCP server a subagent, a tool, or something else?

**Output**: Analysis (A-YYNNN) grounding the distinction, potentially a new ADR clarifying the skill/subagent boundary for the ecosystem

### 2.1 ADR: Skill Dispatcher Architecture

In mentor_generator, informed by 2.0 and 2.05 research:
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
