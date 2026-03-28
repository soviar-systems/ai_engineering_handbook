# Plan: A-26017 — YAML Serializer Variance and Token Economics

Date: 2026-03-27

## The Engineering Challenge

Our session exposed a finding the handbooks do not address: **"YAML" is not a single format for tokenization purposes.** Two tools producing valid, semantically equivalent YAML from the same JSON source yield token counts that differ by 100+ tokens, and the relative ranking of formats flips depending on which tool is used.

Concrete evidence from the session (cl100k_base tokenizer, devops_consultant.json):

| Variant | Tokens |
|---------|--------|
| Minified JSON | 2407 |
| Standard YAML — yq | 2588 |
| Standard YAML — PyYAML | 2689 |
| YAML Literal — PyYAML | 2788 |
| Pretty JSON | 2848 |
| YAML Literal — yq | 2912 |

yq and PyYAML produce **opposite rankings** for YAML Literal vs Pretty JSON. The handbook currently makes authoritative claims about format rankings that are serializer-dependent, not format-dependent. This is an engineering finding, not a development task.

## Root Causes Identified (require verification)

From session diff output, three behavioural differences drive the divergence:

1. **Line wrapping.** PyYAML defaults to 80-char line width and wraps long strings across multiple lines (211 lines vs yq's 154 lines). Each line break adds a `\n` token. Tens of extra tokens across a 154-line document.

2. **Quote style for scalars.** PyYAML uses single quotes for date-like strings (`'2026-01-07'`), yq uses double quotes (`"2026-01-07"`). Different BPE merge pairs in cl100k_base.

3. **Literal block terminator (`|` vs `|-`) and scalar coercion.** PyYAML uses `|` (keep trailing newline). yq uses `|-` (strip trailing newline) AND applies literal style to non-string scalars (booleans: `require_USER_INPUT_field: |-\n  true\n`). This inflates yq's YAML Literal count by ~120 tokens — the largest single driver of the ranking flip.

These are not bugs — both outputs are valid YAML with identical semantics. But they produce different token distributions.

## Investigation Questions

A-26017 must answer five questions before any handbook claim can be considered solid:

1. **Reproducibility.** Are the differences stable across prompt files of different size/structure?
2. **Isolation.** Which serializer decision drives the most tokens? Measure each variable independently: line width alone, quote style alone, `|` vs `|-` alone.
3. **Semantic fidelity.** Does JSON → YAML (serializer) → JSON round-trip losslessly? A serializer that coerces `"true"` string to boolean `true` is disqualified for prompt delivery.
4. **Ranking stability.** For each serializer configuration, does the ranking Minified JSON < Standard YAML < Pretty JSON always hold? Under what conditions does YAML Literal become cheaper than Pretty JSON?
5. **Stack consequence.** Given the findings, what should `prepare_prompt.py` use? Is `yaml.dump(..., width=float('inf'))` the right fix? Or is there a better canonical form?

## Deliverables

### 1. S-26018 (new source)

Save the session's empirical comparison data as a source artifact:
- yq vs PyYAML token comparison table (all variants)
- Diff output (first 20 lines per format pair)
- Raw token counts
- File: `architecture/evidence/sources/S-26018_yaml_serializer_token_variance.md`

### 2. `ai_system/3_prompts/appendix_yaml_serializer_variance.md` (new, Jupytext-paired)

Appendix notebook living next to the handbooks. Contains all experiments as executable Python cells:

**Section A — Serializer Comparison**
- Cell A1: Baseline — all four formats, PyYAML vs yq, token counts table
- Cell A2: Serializer diff — line count, quote style, first differing lines per variant

**Section B — Isolation Experiments**
- Cell B1: Line width effect — PyYAML with `width=80` vs `width=float('inf')`, token delta
- Cell B2: Quote style effect — PyYAML with `default_style='"'` vs default, token delta
- Cell B3: Literal terminator effect — `|` vs `|-`, token delta
- Cell B4: Boolean coercion in yq — count non-string scalars converted to literal style

**Section C — Semantic Fidelity**
- Cell C1: Round-trip test — JSON → PyYAML YAML → JSON, assert equality
- Cell C2: Round-trip test — JSON → yq YAML → JSON (via subprocess), assert equality
- Cell C3: Edge cases — booleans, numbers, dates, null values, multi-line strings

**Section D — Ranking Stability**
- Cell D1: PyYAML with `width=inf` full ranking table (cl100k_base)
- Cell D2: yq full ranking table (cl100k_base)
- Cell D3: Cross-tokenizer ranking: does the flip persist on GPT-2 and Qwen3?
- Cell D4: Visualisation — grouped bar chart comparing PyYAML vs yq across all formats

**Section E — Stack Recommendation**
- Cell E1: Optimal PyYAML configuration — show the winning config and its token count
- Cell E2: Verify the optimal config round-trips correctly

### 3. A-26017 (new analysis)

File: `architecture/evidence/analyses/A-26017_yaml_serializer_variance_token_economics.md`

```
sources: [S-26018]
produces: []  # may produce handbook update recommendation
tags: [prompts, architecture]

## Problem Statement
## Key Findings
  ### 1. YAML is not a single format: the serializer is a hidden variable
  ### 2. Line wrapping is the dominant cost driver (isolation result)
  ### 3. Boolean coercion in yq inflates YAML Literal count
  ### 4. Semantic fidelity: round-trip results
  ### 5. Ranking stability across serializer configurations
  ### 6. The optimal serializer configuration
## Assessment: Handbook Claims That Require Revision
## Stack Consequences
## References
```

### 4. Handbook updates (after analysis is written)

In `ai_system/3_prompts/token_economics_of_prompt_delivery.md`:
- Section 2 intro: add a note that token costs are serializer-dependent
- Section 2.2: add reference to Appendix for tool comparison
- Section 2.5 points 2 and 3: replace absolute claims with tool-qualified statements
- Summary table: qualify the YAML Literal ranking with "(serializer-dependent, see Appendix)"

In `ai_system/3_prompts/format_as_architecture_signal_noise_in_prompt_delivery.md`:
- Comparison table §3.7: add footnote that YAML Literal cost is serializer-dependent

## Execution Order

1. Create S-26018 from session data
2. Create appendix .md file with Jupytext header and all section scaffolding
3. Write cells A1–A2 (baseline comparison)
4. Write cells B1–B4 (isolation experiments)
5. Write cells C1–C3 (fidelity tests)
6. Write cells D1–D4 (ranking stability + visualisation)
7. Write cells E1–E2 (stack recommendation)
8. Write A-26017 from the appendix results
9. Update both handbooks
10. Run jupytext --sync on appendix file
11. Run check_broken_links.py and check_link_format.py

## What This Analysis Is NOT

- Not a bug report on PyYAML or yq
- Not a performance benchmark of serializers
- Not a general YAML specification compliance test

It is a **prompt engineering finding**: the token cost of a format is a function of `(format, serializer, tokenizer)` — three variables, not one. The handbook has been treating it as one.
