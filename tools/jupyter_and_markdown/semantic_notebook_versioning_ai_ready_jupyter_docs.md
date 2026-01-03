---
jupytext:
  formats: ipynb,md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.18.1
kernelspec:
  name: bash
  display_name: Bash
  language: bash
---

# Semantic Notebook Versioning: AI-Ready Jupyter Docs Workflow

+++

---

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.4.0  
Birth: 2025-12-28  
Last Modified: 2026-01-03

---

+++

## **Introduction**

+++

### Purpose

+++

To enable clean Git diffs, prevent notebook metadata noise, and provide high-fidelity Markdown inputs for SLM/LLM assistants (e.g., Aider) while preserving execution state.

:::{attention}
It is supposed that you have already configured your environment for this repository with the [*environment configuration scripts*](helpers/scripts/environment_setup_scripts/).

* **Why:** The central JupyterLab server keeps your workspace stable. Even if a specific project's dependencies break, your "IDE" remains functional.
:::

+++

### Substantiation of the Approach

+++

This workflow is engineered to satisfy **industrial-grade MLOps criteria** under the constraints of Small Language Model (SLM) development environments (1B–14B parameters, CPU/RAM-limited, GitOps-native). It adheres to the **Simplest Viable Architecture (SVA)** principle.

The proposed methodology—semantic notebook versioning via **Jupytext paired `.md`/`.ipynb` artifacts**, enforced by 
- pre-commit sync guards, 
- `.gitattributes` diff suppression, and 
- CI integrity validation

is classified as **Production-Ready** because it:  

- ✅ **Runs fully on CPU/local stack** (uv, JupyterLab, Jupytext CLI)  
- ✅ **Introduces zero vendor lock-in** (open formats: MyST Markdown, standard Jupyter)  
- ✅ **Integrates into GitOps/CI pipelines** (pre-commit + GitHub Actions)  
- ✅ **Produces version-controllable, LLM-efficient inputs** (clean `.md` for Aider/SLMs)  

All components are **traceable to ISO/IEC/IEEE 29148** requirements for *unambiguous, verifiable, and maintainable specification artifacts*, and comply with **SWEBOK Quality-2.1** (verifiability of development artifacts). It is a **minimal, auditable, and enforceable workflow** for AI engineering teams operating at the edge.

+++

### Files to work with

+++

1. UV environment: `pyproject.toml`
1. Aider:
    - `.aider.conf.yml`
    - `aider.CONVENTIONS`
1. Git:
    - `.github/workflows/deploy.yml`
    - `.gitattributes`
    - `.pre-commit-config.yaml`
    - custom hooks in `helpers/scripts/hooks/`:
        - `jupytext-require-paired-staging.sh`
        - `jupytext-sync-auto-fix.sh`

:::{important}
For actual contents of the file inspect the original files in the repo, not the examples here.
:::

+++

## **Phase 1: Environment Provisioning**

+++

After cloning the repo run from within the repo's root directory:

1. Synchronize the environment: 
    ```bash
    uv sync
    ```
    
    All the needed dependencies will be installed to the project's `.venv`, for this configuration they are:
    
    - `jupytext`,
    - `pre-commit`.
    
    :::{important}
    Restart your JupyterLab server after installation for the pairing commands to appear in the palette.
    :::

1. Make the hooks executable:
    ```bash
    # make all shell scripts in repo executable in one shot
    find . -type f -name '*.sh' -exec chmod 0755 {} +
    ```

The configuration described in this instruction was tested in this environment:

```{code-cell}
grep -i 'pretty' /etc/os-release
```

The global uv:

```{code-cell}
uv -V
```

Central JupyterLab server:

```{code-cell}
~/venv/jupyter/bin/jupyter-lab -V
```

## **Phase 2: Mandatory Pairing**

+++

To ensure the LLM assistant can read the semantic content of your work, every engineer must initialize notebook [pairing](https://github.com/mwouts/jupytext/blob/main/docs/paired-notebooks.md).

+++

### Automate Jupytext Defaulting

+++

The `pyproject.toml` file in the **root of the repo** must contain these lines:

```toml
[tool.jupytext]
formats = "ipynb,md:myst"
```

When you open a notebook inside this folder using the central JupyterLab, Jupytext looks "up" the directory tree. It finds this file and automatically applies the "Pair with MyST" setting.

+++

:::{tip} Manual Alternative
:class: dropdown
:open: false
If you ever need to do this operation manually (which is discouraged by our philosophy), in JupyterLab session open the Command Palette (`Ctrl+Shift+C`) and select:

```
Pair with myst md
```
```{figure} ./images/Screenshot_20251228_194236.png
:width: 100%
```
:::

+++

## **Phase 3: Markdown Prirority Setup: The Git Attributes Diff Filter**

+++

Configure Git to treat the `.md` file as the primary source of truth for code reviews and LLM ingestion, while de-emphasizing the bulky `.ipynb` JSON.

File: `.gitattributes`:

```text
# Documentation/Logic: Primary Source for Diffs
*.md diff=markdown

# Execution/Output Artifact: Suppress in Diffs & PR UIs
*.ipynb linguist-generated=true
*.ipynb -diff
```

**Breaking Down the Code**

| Command | Real-World Meaning |
| --- | --- |
| `*.md diff=markdown` | Tells Git: "Treat this as a document. When it changes, show me the words and code lines like a normal text file." |
| `*.ipynb linguist-generated=true` | Tells GitHub: "This file was made by a machine, not a human." GitHub will often hide these files by default in PR statistics. |
| `*.ipynb -diff` | Tells Git: "Do not calculate a line-by-line diff for this file." It treats the notebook as a binary "blob" (like a JPEG), significantly speeding up your Git operations and keeping PRs clean. |

**Why it is important**

In a standard setup, Git treats every file equally, but for Jupyter Notebooks, this creates a problem because `.ipynb` files are massive JSON objects filled with metadata, execution counts, and base64-encoded images that make code reviews impossible.

By using these `.gitattributes`, you are telling Git to **ignore the noise** and focus on the **human-readable** part of your work.

+++

:::{tip} ### Real-World Example: The Data Science Team Review
:class: dropdown
:open: false
Imagine you are a Data Engineer working on a project called `data_cleaning.ipynb`. You change one line of code: you change `drop_na()` to `fillna(0)`.

| Aspect | Without Git Attributes | With Git Attributes |
|--------|------------------------|----------------------|
| **Pull Request Diff** | 500+ lines of changes showing mostly JSON metadata (execution counts, cell IDs, binary strings) | Clean text-only diff showing only actual code changes |
| **Code Change Visibility** | Actual code change (e.g., `fillna(0)`) buried in middle of JSON block | Exact line highlighted: `- drop_na()` and `+ fillna(0)` |
| **Reviewer Experience** | Reviewer fatigue - must scroll through pages of noise to find logic changes | Review your changes using git diff *.md for a human-readable experience; `.ipynb` files diff will appear as "Binary files differ." |
| **File Focus** | .ipynb file shows full JSON diff with all metadata changes | .md file becomes primary source (with `diff=markdown`) |
| **.ipynb File Handling** | Shows complete diff of JSON structure | Shows "Binary file modified" or "Large diff hidden" (with `-diff` attribute) |
| **AI/LLM Integration** | Wastes tokens reading 5,000+ lines of JSON metadata | Reads only 50 lines of pure Markdown/Python logic |
| **Versioning Approach** | Standard notebook versioning with all metadata | Semantic notebook versioning focusing on code/logic |

Now, if you run `git diff` on `.ipynb` file manually, you should see something like this:

```bash
git diff research/slm_from_scratch/01_foundational_neurons_and_backprop/01_foundations.ipynb

diff --git a/research/slm_from_scratch/01_foundational_neurons_and_backprop/01_foundations.ipynb b/research/slm_from_scratch/01_foundational_neurons_and_backprop/01_foundations.ipynb
index e2faef2..f7c4e92 100644

Binary files a/research/slm_from_scratch/01_foundational_neurons_and_backprop/01_foundations.ipynb and b/research/slm_from_scratch/01_foundational_neurons_and_backprop/01_foundations.ipynb differ
```
:::

+++

## **Phase 4: Pre-commit hook: Sync Guard**

+++

> "Jupyter keeps paired `.py` and `.ipynb` files in sync, but the synchronization happens only when you save the notebook in Jupyter. If you edit the `.py` file manually, then the `.ipynb` file will be outdated until you reload and save the notebook in Jupyter, or execute `jupytext --sync`."
> 
> -- [Documentation](https://github.com/mwouts/jupytext/blob/main/docs/using-pre-commit.md)

The standard [`jupytext` hook](https://github.com/mwouts/jupytext/blob/main/docs/using-pre-commit.md) is designed to be **safe rather than aggressive**. When it detects that *both* the `.ipynb` and the `.md` have changed (or are both staged), it stops and asks you to choose a side to avoid accidentally overwriting your work.

To automate file synchronization we created a `.pre-commit-config.yaml` in the repository root and two scripts in `helpers/scripts/hooks/` directory:

+++

### Activate pre-commit hook

+++

Run in your terminal:

```bash
uv run pre-commit install
``` 

Expected output is:
```
pre-commit installed at .git/hooks/pre-commit
```

+++

### Hook files example

+++

:::{seealso} `.pre-commit-config.yaml` example
:class: dropdown
:open: false 
```yaml
repos:
  - repo: local
    hooks:

      - id: require-paired-staging
        name: Require paired .md/.ipynb staging
        entry: ./helpers/scripts/hooks/jupytext-require-paired-staging.sh
        language: script
        fail_fast: true
        pass_filenames: false
        files: \.(md|ipynb)$
        stages: [pre-commit]

      - id: jupytext-sync
        name: Jupytext Sync (Auto-Fix)
        entry: ./helpers/scripts/hooks/jupytext-sync-auto-fix.sh
        language: script
        pass_filenames: false
        files: \.(md|ipynb)$
        stages: [pre-commit]
```
:::

+++

:::{seealso} `helpers/scripts/hooks/jupytext-require-paired-staging.sh` example
:class: dropdown
:open: false
```bash
#!/bin/bash
set -euo pipefail

main() {
    declare -a staged_md
    declare -a staged_notebooks

    # Get staged .md and .ipynb files
    read -ra staged_md <<< $(git diff --cached --name-only --diff-filter=AMR | \
        grep "\.md$")
    read -ra staged_notebooks <<< $(git diff --cached --name-only --diff-filter=AMR | \
        grep "\.ipynb$")

    # Check .md → .ipynb
    for md in "${staged_md[@]}"; do
      ipynb="${md%.md}.ipynb"
      if [[ ! "${staged_notebooks[*]}" =~ "${ipynb}" ]]; then
        echo "ERROR: ${md} is staged, but its pair ${ipynb} is not."
        echo "Run: git add ${ipynb}"
        exit 1
      fi
    done

    # Check .ipynb → .md
    for ipynb in "${staged_notebooks[@]}"; do
      md="${ipynb%.ipynb}.md"
      if [[ ! "${staged_md[*]}" =~ "${md}" ]]; then
        echo "ERROR: ${ipynb} is staged, but its pair ${md} is not."
        echo "Run: git add ${md}"
        exit 1
      fi
    done
}


main "$@"
```
:::

+++

:::{seealso} `helpers/scripts/hooks/jupytext-sync-auto-fix.sh` example
:class: dropdown
:open: false
```bash
#!/bin/bash
set -euo pipefail

main() {
    local -a staged_notebooks
    local base

    # Get staged files matching .md or .ipynb
    staged_notebooks=( $(git diff --cached --name-only --diff-filter=AMR | grep -E "\.(md|ipynb)$") )

    if [[ ${#staged_notebooks[@]} -eq 0 ]]; then
      exit 0  # No notebook files staged → skip
    fi

    # Sync and re-stage
    for file in "${staged_notebooks[@]}"; do
      # sync
      if ! uv run jupytext --sync "${file}"; then
          echo "Error: Failed to sync ${file}" >&2
          exit 1
      fi

      # re-stage
      base="${file%.*}"
      if ! git add "${base}.md"; then
          echo "Error: Failed to add ${base}.md" >&2
          exit 1
      fi
      if ! git add "${base}.ipynb"; then
          echo "Error: Failed to add ${base}.ipynb" >&2
          exit 1
      fi
    done
}


main "$@"
```
:::

+++

### Why we use a `local` hook instead of the official one

+++

Since Aider modifies the `.md` file, its timestamp will be newer. This local hook runs via `uv` (using the established environment) and forces the `.ipynb` to match the `.md` before the commit finishes.

+++

:::{note} Standard Pre-Commit-Hook Problem
:class: dropdown
:open: false
There is another problem with the  [*official `jupytext` hook*](https://github.com/mwouts/jupytext/blob/main/docs/using-pre-commit.md) from their GitHub repository. 

It often fails because it runs in an isolated environment that ignores your local settings and can "hallucinate" formatting differences (like `kernelspec` indentation) that don't actually exist on your disk failing to pass the commit. The conflict becomes unresolvable. Reasons for this behavior are:

* **Environment Isolation:** It creates a fresh environment that doesn't "see" your `pyproject.toml` or `uv` environment.
* **Metadata Sensitivity:** It is often too strict with Jupyter UI state (like `jp-MarkdownHeadingCollapsed`), leading to failed commits for non-code changes.
* **The Stalemate:** If timestamps match exactly, the official hook may skip syncing, whereas the **Local Hook** (using `uv run`) forces parity using your project-specific logic.

The default pre-commit hook is this:

```yaml
repos:
  - repo: https://github.com/mwouts/jupytext
    rev: v1.18.1
    hooks:
      - id: jupytext
        args: [--sync]
        description: "Synchronizes .ipynb and .md from the most recently modified source."
```
:::

+++

**Expected Behavior**

* **The Gatekeeper:** When you run `git commit`, the hook will check if your `.md` and `.ipynb` files are perfectly aligned.
* **Auto-Fix:** If they are out of sync, the hook will attempt to synchronize them using the most recently modified file as the source of truth.
* **Validation:** If the files were inconsistent, the commit will fail, allowing you to `git add` the newly synchronized files and try again.

+++

:::{tip} ### Pre-commit work real example
:class: dropdown
:open: false
Let's change the md file, add it to index without its ipynb pair, and try to commit. We get this:

```bash
$ git status -s
M tools/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.ipynb
M tools/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.md

$ git add tools/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.md

$ git commit
[WARNING] Unstaged files detected.
[INFO] Stashing unstaged files to /home/commi/.cache/pre-commit/patch1767052830-57149.
Jupytext Sync (Auto-Fix).................................................Failed
- hook id: jupytext-sync
- files were modified by this hook

[jupytext] Reading tools/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.md in format md
[jupytext] Loading tools/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.ipynb
[jupytext] Unchanged tools/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.ipynb
[jupytext] Updating tools/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.md

Require paired .md/.ipynb staging........................................Failed
- hook id: require-paired-staging
- exit code: 1

ERROR: tools/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.md is staged, but its pair tools/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.ipynb is not.
Run: git add tools/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.ipynb

[INFO] Restored changes from /home/commi/.cache/pre-commit/patch1767052830-57149.
```

This shows:
1. `jupytext-sync` **modified files** (rewrote `.md` to match `.ipynb` timestamp).
1. Pre-commit
    - detected unstaged changes
    - detected no pair  
    → **failed the hook**
    
    → **No commit occurs.** You **must re-stage**:

1. Re-stage one file again and try to commit:

    ```bash
    $ git add tools/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.md
    
    $ git commit
    [WARNING] Unstaged files detected.
    [INFO] Stashing unstaged files to /home/commi/.cache/pre-commit/patch1767052863-57238.
    Jupytext Sync (Auto-Fix).................................................Passed
    Require paired .md/.ipynb staging........................................Failed
    - hook id: require-paired-staging
    - exit code: 1
    
    ERROR: tools/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.md is staged, but its pair tools/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.ipynb is not.
    Run: git add tools/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.ipynb
    
    [INFO] Restored changes from /home/commi/.cache/pre-commit/patch1767052863-57238.
    ```

1. **Re-stage both files** and commit:
    ```bash
    $ git add tools/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.ipynb tools/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.md
    
    $ git commit -m "WIP: test pre-commit hook on md file"
    Jupytext Sync (Auto-Fix).................................................Passed
    Require paired .md/.ipynb staging........................................Passed
    [fix/34-jupytext-config-examples deb8b34] WIP: test pre-commit hook on md file
    2 files changed, 95 insertions(+), 33 deletions(-)
    ```

Your commit was successful, and the "Gatekeeper" has officially cleared your changes.

To see exactly what the automation did "under the hood," you can run:

```bash
$ git show --name-only
commit deb8b34f22b8936d8d78173f28d29cd095266692 (HEAD -> fix/34-jupytext-config-examples)
Author: Vadim Rudakov <lefthand67@gmail.com>
Date:   Tue Dec 30 04:46:54 2025 +0500

WIP: test pre-commit hook on md file

tools/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.ipynb
tools/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.md
```

You will see that both files were included in the commit. This confirms that your "Source of Truth" (`.md`) is perfectly mirrored in your "Execution Artifact" (`.ipynb`).
:::

+++

## **Phase 5: CI Validation (The Safety Net)**

+++

To prevent out-of-sync pushes from bypassing local hooks, add this check to your CI pipeline (e.g., GitHub Actions).

+++

:::{seealso} `.github/workflows/deploy.yml` example
:class: dropdown
:open: false
```yaml
name: build-and-deploy

on:
  push:
    # Universal trigger for team validation
    branches: ["**"]
    paths-ignore:
      - 'in_progress/*'
      - 'research/slm_from_scratch/old/*'
      - 'RELEASE_NOTES.md'
  # Allows you to trigger the build manually from the Actions tab
  workflow_dispatch:

jobs:
  validate-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
        with:
          # Fetches all history so jupytext can compare timestamps if needed
          fetch-depth: 0

      # --- 1. INTEGRITY CHECK (Enforced on all branches) ---
      - name: Install uv (Python package manager)
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          echo "$HOME/.local/bin" >> $GITHUB_PATH

      - name: Restore project environment using uv.lock
        run: uv sync --frozen

      - name: Verify Notebook Synchronization
        run: |
          # Only validate notebooks with a .md pair (your source of truth)
          for md in **/*.md; do
            if [[ -f "${md%.md}.ipynb" ]]; then
              echo "Testing: $md"
              uv run jupytext --to ipynb --test "$md"
            fi
          done

      # --- 2. DEPLOYMENT STEPS (Only runs on Main) ---
      - name: Setup Node.js
        if: github.ref == 'refs/heads/main'
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install MyST and Build
        if: github.ref == 'refs/heads/main'
        run: |
          npm install -g mystmd
          myst build --html

      - name: Deploy to Server via RSYNC
        if: github.ref == 'refs/heads/main'
        uses: easingthemes/ssh-deploy@main
        with:
          SSH_PRIVATE_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
          # -v (verbose) and -i (itemize-changes) provide good logs in
          # GitHub Actions
          ARGS: "-rlgoDzvc -i --delete"
          SOURCE: "_build/html/"
          REMOTE_HOST: ${{ secrets.SERVER_IP }}
          REMOTE_USER: ${{ secrets.SERVER_USER }}
          REMOTE_PORT: ${{ secrets.SERVER_SSH_PORT }}
          TARGET: "/home/containers/website/html"
```
:::

+++

### How to handle a failure on a branch

+++

If a branch push turns **Red** in GitHub:

1. Stay on your branch.
1. Run your local fix: `uv run jupytext --sync tools/path/to/notebook.ipynb`.
1. Re-stage both files: `git add path/to/notebook.ipynb path/to/notebook.md`.
1. Commit and push again.
1. The Red "X" will turn into a Green "Checkmark," signaling that your branch is "Safe for Main."

+++

### Why Pre-commit Alone Is Not Sufficient

+++

1. Pre-commit hooks can be bypassed
    - `git commit --no-verify` skips all pre-commit hooks.
    - New or rushed engineers may disable hooks temporarily.
    - Automated scripts or IDE-based commits (e.g., VS Code Git UI) sometimes skip hooks if not properly configured.

> 🔒 **CI is the only enforcement point you can’t opt out of.**

2. Merge conflicts break sync silently
    - During a merge or rebase, `.ipynb` and `.md` may diverge **without any local edit**.
    - Pre-commit only runs on *new commits*, not on *incoming changes* from `git pull` or PR merges.
    - Only CI (or a dedicated merge check) can catch this **post-merge drift**.

3. Team heterogeneity
    - Not all contributors may run `pre-commit install` (e.g., external collaborators, CI-generated commits).
    - A CI gate ensures **uniform enforcement**, regardless of local setup.

+++

## **Phase 6: Workflow for AI Engineering**

+++

In a real-world project, your workflow transitions from **active coding** to **version control** using the automation you have built.

- Keep both `.ipynb` and `.md` in Git
- Use `.md` for diffs, PRs, and Aider input
- Use `.ipynb` as the source for `myst build` (so outputs appear)
- Ensure `.ipynb` outputs are up-to-date before merge (via team discipline or CI execution)

This gives you:
- Clean diffs ✅  
- LLM-friendly input ✅  
- Rich, output-inclusive published docs ✅

Here is exactly what happens when you decide to commit your changes.

+++

### Human Workflow

+++

1. **Edit and Execute:** You work inside your `.ipynb` file using your central JupyterLab. You change a function and run the cell to see the output.

1. **Save (Ctrl+S):** When you save in JupyterLab, **Jupytext** immediately updates the paired `.md` file on your disk.
    * *Current state:* Both `.ipynb` and `.md` are updated.


1. **Stage Files for Git:** You go to your terminal or Git UI and add your changes:
    ```bash
    git add my_notebook.ipynb my_notebook.md
    ```

1. **The Commit (The Sync Guard):** You run your commit command:
    ```bash
    git commit -m "refactor: Update data cleaning logic"
    ```

    * **Pre-commit Trigger:** Your `pre-commit` hook kicks in. It runs `jupytext --sync`. If you accidentally edited the `.md` file with another tool (like VS Code or Aider) and forgot to sync it back to the `.ipynb`, the hook ensures they are identical before the commit is finalized.

+++

:::{tip}
If you've been editing the `.md` file externally while `.ipynb` file is opened, do not click 'Save' in a stale JupyterLab tab before committing, as this may update the `.ipynb` timestamp and cause `jupytext --sync` to favor the old notebook content.

**The Risk**: If an engineer has a background process or an IDE extension (like a linter) that "touches" the `.ipynb` after they finished editing the `.md` via Aider, the `--sync` command might overwrite the AI's work with the older notebook state.
:::

+++

### AI-Assisted Workflow with Aider

+++

For smooth work with Aider you need to configure two files:
- `.aider.conf.yml`
- `aider.CONVENTIONS`

:::{note} Alternative
:class: dropdown
:class: false
You can inject a system prompt while working with Aider, like this one:

> *"After editing any .md file, always run 'jupytext --sync <file>' to ensure the paired notebook is updated."*

But this is error prone, because you have to add it manually each time you run Aider.
:::

+++

#### lint-cmd: Configure Commit Workflow

+++

We use Aider's `scripts` or `lint` functionality. By adding this to `.aider.conf.yml`, we tell Aider to treat a desynced notebook as a "linting error" and fix it automatically.

This configuration tells Aider to run the sync command whenever it modifies a file that has a notebook pair.

```yaml
# .aider.conf.yml

# Run Jupytext sync as a 'lint' step after Aider makes changes
lint-cmd:
  - "md: uv run jupytext --sync"
  - "ipynb: uv run jupytext --sync"

auto-lint: true
```

The commit workflow is now fully hands-off:

1. **AI Edit:** You tell Aider: *"Update the loss function in foundations.md."*
2. **Auto-Sync:** Aider finishes the edit. Because of our `lint-cmds` config, Aider automatically runs `jupytext --sync` behind the scenes.
3. **Atomic Commit:** You stage **both** files and commit them together.
4. **Sync Guard Approval:** The pre-commit hook runs, sees that the files are already perfectly in sync, and allows the commit to pass instantly.

+++

:::{important} aider auto-commits off
:class: dropdown
:open: false
Aider’s Auto-Commits fail in our workflow because when it edits `notebook.md`, it:

1. Modifies the `.md` file.
2. (Optionally) runs `lint-cmd` → updates `.ipynb` in working tree.
3. **Stages only the file it directly edited** (`notebook.md`).
4. **Does not stage `.ipynb`**, because aider **never touched it directly**.

Then it runs `git commit` → pre-commit fails → aider silently **aborts** to commit.

Even with `auto-lint: true`, **aider cannot stage files it didn’t edit**. This is a **fundamental limitation** of aider’s architecture.

> 🚫 **aider’s auto-commits are incompatible with paired notebook workflows** that require atomic multi-file commits.

Thus, **disable aider commits** and treat it as an *editor only*:

```yaml
# .aider.conf.yml
auto-commits: false
```

Then:
1. Let aider edit `.md`.
2. Run `git add *.md`.
3. Run `git commit` → pre-commit syncs + fails.
4. Run `git add *.ipynb` → `git commit` → success.

This is **more reliable**, auditable, and aligns with **GitOps**.
:::

+++

#### aider.CONVENTIONS file

+++

For more information see [official documentation](https://aider.chat/docs/usage/conventions.html).

In the repo's root directory create a file `aider.CONVENTIONS`.

+++

##### ✅ Key Principles for aider-Centric `CONVENTIONS`

+++

1. **Ultra-concise**: Max 3–5 lines. aider’s context window is precious.
2. **Imperative tone**: Direct commands, no explanations.
3. **Syntax-prescriptive**: Explicitly state **what to preserve** and **what to never change**.
4. **No examples**: Examples consume tokens and may be reinterpreted as editable content.

+++

##### Instructions

+++

Add these instruction to the file:

```
You are editing a MyST Markdown notebook paired with Jupytext.
NEVER convert ```{code-cell} blocks to standard ```bash or ```python.
ALWAYS preserve the exact syntax: ```{code-cell}[optional-kernel].
NEVER alter, remove, or reformat MyST directive syntax.
```

**Rationale**: This is **178 tokens** (including newlines)—minimal, unambiguous, and fits cleanly in aider’s context without crowding the actual document.

+++

##### 🔧 Implementation Protocol

+++

1. **Save this as `aider.CONVENTIONS`** (distinct name avoids confusion with human docs).
2. **Inject into aider context** via:
    ```yaml
    # .aider.conf.yml
    read: aider.CONVENTIONS
    ```
    or in CLI:
    ```bash
    aider --read aider.CONVENTIONS your_notebook.md
    ```
3. **Keep human-facing conventions in a separate `CONVENTIONS.md`** (if needed).

Now `aider.CONVENTIONS` will be loaded to Aider automatically each time you start it.

:::{caution}
If you name the file with `.md` extension, do not forget to exclude this file from MyST build process and pre-commit hook validation.
:::

+++

##### ❌ What **Not** to Do

+++

- **Do not add a "convention" telling aider to `git add notebook.ipynb`**—aider doesn’t control staging logic directly; it relies on Git’s changed-file detection.
- **Do not add human-style instructions** like “always commit both”—aider ignores narrative, and your automation already guarantees the outcome.

+++

### The Pull Request Experience

+++

When you push to GitHub, the workflow pays off for the **Reviewer**:

* **Reviewer opens the PR:** They see two files changed.
* **They click the `.md`:** They see a clean, line-by-line diff of your logic changes.
* **They ignore the `.ipynb`:** Because of your `.gitattributes`, GitHub collapses the `.ipynb` file. It's treated as an "artifact" (the execution state), while the `.md` is treated as the "source code."

+++

### Semantic Notebook Versioning &  **Critical Maintenance Notes**

+++

* **Conflict Resolution**: If a merge conflict occurs, resolve it within the `.md` file. The pre-commit hook will then propagate those changes back to the `.ipynb`.
* **Sync Logic**: The `--sync` flag updates both files based on the **most recent timestamp**. Ensure your system clock is accurate when working across distributed environments.

+++

:::{iframe} https://www.youtube.com/embed/J5yW-NEJp5Q
:width: 100%
:::
