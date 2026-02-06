# Plan: Finish Two 5_context Companion Articles + Fix ADR-26019 Framing

## Key Correction

The original plan (and ADR-26019) claims YAML frontmatter is "invisible in CLI environments (`cat`, `less`)". This is **wrong** — CLI tools display the entire file including YAML. The **actual gap** is:

- **`myst build --html`** (book-theme) only renders well-known frontmatter fields (`title`, `authors`, `date`, `doi`). Custom fields (`owner`, `version`, `birth`, `last_modified`) are silently ignored in the rendered static website.
- **`mystmd` has no substitution support** (Issue #852, still open). No `{{ frontmatter.owner }}` syntax exists.
- The reflection block is needed because it renders as **normal Markdown content** on the static site, making metadata visible to readers who only see the HTML output.

All three files must use this corrected framing.

---

## Step 0: Fix ADR-26019 Context Section

**File:** `architecture/adr/adr_26019_mirroring_yaml_metadata_to_document_body.md`

**Changes:**

1. **Context paragraph (line 22):** Replace "it is rendered invisible in standard CLI environments (`cat`, `less`), raw Git diffs, and basic Markdown viewers that do not process frontmatter" with corrected text explaining the actual gap: MyST's static site renderer (`myst build --html`) does not render custom YAML frontmatter fields — only well-known fields like `title`, `authors`, `date` appear in the HTML output. CLI tools, JupyterLab, and raw file viewers show YAML just fine.

2. **Context paragraph (line 24):** Adjust the peer review sentence accordingly — the gap is about the published site, not CLI.

3. **Consequences > Positive > Visual Integrity (line 112):** Adjust wording — the benefit is visibility on the rendered static site and in environments that don't show YAML (the published documentation), not terminals/diffs.

4. **Alternatives > No Reflection Block (line 126):** Fix the reasoning — "YAML frontmatter is invisible in `cat`, `less`" is wrong. Replace with: custom YAML fields are not rendered by the MyST book-theme on the static site.

Keep the Decision section unchanged — the positional convention mechanism is sound regardless of the justification.

---

## Step 1: Rewrite `reflected_metadata_pattern.md` (complete rewrite)

**File:** `ai_system/5_context/reflected_metadata_pattern.md`

Follow the original plan's 6-section structure but with **corrected framing throughout**:

**Header:** Keep Jupytext header as-is.

**Title + metadata block + intro + seealso:** Add standard reflection block after title. Rewrite intro to introduce the pattern as a **positional projection** of YAML frontmatter. Frame the problem correctly: MyST's static site renderer does not render custom YAML fields.

**Section 1 "The Architecture of Transparency":** Problem: YAML provides the machine interface but custom fields are invisible on the rendered static site (`myst build --html` ignores them). CLI tools and JupyterLab show YAML fine, but readers of the published documentation only see what the theme renders. Solution: positional convention — first cell after H1 is the human-readable mirror, rendered as normal Markdown content.

**Section 2 "Implementation: The Positional Convention":** Same as original plan — show `+++`/`---`/prose/`---`/`+++` as CORRECT, HTML anchors as REJECTED.

**Section 3 "Automation: The `sync_metadata.py` Pre-Commit Hook":** Same as original plan — `uv run`, ADR-26011 script suite note, `:::{important}` about script not yet existing.

**Section 4 "CI Integration: Validation Gates":** Same as original plan — reference existing hooks, planned validation.

**Section 5 "RAG Integration":** Same as original plan — strip first post-title cell on ingest. Table column: "Reflected Block (Positional)".

**Section 6 "Technical Debt & Pitfalls":** Same three pitfalls from original plan (Jupytext Drift, Positional Fragility, Prerequisite Dependency).

---

## Step 2: Rewrite `yaml_frontmatter_for_ai_enabled_engineering.md` (moderate rewrite)

**File:** `ai_system/5_context/yaml_frontmatter_for_ai_enabled_engineering.md`

Follow the original plan's changes:

- Add metadata reflection block after title
- Add `:::{seealso}` with ADR refs
- Section 3: Replace fictional example with real one from `aidx_industrial_ai_orchestration_framework.md`
- Section 5: Add 4th pitfall (Positional Fragility), update Metadata Drift mitigation
- Section 6: Make concrete to this repo

**Additional correction:** Any reference to YAML being "invisible in CLI" must be corrected to reference the MyST rendering gap instead.

---

## Step 3: Sync and verify

```bash
uv run jupytext --sync ai_system/5_context/reflected_metadata_pattern.md
uv run jupytext --sync ai_system/5_context/yaml_frontmatter_for_ai_enabled_engineering.md
uv run jupytext --sync architecture/adr/adr_26019_mirroring_yaml_metadata_to_document_body.md
uv run tools/scripts/check_broken_links.py --pattern "ai_system/5_context/*.md"
```

---

## Critical Files

| File | Role |
|------|------|
| `architecture/adr/adr_26019_mirroring_yaml_metadata_to_document_body.md` | Fix framing in Context + Consequences + Alternatives |
| `ai_system/5_context/reflected_metadata_pattern.md` | Complete rewrite with corrected framing |
| `ai_system/5_context/yaml_frontmatter_for_ai_enabled_engineering.md` | Moderate rewrite with corrected framing |
| `architecture/adr/adr_26018_universal_yaml_frontmatter_adoption.md` | Reference only (no changes) |
| `ai_system/2_model/selection/choosing_model_size.md` | Quality-bar reference for article style |
| `ai_system/4_orchestration/workflows/aidx_industrial_ai_orchestration_framework.md` | Real example for yaml_frontmatter Section 3 |

## Verification

1. `uv run jupytext --sync` succeeds for all modified files
2. `uv run tools/scripts/check_broken_links.py` passes for modified `.md` files
3. Manual review: no remaining references to "CLI invisibility" as the justification for the reflection block
