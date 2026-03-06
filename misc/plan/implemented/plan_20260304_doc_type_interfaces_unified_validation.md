# Analysis: Documentation Type Interfaces and Unified Validation Architecture

## Context

This analysis addresses the unfinished architecture directory restructuring (ADR-26035) and the deeper question it surfaces: how should documentation types be formally classified, what interfaces should govern them, and how should validation scripts be refactored around those interfaces — across this repo and the entire ecosystem.

The user has questions, not answers. This document synthesizes codebase exploration, industry research, and architectural reasoning to provide the analytical foundation for future ADRs.

---

## Part 1: Architecture Directory Status (ADR-26035)

### Current State: ~85% Complete

The Conceptual Taxonomy from ADR-26035 is implemented:

```
Architecture Knowledge Base
├── Decisions        → ADRs (binding constraints)         ✅ 36+ ADRs
├── Evidence
│   ├── Prospective  → Analyses (A-YYNNN)                ✅ 4 artifacts
│   ├── Retrospective→ Post-mortems (R-YYNNN)            ✅ directory exists, empty
│   └── Sources      → Dialogues (S-YYNNN)              ⚠️  3 formal + 3 orphans
└── Governance       → Manifesto, guides, config          ✅ workflow guide v1.0.0
```

### Remaining Gaps

1. **Orphaned sources**: `gemini_3_flash_semantic_alignment.md`, `qwen-3.5-plus-Conceptual-Architecture-Diagram.txt`, `test.html` lack S-YYNNN naming and frontmatter
2. **ADR-26035 is still "proposed"** — the taxonomy governing the taxonomy is not yet accepted
3. **Legacy `post-mortems/`** not integrated into `evidence/retrospective/`
4. **No retrospectives exist yet** — the R-YYNNN pipeline is untested

### Verdict

The physical structure is sound. The remaining work is operational cleanup, not architectural redesign. However, this cleanup reveals the deeper problem: there is no uniform interface that defines what "a document type" is across the repo. ADRs have one schema. Evidence has another. Notebooks have a third. Script docs have a fourth. This is the real question.

---

## Part 2: The Documentation Landscape — What Exists Today

### Current Document Types (Discovered)

| # | Type | Location | Frontmatter Schema | Validation Script | Sections Schema | Tags |
|---|------|----------|-------------------|-------------------|-----------------|------|
| 1 | ADR | `architecture/adr/` | id, title, date, status, tags | `check_adr.py` | 8 required + conditional | from config |
| 2 | Analysis | `evidence/analyses/` | id, title, date, status, tags, sources, produces | `check_evidence.py` | 2 required + 6 optional | from parent config |
| 3 | Retrospective | `evidence/retrospective/` | id, title, date, status, severity, tags, produces | `check_evidence.py` | 2 required + 7 optional | from parent config |
| 4 | Source | `evidence/sources/` | id, title, date, model, extracted_into | `check_evidence.py` | none (freeform) | none |
| 5 | Notebook (content) | `ai_system/*/` | Jupytext + Owner, Version, Birth, Modified | `jupytext_sync/verify` | none | none |
| 6 | Script Instruction | `tools/docs/scripts_instructions/` | Jupytext + Owner, Version, Birth, Modified | `check_script_suite.py` (existence only) | none | none |
| 7 | Git Workflow Guide | `tools/docs/git/` | Jupytext + Owner, Version, Birth, Modified | none (only link checks) | none | none |
| 8 | Manifesto | `architecture/` | title, author, date, version, birth | none | none | none |
| 9 | Telegram Post | `misc/pr/tg_channel_ai_learning/` | none | none | none | hashtags (inline) |
| 10 | Plan | `misc/plan/` | none | none | none | none |
| 11 | Tech Debt Register | `misc/plan/techdebt.md` | none | none | none | none |
| 12 | Package Spec | `architecture/packages/` | none | none | none | none |
| 13 | Prompt (JSON) | `ai_system/3_prompts/consultants/` | JSON structure | `check_json_files.py` (syntax only) | none | none |

### Key Observation

Only types 1-4 have formal interfaces (schema + validation + lifecycle). Types 5-6 have partial interfaces (Jupytext enforcement + naming convention). Types 7-13 are **untyped** — they exist by convention, not by contract.

This is the "Architectural Orphanage" problem from A-26002: documents that exist outside of governed decision-making.

---

## Part 3: Industry Research — How the World Classifies Documents

### The Convergent Taxonomy

Across DITA (OASIS), Diataxis, ISO 26514, Google, and GitLab CTRT, a stable set of 4-6 base types emerges:

| Semantic Role | DITA | Diataxis | ISO 26514 | Google | GitLab CTRT |
|--------------|------|----------|-----------|--------|-------------|
| "What is it?" | Concept | Explanation | Conceptual | Conceptual | Concept |
| "How do I do it?" | Task | How-to Guide | Instructional | — | Task |
| "Teach me from scratch" | — | Tutorial | — | Tutorial | Tutorial |
| "Look it up" | Reference | Reference | Reference | Reference | Reference |
| "Fix a problem" | Troubleshooting | — | Troubleshooting | — | Troubleshooting |
| "Why was this decided?" | — | — | — | Design Doc | — |

**The "Design Doc" gap**: None of the standard taxonomies have a first-class type for architectural decisions. ADRs are a software engineering innovation (Michael Nygard, 2011) that predates these frameworks' current versions. This repo's ADR system fills a genuine gap.

### DITA Specialization: The Interface Model

DITA is the most relevant precedent because it implements **document type inheritance** — exactly the "interface" concept the user is exploring:

```
topic (base type — abstract interface)
├── concept (extends topic — adds conbody)
├── task (extends topic — adds steps, prerequisites)
├── reference (extends topic — adds tables, parameter lists)
└── troubleshooting (extends topic — adds cause, remedy)
```

Key properties of DITA specialization:
- **Schema-validated**: Each type has a DTD/RELAX NG schema that enforces structure
- **Extensible**: Organizations create custom types that inherit from base types
- **Constraint modules**: Can restrict base types without breaking the contract (narrowing, not widening)
- **Processing inheritance**: A processor that handles `topic` automatically handles all its specializations

**The lesson for vadocs**: DITA proves that typed documentation with formal interfaces is production-viable at enterprise scale (IBM, SAP, Cisco). But DITA's XML toolchain is antithetical to Markdown-native docs-as-code. The opportunity is to bring DITA's conceptual model (typed topics with schema validation) into a Markdown/YAML world.

### Modern Type Systems for Markdown Content

Three tools implement "document type interfaces" in Markdown:

| Tool | Schema Language | Validates | Status |
|------|----------------|-----------|--------|
| **Astro Content Collections** | Zod (TypeScript) | Frontmatter | Production-ready |
| **Contentlayer** | JS config | Frontmatter + routing | Stalled (2023) |
| **mdschema** | YAML | Body structure (sections, headings) | Early stage |

Astro Content Collections is the most mature:

```typescript
const adr = defineCollection({
  schema: z.object({
    title: z.string(),
    status: z.enum(['proposed', 'accepted', 'rejected', 'superseded', 'deprecated']),
    tags: z.array(z.string()),
    date: z.coerce.date(),
  }),
});
```

**The lesson**: Zod-style schemas for frontmatter validation are the industry direction. Our `check_adr.py` and `check_evidence.py` already do this — but in Python/YAML instead of TypeScript/Zod, and without a shared abstraction.

### AI-Native Documentation Standards

Two emerging standards address AI consumption directly:

1. **`llms.txt`** (Jeremy Howard, 2024) — A discovery interface for AI agents. A structured Markdown file at site root listing all content with descriptions. Adopted by Anthropic, Google (A2A), Mintlify.

2. **`skill.md`** (Mintlify) — A capability manifest telling agents what a product/system can do.

Both validate the manifesto's core thesis: documentation is not just for humans anymore, and AI consumers need machine-readable metadata to filter before they read.

### Metadata for RAG Filtering

Research on production RAG systems converges on these critical metadata fields:

- `document_type` — enables query-type routing ("teach me" → tutorial, "look up" → reference)
- `status` / `lifecycle_stage` — filters out deprecated/draft content
- `tags` — controlled vocabulary for domain classification
- `date` / `last_updated` — recency filtering
- `audience` — skill-level routing
- `description` — compact summary for Level 1 discovery (the Progressive Disclosure pattern from A-26002)

**Dublin Core** (ISO 15836) provides a standardized 15-element metadata set. **Schema.org** provides `TechArticle`, `HowTo`, `LearningResource` types. Both are relevant as reference vocabularies, though neither is directly usable as a validation schema.

---

## Part 4: The Common Kernel — What Validation Scripts Share

### Factual Duplication Analysis

The exploration identified **six shared patterns** duplicated across 2+ scripts:

| Pattern | Scripts Using It | Estimated Duplication |
|---------|-----------------|----------------------|
| **Frontmatter Parsing** (regex + YAML) | `check_adr.py`, `check_evidence.py` | ~15 LOC × 2 |
| **Section Extraction** (code fence removal + heading regex) | `check_adr.py`, `check_evidence.py` | ~10 LOC × 2 |
| **File Discovery** (rglob + exclusion filtering) | `check_broken_links.py`, `check_link_format.py`, `check_json_files.py` | ~40 LOC × 3 |
| **Config Loading** (repo root → pyproject.toml → YAML) | `check_adr.py`, `check_evidence.py`, `validate_commit_msg.py` | ~25 LOC × 3 |
| **Git Client** (root, staged files, renamed files) | `check_adr.py`, `check_evidence.py`, `check_link_format.py`, `check_script_suite.py` | ~20 LOC × 4 |
| **CLI / Error Reporting** (argparse + exit codes) | All 10 scripts | ~30 LOC × 10 |

### What Should NOT Be Extracted

Per UNIX philosophy and SVA (ADR-26037): extraction is only justified when the duplication causes **maintenance pain** or **behavioral inconsistency**. Single-use utilities, even if structurally similar, should remain inline if they serve a single script.

### The Extraction Boundary

The natural extraction boundary aligns with the UNIX syscall analogy:

```
┌─────────────────────────────────────────────────────┐
│                  Document Type Scripts               │
│  (check_adr.py, check_evidence.py, future types)    │
│  ─ Type-specific validation rules                    │
│  ─ Type-specific fixers                              │
│  ─ Type-specific CLI flags                           │
├─────────────────────────────────────────────────────┤
│                   "Syscall" Layer                     │
│  (shared modules — the vadocs kernel)                │
│  ─ parse_frontmatter(content) → dict                 │
│  ─ extract_sections(content) → list[str]             │
│  ─ find_files(root, pattern, excludes) → list[Path]  │
│  ─ load_config(tool_name) → dict                     │
│  ─ get_repo_root() → Path                            │
│  ─ get_staged_files() → set[str]                     │
│  ─ ValidationError dataclass                         │
│  ─ report_errors(errors) → exit_code                 │
├─────────────────────────────────────────────────────┤
│                   Infrastructure                     │
│  (stdlib: pathlib, tomllib, yaml, re, subprocess)    │
└─────────────────────────────────────────────────────┘
```

This is the vadocs kernel. Each document type script is an "application" that calls these syscalls.

---

## Part 5: The Interface Design — Documentation Types as Contracts

### The UNIX Analogy, Elaborated

In UNIX:
- **Syscalls** are the stable interface (open, read, write, close)
- **File types** are distinguished by the kernel (regular, directory, socket, pipe)
- **Applications** operate on files through syscalls without knowing internal details
- **New file types** can be added without changing applications (via the VFS layer)

Translating to documentation:

| UNIX Concept | Docs-as-Code Equivalent |
|-------------|------------------------|
| Syscall | Validation primitive (parse_frontmatter, extract_sections, validate_field) |
| File type | Document type (ADR, Analysis, Tutorial, Reference, etc.) |
| VFS (Virtual File System) | Document Type Registry — maps types to their schemas and validators |
| inode metadata | YAML frontmatter — the machine-readable header every document carries |
| File permissions | Document lifecycle (status field controls what operations are valid) |
| Mount point | Directory convention — where a type's files live in the repo tree |

### The Document Type Interface

Every document type in the ecosystem would implement this contract:

```yaml
# Conceptual interface — each type defines:
document_type:
  name: "adr"                          # Type identifier (used in frontmatter, tags, routing)
  directory: "architecture/adr/"       # Where files of this type live
  naming_pattern: "^adr_\\d{5}_.*\\.md$"  # Filename regex

  frontmatter:                         # Required/optional YAML fields
    required: [id, title, date, status, tags]
    optional: [superseded_by]
    controlled_vocabularies:
      status: [proposed, accepted, rejected, superseded, deprecated]
      tags: "@parent_config:tags"      # Pointer to shared vocabulary

  sections:                            # Required/optional ## headings
    required: [Context, Decision, Consequences, Alternatives, References, Participants]
    conditional:
      rejected: [Rejection Rationale]

  lifecycle:                           # Status transitions + cleanup rules
    promotion_path: proposed → accepted
    terminal_states: [rejected, superseded, deprecated]
    cleanup_policy: preserve           # vs. "ephemeral" for sources

  validation_script: "check_adr.py"    # The "application" that enforces this contract
  config_file: "adr_config.yaml"       # SSoT for this type's rules
```

### The Proposed Taxonomy

Combining industry research with the repo's existing doc types, here is a proposed unified taxonomy. The left column shows the **semantic role** (from Diataxis/DITA/ISO convergence), the right shows how this repo's existing types map:

```
Document Type Taxonomy
├── GOVERNANCE (decisions and principles — unique to this ecosystem)
│   ├── adr              — Architectural Decision Record
│   ├── manifesto         — Declaration of principles (singleton)
│   └── policy            — Enforceable rules (security policy, git policy)
│
├── EVIDENCE (research artifacts — the ADR-26035 taxonomy)
│   ├── analysis          — Prospective trade study (A-YYNNN)
│   ├── retrospective     — Post-mortem / failure analysis (R-YYNNN)
│   └── source            — Ephemeral dialogue transcript (S-YYNNN)
│
├── LEARNING (human-oriented educational content)
│   ├── tutorial          — Guided walkthrough for beginners (ai_system notebooks)
│   ├── handbook          — Comprehensive reference + explanation hybrid
│   └── guide             — How-to for a specific workflow (git guides, workflow docs)
│
├── REFERENCE (lookup material)
│   ├── script_instruction — How to use a specific tool (tools/docs/scripts_instructions)
│   ├── api_reference      — Auto-generated or structured API docs
│   └── index              — Auto-generated navigation (adr_index.md)
│
├── OPERATIONAL (project management — ephemeral by nature)
│   ├── plan               — Implementation plan (misc/plan/)
│   ├── tech_debt          — Intentional shortcuts register
│   ├── changelog          — Auto-generated release history
│   └── release_notes      — Curated release summary
│
└── PROMOTIONAL (external communication)
    └── announcement       — Telegram/blog posts (misc/pr/)
```

### How Types Relate to the Agentic OS

From the Qwen source and A-26002, the Agentic OS maps:
- **LLM = Processor** — consumes documents as input tokens
- **Agent = OS** — routes queries to the right document type
- **Skills = Apps** — domain expertise packaged as typed documents

The document type taxonomy directly enables the agent's routing:

| Agent Query Intent | Route To Type | Metadata Filter |
|-------------------|---------------|-----------------|
| "What was decided about X?" | `adr` | status: accepted |
| "Why did we reject Y?" | `adr` | status: rejected |
| "How do I use tool Z?" | `script_instruction` | — |
| "Teach me about embeddings" | `tutorial` | tags: model |
| "What went wrong with incident W?" | `retrospective` | severity: high |
| "What are we researching?" | `analysis` | status: active |

This is the Progressive Disclosure pattern (A-26002, Level 1): the agent reads frontmatter `type` + `tags` + `description` fields to decide whether to load the full document — saving tokens.

### Tags: The Cross-Cutting Classification

Tags are orthogonal to types. A type defines *what kind of document* it is; tags define *what domain* it belongs to.

Current tag vocabulary (11 values from `architecture.config.yaml`): `architecture`, `ci`, `context_management`, `devops`, `documentation`, `git`, `governance`, `hardware`, `model`, `security`, `testing`, `workflow`.

**Gap**: These tags are architecture-centric. They don't cover the ai_system content layers. A unified tag vocabulary should include:

```yaml
# Domain tags (what the document is about)
domain_tags:
  # Infrastructure
  - architecture
  - ci
  - devops
  - git
  - security
  - hardware

  # AI System layers (mirrors directory structure)
  - execution       # Layer 1
  - model            # Layer 2
  - prompts          # Layer 3
  - orchestration    # Layer 4
  - context          # Layer 5

  # Cross-cutting
  - documentation
  - governance
  - testing
  - workflow
  - context_management
```

Tags would live in a single SSoT (`architecture.config.yaml` or a new repo-level `docs.config.yaml`) and be validated by any type-specific script via `parent_config` pointer.

---

## Part 6: The vadocs Evolution Path

### Current vadocs Scope (from `architecture/packages/vadocs.md`)

vadocs v0.1.0 is a library-only PoC with:
- `Document` model (path, content, frontmatter, doc_type)
- `ValidationError` model
- `Validator` protocol (validate + supports)
- `Fixer` protocol (fix + supports)
- `FrontmatterValidator`, `AdrValidator`, `AdrTermValidator`
- Config loading from YAML

### The Question: What Should vadocs Become?

The user identified a tension:

> "vadocs looks good because it governs the docs validation and these git scripts also are the validation gates for the docs so I can control the process from within one package. vadocs looks not a good choice because git operations, hooks, and CI are specific operations with their own goals."

This tension is resolved by the UNIX analogy:

**vadocs = the documentation kernel** (syscalls for document validation)
**Git validation = a separate package** (uses git-specific tools)
**Pre-commit hooks = the shell** (orchestrates both)

The boundary: **vadocs validates document content** (frontmatter, sections, cross-references). It does NOT validate git operations (commit messages, branch naming, staging rules). Git is a delivery mechanism, not a document property.

### vadocs as the Interface Registry

The key evolution: vadocs should own the **Document Type Registry** — the central definition of what types exist and what contracts they enforce. This registry is the "VFS layer":

```python
# Conceptual: vadocs type registry
class DocumentTypeRegistry:
    """The VFS layer — maps doc_type to its schema and validators."""

    def register(self, type_def: DocumentTypeDefinition) -> None: ...
    def resolve_type(self, path: Path, frontmatter: dict) -> str: ...
    def get_validators(self, doc_type: str) -> list[Validator]: ...
    def get_schema(self, doc_type: str) -> FrontmatterSchema: ...
```

Each repo configures its types via YAML:

```yaml
# docs.config.yaml (repo-level)
document_types:
  adr:
    config: architecture/adr/adr_config.yaml
  evidence:
    config: architecture/evidence/evidence.config.yaml
  tutorial:
    config: ai_system/content.config.yaml
  # ... etc
```

This is the **uniform design** for any new repo: install vadocs, define your types in `docs.config.yaml`, and the validation pipeline works.

---

## Part 7: The Gemini Source — Semantic Alignment Assessment

The `gemini_3_flash_semantic_alignment.md` source provides an external validation of the system's architectural integrity, with two critical findings:

### Finding 1: WRC Drop from 0.91 to 0.71 in Agent-Led Development

The source calculates that the Documentation-as-Code methodology drops from "Production-Ready" (WRC 0.91) to "Production-Adaptable" (WRC 0.71) when developed primarily by an AI agent, due to:
- **C1 Vendor Lock-in**: High dependency on Claude-specific formatting (-0.10)
- **C5 Scalability**: Context window exhaustion as repo grows (-0.10)

**Relevance to this analysis**: This validates the need for **agent-agnostic interfaces**. The document type system should be defined in YAML configs (machine-readable by any agent), not in CLAUDE.md instructions (Claude-specific).

### Finding 2: Contract-First Agentic Development (WRC 0.92)

The source recommends "Contract-First Agentic Dev" — strict enforcement of schemas before code generation. This is exactly what the Document Type Interface system provides: a formal contract that any agent (Claude, Gemini, local SLM) can validate against.

### Finding 3: Semantic Linting

The source proposes `check_semantic_alignment.py` — using a local SLM to verify code changes against ADR constraints. This is a future evolution beyond structural validation (does the document have the right sections?) toward semantic validation (does the content align with the governing ADR?).

**Assessment**: Semantic linting is Stage 2. Stage 1 (this analysis) is getting the structural type system right. Without a formal type registry, semantic linting has no stable surface to validate against.

---

## Part 8: The Qwen Source — Agentic OS Architecture Diagram

The `qwen-3.5-plus-Conceptual-Architecture-Diagram.txt` source provides the UNIX ↔ Agentic OS mapping table that grounds the interface analogy:

| UNIX/Linux Concept | Agentic OS Equivalent |
|---|---|
| System Calls (open, read, write) | Tool Invocations |
| User Space Processes | Skills / Plugins |
| Memory Management (VM/Paging) | Context Window Management |
| File System | Knowledge Base / Vector Store |
| Permissions (UID/GID) | Policy & Safety Guards |
| Kernel Modules (LKM) | Dynamic Skill Loading |

**The missing row**: The source doesn't map **file types** (regular, directory, socket) to the Agentic OS. This is the gap this analysis fills:

| UNIX Concept | Agentic OS Equivalent |
|---|---|
| **File types** (regular, dir, socket, pipe) | **Document types** (adr, tutorial, reference, analysis) |
| **VFS** (Virtual File System) | **Document Type Registry** (vadocs) |
| **inode metadata** | **YAML frontmatter** |
| **`stat()` syscall** | **`parse_frontmatter()`** |
| **`file` command** | **`resolve_type(path, frontmatter)`** |

---

## Part 9: Open Questions

### Q1: Should frontmatter be unified across all doc types?

**Current state**: ADRs use `id, title, date, status, tags`. Notebooks use `Owner, Version, Birth, Last Modified` (non-YAML, inline). Evidence uses `id, title, date` + type-specific fields. Most other types have no frontmatter.

**TD-001** already identifies this as tech debt: `common_required_fields` in `evidence.config.yaml` should be repo-wide.

**Options**:

A. **Minimal common core** — all docs get `title`, `date`, `type`, `tags`, `version`. Type-specific fields extend this core. Least disruption, but requires migrating all existing docs.

B. **Two-tier standard** — governed docs (ADRs, evidence, tutorials) get full frontmatter with lifecycle; unstructured docs (plans, posts, misc) remain freeform. Pragmatic, but creates a permanent second class.

C. **Full uniformity** — every `.md` file in the repo gets typed frontmatter. Maximum AI-readability, but high migration cost and maintenance burden for ephemeral content.

**Recommendation direction**: Option A with lazy migration (ADR-26023 pattern). Define the core, enforce on new files, migrate existing files opportunistically.

### Q2: Where should the type registry config live?

**Options**:
- `pyproject.toml [tool.vadocs]` — consistent with existing pattern, but pyproject.toml is getting large
- `docs.config.yaml` (repo root) — dedicated config, clean separation
- `architecture/docs.config.yaml` — groups with architectural configs

**Recommendation direction**: `pyproject.toml [tool.vadocs]` pointing to `docs.config.yaml` at repo root (mirrors the `[tool.check-adr]` → `adr_config.yaml` pattern).

### Q3: Should vadocs validate ALL doc types or only "governed" types?

Plans, telegram posts, and misc files are inherently ephemeral. Forcing frontmatter on them creates friction without value. The type system should distinguish:

- **Governed types** — validated by vadocs (ADRs, evidence, tutorials, script docs)
- **Convention types** — naming convention only, no content validation (plans, posts)
- **Untyped** — anything in `misc/` or scratch areas

### Q4: How does this relate to hub-spoke ecosystem?

vadocs as a package is installed in every spoke repo. The type registry must be:
- **Portable** — same interface works in `ai_engineering_book`, `mentor_generator`, `vadocs` itself
- **Configurable** — each repo defines which types it uses and their specific rules
- **Extensible** — a spoke can define custom types without modifying vadocs

This means vadocs provides **base type definitions** (like DITA's base `topic`) and repos **specialize** them (like DITA's specialization).

### Q5: How do tags unify across git policy, ADRs, skills, and RAG?

The tag vocabulary serves multiple consumers:
- **Git policy**: commit prefixes (`feat:`, `docs:`, `arch:`) already classify changes by domain
- **ADRs/Evidence**: `tags` field in frontmatter, validated against config
- **Skills**: `tags` field in SKILL.md frontmatter, used for progressive disclosure filtering
- **RAG**: metadata filters on vector store queries

A unified tag vocabulary would mean the same tag `model` used in an ADR, a commit, a skill, and a RAG query all refer to the same domain. This requires a single SSoT (likely `architecture.config.yaml` or a repo-level `tags.yaml`) consumed by all validation scripts and the RAG indexer.

**Open sub-question**: Should commit type prefixes (`feat`, `docs`, `arch`) and domain tags (`model`, `security`, `ci`) be formally related? Currently they're independent vocabularies.

---

## Part 10: Synthesis — The Path Forward

### The Big Picture

```
Industry Standard          This Repo Today              Target State
─────────────────          ──────────────────           ─────────────────
DITA specialization   →    ad-hoc per-script schemas  → vadocs Type Registry
Astro/Zod schemas     →    Python/YAML validation     → YAML type definitions
Dublin Core metadata  →    inconsistent frontmatter   → unified core frontmatter
llms.txt / skill.md   →    CLAUDE.md (agent-specific) → agent-agnostic type metadata
Diataxis taxonomy     →    implicit directory-based   → explicit type field + taxonomy
```

### What This Analysis Produces

This analysis does NOT produce a plan. It produces:

1. **A vocabulary** — the document type taxonomy (Part 5)
2. **A conceptual model** — the UNIX interface analogy (Parts 4, 5, 8)
3. **A gap analysis** — what exists vs. what's needed (Parts 2, 3)
4. **Open questions** — requiring human judgment (Part 9)
5. **An industry benchmark** — what mature systems look like (Part 3)

### Recommended Next Steps (for future sessions)

1. **ADR**: Formalize the Document Type Taxonomy as an ADR (supersedes/extends ADR-26035)
2. **ADR**: Unified Frontmatter Standard (resolves TD-001, supersedes ADR-26023 partially)
3. **ADR**: Tag Vocabulary Unification (extends `architecture.config.yaml` scope)
4. **Implementation**: Extract the common kernel from validation scripts into vadocs shared modules
5. **Implementation**: Add `type` field to frontmatter and `resolve_type()` to vadocs
6. **Cleanup**: Formalize orphaned sources, promote ADR-26035, migrate legacy post-mortems

---

## Implementation Tasks

Based on the analysis above, the concrete implementation work for this session:

### Task 1: Create the Analysis Artifact (A-26005)
Save this analysis as a formal evidence artifact `A-26005_doc_type_interfaces_unified_validation.md` in `architecture/evidence/analyses/`, with proper frontmatter following the evidence.config.yaml schema.

### Task 2: Formalize Orphaned Sources
Convert the three non-conforming files in `architecture/evidence/sources/` to proper S-YYNNN format:
- `gemini_3_flash_semantic_alignment.md` → `S-26004_gemini_semantic_alignment_assessment.md`
- `qwen-3.5-plus-Conceptual-Architecture-Diagram.txt` → `S-26005_qwen_agentic_os_architecture_diagram.md`
- `test.html` → assess and either formalize or remove

### Task 3: Update S-26001 extracted_into
Set `extracted_into: A-26002` on S-26001 since the content feeds that analysis.

### Task 4: Promote ADR-26035
Change ADR-26035 status from `proposed` to `accepted` — the taxonomy has been implemented and proven in practice with 4 analyses, 3 formal sources, and a working validation script.

### Task 5: Update Tech Debt Register
Add TD-004 for the Document Type Interface system (this analysis identifies the gap but doesn't implement the solution).

---

## References

### Internal
- [ADR-26035: Architecture Knowledge Base Taxonomy](/architecture/adr/adr_26035_architecture_knowledge_base_taxonomy.md)
- [A-26002: Agentic OS, Tiered Memory, Package Infrastructure](/architecture/evidence/analyses/A-26002_agentic_os_skills_tiered_memory_package_infra.md)
- [vadocs Package Spec](/architecture/packages/vadocs.md)
- [Manifesto: Documentation as Source Code](/architecture/manifesto.md)
- [Technical Debt Register](/misc/plan/techdebt.md)
- Gemini 3 Flash Semantic Alignment (evidence/sources/)
- Qwen 3.5+ Conceptual Architecture Diagram (evidence/sources/)

### External Standards
- **DITA** (OASIS) — Document type specialization and schema validation
- **Diataxis** — Four-type documentation taxonomy (Tutorial, How-to, Reference, Explanation)
- **ISO/IEC/IEEE 26514:2022** — Six information models
- **Dublin Core** (ISO 15836) — 15-element metadata standard
- **Schema.org** — Structured data vocabulary
- **llms.txt** — AI-native content discovery standard
- **GitLab CTRT** — Production docs-as-code type system

### External Tools
- **Astro Content Collections** — Zod-validated typed content
- **Vale** — Prose linting with custom style rules
- **mdschema** — Markdown body structure validation
- **Contentlayer** — defineDocumentType (stalled)

### Company Practices
- **Google** — Five doc types (Reference, Design Doc, Tutorial, Conceptual, Landing)
- **Datadog** — Custom Vale rules for docs CI
- **Mintlify** — AI-native documentation platform with skill.md
