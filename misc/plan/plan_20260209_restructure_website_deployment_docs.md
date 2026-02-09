# Plan: Restructure Website Deployment Documentation

## Context

The repo has two deployment guides scattered across two directories:

| File | Location | Approach | Renders on website? |
|------|----------|----------|---------------------|
| `github_pages_setup.md` | `tools/docs/git/` | GitHub Pages (**current**) | **No** — plain `.md`, no `.ipynb` pair |
| `mystmd_website_deployment_instruction.md` | `tools/docs/website/` | Self-hosted SSH/rsync (**deprecated** per ADR-26022) | **Yes** — Jupytext paired |

Problems: (1) deployment docs split across `git/` and `website/`, (2) the current approach is invisible on the website, (3) the self-hosted doc contains an outdated `deploy.yml`, (4) common setup content (MyST init, myst.yml, local testing) is trapped in the deprecated doc only.

## Approach: Two docs, both in `tools/docs/website/`, both Jupytext notebooks

One combined mega-doc would be 800+ lines mixing active and deprecated content. Separate docs with clear naming is better for discoverability. Common content (MyST init, myst.yml, local testing) goes into the GitHub Pages doc since that's the active guide.

## Steps

### 1. Create `tools/docs/website/01_github_pages_deployment.md` (new Jupytext notebook)

Content structure:
1. **Title**: "Deploying a MyST Website to GitHub Pages"
2. **Metadata**: Owner, version, birth/modified dates
3. **Intro**: Purpose, reference to ADR-26022, link to self-hosted doc for private infra
4. **Section 1 — Local Repository Setup**: MyST init, myst.yml config, local testing (extracted from the self-hosted doc sections 1.1, 1.2, and 4)
5. **Section 2 — Enable GitHub Pages**: Content from `github_pages_setup.md` Step 1
6. **Section 3 — Deployment Workflow**: Annotated workflow blocks from `github_pages_setup.md` Step 2
7. **Section 4 — Verify**: CLI check, site URLs — from `github_pages_setup.md` Step 3
8. **Common Pitfalls**: The troubleshooting table from `github_pages_setup.md`

### 2. Rename + refactor the self-hosted doc

- `git mv` both files:
  - `mystmd_website_deployment_instruction.md` → `02_self_hosted_deployment.md`
  - `mystmd_website_deployment_instruction.ipynb` → `02_self_hosted_deployment.ipynb`
- Edit `02_self_hosted_deployment.md`:
  - Update title to "Self-Hosted Website Deployment (Podman / Nginx / Traefik)"
  - Add `:::{warning}` deprecation notice at top with link to the GitHub Pages guide
  - Replace sections 1.1, 1.2 (MyST init, myst.yml) and section 4 (local testing) with a short pointer to the new GitHub Pages doc
  - Add a `:::{warning}` inside the deploy.yml dropdown marking it as the old/superseded workflow
  - Keep all server-side content (sections 2–3, Appendix A–B) intact

### 3. Sync Jupytext pairs

```bash
uv run jupytext --sync tools/docs/website/01_github_pages_deployment.md
uv run jupytext --sync tools/docs/website/02_self_hosted_deployment.md
```

### 4. Delete `tools/docs/git/github_pages_setup.md`

Content fully absorbed into the new guide.

### 5. Update inbound links (4 files)

| File | Line | Old link | New link |
|------|------|----------|----------|
| `architecture/adr/adr_26022_...md` | 22 | `mystmd_website_deployment_instruction.ipynb` | `02_self_hosted_deployment.ipynb` |
| `architecture/adr/adr_26022_...md` | 67 | `mystmd_website_deployment_instruction.ipynb` | `02_self_hosted_deployment.ipynb` |
| `architecture/packages/creating_spoke_packages.md` | 111 | `/tools/docs/git/github_pages_setup.md` | `/tools/docs/website/01_github_pages_deployment.ipynb` |
| `architecture/packages/README.md` | 24 | `/tools/docs/git/github_pages_setup.md` | `/tools/docs/website/01_github_pages_deployment.ipynb` |

Also add a new reference in ADR-26022's References section pointing to the new GitHub Pages guide.

### 6. Optional: fix `mutli-site/` typo → `multi-site/`

The configs subdirectory has a typo. Low-risk fix if desired.

## Files involved

- **Create**: `tools/docs/website/01_github_pages_deployment.md`
- **Rename**: `tools/docs/website/mystmd_website_deployment_instruction.(md|ipynb)` → `02_self_hosted_deployment.(md|ipynb)`
- **Edit**: `tools/docs/website/02_self_hosted_deployment.md` (deprecation notice, remove duplicated content)
- **Delete**: `tools/docs/git/github_pages_setup.md`
- **Edit (links)**: `architecture/adr/adr_26022_...md`, `architecture/packages/creating_spoke_packages.md`, `architecture/packages/README.md`

## Verification

1. `uv run jupytext --sync tools/docs/website/01_github_pages_deployment.md` — creates `.ipynb`
2. `uv run jupytext --sync tools/docs/website/02_self_hosted_deployment.md` — updates `.ipynb`
3. `uv run myst start` — verify both docs render, links work, no broken references
4. `uv run tools/scripts/check_broken_links.py --pattern "*.md"` — validate no broken internal links
5. `uv run pytest tools/tests/` — general test suite passes
