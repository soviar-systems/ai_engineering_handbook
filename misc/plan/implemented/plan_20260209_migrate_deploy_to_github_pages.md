# Plan: Migrate deploy.yml from SSH/rsync to GitHub Pages

## Context

ADR-26022 standardizes GitHub Pages as the canonical hosting for public documentation, deprecating the self-hosted SSH/rsync approach. The current `deploy.yml` uses `easingthemes/ssh-deploy@main` with SSH keys to rsync `_build/html/` to a private server. The vadocs repo already implements the GH Pages pattern and serves as the reference.

## Changes

### File: `.github/workflows/deploy.yml`

Restructure from single-job to two-job pipeline (matching vadocs pattern):

**1. Add workflow-level config:**
- `env.BASE_URL: /${{ github.event.repository.name }}` — required for GH Pages subpath (`/<repo>/`)
- `permissions: contents: read, pages: write, id-token: write` — OIDC auth for Pages
- `concurrency: group: 'pages', cancel-in-progress: false` — prevent parallel deployments

**2. Job 1: `validate`** (runs on all branches, as today)
- Checkout with `fetch-depth: 0`
- Install uv, restore env
- Jupytext sync check (`uv run tools/scripts/jupytext_sync.py --all --test`)

**3. Job 2: `build-deploy`** (needs: validate)
- Environment: `github-pages` with `url: ${{ steps.deployment.outputs.page_url }}`
- Checkout code
- `actions/configure-pages@v3`
- Setup Node.js 20, install mystmd, `myst build --html`
- `actions/upload-pages-artifact@v3` with `path: './_build/html'`
- `actions/deploy-pages@v4` (conditional: `if: github.ref == 'refs/heads/main'`)

**What's removed:**
- `easingthemes/ssh-deploy@main` action and all SSH secret references (`SSH_PRIVATE_KEY`, `SERVER_IP`, `SERVER_USER`, `SERVER_SSH_PORT`)

**What's preserved:**
- Trigger on all branches (`branches: ["**"]`) + `workflow_dispatch`
- `paths-ignore` list
- Jupytext sync validation step
- Node.js 20 + `myst build --html` build step

### File: `tools/docs/git/03_precommit_ci_validation_system.md`

Line 92 says `Build + Deploy | Main only | MyST build + RSYNC`. Update to `MyST build + GitHub Pages` to reflect the new deployment method.

### Verified correct — no changes needed:
- `tools/docs/git/github_pages_setup.md` — already accurate, matches vadocs pattern exactly (triggers, permissions, concurrency, actions versions, BASE_URL, conditional deploy)
- `myst.yml` — stays identical
- `quality.yml` — unaffected
- `.gitignore` — already has `_build`

## Manual steps required after merge

1. **GitHub repo settings** → Pages → Source: set to "GitHub Actions" (not "Deploy from a branch")
2. Optionally remove the now-unused secrets: `SSH_PRIVATE_KEY`, `SERVER_IP`, `SERVER_USER`, `SERVER_SSH_PORT`

## Verification

1. Push to a non-main branch → validate job runs, build-deploy builds but does NOT deploy
2. Push/merge to main → validate passes, build-deploy builds and deploys to GH Pages
3. Confirm site is live at `https://<org>.github.io/ai_engineering_handbook/`
