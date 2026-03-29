# Plan: Meetup talk preparation — Format as Semantics

## Context

Preparing a presentation for the local Russian-speaking AI community meetup on the topic
"Format as Semantic Tooling" — how serialization format acts as a learned semantic signal
that primes different processing modes in different LLMs. The organizer asked for the topic;
a summary needs to be saved and sent to a colleague for assessment.

## Files for context

### ai_engineering_book (this repo)

| File | Role in talk |
|---|---|
| `ai_system/3_prompts/format_as_architecture_signal_noise_in_prompt_delivery.md` | **Primary source** — conceptual framework: two-audience principle, training distribution, attention mechanics, security, decision framework |
| `ai_system/3_prompts/token_economics_of_prompt_delivery.md` | **Measurements** — BPE mechanics, format cost table, cross-tokenizer validation, Russian vs English (7.18x GPT-2, 2.39x Qwen3), chars/token metric |
| `ai_system/3_prompts/appendix_yaml_serializer_variance.md` | **Serializer trap** — PyYAML vs yq, width=80 hidden tax, 100+ token difference, round-trip fidelity |
| `misc/token_economics_of_prompt_delivery.html` | Rendered notebook with executed measurements and charts |
| `misc/appendix_yaml_serializer_variance.html` | Rendered notebook with executed measurements and charts |
| `architecture/evidence/analyses/A-26016_causal_masking_attention_mechanics_for_prompt_engineering.md` | Grounds attention claims — causal masking, softmax distribution mechanics |
| `architecture/evidence/analyses/A-26017*` | YAML serializer variance analysis — token cost = f(format, serializer, tokenizer) |
| `architecture/evidence/analyses/A-26018*` | XML tags as scope boundaries — hybrid YAML+XML pattern |
| `misc/plan/techdebt.md` | TD-007 destination for open research question |

### mentor_generator (sibling repo)

| File | Role in talk |
|---|---|
| `docs/architecture/adr/adr_26007_format_is_architecture.md` | **ADR** — format choice decision: JSON for compiler input, YAML for runtime instructions, 60% less structural noise |
| `docs/architecture/adr/adr_26004_templates_as_output_schemas.md` | Field taxonomy: literal, placeholder, internal guidance, generator-only guidance |
| `docs/architecture/adr/adr_26005_embed_templates_for_web_chat.md` | Single-file output with embedded templates — YAML output, 60% less noise |
| `docs/architecture/postmortem/ARCHITECTURE_POSTMORTEM_v0.30.md` | v0.30 failure: role confusion, 450-line JSON regeneration, "constraints beat instructions" |
| `docs/architecture/postmortem/ARCHITECTURE_POSTMORTEM_v0.32.md` | v0.32: three-template architecture, append-only sessions |
| `docs/architecture/postmortem/ARCHITECTURE_POSTMORTEM_v0.40.md` | **v0.40 catastrophe** — Qwen dropped 10/15 sections, rewrote immutable fields. Root cause: web chat treats attached files as context, not source code (execution environment mismatch — separate problem from format semantics, do NOT conflate) |
| `docs/architecture/research/2026_02_25_meetup_topics.md` | Earlier topic sketch from February — now superseded by revised material |

## Tasks

### Task 1: Save talk summary

Create directory structure and write the summary file:
- Path: `../teaching/meetups/2026/format_as_semantics_talk_summary.md`
- Content: the Russian-language summary from this conversation

### Task 2: Mark open research question in handbook

**2a.** In `ai_system/3_prompts/format_as_architecture_signal_noise_in_prompt_delivery.md`,
Section 4 (Training Distribution Effects) — add blockquote after the per-format training
distribution paragraph:

> **Open question:** If format response is learned from training corpus, the same format
> may prime different cognitive modes in different models. This makes format a hidden variable
> in cross-model instruction-following benchmarks. No controlled experiment exists yet.
> Tracked in `techdebt.md` (TD-007).

**2b.** In `misc/plan/techdebt.md` — add TD-007 entry:

```
### TD-007: Format as model-specific semantic contract — open research question (2026-03-29)

- **Location:** ai_system/3_prompts/format_as_architecture_signal_noise_in_prompt_delivery.md, Section 4
- **Context:** If format response is learned from training corpus, the same format primes different
  cognitive modes in models trained on different corpora. Format becomes a hidden variable in
  cross-model instruction-following benchmarks.
- **Evidence needed:** Controlled experiment — same semantic content × multiple formats
  (JSON/YAML/Markdown) × multiple models (Claude, Qwen, GigaChat, Gemini) × behavioral outcome
  (instruction adherence rate, section survival, field preservation).
- **Collection opportunity:** Local AI community meetup presentation — audience uses multiple
  models across Cursor/Cline/LangFlow, can contribute informal observations.
- **Future artifact:** S-YYNNN (collected evidence) → A-26019 (analysis) → Section 4 update
- **Introduced by:** meetup talk brainstorming session (2026-03-29)
```

## Verification

- Read `techdebt.md` to confirm TD-007 doesn't collide (checked: next available is TD-007)
- `uv run tools/scripts/check_broken_links.py` after handbook edits
- No frontmatter version bumps needed (techdebt.md has no frontmatter; format_as_architecture edit is a blockquote addition, not structural change)
