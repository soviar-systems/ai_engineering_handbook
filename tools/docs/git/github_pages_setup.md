# Setting Up GitHub Pages with GitHub Actions

A step-by-step guide for deploying a static documentation site to GitHub Pages using GitHub Actions. Implements {term}`ADR-26022`.

## Prerequisites

- Repository hosted on GitHub (personal account or organization)
- Site builds to a static HTML directory (e.g. `_build/html/`)

## Step 1: Enable GitHub Pages in Repo Settings

**Important:** This must be done **before** the workflow runs, otherwise `actions/configure-pages` will fail with `"Get Pages site failed. Please verify that the repository has Pages enabled"`.

1. Go to the **repository** settings (not the organization settings — the org-level Pages page only manages custom domains)
2. Navigate to **Settings** > **Pages** in the left sidebar
3. Under **Source**, select **GitHub Actions** (not "Deploy from a branch")
4. Save

The URL is: `https://github.com/<ORG>/<REPO>/settings/pages`

## Step 2: Create the Workflow File

Create `.github/workflows/deploy.yml`.

### Complete Workflow

```yaml
name: Build and Deploy Docs

on:
  push:
    branches: [main]          # Full pipeline: validate + build + deploy
  pull_request:
    branches: [main]          # PR checks: validate + build only (deploy skipped)
  workflow_dispatch:           # Manual trigger from Actions tab
```

**Triggers:** Three triggers cover all cases. PRs get validation without deploying. `workflow_dispatch` allows manual re-deploys.

```yaml
env:
  BASE_URL: /${{ github.event.repository.name }}
```

**BASE_URL:** GitHub Pages serves org repos at `<org>.github.io/<repo>/`, so assets need the repo name as a path prefix. `configure-pages` uses this to inject the correct base path.

```yaml
permissions:
  contents: read              # Read repo files
  pages: write                # Write to GitHub Pages
  id-token: write             # Required for Pages OIDC token
```

**Permissions:** Minimum required. `id-token: write` is mandatory — GitHub Pages uses OIDC authentication for deployments, not PATs.

```yaml
concurrency:
  group: 'pages'
  cancel-in-progress: false
```

**Concurrency:** Prevents parallel deploys that could corrupt the site. `cancel-in-progress: false` ensures a running deploy finishes rather than being killed by a newer push.

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

**Job 1 — validate:** Runs tests on every trigger. Uses `--frozen` to install from lockfile (reproducible) and `--dev` to include test dependencies from `[dependency-groups]` dev.

Note: if your test dependencies are under `[project.optional-dependencies]` instead of `[dependency-groups]`, use `--extra dev` instead of `--dev`.

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

**Job 2 — build-deploy:** `needs: validate` ensures tests pass first. `environment: github-pages` links the deployment to GitHub's Pages environment — this shows the URL in the repo sidebar and enables environment protection rules.

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

**Build steps:** MyST Markdown requires Node.js. `myst build --html` outputs to `_build/html/` by default. Replace these with your own build tool (Sphinx, MkDocs, Jekyll, etc.).

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

**Upload + Deploy:** `upload-pages-artifact` packages the build output as a GitHub Pages artifact. `deploy-pages` publishes it.

The `if:` guard is critical — without it, PR builds would also deploy, overwriting your production site. The `id: deployment` is referenced by the `environment.url` at the top to display the URL.

## Step 3: Verify

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

## Common Pitfalls

| Problem | Cause | Fix |
|---------|-------|-----|
| `Get Pages site failed` | Pages not enabled in repo settings | Enable Pages with source "GitHub Actions" (Step 1) |
| `Failed to spawn: pytest` | Test deps not installed | Use `uv sync --frozen --dev` (not just `--frozen`) |
| Assets/CSS broken on site | Missing base URL for subpath | Ensure `BASE_URL` env var is set and `configure-pages` runs before build |
| Org Pages settings only shows "Verified domains" | Looking at org-level settings | Go to the **repository** settings instead |
