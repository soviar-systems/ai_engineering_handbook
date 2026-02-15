---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.0
kernelspec:
  name: bash
  display_name: Bash
  language: bash
---

---
title: "Format as Architecture: Signal-to-Noise in Prompt Delivery"
author: Vadim Rudakov, rudakow.wadim@gmail.com
date: 2026-02-15
options:
  version: 0.1.1
  birth: 2026-02-15
---

+++

This article examines how the serialization format of a system prompt affects LLM behavior. The choice between JSON, YAML, and Markdown is not cosmetic -- it changes the signal-to-noise ratio in the transformer's attention budget and may bias the model toward different processing modes. We present a token-level analysis, BPE tokenizer mechanics, empirical measurements on a production prompt, and a decision framework for choosing prompt delivery format.

+++

## **1. The Problem: Format Is Not Neutral**

+++

A transformer processes every token with equal computational cost. Each token in the input sequence gets its own attention weight across all layers. When structural characters like `{`, `}`, `"`, `,` appear in a prompt, the model must attend to them -- allocating capacity that could otherwise attend to instructional content.

This creates a measurable trade-off: **structural tokens that convey no semantic meaning consume the same attention budget as tokens that carry the actual instructions.**

The question is not "which format is prettiest" but "which format maximizes instructional signal per attention-weighted token."

+++

## **2. Token Noise Analysis by Format**

+++

### 2.1 JSON

JSON requires explicit delimiters for every structural boundary:

```json
"patience_with_attempts": {
  "rule": "Give the student two attempts to answer before simplifying",
  "on_first_miss": "Guide toward understanding with a hint or different angle",
  "on_second_miss": "Simplify the explanation and try a different approach"
}
```

Structural tokens: `"` (x14), `{`, `}`, `:` (x4), `,` (x2) = ~22 noise tokens.

In a typical 300-line JSON system prompt, 20-30% of tokens are structural characters. These characters encode information (nesting, type boundaries) that is redundant when indentation already conveys hierarchy.

+++

### 2.2 Markdown

Markdown replaces JSON delimiters with formatting symbols:

```markdown
### Patience with Attempts
- **Rule**: Give the student two attempts to answer before simplifying
- **On first miss**: Guide toward understanding with a hint or different angle
- **On second miss**: Simplify the explanation and try a different approach
```

Structural tokens: `###`, `-` (x3), `**` (x6) = ~10 noise tokens.

Markdown has less structural noise than JSON, but its formatting symbols (`*`, `#`, `` ` ``) are not zero-cost. Each `**bold**` marker is 2 tokens (`**` open + `**` close) that carry no semantic content -- only a formatting signal. For a 300-line file, Markdown formatting overhead is roughly 10-15% of tokens.

More critically, **Markdown destroys machine-readable structure**. Keys become headings, values become prose, and nesting becomes ambiguous. A downstream system cannot reliably extract `patience_with_attempts.on_first_miss` from Markdown the way it can from JSON or YAML.

+++

### 2.3 YAML

YAML conveys structure through indentation and minimal punctuation:

```yaml
patience_with_attempts:
  rule: Give the student two attempts to answer before simplifying
  on_first_miss: Guide toward understanding with a hint or different angle
  on_second_miss: Simplify the explanation and try a different approach
```

Structural tokens: `:` (x4) = 4 noise tokens.

Indentation uses whitespace tokens, which are among the lightest tokens for attention. YAML achieves the lowest structural noise of any format that preserves machine-readable key-value structure.

+++

### 2.4 Minified JSON

Minified JSON (`jq -c`) removes all whitespace between structural elements, collapsing the entire prompt onto a single line:

```json
{"patience_with_attempts":{"rule":"Give the student two attempts to answer before simplifying","on_first_miss":"Guide toward understanding with a hint or different angle","on_second_miss":"Simplify the explanation and try a different approach"}}
```

Structural tokens remain the same (`"`, `{`, `}`, `:`, `,`), but every indentation space and newline is eliminated. This makes minified JSON the **token champion** -- the lowest absolute token count of any format.

The trade-off: without newlines or indentation, there are no **attention anchors**. The transformer receives a dense, continuous stream with no structural signposts to segment sections. For short prompts this is negligible; for 2,000+ token prompts the model's attention must work harder to maintain positional awareness across the "wall of text."

+++

### 2.5 YAML Literal Block Scalar

The YAML `|` (literal block scalar) style preserves newlines exactly as written:

```yaml
patience_with_attempts:
  rule: |
    Give the student two attempts to answer before simplifying
  on_first_miss: |
    Guide toward understanding with a hint or different angle
  on_second_miss: |
    Simplify the explanation and try a different approach
```

Counterintuitively, this is the **most expensive** format. Every line inside a `|` block must be indented relative to the key, adding leading whitespace tokens to every single line. The `|` marker itself, plus the forced newlines and deep indentation, push the token count above even raw pretty-printed JSON.

Use `|` only when whitespace must be preserved exactly (e.g., embedded code snippets or Bash scripts inside a prompt).

+++

### 2.6 Comparison Table

| Format | Structural noise (est.) | Token cost (relative) | Key-value addressable | Attention anchors |
|--------|------------------------|-----------------------|----------------------|-------------------|
| Minified JSON | 20-30% (but zero whitespace) | Lowest | Yes | None |
| Standard YAML | 3-5% | Low | Yes | Strong (indentation) |
| Raw JSON (pretty) | 20-30% | Medium | Yes | Moderate (braces) |
| Markdown | 10-15% | Medium | No | Strong (headers) |
| YAML Literal (`\|`) | 3-5% + indentation tax | Highest | Yes | Strong (indentation) |

+++

### 2.7 Why Formats Differ: BPE Tokenizer Mechanics

The token differences are not arbitrary -- they follow directly from how Byte Pair Encoding (BPE) tokenizers work.

**Space+word merging.** Most BPE tokenizers (cl100k_base, o200k_base, Llama) treat a space followed by a word as a single token. The sequence ` hello` (space-prefixed) is one token, while `hello` without a leading space is a different token. This is why YAML's `key: value` structure is efficient -- the space after the colon merges with the following word.

**Indentation cost.** BPE tokenizers compress runs of spaces, but not infinitely. Four spaces might be one token, but eight spaces is typically two tokens. Deep nesting (common in YAML `|` blocks) accumulates an "indentation tax" -- each line pays for its leading whitespace. This is why YAML literal style is more expensive than standard YAML, which keeps values on the same line as keys.

**Punctuation merging.** Tokenizers trained on code (which is most modern tokenizers) have merged common patterns like `{"`, `":`, `"}` into single tokens. This is why minified JSON is so efficient -- the structural characters are already in the tokenizer's vocabulary as merged pairs.

**Why you cannot remove all whitespace.** BPE tokenizers are trained on text with spaces between words. Removing inter-word spaces (e.g., `Thecatisfast`) forces the tokenizer into sub-word fragments it was not trained to interpret. The model can still decode it, but it spends reasoning capacity on parsing rather than understanding. Structural whitespace (indentation, newlines) can be removed; semantic whitespace (between words) cannot.

+++

## **3. Training Distribution Effects**

+++

Beyond raw token counts, the format may influence how the model processes the content. This is an empirical observation, not a proven mechanism, but it is consistent across testing.

**JSON in training data** appears primarily as serialized data: API responses, database exports, configuration dumps, package manifests. Models trained on this distribution may associate JSON structure with "data to parse and extract from" rather than "instructions to follow."

**YAML in training data** appears in configuration and instruction contexts: Kubernetes manifests, Ansible playbooks, CI/CD pipelines, Docker Compose files, GitHub Actions workflows. These are contexts where the YAML content IS the instruction set -- the system reads it and executes it.

**Markdown in training data** appears as documentation, READMEs, blog posts, and technical guides. The association is with "content to present to humans" rather than "structured configuration to execute."

The hypothesis: when a model reads a system prompt in JSON format, the training-distribution prior nudges it toward treating the content as data. When it reads the same content in YAML, the prior nudges it toward treating the content as operational instructions.

Independent testing with multiple LLMs (including the token measurements in Section 5 and the behavioral testing in Section 6) is consistent with this hypothesis. Models show higher instruction adherence with YAML-formatted prompts, even when the semantic content is identical.

+++

## **4. The Two-Audience Principle**

+++

A system prompt pipeline typically involves two distinct consumers:

1. **The compiler/generator** -- reads the source template once, performs transformations (placeholder substitution, curriculum generation), and outputs the result. This consumer needs unambiguous structure, tooling support (`jq`, `json.load()`), and validation.

2. **The runtime model** -- reads the generated output every session. This consumer needs to internalize behavioral rules, reference structured data (curriculum phases, user profile), and follow protocols. Signal-to-noise ratio directly affects instruction compliance.

These consumers have different format requirements:

| Consumer | Needs | Optimal format |
|----------|-------|---------------|
| Compiler (one-time) | Validation, tooling, unambiguous structure | JSON |
| Runtime model (every session) | Low noise, instruction compliance, field access | YAML |
| Structured data records | Strictness, parseable fields | JSON |

This leads to a natural format boundary: **JSON for development artifacts, YAML for runtime instructions, JSON for structured data records.**

The `prepare_prompt.py` tool in this repository implements this boundary -- it converts JSON source prompts to YAML-like format before delivery to the LLM.

+++

## **5. Practical Measurement: Token Cost by Format**

+++

The analysis above makes theoretical predictions. This section provides runnable measurements on an actual production prompt (`devops_consultant.json`) so you can verify the claims and reproduce them on your own prompts.

We use OpenAI's `tiktoken` library because it implements the exact BPE tokenizers used by GPT-4 (`cl100k_base`) and GPT-4o (`o200k_base`). For other models (Qwen, Llama, Mistral), use HuggingFace `transformers` with the model-specific tokenizer -- the relative rankings between formats will be similar, though absolute counts differ.

+++

### 5.1 Setup

```{code-cell} bash
env -u VIRTUAL_ENV uv add tiktoken
```

```{code-cell} bash
yq --version
```

```{code-cell} bash
# Define the prompt file path (relative to repository root)
PROMPT_FILE="../3_prompts/consultants/devops_consultant.json"
echo "Prompt file:"
head -n10 "${PROMPT_FILE}"
echo "File size: $(wc -c < "${PROMPT_FILE}") bytes"
```

### 5.2 Pretty JSON (raw file)

```{code-cell} bash
cat "${PROMPT_FILE}" \
  | env -u VIRTUAL_ENV uv run python3 -c "
import sys, tiktoken
enc = tiktoken.get_encoding('cl100k_base')
text = sys.stdin.read()
tokens = enc.encode(text)
print(f'Pretty JSON (cl100k_base): {len(tokens)} tokens')
"
```

### 5.3 Standard YAML

```{code-cell} bash
yq -oy "${PROMPT_FILE}" \
  | env -u VIRTUAL_ENV uv run python3 -c "
import sys, tiktoken
enc = tiktoken.get_encoding('cl100k_base')
text = sys.stdin.read()
tokens = enc.encode(text)
print(f'Standard YAML (cl100k_base): {len(tokens)} tokens')
"
```

### 5.4 Minified JSON

```{code-cell} bash
jq -c . "${PROMPT_FILE}" \
  | env -u VIRTUAL_ENV uv run python3 -c "
import sys, tiktoken
enc = tiktoken.get_encoding('cl100k_base')
text = sys.stdin.read()
tokens = enc.encode(text)
print(f'Minified JSON (cl100k_base): {len(tokens)} tokens')
"
```

### 5.5 YAML Literal Block Scalar

```{code-cell} bash
yq -oy '..style="literal"' "${PROMPT_FILE}" \
  | env -u VIRTUAL_ENV uv run python3 -c "
import sys, tiktoken
enc = tiktoken.get_encoding('cl100k_base')
text = sys.stdin.read()
tokens = enc.encode(text)
print(f'YAML Literal (cl100k_base): {len(tokens)} tokens')
"
```

### 5.6 Comparison with `o200k_base` (GPT-4o tokenizer)

The `o200k_base` tokenizer has a larger vocabulary (200k vs 100k tokens), which means it can represent more character sequences as single tokens. Let's see how this affects the ranking.

```{code-cell} bash
# Compare two formats with o200k_base
for fmt_name in "Minified JSON" "Standard YAML"; do
  if [ "${fmt_name}" = "Minified JSON" ]; then
    content=$(jq -c . "${PROMPT_FILE}")
  else
    content=$(yq -oy "${PROMPT_FILE}")
  fi
  echo "${content}" | env -u VIRTUAL_ENV uv run python3 -c "
import sys, tiktoken
enc = tiktoken.get_encoding('o200k_base')
text = sys.stdin.read()
tokens = enc.encode(text)
print(f'${fmt_name} (o200k_base): {len(tokens)} tokens')
"
done
```

### 5.7 Results Analysis

When measured on `devops_consultant.json` with `cl100k_base`, the ranking is:

| Format | Tokens (cl100k_base) | Delta from cheapest |
|--------|---------------------|---------------------|
| Minified JSON | 2,306 | baseline |
| Standard YAML | 2,482 | +176 (+7.6%) |
| Pretty JSON | 2,734 | +428 (+18.6%) |
| YAML Literal (`\|`) | 2,798 | +492 (+21.3%) |

With `o200k_base` (GPT-4o), the ranking holds: Minified JSON = 2,313 tokens, Standard YAML = 2,480 tokens. The larger vocabulary compresses both formats almost equally, preserving the relative gap.

Key observations:

1. **Minified JSON is the token champion** -- 21% cheaper than the most expensive format. If you are strictly budget-constrained or hitting a context window limit, `jq -c` is the answer.

2. **Standard YAML beats raw JSON** -- by 252 tokens (9.2%). The colons-and-indentation structure is genuinely more token-efficient than braces-and-quotes. This contradicts the naive assumption that "less punctuation = fewer tokens"; what matters is how well the format aligns with BPE merge patterns.

3. **YAML literal (`|`) is the most expensive** -- even more than pretty-printed JSON. The indentation tax on every line inside a `|` block overwhelms the savings from removing quotes. This is the most counterintuitive finding: the "most readable" YAML variant is the "most expensive."

4. **Token efficiency ≠ reasoning quality.** Minified JSON saves tokens but eliminates the structural signposts (newlines, indentation) that help the transformer maintain positional awareness. Standard YAML costs 7.6% more than minified JSON but provides attention anchors that improve instruction adherence in complex prompts. For most production use cases, the 176-token difference is worth the reasoning quality gain.

+++

## **6. Empirical Evidence**

+++

### 6.1 Mentor Generator v0.40.0 vs v0.41.0

The Mentor Generator project provides controlled evidence. In v0.40.0, the system used separate template files that the LLM was instructed to copy and fill. Testing on Qwen3-Max revealed catastrophic drift: 10 sections dropped, immutable fields rewritten, structural parity violated. The LLM treated the templates as context to understand, not source code to copy.

In v0.41.0, templates were embedded in the meta-prompt and the output format was changed to YAML. Testing the same model (Qwen3-Max) showed ~95% compiler fidelity: all 15 top-level sections present, literal values preserved verbatim in the vast majority of fields, correct placeholder substitution.

The remaining ~5% fidelity issues (one key renamed, two nested fields dropped, one key truncated) are compiler compliance issues, not format problems -- the model understood the instructions but didn't execute perfectly.

+++

### 6.2 Qwen3-Max format discussion

When asked directly about format choice, Qwen3-Max independently confirmed YAML as optimal for the generated output, citing the same signal-to-noise argument. When presented with the "format as architecture" analysis, it agreed that format shapes LLM processing mode and recommended keeping JSON for the meta-prompt (compiler input) and YAML for the generated file (runtime instructions).

+++

## **7. Security Considerations**

+++

Indentation-based formats introduce a specific class of prompt injection vulnerability that delimiter-based formats (JSON, XML) are less susceptible to.

### 7.1 The "Out-Indenting" Attack

In YAML or any indentation-scoped format, hierarchy is determined by whitespace depth. If user-generated content is dynamically inserted into an indented block, a malicious input can "out-indent" -- using fewer leading spaces to escape the intended scope and inject instructions at a higher level of the prompt hierarchy.

For example, if user input is inserted at 4-space indentation depth, an attacker can submit content with 0-space indentation to place instructions at the root level, potentially overriding system instructions.

### 7.2 Mitigation

- **Terminal anchors.** End critical instruction blocks with explicit markers (e.g., a new top-level key) so that scope cannot be extended by injected content.
- **Programmatic indentation enforcement.** When inserting dynamic content, strip all leading whitespace and re-indent programmatically to the intended depth. Never trust user-supplied indentation.
- **Validate after assembly.** Parse the assembled prompt as YAML/JSON before sending it to the LLM. If the structure does not match the expected schema, reject it.

### 7.3 Format Comparison for Injection Resistance

JSON and XML have explicit delimiters (`}`, `</tag>`) that are harder to forge in free-text input. YAML and Markdown rely on whitespace, which is invisible and easy to manipulate. If your prompt pipeline inserts untrusted content, prefer delimiter-based formats for the injection boundary or sanitize aggressively.

+++

## **8. Decision Framework**

+++

When choosing a format for any prompt or LLM-consumed file:

1. **Who reads this file?** If a compiler/tooling reads it once, use JSON. If the LLM reads it every session as instructions, use YAML.

2. **Does the consumer need to follow instructions or parse data?** Instructions benefit from low noise (YAML). Data parsing benefits from strictness (JSON).

3. **Does the consumer need key-value access?** If yes, Markdown is unsuitable. Choose between JSON (strict) and YAML (clean).

4. **How large is the file?** For small files (<50 lines), format barely matters. For large files (300+ lines), the 20-30% noise difference between JSON and YAML is significant.

5. **What is the delivery mechanism?** Web chat (paste/attach) favors YAML for readability. API calls favor JSON for tooling. Configuration management favors YAML for editability.

6. **Token budget or reasoning quality?** If you are hitting a context window ceiling, minified JSON (`jq -c`) gives the lowest token count. If you have headroom, standard YAML provides better attention anchors and instruction adherence at a modest token premium (~7-8% over minified JSON). YAML literal (`|`) should be avoided unless you need exact whitespace preservation -- it is the most expensive format.

7. **Does the pipeline insert untrusted content?** If yes, prefer delimiter-based formats (JSON) at the injection boundary, or sanitize indentation programmatically (see Section 7).

+++

## **9. Summary**

+++

Format is not a cosmetic choice. It is an architectural decision that affects:

- **Signal-to-noise ratio** in the transformer's attention budget
- **Processing mode** influenced by training data distribution
- **Token cost** with measured differences of up to 21% between formats on the same content (2,306 vs 2,798 tokens)
- **Structural integrity** of key-value data downstream
- **Security posture** when inserting dynamic content into prompts

Practical measurement on a production prompt (`devops_consultant.json`) confirms the ranking: minified JSON is cheapest, standard YAML is the best balance of cost and reasoning quality, pretty-printed JSON is moderately expensive, and YAML literal (`|`) is the most expensive. The critical insight: **token efficiency ≠ reasoning quality** -- the cheapest format eliminates the structural signposts that help the transformer follow complex instructions.

YAML occupies the optimal position for LLM-consumed instruction files: lowest structural noise among formats that preserve machine-readable structure, with attention anchors that promote instruction adherence. JSON is optimal for development artifacts, structured data records, and injection-boundary safety. Markdown is appropriate for human documentation but unsuitable for structured prompt delivery.

The `prepare_prompt.py` script in this repository implements this principle by converting JSON source prompts to clean YAML before LLM delivery.
