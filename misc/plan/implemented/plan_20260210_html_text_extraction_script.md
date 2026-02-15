# Plan: RFC→ADR Workflow Formalization + HTML Extraction Script

## Context

Two needs converge before the structured commit bodies plan (plan_20260209) can be implemented:

1. **Operational**: The `gemini_rfc.html` file (974KB) cannot be read directly by Claude Code. A reusable HTML text extraction script is needed — follows the standard script suite pattern (ADR-26011).

2. **Architectural**: The Gemini RFC conversation concludes that ADRs with `status: proposed` already serve as RFCs. This workflow is implicit — it needs formal codification as ADR-26025 before new ADRs are created.

### Key decisions from analysis

- **No new directory**: No `misc/rfc/` or `architecture/rfc/`. The ADR itself is the permanent record. Gemini/Claude consultations are working files that get absorbed into the ADR's Alternatives section.
- **Fat ADR pattern**: The ADR's `## Alternatives` section gets thorough treatment — each rejected option with full analysis paragraph, not just 2-sentence summaries.
- **Cleanup**: `gemini_rfc.html`, `gemini_rfc_files/`, and `misc/plan/gemini_*.md` are local working files, kept untracked.

---

## Part 1: HTML Text Extraction Script

### Step 1.1: Write tests (TDD)

**File**: `tools/tests/test_extract_html_text.py`

Test contracts:
- Input: path to HTML file → Output: extracted text to stdout or file
- Strips `<script>`, `<style>`, `<noscript>` tags and their content
- Preserves meaningful text from semantic tags (p, li, h1-h6, td, etc.)
- Handles UTF-8 encoding
- Exit 0 on success, exit 1 on file not found / read error
- `--output` flag writes to file instead of stdout
- Empty HTML → empty output (no crash)

### Step 1.2: Write the script

**File**: `tools/scripts/extract_html_text.py`

Interface:
```bash
# Extract to stdout
uv run tools/scripts/extract_html_text.py gemini_rfc.html

# Extract to file
uv run tools/scripts/extract_html_text.py gemini_rfc.html --output /tmp/output.md
```

Implementation:
- `html.parser.HTMLParser` from stdlib (no external deps)
- Top-down design: `main()` at top
- `pathlib.Path` throughout
- Strips script/style/noscript content
- ~50-80 lines

### Step 1.3: Write script documentation

**File**: `tools/docs/scripts_instructions/extract_html_text_py_script.md` (+ `.ipynb` via jupytext sync)

### Step 1.4: Run the script on gemini_rfc.html

Extract content and verify it's readable.

---

## Part 2: RFC→ADR Workflow Formalization

### Step 2.1: Write ADR-26025

**File**: `architecture/adr/adr_26025_rfc_adr_workflow_formalization.md`

### Step 2.2: Update `check_adr.py` — add promotion gate rules

New validation rules:
- `accepted` ADRs: **fail** if `## Alternatives` has <2 entries or `## Participants` is empty
- `proposed` ADRs: **warn** (not fail) if `## Alternatives` is empty
- Entry detection: count lines matching `^- \*\*` or `^\d+\.` under `## Alternatives`

### Step 2.3: Write tests for new check_adr.py rules (TDD — tests first)

### Step 2.4: Update `what_is_an_adr.md` — add RFC workflow section

### Step 2.5: Update `adr_index.md` — add ADR-26025

---

## Verification

### Part 1
1. `uv run pytest tools/tests/test_extract_html_text.py` — all pass
2. `uv run tools/scripts/extract_html_text.py gemini_rfc.html` — produces readable text
3. `uv run tools/scripts/check_script_suite.py` — validates script+test+doc triplet

### Part 2
1. `uv run pytest tools/tests/test_check_adr.py` — all pass
2. `uv run tools/scripts/check_adr.py` — runs clean against all current ADRs
3. ADR-26025 appears in `adr_index.md` under Evolutionary Proposals
4. `architecture/what_is_an_adr.md` contains RFC workflow section
