---
jupytext:
  formats: md:myst,ipynb
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.0
kernelspec:
  name: python3
  display_name: Python 3 (ipykernel)
  language: python
---

# The Reflected Metadata Pattern

+++

---

Owner: Vadim Rudakov, rudakow.wadim@gmail.com
Version: 0.2.0
Birth: 2026-02-05
Last Modified: 2026-02-06

---

+++

The Reflected Metadata Pattern is a **positional projection** of YAML frontmatter into the document body. It solves a specific rendering gap: the MyST static site renderer (`myst build --html`) only renders well-known frontmatter fields (`title`, `authors`, `date`, `doi`), silently ignoring custom fields like `owner`, `version`, `birth`, and `last_modified`. The reflection block renders these fields as normal Markdown content, making them visible to readers of the published documentation site.

:::{seealso}
> 1. {term}`ADR-26019`: Mirroring YAML Metadata to Document Body for Human Verification
> 2. {term}`ADR-26018`: Universal YAML Frontmatter Adoption for Machine-Readable Documentation
> 3. [YAML Frontmatter for AI-Enabled Engineering](/ai_system/5_context/yaml_frontmatter_for_ai_enabled_engineering.ipynb) — companion article on the frontmatter schema itself
:::

+++

## 1. The Architecture of Transparency

+++

In a system where Git is the Single Source of Truth (SSoT), YAML frontmatter provides the machine interface: AI agents, RAG pipelines, and CLI tools like `yq` can parse `owner`, `version`, and `last_modified` deterministically.

The problem is not that YAML is invisible everywhere — CLI tools (`cat`, `less`), JupyterLab, and raw Git diffs display the full YAML block. The gap is specific to the **rendered static site**:

* **`myst build --html`** (book-theme) renders only well-known fields. Custom fields are silently dropped from the HTML output.
* **`mystmd` has no substitution support** — there is no `{{ frontmatter.owner }}` syntax. [Issue #852](https://github.com/jupyter-book/mystmd/issues/852) remains open.

Without a reflection block, readers who consume the published documentation have **zero visibility** into document ownership or freshness. The solution is a **positional convention**: the first cell after the H1 title contains a human-readable mirror of the YAML metadata, rendered as normal Markdown content that survives every output format.

+++

## 2. Implementation: The Positional Convention

+++

### Correct Implementation ({term}`ADR-26019`)

The reflection block uses `+++` MyST cell breaks and `---` thematic breaks — the pattern already established across all content articles in this repository:

```markdown
---
owner: "Vadim Rudakov"
version: "0.1.3"
birth: 2026-01-14
last_modified: 2026-01-17
---

# Article Title

+++

---

Owner: Vadim Rudakov
Version: 0.1.3
Birth: 2026-01-14
Last Modified: 2026-01-17

---

+++

Technical content begins here...
```

The YAML block is the **source**; the `---` / prose / `---` block is the **deterministic projection**. The `+++` cell breaks make the block a distinct Jupytext cell, which matters for both rendering and RAG ingestion (Section 5).

+++

### Rejected Alternative: HTML Comment Anchors

An earlier draft proposed `<!-- meta -->...<!-- /meta -->` delimiters:

```markdown
<!-- meta -->
> **Owner**: Vadim Rudakov | **Status**: accepted
<!-- /meta -->
```

This was **rejected** ({term}`ADR-26019`, Alternatives) because:

1. It introduces a new delimiter syntax not present in any existing article.
2. It adds parsing complexity without solving a real collision problem — the `+++` / `---` pattern has been used across 20+ articles without ambiguity.
3. It would require migrating all existing articles to a new format.

+++

## 3. Automation: The `sync_metadata.py` Pre-Commit Hook

+++

To prevent **Metadata Drift** (YAML and reflection block diverging), a pre-commit hook will automate synchronization.

### Planned Logic for `tools/scripts/sync_metadata.py`

1. **Parse**: Use `python-frontmatter` to extract `owner`, `version`, `birth`, `last_modified` from the YAML block.
2. **Format**: Construct the human-readable reflection block.
3. **Replace**: Overwrite the content of the first post-title `+++`-delimited cell.
4. **Sync**: If a paired `.ipynb` exists (via Jupytext), run `uv run jupytext --sync`.

### Hook Configuration

```yaml
- repo: local
  hooks:
    - id: sync-metadata
      name: Sync YAML to Body
      entry: uv run python tools/scripts/sync_metadata.py
      language: python
      files: \.(md|ipynb)$
      additional_dependencies: ['python-frontmatter']
```

:::{important}
The `sync_metadata.py` script does not exist yet. This section documents the planned automation per {term}`ADR-26019`. When implemented, it must follow the mandatory Script Suite convention ({term}`ADR-26011`): script + test suite + documentation as a 1:1:1 ratio.
:::

+++

## 4. CI Integration: Validation Gates

+++

The repository already enforces several pre-commit hooks for documentation quality (`check_broken_links.py`, `jupytext --sync`, `verify_jupytext_sync.py`). The metadata sync hook will integrate into this existing pipeline.

### Planned Validation

* **Format Check**: Verify that the first post-title cell matches the expected reflection format (`---` / key-value lines / `---`).
* **Content Check**: Compare the reflection block content against the YAML source. If they differ, the hook rewrites the block and stages the change.
* **Presence Check**: Fail any content article PR that lacks both the YAML metadata fields and the reflection block.

+++

## 5. RAG Integration: Signal-to-Noise Ratio

+++

When documents are ingested into a Vector Database for RAG, the reflection block becomes **redundant noise** — it duplicates information already available as structured YAML metadata.

### Ingestion Strategy

1. **Extract YAML**: Map frontmatter fields to vector store metadata (e.g., Qdrant/Milvus payload fields) for hard filtering.
2. **Strip the Reflection Block**: Identify the first post-title `+++`-delimited cell and remove it before generating embeddings.
3. **Result**: The AI retrieves chunks containing pure technical content, while still filtering by `owner` or `last_modified` via the database metadata layer.

### Comparison Table: RAG Performance

| Feature | No Mirroring | Unstructured Mirror | Reflected Block (Positional) |
| --- | --- | --- | --- |
| **Human Visibility (Static Site)** | Zero | High | **High** |
| **Vector Accuracy** | High | Low (Noise) | **High (Stripped on ingest)** |
| **Automation Robustness** | N/A | Low (Regex fragile) | **High (Positional convention)** |

+++

## 6. Technical Debt & Pitfalls

+++

1. **Jupytext Drift**: If metadata is updated in a notebook's JSON but not the paired `.md`, the reflection block diverges from the actual YAML source. **Constraint**: Always modify metadata in the `.md` file or the YAML frontmatter — never in the notebook JSON directly.

2. **Positional Fragility**: If an author inserts content between the title and the reflection block, the sync script will overwrite the wrong cell. **Mitigation**: The pre-commit hook validates that the first post-title cell matches the expected reflection format before overwriting. If the format does not match, the hook fails with a diagnostic message rather than silently corrupting content.

3. **Prerequisite Dependency**: This pattern is inert until {term}`ADR-26018` (Universal YAML Frontmatter Adoption) is implemented. Until content articles carry `owner`, `version`, `birth`, `last_modified` fields in their YAML frontmatter, there is nothing to automate. **Mitigation**: Explicit sequencing documented in {term}`ADR-26019`.
