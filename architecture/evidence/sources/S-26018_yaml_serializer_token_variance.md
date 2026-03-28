---
id: S-26018
title: "YAML Serializer Token Variance — PyYAML vs yq Session Measurements"
date: 2026-03-27
model: manual
extracted_into: [A-26017]
---

# S-26018: YAML Serializer Token Variance — PyYAML vs yq Session Measurements

Empirical measurements from an interactive session comparing PyYAML and yq YAML serialization of the same JSON prompt file (`devops_consultant.json`). Reveals that the same logical format ("YAML") produces different token counts depending on the serializer tool, and that the relative ranking of YAML Literal vs Pretty JSON flips between tools. Primary source for A-26017.

+++

## Measurement Setup

- **Input file:** `ai_system/3_prompts/consultants/devops_consultant.json`
- **Tokenizer:** `tiktoken` cl100k_base (GPT-4)
- **Tools compared:** PyYAML 6.0.3 (`yaml.dump()` with defaults), yq (Go implementation, CLI)
- **yq commands:** `yq -oy <file>` (standard), `yq -oy '..style="literal"' <file>` (literal)
- **PyYAML commands:** `yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)` (standard), custom `LiteralStr` representer for literal style

+++

## Token Count Results

All four format variants, both tools, cl100k_base tokenizer:

| Variant | Tokens | Chars | chars/token |
|---------|--------|-------|-------------|
| Minified JSON (`json.dumps` separators) | 2407 | 10575 | 4.39 |
| Pretty JSON (`json.dumps` indent=2) | 2848 | 12102 | 4.25 |
| Pretty JSON (original file) | 2843 | 12191 | 4.29 |
| Standard YAML — PyYAML | 2689 | 11333 | 4.21 |
| Standard YAML — yq | 2588 | 11109 | 4.29 |
| YAML Literal — PyYAML | 2788 | 11840 | 4.25 |
| YAML Literal — yq | 2912 | 12228 | 4.20 |

**Key finding:** yq Standard YAML (2588) is 101 tokens cheaper than PyYAML Standard YAML (2689). yq YAML Literal (2912) is 124 tokens more expensive than PyYAML YAML Literal (2788). The ranking of YAML Literal vs Pretty JSON flips between tools.

+++

## Format Ranking by Tool

**PyYAML ranking (cl100k_base):**
1. Minified JSON — 2407 (baseline)
2. Standard YAML — 2689 (+11.7%)
3. YAML Literal — 2788 (+15.8%)
4. Pretty JSON — 2848 (+18.3%)

**yq ranking (cl100k_base):**
1. Minified JSON — 2407 (baseline)
2. Standard YAML — 2588 (+7.5%)
3. Pretty JSON — 2848 (+18.3%)
4. YAML Literal — 2912 (+21.0%)

The top-2 and the absolute cheapest are consistent. Positions 3 and 4 flip.

+++

## Structural Diff: Standard YAML

PyYAML and yq produce different line counts (211 vs 154) and different quoting for the same data.

Selected diff (first diverging lines, line numbers are PyYAML / yq respectively):

```
PyYAML line 3: "  birth: '2026-01-07'"
yq     line 3:  '  birth: "2026-01-07"'

PyYAML line 5: '  purpose: Architectural peer review and engineering of high-integrity CI/CD pipelines,'
PyYAML line 6: '    infrastructure-as-code (IaC), and automation tooling.'
yq     line 5: '  purpose: Architectural peer review and engineering of high-integrity CI/CD pipelines, infrastructure-as-code (IaC), and automation tooling.'
```

PyYAML wraps at ~80 characters (default `width=80`). yq does not wrap. PyYAML uses single quotes for date-like strings; yq uses double quotes.

+++

## Structural Diff: YAML Literal

PyYAML uses `|` (keep trailing newline); yq uses `|-` (strip trailing newline). yq also applies literal style to non-string scalars (booleans), which PyYAML does not.

Selected diff:

```
PyYAML line 1: '  id: |'
yq     line 1: '  id: |-'

PyYAML line 14: '  require_USER_INPUT_field: true'
yq     line 14: '  require_USER_INPUT_field: |-'
yq     line 15: '    true'
```

yq converts the boolean scalar `true` to a literal block containing the string `"true\n"`. This adds 2 extra tokens per boolean field (the `|-` indicator + the indented value on its own line). Across the entire document, this boolean coercion is the primary driver of yq's inflated YAML Literal count.

+++

## Cross-Tokenizer Results (PyYAML formats)

GPT-2 (50k vocab) and Qwen3 (151k vocab), PyYAML serialization:

| Format | GPT-2 (50k) | Qwen3 (151k) |
|--------|------------|--------------|
| Minified JSON | 2681 (3.94 c/t) | 2458 (4.30 c/t) |
| Standard YAML | 3606 (3.14 c/t) | 2740 (4.14 c/t) |
| Pretty JSON | 4165 (2.91 c/t) | 2899 (4.17 c/t) |
| YAML Literal | 4036 (2.93 c/t) | 2839 (4.17 c/t) |

GPT-2 warning: `Token indices sequence length is longer than the specified maximum sequence length for this model (2681 > 1024)` — counts are valid but the model cannot process these prompts at full context.

The PyYAML ranking (YAML Literal < Pretty JSON) holds across both cross-tokenizers.

+++

## Open Questions for A-26017

1. What is the token delta when PyYAML `width` is set to `float('inf')` (no line wrapping)?
2. Does single-quote vs double-quote style affect tokens, and by how much?
3. Is the yq YAML output semantically round-trip identical to the source JSON?
4. Does the PyYAML output round-trip correctly (no boolean coercion or type changes)?
5. Is there a PyYAML configuration that matches yq's token efficiency without semantic loss?
