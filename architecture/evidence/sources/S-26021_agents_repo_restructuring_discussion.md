---
id: S-26021
title: "Agents repo restructuring discussion"
date: "2026-04-05"
model: "Qwen Code (qwen3-coder-plus via API)"
extracted_into: A-26022
---

# Agents Repo Restructuring Discussion

**Session:** 2026-04-05, Qwen Code v0.14.0
**Session file:** JSONL log, 1129 records, 32 user messages, 17.1% context used — no compression performed

## The Discussion

The restructuring discussion emerged from the context management guide commit process. Here is the full exchange, reconstructed from the JSONL session log:

### Phase 1: The Tag Scope Question

The commit was blocked by frontmatter validation — missing `token_size` field and unknown tag `agents`. The user chose to add the tag to `.vadocs/conf.json` rather than just fix the files.

I proposed an initial description: "architecture analysis, context management, tooling, multi-agent orchestration."

**User pushback:** "description is too broad and misleading. architecture analysis, context management, tooling, multi-agent orchestration — looks like other tags cover this already."

**My narrowed proposal:** "external agent source code analysis"

**User's counter-position:** "I see it like we have a deal with a new era entities — agents. these are complete engineering creatures that have their own specifics, they accumulate all the ai system parts and become the ai system part themselves. this is their role and place. your opinon? peer review my position, devil advocate it."

### Phase 2: Devil's Advocate — Is "agents" a Legitimate Tag?

I challenged the position from four angles:

1. **Container vs topic.** The tag should classify what domain is being discussed, not what product is being analyzed. An analysis of Claude Code's context management belongs to `context_management`. An analysis of Aider's git integration belongs to `git`.

2. **Existing tags cover sub-topics.** The files written that session are about context compression (→ `context_management`), session history (→ `context_management`/`workflow`), tool orchestration (→ `workflow`).

3. **Risk of catch-all.** Tomorrow: "Agent Safety" — `agents` or `security`? "Agent Evaluation" — `agents` or `testing`? If `agents` becomes "anything agent-related," it stops providing classification signal.

4. **Directory already scopes the topic.** Files in `6_agents/` are already about agents by location. Tags should provide cross-cutting classification — what domain, not what folder.

**My concession:** There ARE genuinely agent-level phenomena that don't fit existing tags:
- Autonomous decision-making — the agent choosing which tool to use, when to ask questions
- Multi-agent coordination — agent-to-agent delegation, consensus, conflict resolution
- Skill systems — discovery, indexing, triggering (not just prompts, not just workflow — emergent behavior)
- Agent identity — personality, behavioral consistency across sessions

These aren't any single component — they're the emergent properties of the whole system interacting.

**My verdict:** The tag is justified, but the description needs to be precise enough to prevent catch-all creep. Proposed: "Autonomous agent-level phenomena: decision-making, multi-agent coordination, skill systems."

### Phase 3: The Deeper Question — Where Should Agents Live?

**User:** "your argumentation raises another problem — whether we should move 6_agents one dir above or even to tools dir. your opinion?"

I argued against both:
- **Move to repo root:** Breaks the six-layer numbering convention. `6_` only makes sense inside `ai_system/`.
- **Move to `tools/`:** Wrong categorically. `tools/` is for scripts, tests, and config that the project uses. Agent source code is a research subject, not a tool.

I proposed keeping `6_agents/` inside `ai_system/` with better internal organization (topic directories like `context_management/`, `skill_systems/`, etc.).

### Phase 4: The Category Error Revealed

**User:** "I appreciate your concern on classification criteria problem — agents break the ai system classification, they are not a part of it. so, where this new abstract layer should live in my repo?"

This was the pivot point. The user correctly identified that agents are not "another layer" — they break the classification entirely.

**My response:** Proposed moving to repo root as `ai_agents/`. The six layers describe components you build. Agents are products that contain all components. The relationship:

```
ai_system/     → the architecture (how to build)
ai_agents/     → the products (what's been built)
```

They're parallel concepts, not stacked layers.

### Phase 5: Rename ai_system Too

**User:** "I agree. let's do that, and refine the ai_agents README.md with the arguments we have just discussed. I appreciate your scientific honesty. also we need to verify all other documents, like AGENTS.md, repo level README.md, etc. correctly describe the new member of the repo — ai_agents. but before doing this, critically assess our decision again, in best Richard Heuer analytical traditions."

**User (follow-up):** "I lean to ai_agents dir in root (the car analogy is very good), but now I this we should rename ai_system dir because the agent IS the ai system, and our current ai_system dir is like an 'engine parts' catalog. your opinion? stay Heuer styled."

I evaluated three alternatives with Heuer-style structured analysis:

- **H1: Keep `6_agents/` inside `ai_system/`, reframe as "capstone layer."** Rejected — preserves broken numbering, makes agents a "part."
- **H2: Move to root as `ai_agents/`, rename `ai_system/` to `ai_architecture/`.** Honest assessment: H2 is actually the cleanest name. "Architecture" matches existing repo vocabulary (ADRs already use it). BUT — agents have their own architecture too. Multi-agent systems have their own architecture.
- **H3: Move to root as `ai_agents/`, rename `ai_system/` to `ai_system_layers/`.** Longer but unambiguous. "These are the numbered layers" — claims only what it is.

### Phase 6: Final Decision

**User:** "how about ai_system_layers?"

I agreed — clean and precise. `ai_system_layers/` says exactly what it is: a numbered stack of technical components. `ai_agents/` at root is a separate research domain.

**User (final word):** "no, the agents have their own architecture, the multi-agent system have their, who know what new products I will add tomorrow to my catalog?"

This confirmed H3 over H2. Any future product would make `ai_architecture/` ambiguous. `ai_system_layers/` is the only name that says "these specific numbered levels, nothing more."

## Decision Reached

| Change | Before | After |
|--------|--------|-------|
| Component catalog | `ai_system/` | `ai_system_layers/` |
| Agent research | `ai_system/6_agents/` | `ai_agents/` (repo root) |
| Layer numbering | 1–6 | 1–5 (no phantom layer 6) |

## Next Steps

- Implementation plan saved to `misc/plan/plan_20260405_restructure_ai_system_and_agents.md`
- Breaking change — requires major version bump
- Migration notice needed in `AGENTS.md` for 2-3 release cycles
- Analysis saved to `architecture/evidence/analyses/A-26022_agents_break_the_layer_model.md`
