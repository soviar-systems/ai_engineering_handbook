# Decision: Keep or Discard Two Early Articles

## Context

Two articles under review, both born **2025-10-19** (early repo era), cross-reference each other:
- `ai_system/2_model/selection/choosing_model_size.md` (v0.2.3)
- `ai_system/4_orchestration/patterns/llm_usage_patterns.md` (v0.1.5)

The repo has since matured significantly. Newer content (born Jan 2026) sets a much higher bar:
- `ai_system/2_model/selection/general_purpose_vs_agentic_models.md` — ADR-backed model classification with Agentic/General Purpose/Thinking tiers
- `ai_system/4_orchestration/workflows/aidx_industrial_ai_orchestration_framework.md` — 5-phase pipeline (Research→Planning→Execution→Validation→Review) with ISO 29148 references, VRAM isolation, Hard Reset pattern

---

## Analysis

### `llm_usage_patterns.md` — Verdict: **DISCARD**

**What it covers:** Chat vs. Workflow vs. Agent taxonomy with definitions, comparison table, toy code skeletons (`llm.call()`).

**Why discard:**

1. **Superseded.** The aidx framework article already provides a far richer orchestration taxonomy (5-phase pipeline with role separation) that goes beyond the simplistic Chat/Workflow/Agent split. The repo's actual methodology doesn't map to these three categories — it maps to Research/Architect/Editor/CI/Forensic.

2. **Below quality bar.** The article reads as a "101 blog post." It references "LangChain Pipelines" generically, uses `llm.call()` pseudocode, and offers no ADR references, no framework integration, and no connection to the repo's methodology. Compare to the aidx article which cites ISO 29148, references 5 ADRs, and includes real YAML configuration.

3. **Common knowledge.** The Chat/Workflow/Agent taxonomy is covered in every introductory AI engineering resource. A production methodology repo doesn't need to re-teach this — it needs to show how its own framework *transcends* these basic categories.

4. **Orphaned.** It's the only file in `ai_system/4_orchestration/patterns/` — no sibling content, no integration into a broader narrative.

**What to preserve:** Nothing unique. The vocabulary (chat, workflow, agent) is already used naturally throughout the repo without needing a dedicated explainer.

---

### `choosing_model_size.md` — Verdict: **KEEP, but SUBSTANTIALLY REWRITE**

**What it covers:** Model size tiers, KV Cache budgeting, Schema-Guided Reasoning (SGR) with scratchpad, Verifier Cascade pattern, Hybrid Routing pattern, quantization guidance, VRAM checklist.

**Why keep (the unique value):**

1. **KV Cache / VRAM budgeting** — The aidx article mentions "KV cache below 4GB" and "max-chat-history-tokens: 2048" as configuration, but `choosing_model_size.md` explains *why* (the "Short-Term Memory Tax"). This is the engineering rationale that production teams need.

2. **SGR (Schema-Guided Reasoning)** with the "scratchpad" pattern — Not covered anywhere else in the repo. This is a concrete technique for making small models reliable via structured output enforcement. Directly relevant to the hybrid methodology.

3. **Quantization guidance** (Q4_K_M, 50% size reduction, ~1% logic loss) — Practical detail not covered elsewhere. Essential for anyone deploying local SLMs per the aidx framework.

4. **Production patterns** (Verifier Cascade, Hybrid Routing) — Valid patterns that complement the aidx pipeline. The Verifier Cascade maps naturally to the Architect→Editor flow.

**What's wrong with it now:**

| Problem | Example |
|---------|---------|
| Outdated model references | "GPT-4 or Claude" as frontier 100B+ models |
| Oversimplified size tiers | "3B–8B for chats, 14B–70B+ for agents" — doesn't reflect Agentic/GP/Thinking classification |
| No ADR references | Zero connection to ADR-26005, ADR-26006, or aidx framework |
| No framework integration | Doesn't mention aidx, Hard Reset, or the 5-phase pipeline |
| Stale cross-reference | Links to `llm_usage_patterns.md` which should be discarded |

**Rewrite scope:**
- Reframe around the repo's actual model zoo (Jan 2026 classification)
- Connect KV Cache / VRAM content to aidx's Hard Reset and Context Gating patterns
- Reference relevant ADRs (ADR-26005 for VRAM isolation, ADR-26006 for model selection)
- Update model references to current landscape (Claude 4.0 Sonnet, Gemini 3 Flash, qwen2.5-coder:14b, etc.)
- Remove the `seealso` link to `llm_usage_patterns.md`
- Consider renaming to better reflect the unique value: something like "Model Sizing, Quantization, and VRAM Budgeting for Local Deployment"

---

## Summary

| Article | Decision | Rationale |
|---------|----------|-----------|
| `llm_usage_patterns.md` | **Discard** | Superseded by aidx article; 101-level content below repo quality bar; no unique value |
| `choosing_model_size.md` | **Keep & Rewrite** | Contains unique technical content (KV Cache, SGR, quantization, production patterns) not covered elsewhere; needs ADR integration and updated model references |

## Archival Decision & RAG Rationale

**Delete content articles completely. Never delete ADRs.** These have fundamentally different RAG risk profiles:

| Artifact Type | What RAG Retrieves | Risk if Stale | Policy |
|---|---|---|---|
| **Content article** | Recommendations ("use 3B–8B for chats") | **Misleading** — presents outdated advice as current truth | **Delete.** Git history is the archive. |
| **ADR** | Decision rationale ("we chose X because Y, rejected Z because W") | **Valuable** — prevents teams from re-exploring dead ends | **Never delete.** Mark as `superseded`/`deprecated` via YAML frontmatter. |

**Why this asymmetry works:**
- A superseded ADR retrieved by RAG says: *"This approach was tried and replaced by ADR-26XXX because [reason]"* — that's useful negative knowledge.
- An outdated content article retrieved by RAG says: *"Use GPT-4 as your frontier model"* — that's harmful misinformation.

The existing ADR infrastructure already handles this:
- `adr_index.md` partitions ADRs into Active Architecture / Evolutionary Proposals / Historical Context
- YAML `status` field + `superseded_by` pointer enables RAG pipeline filtering
- RAG can ingest `accepted` ADRs as binding constraints and `superseded` ADRs as historical context

**This decision itself should be captured as an ADR** (ADR-26021) to formalize the content lifecycle policy.

## Actions

### Step 1: Create ADR-26021 — Content Lifecycle Policy for RAG-Consumed Repositories
- File: `architecture/adr/adr_26021_content_lifecycle_policy_for_rag_consumed.md`
- Status: `proposed`
- **Context:** The repo is consumed by RAG for weighted decision-making. Outdated content articles (unlike ADRs) present stale recommendations as current truth, polluting retrieval.
- **Decision:** Superseded content articles are deleted (git history = archive). ADRs follow the existing immutable lifecycle (ADR-26016) with status metadata for RAG filtering.
- **References:** ADR-26016 (metadata lifecycle), ADR-26018 (YAML frontmatter)
- Add entry to `architecture/adr_index.md` under Evolutionary Proposals

### Step 2: Delete `llm_usage_patterns` (both files)
- `rm ai_system/4_orchestration/patterns/llm_usage_patterns.md`
- `rm ai_system/4_orchestration/patterns/llm_usage_patterns.ipynb`
- Remove the empty `patterns/` directory if no other files remain

### Step 3: Remove stale cross-references
- Delete the `:::{seealso}` block in `choosing_model_size.md` that links to the deleted file
- Search repo-wide for `llm_usage_patterns` to catch any remaining references

### Step 4: Rewrite `choosing_model_size.md`
Salvage unique content (KV Cache, SGR, quantization, production patterns), reframe around:
- The repo's Jan 2026 model zoo (Agentic/GP/Thinking classification)
- aidx framework integration (Hard Reset, Context Gating, VRAM isolation)
- ADR references (ADR-26005, ADR-26006, ADR-26021)
- Current model names (Claude 4.0 Sonnet, Gemini 3 Flash, qwen2.5-coder:14b)
- Consider renaming to "Model Sizing, Quantization, and VRAM Budgeting for Local Deployment"

### Step 5: Sync and verify
- `uv run jupytext --sync`
- `uv run tools/scripts/check_broken_links.py --pattern "*.md"`
- `uv run tools/scripts/check_adr.py` to validate the new ADR

## Verification

- `uv run tools/scripts/check_adr.py` — validate ADR-26021 format, frontmatter, and index sync
- `uv run tools/scripts/check_broken_links.py --pattern "*.md"` — catch dangling references to deleted file
- `uv run jupytext --sync` — ensure notebook pairs are consistent
- Manual review that rewritten article references correct ADRs and integrates with aidx framework
