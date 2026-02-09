---
jupytext:
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

---
title: Deploying a MyST Website to GitHub Pages
author: Vadim Rudakov, rudakow.wadim@gmail.com
date: 2026-02-09
options:
  version: 1.0.0
  birth: 2026-02-09
---

+++

This guide covers the full lifecycle of deploying a MyST Markdown documentation site to **GitHub Pages** — from local setup to automated CI/CD.

This is the **canonical deployment method** for all public repositories in the ecosystem, as decided in {term}`ADR-26022`.

:::{seealso}
For private infrastructure or air-gapped environments, see the [Self-Hosted Deployment guide](/tools/docs/website/02_self_hosted_deployment.ipynb) (deprecated for public repos).
:::

+++

## **1. Local Repository Setup**

+++

### 1.1 Initialize MyST Locally

+++

Before automation can work, your repository needs to be recognized as a MyST project.

1. Open your terminal in the root of your local repository.
2. Run `myst init`. Follow the prompts if there are any.
3. **Crucial:** Open your `.gitignore` file. If `myst.yml` was added there, **remove it**. You must track `myst.yml` in Git, while keeping the `_build/` folder ignored.
4. Commit and push the `myst.yml` to your repo.

+++

### 1.2 Configure `myst.yml`

+++

This file is the entry point for rendering your repo to HTML. Here you can:
- set the project's and site's title,
- set the link to the GitHub project,
- set logo and favicon,
- **exclude some repo's paths** from rendering.

+++

:::{tip} `myst.yml` example
:class: dropdown
```yaml
# See docs at: https://mystmd.org/guide/frontmatter
version: 1
project:
  id: <any_id>
  title: <your_project_title>
  description: <your_website_description>
  # keywords: []
  # authors: []
  github: <link_to_github>
  exclude:
    - "RELEASE_NOTES.*"
    - "in_progress/*"
    - "pr/*"
    # jupytext pairs md to ipynb
    - "*/**/*.md"
site:
  template: book-theme
  title: <your_site_title>
  options:
    logo: /path/to/logo.png
    logo_text: <text_for_logo>
    favicon: /path/to/favicon.png
```
:::

+++

As you can see, we exclude all `.md` files from rendering because we use [*jupytext ipynb-md pairing*](/tools/docs/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.ipynb).

+++

### 1.3 Local Testing

+++

```bash
$ uv tool install mystmd
$ uv run myst start
```

`uv tool install` ensures that the installed mystmd is not the project dependency but the global tool.

You do not need to initialize the myst project because you are testing the existing project — the repo's `myst.yml`.

That's it: now you have a locally running website of the repo with all the files in your working directory, i.e. all the local files you have in the directory, including unstaged and in `.gitignore`. Here you can test all the changes you have made to the website or your notebooks.

When testing is done, you can safely remove the `_build` directory with the rendered files.

You can also remove mystmd, optionally:

```bash
$ uv tool uninstall mystmd
```

+++

## **2. Enable GitHub Pages**

+++

**Important:** This must be done **before** the workflow runs, otherwise `actions/configure-pages` will fail with `"Get Pages site failed. Please verify that the repository has Pages enabled"`.

1. Go to the **repository** settings (not the organization settings — the org-level Pages page only manages custom domains)
2. Navigate to **Settings** > **Pages** in the left sidebar
3. Under **Source**, select **GitHub Actions** (not "Deploy from a branch")
4. Save

The URL is: `https://github.com/<ORG>/<REPO>/settings/pages`

+++

## **3. Deployment Workflow**

+++

Create `.github/workflows/deploy.yml`.

+++

### 3.1 Triggers

+++

```yaml
name: Build and Deploy Docs

on:
  push:
    branches: [main]          # Full pipeline: validate + build + deploy
  pull_request:
    branches: [main]          # PR checks: validate + build only (deploy skipped)
  workflow_dispatch:           # Manual trigger from Actions tab
```

Three triggers cover all cases. PRs get validation without deploying. `workflow_dispatch` allows manual re-deploys.

+++

### 3.2 Environment Variables and Permissions

+++

```yaml
env:
  BASE_URL: /${{ github.event.repository.name }}
```

GitHub Pages serves org repos at `<org>.github.io/<repo>/`, so assets need the repo name as a path prefix. `configure-pages` uses this to inject the correct base path.

```yaml
permissions:
  contents: read              # Read repo files
  pages: write                # Write to GitHub Pages
  id-token: write             # Required for Pages OIDC token
```

Minimum required permissions. `id-token: write` is mandatory — GitHub Pages uses OIDC authentication for deployments, not PATs.

```yaml
concurrency:
  group: 'pages'
  cancel-in-progress: false
```

Prevents parallel deploys that could corrupt the site. `cancel-in-progress: false` ensures a running deploy finishes rather than being killed by a newer push.

+++

### 3.3 Validate Job

+++

```yaml
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true

      - name: Restore Python environment
        run: uv sync --frozen --dev

      - name: Run tests
        run: uv run pytest
```

Runs tests on every trigger. Uses `--frozen` to install from lockfile (reproducible) and `--dev` to include test dependencies from `[dependency-groups]` dev.

Note: if your test dependencies are under `[project.optional-dependencies]` instead of `[dependency-groups]`, use `--extra dev` instead of `--dev`.

+++

### 3.4 Build and Deploy Job

+++

```yaml
  build-deploy:
    needs: validate
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Pages
        uses: actions/configure-pages@v3
```

`needs: validate` ensures tests pass first. `environment: github-pages` links the deployment to GitHub's Pages environment — this shows the URL in the repo sidebar and enables environment protection rules.

`configure-pages` reads the Pages configuration and injects environment variables like `BASE_URL` for the build tool.

```yaml
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install MyST Markdown
        run: npm install -g mystmd

      - name: Build HTML
        run: myst build --html
```

MyST Markdown requires Node.js. `myst build --html` outputs to `_build/html/` by default. Replace these with your own build tool (Sphinx, MkDocs, Jekyll, etc.).

```yaml
      - name: Upload Pages artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: './_build/html'

      - name: Deploy to GitHub Pages
        if: github.ref == 'refs/heads/main'
        id: deployment
        uses: actions/deploy-pages@v4
```

`upload-pages-artifact` packages the build output as a GitHub Pages artifact. `deploy-pages` publishes it.

The `if:` guard is critical — without it, PR builds would also deploy, overwriting your production site. The `id: deployment` is referenced by the `environment.url` at the top to display the URL.

+++

## **4. Verify**

+++

1. Push the workflow to `main`
2. Check the **Actions** tab for a successful run
3. The deploy step logs will show the deployed URL
4. Visit the site:
   - **Org repos:** `https://<ORG>.github.io/<REPO>/`
   - **Personal repos:** `https://<USERNAME>.github.io/<REPO>/`

You can also check via CLI:

```bash
gh api repos/<ORG>/<REPO>/pages --jq '.html_url'
```

+++

## **Common Pitfalls**

+++

| Problem | Cause | Fix |
|---------|-------|-----|
| `Get Pages site failed` | Pages not enabled in repo settings | Enable Pages with source "GitHub Actions" (Step 1) |
| `Failed to spawn: pytest` | Test deps not installed | Use `uv sync --frozen --dev` (not just `--frozen`) |
| Assets/CSS broken on site | Missing base URL for subpath | Ensure `BASE_URL` env var is set and `configure-pages` runs before build |
| Org Pages settings only shows "Verified domains" | Looking at org-level settings | Go to the **repository** settings instead |
