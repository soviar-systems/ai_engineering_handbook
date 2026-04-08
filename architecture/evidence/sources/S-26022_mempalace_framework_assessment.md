---
id: S-26022
title: "MemPalace framework assessment and mentor_generator context management"
date: "2026-04-08"
model: "Qwen Code (qwen3-coder-plus via API)"
extracted_into: A-26023
---

# MemPalace Framework Assessment and Mentor Generator Context Management

**Session:** 2026-04-08, Qwen Code
**Session file:** JSONL log

## The Dialogue

---

### Exchange 1 — User: "I need to understand what ai_agents/agents_source_code/mempalace/ is and how I can work with it"

The user asked about the MemPalace directory in `ai_agents/agents_source_code/`.

**Assistant response:** Provided an overview of MemPalace:

- Open-source AI memory system, 96.6% R@5 on LongMemEval (highest ever published)
- Stores conversations verbatim in ChromaDB with hierarchical "memory palace" structure
- Core concept: Wings (people/projects), Halls (memory types), Rooms (topics), Closets (summaries), Drawers (verbatim files), Tunnels (cross-wing connections)
- Key features: raw verbatim storage, MCP integration (19 tools), knowledge graph with temporal entity-relationships, AAAK experimental compression dialect, specialist agents
- Quick start commands: `mempalace init`, `mempalace mine`, `mempalace search`, `mempalace status`
- Repository structure: `mempalace/` main package, `tests/`, `benchmarks/`, `examples/`, `hooks/`
- Current status: authors acknowledged issues — AAAK regression (84.2% vs 96.6%), overstated README claims, contradiction detection not wired into KG

---

### Exchange 2 — User: "1 mempalace search 'why did we switch to GraphQL' - I do not understand how it works, whether I should run within the CC or Qwen Code session or in the terminal. how does it connect to the LLM?"

The user expressed confusion about how the search command works and whether it's run manually or through an AI session.

**Assistant response:** Clarified two distinct usage modes:

**Mode 1: CLI (Manual, You Drive)** — `mempalace search "query"` in terminal. No LLM involved. Returns verbatim snippets. User reads them manually.

**Mode 2: MCP (AI-Driven, Transparent to You)** — Set up once: `claude mcp add mempalace -- python -m mempalace.mcp_server`. After that, when you ask the AI a question, the AI itself calls `mempalace search` behind the scenes. Architecture diagram:

```
┌─────────────┐        MCP protocol         ┌──────────────────┐
│   You chat   │ ── "why GraphQL?" ──▶     │  Claude Code     │
│   with AI    │                            │  (or Cursor, etc)│
└─────────────┘                            └────────┬─────────┘
                                                    │
                                          calls tool via MCP
                                                    │
                                                    ▼
                                             ┌──────────────┐
                                             │  mempalace   │
                                             │  mcp_server  │
                                             └──────┬───────┘
                                                    │
                                          queries local ChromaDB
                                                    │
                                                    ▼
                                             ┌──────────────┐
                                             │  ChromaDB    │
                                             │  (on disk)   │
                                             └──────────────┘
```

**Key insight:** MemPalace is not an LLM. It's structured storage + retrieval. The LLM is separate. The 96.6% score is about finding the right snippets, not answering.

**Summary table:**
| If you want... | Do this |
|----------------|---------|
| Explore data manually | `mempalace search` in terminal |
| AI remembers across sessions | Set up MCP once, then just chat |
| Use with local models | `mempalace wake-up > context.txt` |

---

### Exchange 3 — User: "I have never worked with ChromaDB. does it have some embedding model under the hood to translate my querry into the vector search?"

**Assistant response:** Confirmed ChromaDB handles the full pipeline automatically:

```
"why did we switch to GraphQL"
         │
         ▼
   Embedding model    ← built-in, runs locally
   (text → vector)
         │
         ▼
   Vector search in
   ChromaDB on disk
```

Default model: `all-MiniLM-L6-v2` — ~80MB, fast, open-source, runs entirely on CPU. Produces 384-dimensional vectors. Cosine similarity search.

**Key table:**
| Question | Answer |
|----------|--------|
| Configure the model? | No, works out of the box |
| Can change it? | Yes — `chromadb.utils.embedding_functions` supports OpenAI, Cohere, custom HuggingFace |
| Runs locally? | Yes, default model is local |
| MemPalace custom config? | No — uses ChromaDB defaults |

Pipeline: `Your query → MiniLM embedding → vector → cosine similarity → top results from ChromaDB`. No LLM, no cloud.

---

### Exchange 4 — User: "so, this framework builds RAG from my project, correct?"

**Assistant response:** Confirmed — textbook RAG with a specific twist:

```
┌─────────────────────────────────────────────┐
│              RAG Pipeline                    │
│  Ingest: Mine conversations/code → embed → store (ChromaDB) │
│  Retrieve: Query → embed → semantic search  │
│  Augment: Retrieved snippets → injected into LLM context via MCP │
│  Generate: LLM answers using retrieved context │
└─────────────────────────────────────────────┘
```

The twist: structured retrieval. Standard RAG = flat index. MemPalace = metadata filtering on top:

```
Standard RAG:          MemPalace:
All docs in             Wing → Person
one index               Wing → Project A
                        Wing → Project B
Embedding               Search "auth"
similarity              → filter by wing
only                    → filter by hall
60.9% R@10              → filter by room
                        94.8% R@10
```

Comparison table:
| Aspect | Typical RAG | MemPalace |
|--------|-------------|-----------|
| Source | Docs, wiki, codebase | Conversations |
| Structure | Flat chunks | Wings, halls, rooms |
| Who queries | Application code | The LLM itself (via MCP) |
| Persistence | Manual rebuild | Auto-hooks during sessions |
| Knowledge graph | Usually separate | Built-in with temporal validity |

It's RAG, but optimized for conversational memory rather than document retrieval.

---

### Exchange 5 — User: "is this metadata filtering similar to my idea of YAML frontmatter 3-tier system?"

**Assistant response:** Confirmed — conceptually identical. Both are hierarchical metadata systems narrowing search scope before semantic search.

Mapping table:
| Level | MemPalace | Frontmatter | Purpose |
|-------|-----------|-------------|---------|
| 1 | Wing (driftwood, kai) | Document type (adr, evidence) | Broadest category |
| 2 | Hall (hall_facts, hall_events) | Status (proposed, accepted) | Lifecycle/context |
| 3 | Room (auth-migration, graphql) | Primary tag (devops, architecture) | Specific topic |

Same mechanism, different domain:
- **MemPalace:** conversation-centric — metadata describes who was involved, what memory type, what topic
- **Frontmatter:** document-centric — metadata describes what kind of document and how mature the decision is

Same architectural pattern:
```
Hierarchical metadata filter (narrow scope)
        ↓
Semantic search within narrowed set (find matches)
```

This is why MemPalace goes from 60.9% → 94.8% R@10. And why the frontmatter system makes documents findable by type → status → tag rather than flat indexing.

"You arrived at the same pattern from the document management side."

---

### Exchange 6 — User: "compare both approaches using this system prompt ai_system_layers/3_prompts/consultants/ai_systems_consultant_hybrid.json"

The assistant read the consultant JSON file, then applied the WRC framework.

**Assistant response:** Full assessment structured per the consultant protocol.

**WRC Calculation — MemPalace Filtering:**

| Component | Score | Rationale |
|-----------|-------|-----------|
| E | 0.85 | Proven: 60.9% → 94.8% R@10 on 22k conversations |
| A | 0.60 | Single-project, author-driven. No enterprise adoption of palace metaphor |
| P | 0.80 raw → 0.60 final | C3 violation (raw sources + extracted artifacts coexist), C6 violation (22k not 220k) |

**WRC = (0.85 × 0.35) + (0.60 × 0.25) + (0.60 × 0.40) = 0.688 — PoC-only**

**WRC Calculation — Frontmatter 3-Tier:**

| Component | Score | Rationale |
|-----------|-------|-----------|
| E | 0.75 | No published benchmarks, but structurally identical pattern |
| A | 0.85 | YAML frontmatter is industry-standard (Jekyll, Hugo, Obsidian) |
| P | 0.90 raw → 0.80 final | C5 violation (custom validation scripts, but wrap standard jsonschema) |

**WRC = (0.75 × 0.35) + (0.85 × 0.25) + (0.80 × 0.40) = 0.796 — Production-adaptable**

**Methodology Comparison Table:**

| Methodology | WRC | Pros | Cons | Best For | Source |
|-------------|-----|------|------|----------|--------|
| Frontmatter 3-Tier (Recommended) | 0.796 | Git-native, zero runtime, validated schema, pre-commit enforcement | No retrieval benchmarks, relies on text search | Document management, ADRs | Community |
| MemPalace Palace Structure | 0.688 | Proven retrieval gains (34%), automatic mining, MCP integration | Requires ChromaDB runtime, unresolved bugs, single-author | Conversational memory | Academic |
| Flat Vector Index | 0.55 | Simplest to set up | 60.9% R@10, degrades with scale | Prototypes, <100 docs | Enterprise |
| Full-Text Search + Tags | 0.72 | Deterministic, no embedding model | Loses semantic understanding | Code search, API docs | Enterprise |

**Root Cause Analysis:** Fundamental difference is what's being stored:

| Dimension | MemPalace | Frontmatter System |
|-----------|-----------|-------------------|
| Content | Conversations (ephemeral → captured) | Documents (authored → persisted) |
| Author | AI mining chats | Human writing ADRs/articles |
| Structure | Auto-detected during mining | Intentional during authoring |
| Storage | ChromaDB (binary vectors + text) | Git (plain text + YAML) |
| Validation | None at ingest | Pre-commit + JSON Schema |
| Search consumer | LLM via MCP | Human reader + scripts |

**Assumption Interrogation:**
| Assumption | Status | Falsifying Evidence |
|------------|--------|---------------------|
| "MemPalace structure would work for documents" | Unsupported | Never benchmarked on authored documents |
| "Frontmatter filtering gives same 34% gains" | Unverified | No R@10 benchmarks on document corpus |
| "Both patterns are the same architecture" | Plausible | Both hierarchical metadata → semantic search, but different search type |

**Recommended approach:** Keep them separate. Conversations aren't authored — they're mined. Documents aren't mined — they're written. Metadata structures converge because retrieval problem is the same, but ingest pipelines are fundamentally different.

**Immediate Next Step:** Run retrieval benchmark — 50 questions about ADRs, measure R@10 with type → status → tag filtering vs. no filtering.

---

### Exchange 7 — User: "can this mempalace framework be used for mentor_generator context management? read all the necessary files on mentor_generator architecture to formulate the answer"

The assistant performed comprehensive research using the Explore agent across 14+ files.

**Files analyzed:**
- **5 ADRs:** ADR-26031 (namespace), ADR-26034 (rejected agentic OS), ADR-26038 (context engineering), ADR-26041 (client-side logic), ADR-26043 (ecosystem package boundary)
- **3 Analysis files:** A-26002 (Agentic OS, tiered memory), A-26005 (VFS interfaces), A-26006 (agent runtime + RAG)
- **Roadmap:** `plan_20260308_ecosystem_roadmap_vadocs_to_mentor.md` (529 lines)
- **Evidence sources:** S-26015 (handbook peer review), 2026 CLI agents comparison
- **Manifesto:** `architecture/manifesto.md`
- **Telegram post:** Russian-language announcement

The assistant then read the full text of A-26002 and A-26038 and A-26006.

**Key findings from research:**

From A-26002: Mentor generator's three systemic failures — Cognitive Overload (monolithic prompt → Instruction Drift), Context Tax (reference data competing with procedural logic), Distribution Friction (no versioned skill units). Three-tier knowledge model: Skills (procedural), Context (state), RAG (declarative). Builder/Runtime separation (compiler + VM).

From ADR-26038 (accepted): Single-agent architecture with skill dispatch. Three-tier memory: working memory (context window), episodic memory (session history), semantic memory (vector store). Context budget as first-class constraint. Tool minimalism. Format-aware context delivery (JSON→YAML improved compiler fidelity from catastrophic drift to ~95%).

From A-26006: Master loop pattern (litellm + MCP). pgvector schema-per-repo design. JIT context injection. Why not LangChain.

**Verdict: No — but parts are useful.**

Architectural mismatch:
| Mentor Generator Needs | MemPalace Provides | Verdict |
|----------------------|-------------------|---------|
| Working memory (token-counted context) | None | ✗ |
| Episodic memory (course_history) | Wings+rooms with verbatim | ⚠️ Overkill, wrong shape |
| Semantic memory (pgvector, schema-per-repo) | ChromaDB with palace | ⚠️ Different engine, committed to pgvector |
| Skill dispatch | None | ✗ |
| Master loop | MCP server (19 tools) | ⚠️ Can be tool provider, not the loop |

Three fundamental conflicts:
1. Storage engine divergence — ADR-26039 commits to pgvector. MemPalace uses ChromaDB. Running both doubles vector infrastructure.
2. Context budget — ADR-26038 makes token counting first-class. MemPalace has no token budget awareness.
3. JIT vs. stateful — ADR-26030 mandates stateless JIT. MemPalace is inherently stateful.

**WRC: 0.290 (PoC-only)**
- E: 0.50 — No evidence for course delivery use case
- A: 0.30 — Zero adoption, unresolved bugs
- P: 0.40 raw → 0.10 final (C4: ChromaDB + pgvector both running, C5: duplicates semantic search, C6: untested at scale)

**Three-tier memory mapping:**
| ADR-26038 Memory | MemPalace Equivalent | Gap |
|-------------------|---------------------|-----|
| Working Memory | None | No token budget awareness |
| Episodic Memory | Wings + halls + drawers | Conceptual match — but stores conversations, not course state |
| Semantic Memory | ChromaDB semantic search | Same mechanism, but ecosystem committed to pgvector |

**Where MemPalace could help (limited):**
| Use Case | How | Effort |
|----------|-----|--------|
| Cross-course memory | Wing per student, room per concept | Medium |
| MCP tool provider | Add mempalace_search as mentor tool | Low |
| Knowledge graph | Track student progress entities | Medium — overlaps with student_state.json |

**Honest assessment:** MemPalace is for conversations about work. Mentor generator is a course delivery system. Different retrieval problems.

---

### Exchange 8 — User: "So, the mentor sessions can benefit from this framework. I am planning to add books, articles, video lectures transcripts to the courses of the mentors. We can consider two scenarios of working with the mentor: local based (the user side solution, no server support) and cloud based (a service). Looks like, the local usage should use mempalace while the cloud solution should be stick to pgvector for scalability. Asses it using ai_system_layers/3_prompts/consultants/ai_systems_consultant_hybrid.json"

The user proposed a nuanced split: MemPalace for local, pgvector for cloud. Requested WRC assessment.

The assistant read the ecosystem roadmap file (first 50 lines) to confirm the pgvector commitment in the dependency chain.

**Assistant response:** Full WRC assessment per consultant protocol.

**Critical Diagnosis & Re-framing [ISO 29148: Completeness]:**

The real question is not which storage engine — it is whether the retrieval mechanism is the same across deployment models. If local and cloud use different engines, you double validation surface, chunking logic, embedding model management, and test matrix. The retrieval contract (query → relevant passages) is identical. Only deployment topology differs.

The proposed split conflates two orthogonal decisions:
- Deployment topology (local vs. cloud) — where does the vector store run?
- Storage engine (ChromaDB vs. pgvector) — what format are vectors stored in?

**WRC — MemPalace (Local):**

P-Score Audit:
| Constraint | Violated? | Reason |
|------------|-----------|--------|
| C1 Automation-First | No | CLI, automatable |
| C2 Vendor Portability | **Yes** | Separate engine from pgvector. Re-switching requires re-chunk, re-embed, re-store |
| C3 Git-Native | **Yes** | ChromaDB stores in SQLite binary. No commit_sha tracking. Can't diff what's indexed |
| C4 Proportional Complexity | No | Embedded, no server |
| C5 Reuse Before Invention | **Yes** | Duplicates RAG retrieval logic that pgvector already implements |
| C6 Bounded Scalability | No | Not tested at 10x for books/transcripts |

Penalty: 3 × 0.10 = 0.30

| Component | Raw | Weighted | Calculation |
|-----------|-----|----------|-------------|
| E | 0.70 | × 0.35 = 0.245 | 96.6% on conversations. Zero evidence on books, articles, transcripts |
| A | 0.40 | × 0.25 = 0.100 | Single-author. No known production deployments for educational content |
| P | 0.60 | × 0.40 = 0.240 | Local good, but 3 SVA violations. P_final = 0.60 - 0.30 = 0.30 |

**WRC = 0.245 + 0.100 + 0.120 = 0.465 — PoC-only**

**WRC — pgvector (Cloud):**

P-Score Audit: Zero violations. All C1-C6 satisfied.

| Component | Raw | Weighted |
|-----------|-----|----------|
| E | 0.85 | × 0.35 = 0.298 |
| A | 0.90 | × 0.25 = 0.225 |
| P | 0.90 | × 0.40 = 0.360 |

**WRC = 0.883 — Production-adaptable** (0.007 short of 0.890)

**Methodology Comparison Table:**

| Methodology | WRC | Pros | Cons | Best For | Source |
|-------------|-----|------|------|----------|--------|
| pgvector — Unified Engine (Recommended) | 0.883 | One code path, ecosystem standard, commit_sha tracking, hybrid search, halfvec for local RAM | Requires Postgres runtime even locally | Both local and cloud | Enterprise |
| MemPalace Local / pgvector Cloud | 0.465/0.883 | Local users get zero-server. Cloud gets scale | Two retrieval pipelines. Two chunking strategies. Two embedding configs. Testing burden doubles | Organizations maintaining divergence | Community |
| ChromaDB for Both | 0.55 | Same engine everywhere. Embedded mode genuinely zero-server | Cloud not proven at pgvector scale. Ecosystem committed to pgvector. Loses commit_sha | Teams wanting simplicity | Community |
| FAISS + Files / pgvector Cloud | 0.48 | FAISS is fastest for local | FAISS has no persistence format. No metadata filtering. Two code paths | Performance-critical at massive scale | Academic |

**Assumption Interrogation:**

| Assumption | Status | Falsifying Evidence |
|------------|--------|---------------------|
| "Local users can't run Postgres" | Unsupported | Postgres runs via `podman play kube` — already ecosystem's deployment target. Single YAML. No root required |
| "MemPalace is easier for local users" | Plausible but untested | `pip install` is one command vs. Podman setup. But mining pipeline not designed for structured content ingestion |
| "Books/transcripts = same retrieval as conversations" | Unsupported | Books have chapters, figures, tables. Transcripts have speaker turns. Optimal chunking differs |
| "Cloud needs pgvector, local needs something lighter" | Unsupported | pgvector with halfvec uses ~2x less RAM. 10K-chunk book index at 384-dim half-precision = ~3MB. Negligible on 8GB machine |

**Recommended Architecture: Unified Engine, Two Deployment Topologies:**

```
┌─────────────────────────────────────────────────────────┐
│              pgvector (SAME ENGINE)                      │
│  LOCAL DEPLOYMENT          CLOUD DEPLOYMENT             │
│  ┌───────────────────┐     ┌─────────────────────────┐  │
│  │ Podman sidecar on │     │ Shared Postgres cluster │  │
│  │ user's machine    │     │ Schema-per-user         │  │
│  │ Schema: user_X    │     │ API via psycopg/litellm │  │
│  │ Rootless, no sudo │     │ Multi-tenant RBAC       │  │
│  └───────────────────┘     └─────────────────────────┘  │
│  Both use: nomic-embed-text, halfvec, commit_sha,       │
│  hybrid search (cosine + tsvector), same chunking logic  │
└─────────────────────────────────────────────────────────┘
```

The local deployment is not "serverless" — it's "single-tenant server." Podman already runs as user service (`systemctl --user`). Same Kube YAML, different deployment target.

**Why MemPalace is wrong even for local:**
1. Mining pipeline mismatch — tuned for conversations, not structured documents. Custom ingestion needed anyway.
2. No commit_sha tracking — can't detect stale vectors when book editions update.
3. Chunking strategy — books need chapter/section chunking. Transcripts need speaker-aware. MemPalace auto-detects rooms from conversations, doesn't understand document structure.
4. Podman constraint — ADR-26040 mandates Kube YAML via systemctl --user. Postgres already has Kube manifest. Adding to local pod is config change, not architectural decision.

**Viability Classification:**

| Scenario | Classification | Justification |
|----------|---------------|---------------|
| MemPalace local + pgvector cloud | PoC-only | Two engines, double validation, no proven benefit, WRC 0.465 |
| pgvector for both (unified) | Production-ready (0.883) | Single engine, ecosystem alignment, proven scale, same code path, zero SVA violations |

**Actionable Strategies:**

Strategy 1: Single Engine, Two Topologies (WRC 0.883) [ISO 29148: Traceability-3.2]
- Pattern: One pgvector. Local = Podman sidecar (rootless, systemctl --user). Cloud = shared Postgres cluster, schema-per-user.
- Trade-off: [Simplicity / Local overhead]. ~200MB RAM idle on user machine. 2.5% of 8GB. Acceptable but not invisible.
- Sources: pgvectorscale benchmarks, ADR-26039, ADR-26040

Strategy 2: Hybrid Search for Educational Content (WRC 0.850) [ISO 29148: Verifiability-4.1]
- Pattern: pgvector semantic + tsvector keyword in single SQL query. Books have terminology keyword search finds better than embeddings.
- Trade-off: [Recall / Query complexity]. Requires maintaining both embedding model and tsvector index.
- Sources: pgvector docs, Lewis et al. 2020

**Pitfalls and Hidden Technical Debt:**
1. Book licensing — can't distribute copyrighted books. Users must provide own materials or only public-domain content.
2. Video transcript quality — auto-generated transcripts (Whisper) contain errors, timestamps, speaker mis-attribution.
3. Embedding model drift — nomic-embed-text will be superseded. Re-embedding all vectors. With commit_sha, detect which chunks need it. Without it (MemPalace), re-index everything.
4. Local Podman friction — some users won't have Podman. Setup script for rootless Podman is non-trivial.

**Security Implications:**
- Local: ChromaDB has no authentication. If binds to 0.0.0.0, any process can query. Postgres has native RBAC.
- Cloud: pgvector inherits Postgres security — RLS, schema isolation, SSL. MemPalace has no cloud story.
- Data leakage: Local keeps everything on user's machine. Cloud must encrypt at rest and in transit.

**Immediate Next Step:** Build retrieval benchmark specific to content — 10 book chapters + 5 video transcripts, 50 questions, measure R@10 for ChromaDB default chunking, pgvector with structure-aware chunking, and hybrid search on pgvector. Gives empirical E scores.

**Reference List:** pgvector contributors 2026, TimescaleDB/pgvectorscale 2026, ADR-26039, ADR-26040, ADR-26038, A-26006, Lewis et al. 2020, LongMemEval/MemPalace 2026.

---

### Exchange 9 — User: "so, what are the use cases of mempalace then? should I ever use it for my ecosystem in any cases?"

**Assistant response:** Clarified MemPalace's actual role:

**The Distinction:**
```
┌──────────────────────────────────────────────────────┐
│                  Your Ecosystem                       │
│  APPLICATION MEMORY          DEVELOPMENT MEMORY       │
│  (what the mentor knows)     (what you discussed      │
│                               while building it)      │
│  Books, transcripts,         "Why did we choose       │
│  course materials,           pgvector?"               │
│  student history             "What was Soren's        │
│                              feedback on the          │
│                              curriculum?"             │
│  → pgvector                  → MemPalace              │
└──────────────────────────────────────────────────────┘
```

**Four Concrete Use Cases:**

1. **Architecture Decision Memory** — 27+ ADRs born from conversations (Gemini dialogues S-26008/09/10, Claude Code sessions, design debates). Those conversations are gone. With MemPalace: mine them, then 6 months later ask "What were the tradeoffs we discussed for chunking strategies?" Returns verbatim conversation with reasoning that didn't make it into the ADR.

2. **Cross-Repo Development Context** — Work across multiple repos simultaneously. Wings for vadocs, mentor_generator, ai_engineering_book. Same room name (e.g., "config-migration"), three wings. Tunnel connects them. Search once, get full cross-repo context.

3. **Post-Mortem Evidence Capture** — Already done manually (raw dialogues → S-YYNNN → A-YYNNN). MemPalace automates: `mempalace mine --mode convos --extract general`. Classifies into hall_facts, hall_decisions, hall_advice. Still create formal ADRs, but never lose raw discussion.

4. **Solo Developer Cross-Project Memory** — Design discussions about course structure, interview flows, format decisions. Not the content itself — the reasoning about it.

**When NOT to Use MemPalace:**

| Scenario | Why Not | Use Instead |
|----------|---------|-------------|
| Course reference materials | Mining pipeline tuned for conversations | pgvector with structure-aware chunking |
| Student session history | Needs structured state, not verbatim search | Course package directory |
| Mentor's curriculum graph | Graph data, not conversational text | curriculum_graph.json |
| Production RAG | Ecosystem committed to pgvector | pgvector + hybrid search |
| Formal decisions | ADRs are the SSoT | architecture/adr/ |

**The ecosystem split is clean:**

| What | Where |
|------|-------|
| Development conversations | MemPalace (ChromaDB, local) |
| Formal decisions (ADRs) | architecture/adr/ (Git) |
| Course reference materials | pgvector (Postgres) |
| Student session state | Mentor package (JSON files) |
| Skills / prompts | Skills directory (Git) |

"MemPalace has a place. It's just not the one you initially thought."

---

### Exchange 10 — User: "I use qwen code. outline the workflow how I can integrate mempalace to my daily work"

The assistant searched the Qwen Code source for MCP configuration patterns, finding that Qwen Code reads MCP servers from settings.json via `mcpServers` or `mcp` config blocks, with integration tests confirming the pattern.

**Assistant response:** Full workflow outline.

**One-Time Setup:**

1. Install: `uv pip install mempalace` (or `pip install mempalace`)

2. Initialize palace:
```bash
mempalace init /home/commi/Yandex.Disk/it_working/projects/soviar-systems/ai_engineering_book
```
Creates `~/.mempalace/palace/` with initial structure.

3. Mine existing conversation history:
```bash
mempalace mine ~/.claude/projects/ --mode convos --wing ai_engineering_book
mempalace mine ~/chats/chatgpt_exports/ --mode convos --wing ai_engineering_book
mempalace mine ~/chats/ --mode convos --extract general
```

4. Register as MCP server in Qwen Code settings (`~/.qwen/settings.json` or project-level `.qwen/settings.json`):
```json
{
  "mcpServers": {
    "mempalace": {
      "command": "python",
      "args": ["-m", "mempalace.mcp_server"],
      "cwd": "/home/commi/Yandex.Disk/it_working/projects/soviar-systems/ai_engineering_book"
    }
  }
}
```

Or if newer `mcp` block format:
```json
{
  "mcp": {
    "servers": {
      "mempalace": {
        "command": "python",
        "args": ["-m", "mempalace.mcp_server"]
      }
    }
  }
}
```

5. Verify: Start Qwen Code session, ask "What MCP servers do you have available?" Should list 19 MemPalace tools.

**Daily Workflow — Scenario 1: Need Past Context**

Working on pgvector integration. Instead of re-explaining:
> You: "What did we decide about chunking strategies for the RAG pipeline?"
> Qwen Code calls mempalace_search internally.
> Returns conversation from 3 weeks ago. No copy-paste. No re-explanation.

**Scenario 2: Debugging Recurring Issue**

> You: "Did we encounter this Podman rootless permission issue before?"
> Qwen Code searches → "Yes — February 28. Fix was adding securityContext.runAsNonRoot: false to Kube manifest."

**Scenario 3: Cross-Project Context**

> You: "What's the status of the vadocs config migration?"
> Qwen Code searches across wings → returns facts from vadocs wing, decisions from ai_engineering_book wing, advice from mentor_generator wing.

**Keeping It Fresh:**

After productive session, trigger save:
- MemPalace has auto-save hooks for Claude Code (Stop + PreCompact). Qwen Code doesn't have equivalent. Manual mining needed.
- Or mine periodically in batch: `mempalace mine <new_sources>`
- Check palace health: `mempalace status`, `mempalace list_wings`, `mempalace get_taxonomy`

**Wake-Up Pattern (for local model sessions):**

```bash
mempalace wake-up > /tmp/mempalace_context.txt
```
~170 tokens of critical facts. Paste into system prompt before starting.

**The Daily Loop:**

```
Morning:          Start Qwen Code session → MemPalace MCP tools available
During session:   Ask questions about past decisions → Qwen searches automatically
End of session:   No action needed (past data already mined)
                  OR: mine new exports if available
Weekly:           mempalace mine <new_sources>
                  mempalace status
```

**The Honest Limitations:**

1. Still need to mine — doesn't auto-capture Qwen Code sessions unless exported
2. No auto-save hook for Qwen Code yet — manual mining required
3. Read-heavy — doesn't help write ADRs, build features, run tests
4. 96.6% score on conversations — code-heavy development discussions may differ

"Integration is: install → mine → register MCP → use. Qwen Code does the rest."
