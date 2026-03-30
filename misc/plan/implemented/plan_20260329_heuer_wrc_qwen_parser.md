# Plan: Heuer Methodology Integration + WRC Formalization + Qwen Parser

## Context

A Qwen 3.5 dialogue explored integrating Richard Heuer's "Psychology of Intelligence Analysis" into consultant prompts. Key finding: Heuer's methodology is **procedural enforcement for LLM output**, not human cognitive correction — the transformer's satisficing tendency (next-token prediction favoring first plausible answer) mirrors exactly the cognitive bias Heuer warns about. This must be embedded as instructions, not RAG.

This triggers a cascade of related work: formalizing WRC (TD-006), adding a common-block composition mechanism to avoid duplicating Heuer across 3 prompts, building a reusable Qwen JSON parser (skill), and applying YAML serializer variance findings to prepare_prompt.py.

## Phasing (revised per user input)

```
Phase 1: WS-5 (Qwen parser script + skill) — tool-first, TDD
  │
Phase 2: WS-1 (S-26019 + A-26019) — use parser to generate source, then extract analysis
  │
Phase 3: Brainstorm (/sv-ai-brainstorm-colleague) — challenge A-26019 before ADRs
  │
Phase 4: WS-2 (Heuer ADR) + WS-3 (WRC ADR) — parallel, numbers assigned dynamically
  │
Phase 5: WS-4 (prepare_prompt.py block composition) — depends on WS-2 block format
  │
Phase 6: Cleanup + verification
```

---

## Phase 1: Qwen JSON Parser Script + Skill (WS-5)

### TDD: `tools/tests/test_convert_qwen_export.py` (write first)

Contract tests:
- Parses valid Qwen export JSON (`[0].chat.history.messages` dict keyed by UUID)
- Extracts user messages from `content` field
- Extracts assistant messages from `content_list` array (`text` field, filter non-empty)
- Reconstructs thread order via `parentId`/`childrenIds` chain
- Generates valid S-YYNNN markdown with frontmatter (`id`, `title`, `date`, `model`)
- Detects model name from `modelName` field on assistant messages
- Notes file attachments from `files` array on user messages
- Edge cases: empty content_list, missing fields, multiple chat items in root array
- Exit code 0 on success, 1 on parse error

### Script: `tools/scripts/convert_qwen_export.py`

- **Qwen JSON structure** (documented from raw file analysis):
  - Root: `list[dict]` (usually 1 item)
  - Messages: `[0].chat.history.messages` — dict keyed by UUID (full content)
  - NOT `[0].chat.messages` — that list has empty assistant `content`
  - User: `role: "user"`, content in `content` (string)
  - Assistant: `role: "assistant"`, content in `content_list` array, each item has `text` field
  - Model: `modelName` on assistant messages (e.g., "Qwen3.5-Plus")
  - Files: `files` array on user messages (`name`, `file_type`)
  - Timestamps: `timestamp` (Unix epoch)
  - Thread order: `parentId` / `childrenIds` chain (dict is unordered!)

- **CLI:**
  ```
  convert_qwen_export.py <input.json> --id S-26019 [--title "..."] [--output-dir <path>]
  ```
  Default output dir: `architecture/evidence/sources/`

- **Output:** S-YYNNN markdown with:
  - Frontmatter: id, title, date (from earliest timestamp), model
  - Dialogue: `### User` / `### Assistant` sections
  - Attachments: `> Attached: filename.ext (type)`

- **Conventions:** top-down design, pathlib, `detect_repo_root` from `git.py`, dataclasses for message structures

### Skill: `.claude/skills/convert-qwen-export/`

- **SKILL.md** — utility skill (new archetype: script invocation, no persona prompt):
  ```
  ---
  name: convert-qwen-export
  description: Convert Qwen chat export JSON to S-YYNNN evidence source
  argument-hint: <path-to-json> --id <S-YYNNN> [--title "..."]
  ---
  Run: !`uv run tools/scripts/convert_qwen_export.py $ARGUMENTS`
  After: review generated file, delete raw JSON, consider A-YYNNN extraction.
  ```
- No `prompt.json` symlink needed (utility, not consultant persona)
- Script lives at `tools/scripts/`, will ship with vadocs package in future

### Doc triad

- TD-004 not yet relaxed → create `tools/docs/scripts_instructions/convert_qwen_export_py_script.md` (+ `.ipynb` pair)

---

## Phase 2: Evidence Foundation (WS-1)

### S-26019: Source from Qwen dialogue

- **Generate using parser:** `uv run tools/scripts/convert_qwen_export.py architecture/evidence/sources/qwen-3.5-integrating-heuer-methodology.json --id S-26019 --title "Qwen 3.5 — Integrating Heuer Methodology into Consultant Prompts"`
- Review/refine generated output
- Frontmatter: `id: S-26019`, `date: 2026-03-27`, `model: qwen3.5-plus`, `extracted_into: [A-26019]`
- Note: msg 1 had `appendix_yaml_serializer_variance.html` attached as file context
- **Delete** raw JSON after extraction (Evidence Source Hygiene)

### A-26019: Heuer Methodology Integration Analysis

- **File:** `architecture/evidence/analyses/A-26019_heuer_methodology_integration_for_consultant_prompts.md`
- Frontmatter: `id: A-26019`, `status: active`, `tags: [prompts, architecture]`, `sources: [S-26019]`
- `produces` field: left empty until ADR numbers assigned in Phase 4
- **Key insights to extract:**
  1. Heuer = instructions not RAG (procedural enforcement vs informational retrieval)
  2. Transformer satisficing mirrors human cognitive bias (Chapter 4)
  3. ACH as mandatory protocol for methodology comparison (already partially present in output_protocol section 7)
  4. Disconfirmation priority > confirmation (Popperian logic aligns with existing `peer_review` principle)
  5. Linchpin Analysis for assumption identification (maps to existing "Assumption Interrogation" table)
  6. Heuer is a structuring tool for human consumption of AI output, not a cognitive model for AI
  7. Qwen's refined prompt (msg 11) provides concrete integration blueprint

---

## Phase 3: Brainstorm Session

- Invoke `/sv-ai-brainstorm-colleague` to stress-test A-26019 conclusions
- Challenge questions:
  - Is Heuer cargo-cult reasoning for transformers, or genuinely useful structuring?
  - Does the token cost of Heuer instructions justify the output quality improvement?
  - Are there lighter alternatives (just ACH, skip the rest)?
  - Does Heuer help equally across consultant archetypes (hybrid vs devops vs local)?
- Outcome feeds into ADR Context and Alternatives sections

---

## Phase 4: Architectural Decisions (WS-2 + WS-3, parallel)

### WS-2: Heuer Integration ADR

- **Number:** assigned dynamically via `check_adr.py`
- **Decision:** Embed Heuer's tradecraft as procedural instructions in WRC-bearing consultant prompts via a shared common block
- **Common block architecture:**
  - `ai_system/3_prompts/consultants/blocks/heuer_tradecraft.json` — SSoT
  - Consultant JSONs get `"_includes": ["heuer_tradecraft"]` metadata field
  - `prepare_prompt.py` resolves `_includes` at JIT time (Phase 5)
  - Until Phase 5: manual embedding, block file is reference SSoT
- **Heuer block content** (from Qwen msg 11, refined):
  - `tradecraft_standards` — reference to Heuer's work
  - `bias_check_protocol` — 4-step: Linchpin → Disconfirmation → Bias Scan → Uncertainty Quantification
  - `ach_mandatory` — when to invoke ACH
  - `heuristics_mitigation` — Availability Bias, Anchoring, Mirror-Imaging checks
- **Alternatives rejected:** per-prompt duplication (C5), RAG (A-26019), conf.json (wrong scope)
- **Token budget:** measure block cost, set ceiling in ADR

### WS-3: WRC Formalization ADR

- **Number:** assigned dynamically
- **Decision:** Formalize WRC as ecosystem evaluation metric
- **Formula:** `WRC = 0.35*E + 0.25*A + 0.40*P`
- **Weight rationale:** P=0.40 (binding constraint), E=0.35 (falsifiable), A=0.25 (lagging indicator)
- **Thresholds:** ≥0.89 production-ready, P<0.70 after SVA = PoC-only
- **SVA relationship:** `P_final = P_raw - (violations × 0.10)`, per ADR-26037 C1-C6
- **Consequences:** prompts retain compact operational WRC in-context, ADR is authoritative source
- **Resolves:** TD-006

---

## Phase 5: Tooling Integration (WS-4)

### prepare_prompt.py: `_includes` block composition

- **Prerequisite:** WS-2 accepted (block format defined)
- Add resolution step: after JSON parse, before metadata strip
- Read `_includes` array → resolve each to `consultants/blocks/<id>.json`
- Deep-merge block `content` into target `scope` path
- Strip `_includes` from output
- **Tests:** 0 includes (no-op), 1 include, 2 includes, missing file (exit 1)

### prepare_prompt.py: PyYAML width=inf

- Current script uses custom `to_yaml_like` serializer, NOT `yaml.dump()`
- **Likely a no-op** — verify by reading the current serialization path
- If `yaml.dump()` is used anywhere: add `width=float('inf')`

### Update consultant JSONs

- Add `"_includes": ["heuer_tradecraft"]` to 3 WRC-bearing prompts
- Remove duplicated Heuer content (replaced by block resolution)
- Bump version fields

---

## Phase 6: Cleanup

1. Resolve TD-006 in `techdebt.md` (WRC ADR written)
2. Update TD-007 — note A-26019 as related evidence
3. Update MEMORY.md — next numbers, new ADRs, completed workstreams
4. Run: `check_evidence.py`, `check_adr.py --fix`, `check_broken_links.py`, `check_json_files.py`
5. Verify pre-commit hooks pass

---

## Critical Files

| File | Role |
|---|---|
| `architecture/evidence/sources/qwen-3.5-integrating-heuer-methodology.json` | Raw source (parse target for WS-5, delete after S-26019) |
| `ai_system/3_prompts/consultants/ai_systems_consultant_hybrid.json` | Primary WRC+SVA prompt, Heuer integration target |
| `ai_system/3_prompts/consultants/local_ai_systems_consultant.json` | WRC prompt #2 |
| `ai_system/3_prompts/consultants/devops_consultant.json` | WRC prompt #3 |
| `tools/scripts/prepare_prompt.py` | JIT prompt transformer, needs `_includes` resolution |
| `tools/scripts/git.py` | Reuse: `detect_repo_root()` |
| `tools/scripts/paths.py` | Reuse: `get_config_path()` |
| `.claude/skills/sv-python-test-architect/SKILL.md` | Reference pattern for skill structure |
| `misc/plan/techdebt.md` | TD-006 (WRC), TD-007 (format-as-contract) |

## Verification

- [ ] `convert_qwen_export.py` tests pass: `uv run pytest tools/tests/test_convert_qwen_export.py`
- [ ] Skill `/convert-qwen-export` invocable
- [ ] S-26019 generated by parser, raw JSON deleted
- [ ] A-26019 has Problem Statement + References sections, passes `check_evidence.py`
- [ ] Brainstorm session completed, findings captured
- [ ] Both ADRs pass `check_adr.py`
- [ ] TD-006 resolved in techdebt.md
- [ ] `prepare_prompt.py` with `_includes`: all 96+ existing tests still pass
- [ ] Pre-commit hooks pass on all modified files
