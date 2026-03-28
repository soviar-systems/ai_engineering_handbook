# Plan: Refine "Format as Architecture" into a Two-Part Series

## Context

Peer review (S-26015) identified that the article mixes three concerns: conceptual argument, BPE mechanics, and hands-on measurement. The user's teaching notebook (`token_comparison.ipynb`) provides cross-tokenizer and cross-language evidence that strengthens the measurement sections. Splitting into two articles lets each serve a distinct reading goal and keeps individual article size manageable.

## Source material

- Current article: `ai_system/3_prompts/format_as_architecture_signal_noise_in_prompt_delivery.md` (411 lines, paired `.ipynb`)
- Peer review: `architecture/evidence/sources/S-26015_handbook_peer_review_format_as_architecture.md`
- Teaching notebook: `teaching/urfu/2026_spring/01_system_prompts/token_comparison.ipynb` (reference only, not modified)
- Referenced script: `tools/scripts/prepare_prompt.py`

## File plan

### Part 1 (refine existing file)

**File:** `ai_system/3_prompts/format_as_architecture_signal_noise_in_prompt_delivery.md`

Conceptual article — "why format is an architectural decision and how to choose."

**Structure:**

1. The Problem: Format Is Not Neutral (soften "equal computational cost" → "fixed compute per position")
2. The Two-Audience Principle (moved from current §4 — conceptual anchor first)
3. Token Noise Analysis by Format
   - JSON, Markdown, YAML, Minified JSON, YAML Literal Block Scalar
   - **Add XML** subsection
   - Fix colon-counting inconsistency (honest delta: what JSON adds beyond YAML)
   - Comparison table (qualitative + link to Part 2 for measured numbers)
4. Training Distribution Effects (acknowledge hypothesis strength, hedge v0.40→v0.41 confound)
5. Security Considerations (add note on XML injection resistance, mixed-format boundaries)
6. Empirical Evidence — Mentor Generator case study (brief, fix confounding acknowledgment; reframe or remove §6.2 Qwen3-Max "agreement")
7. Decision Framework (add XML branch, add mixed-format note)
8. Summary (reference Part 2 for proof)

**Frontmatter fixes:**
- `author:` → `authors:` (MyST list-of-objects format)
- Add `type: guide`
- Add `description:` (one-line elevator pitch)
- Add `tags:` (e.g., `[prompts, architecture]`)

**Other fixes:**
- Remove `**` bold wrapping from `##` headings
- Add link to `prepare_prompt.py`: `[prepare_prompt.py](/tools/scripts/prepare_prompt.py)`
- Remove all code cells (they move to Part 2)
- Keep `kernelspec` as bash (Jupytext pairing preserved)

### Part 2 (new file)

**File:** `ai_system/3_prompts/token_economics_of_prompt_delivery.md`

Hands-on measurement article — "prove the claims, explore BPE mechanics."

**Structure:**

1. Introduction — link to Part 1, state goal: "verify format claims with measurements"
2. BPE Tokenizer Mechanics (moved from current §2.7, expanded)
   - Space+word merging (add nuance: vocabulary-specific, not universal BPE property)
   - Indentation cost
   - Punctuation merging
   - Why you cannot remove all whitespace
3. Practical Measurement: Token Cost by Format
   - Setup (tiktoken)
   - Pretty JSON, Standard YAML, Minified JSON, YAML Literal — code cells from current §5
   - Results table with measured numbers
   - `o200k_base` comparison
4. Cross-Tokenizer Validation (NEW — borrowed from teaching notebook pattern)
   - Adapt `TokenizerAnalyzer` for HuggingFace `AutoTokenizer`
   - Run `devops_consultant.json` through GPT-2, Qwen2.5-0.5B in all 4 formats
   - Add `chars/token` metric
   - Comparison table: format × tokenizer
5. Language Effects (NEW — informed by teaching notebook)
   - Same text in Russian vs English
   - Show that format overhead percentage changes by language and vocab size
   - Implication: format choice matters MORE for English on large-vocab tokenizers, LESS for Russian on small-vocab
6. Summary — confirm or refine the ranking from Part 1

**Frontmatter:**
- `title: "Token Economics of Prompt Delivery"`
- `type: guide`
- `authors:` (MyST format)
- `description:`, `tags:`, `date:`, `options.birth`, `options.version`

**Jupytext:** new paired `.ipynb` will be created by `jupytext --sync`

## Execution order

1. Fix frontmatter on Part 1
2. Restructure Part 1 (move sections, add XML, fix accuracy issues, remove code cells)
3. Create Part 2 scaffold with sections and frontmatter
4. Move code cells from Part 1 to Part 2
5. Write new sections in Part 2 (cross-tokenizer, language effects)
6. Add cross-references between Part 1 ↔ Part 2
7. Run `jupytext --sync` on both files
8. Run `check_broken_links.py` and `check_link_format.py`

## Handbook implications from A-26016

Extracted from A-26016 analysis (these are editorial directions, not analysis content):

1. **Part 1 (Format as Architecture)** should avoid the "attention budget" metaphor and instead describe the mechanism precisely: structural tokens increase sequence length and dilute the attention distribution over content tokens.
2. **Part 2 (Token Economics)** should ground the "why you cannot remove all whitespace" section in the distributional shift explanation: different tokens, different learned associations — not vague "reasoning capacity."
3. Both articles should note that the "attention anchors" concept is an empirical observation about models trained on structured text, not an architectural property of transformers. It holds for current LLMs but is not guaranteed for all models.
4. The prefill/decode distinction should be mentioned when explaining why prompt format matters — it is during the parallel prefill phase that all prompt tokens compete for attention simultaneously.

## Verification

- `uv run jupytext --sync ai_system/3_prompts/format_as_architecture_signal_noise_in_prompt_delivery.md`
- `uv run jupytext --sync ai_system/3_prompts/token_economics_of_prompt_delivery.md`
- `uv run tools/scripts/check_broken_links.py --pattern "ai_system/3_prompts/*.md"`
- `uv run tools/scripts/check_link_format.py`
- Manual review: Part 1 has zero code cells, Part 2 has all measurement code
