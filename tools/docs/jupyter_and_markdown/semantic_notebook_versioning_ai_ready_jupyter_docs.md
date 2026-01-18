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
Version: 0.5.0  
Birth: 2025-12-28  
Last Modified: 2026-01-18

---

+++

## **Introduction**

+++

### Purpose

+++

To enable clean Git diffs, prevent notebook metadata noise, and provide high-fidelity Markdown inputs for SLM/LLM assistants (e.g., Aider) while preserving execution state.

:::{attention}
It is supposed that you have already configured the central JupyterLab server (configuration scripts are in progress phase).

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
    - `/.aider.conf.yml`
    - `/CONVENTIONS.md`
1. Git:
    - `/.github/workflows/deploy.yml`
    - `/.gitattributes`
    - `/.pre-commit-config.yaml`
    - custom hook `/helpers/scripts/hooks/sync_and_verify.sh`

:::{important}
For actual contents of the file inspect the original files in the repo, not the examples here.
:::

+++

## **Phase 1: Environment Provisioning**

+++

### **Critical Architecture: Jupytext Installation Location**

+++

:::{danger}
**Jupytext MUST be installed in the central JupyterLab environment, NOT only in the project's `.venv`.**

**Why:** JupyterLab server extensions (like Jupytext) must be discoverable by the JupyterLab process. If installed only in a project's virtual environment, the central JupyterLab server cannot see the extension, and the pairing commands will not appear in the Command Palette.
:::

+++

### Step 1: Configure Central JupyterLab Environment

+++

Assuming your central JupyterLab is installed in `~/venv/jupyter`:

```bash
# Activate the central JupyterLab environment
source ~/venv/jupyter/bin/activate

# Install Jupytext into the central environment
pip install jupytext

# Verify installation
jupyter labextension list | grep jupytext

# Restart your JupyterLab server for changes to take effect
```

:::{important}
**Restart your JupyterLab server after installation** for the pairing commands to appear in the palette.
:::

+++

### Step 2: Configure Project Environment

+++

After cloning the repo, run from within the repo's root directory:

1. **Synchronize project dependencies:**
    ```bash
    uv sync
    ```
    
    This installs project-level dependencies to `.venv`:
    - `pre-commit` (required for Git hooks)
    - **Other project dependencies** (including project levelv Jupytext for synchronization in the project environment during the terminal level operations)
    
    :::{note}
    The project's `pyproject.toml` may list `jupytext` as a dependency for CLI operations (e.g., `uv run jupytext --sync`), but the **JupyterLab extension** must be installed in the central environment as shown in Step 1.
    :::

2. **Make hook scripts executable:**
    ```bash
    # Make all shell scripts in repo executable
    find . -type f -name '*.sh' -exec chmod 0755 {} +
    ```

+++

### Environment Verification

+++

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

Verify Jupytext is accessible from the central environment:

```{code-cell}
~/venv/jupyter/bin/jupytext --version
```

## **Phase 2: Mandatory Pairing: Automate Jupytext Defaulting**

+++

To ensure the LLM assistant can read the semantic content of your work, every engineer must initialize notebook [pairing](https://github.com/mwouts/jupytext/blob/main/docs/paired-notebooks.md).

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

:::{tip} Real-World Example: The Data Science Team Review
:class: dropdown
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
> — Jupytext official documentation

This means:
- If you edit the `.md` file in Aider → `.ipynb` is stale.
- If you open the `.ipynb` in Jupyter and save it → `.md` is up to date.
- If you commit without syncing → Git sees **two different versions** (one is outdated).

+++

### **The Pre-commit Hook as a Safety Guard**

+++

Before each commit, the hook runs:

```bash
jupytext --sync <file>
```

If the two files differ, the hook **fails** and the commit is blocked, forcing you to fix the inconsistency.

+++

### **Implementation**

+++

#### Option 1: Use Pre-commit Framework (Recommended)

+++

File: `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: jupytext-sync
        name: Jupytext Sync Check
        entry: bash -c 'uv run jupytext --sync'
        language: system
        files: '\.(ipynb|md)$'
        pass_filenames: true
```

Install the hook:

```bash
uv run pre-commit install
```

+++

#### Option 2: Manual Git Hook Script

+++

File: `.git/hooks/pre-commit`:

```bash
#!/usr/bin/env bash

set -e

# Find all staged .ipynb and .md files
staged_files=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(ipynb|md)$' || true)

if [[ -z "$staged_files" ]]; then
    exit 0
fi

# Run sync for each file
echo "$staged_files" | while read -r file; do
    if [[ -f "$file" ]]; then
        echo "Syncing: $file"
        uv run jupytext --sync "$file"
        
        # Re-stage if the sync modified the file
        git add "$file"
    fi
done

exit 0
```

Make it executable:

```bash
chmod +x .git/hooks/pre-commit
```

+++

## **Phase 5: CI Verification**

+++

To ensure that no desynchronized notebooks reach the main branch, add a CI check that validates all paired notebooks are in sync.

File: `.github/workflows/verify-notebooks.yml`:

```yaml
name: Verify Notebook Sync

on:
  pull_request:
    paths:
      - '**.ipynb'
      - '**.md'
  push:
    branches:
      - main

jobs:
  verify-sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install UV
        uses: astral-sh/setup-uv@v5
        
      - name: Sync notebooks
        run: |
          uv sync
          uv run jupytext --sync **/*.ipynb **/*.md
          
      - name: Check for changes
        run: |
          if ! git diff --exit-code; then
            echo "❌ Notebooks are out of sync!"
            echo "Run 'jupytext --sync' locally and commit the changes."
            exit 1
          fi
          echo "✅ All notebooks are in sync."
```

This workflow:
1. Syncs all notebooks
2. Fails the CI if any files changed (indicating they were out of sync)

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

2. **Save (Ctrl+S):** When you save in JupyterLab, **Jupytext** immediately updates the paired `.md` file on your disk.
    * *Current state:* Both `.ipynb` and `.md` are updated.


3. **Stage Files for Git:** You go to your terminal or Git UI and add your changes:
    ```bash
    git add my_notebook.ipynb my_notebook.md

    # or just
    git add my_notebook.*
    ```

4. **The Commit (The Sync Guard):** You run your commit command:
    ```bash
    git commit -m "refactor: Update data cleaning logic"
    ```

    * **Pre-commit Trigger:** Your `pre-commit` hook kicks in. It runs `jupytext --sync`. If you accidentally edited the `.md` file with another tool (like VS Code or Aider) and forgot to sync it back to the `.ipynb`, the hook ensures they are identical before the commit is finalized.

+++

:::{warning}
If you've been editing the `.md` file outside the JupyterLab while `.ipynb` file is opened, do not click 'Save' in a stale JupyterLab tab before committing, as this may update the `.ipynb` timestamp and cause `jupytext --sync` to favor the old notebook content.

**The Risk**: If an engineer has a background process or an IDE extension (like a linter) that "touches" the `.ipynb` after they finished editing the `.md` via Aider, the `--sync` command might overwrite the AI's work with the older notebook state.
:::

+++

### AI-Assisted Workflow with Aider

+++

For smooth work with Aider you need to configure two files:
- `.aider.conf.yml`
- `CONVENTIONS.md`

:::{note} Alternative
:class: dropdown
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
Aider's Auto-Commits fail in our workflow because when it edits `notebook.md`, it:

1. Modifies the `.md` file.
2. (Optionally) runs `lint-cmd` → updates `.ipynb` in working tree.
3. **Stages only the file it directly edited** (`notebook.md`).
4. **Does not stage `.ipynb`**, because aider **never touched it directly**.

Then it runs `git commit` → pre-commit fails → aider silently **aborts** to commit.

Even with `auto-lint: true`, **aider cannot stage files it didn't edit**. This is a **fundamental limitation** of aider's architecture.

> 🚫 **aider's auto-commits are incompatible with paired notebook workflows** that require atomic multi-file commits.

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

#### CONVENTIONS.md file

+++

For more information see [official documentation](https://aider.chat/docs/usage/conventions.html).

In the repo's root directory create a file `CONVENTIONS.md`.

+++

##### ✅ Key Principles for aider-Centric `CONVENTIONS`

+++

1. **Ultra-concise**: Max 3–5 lines. aider's context window is precious.
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

**Rationale**: This is **178 tokens** (including newlines)—minimal, unambiguous, and fits cleanly in aider's context without crowding the actual document.

+++

##### 🔧 Implementation Protocol

+++

1. **Save this as `CONVENTIONS.md`**.
2. **Inject into aider context** via:
    ```yaml
    # .aider.conf.yml
    read: CONVENTIONS.md
    ```
    or in CLI:
    ```bash
    aider --read CONVENTIONS.md your_notebook.md
    ```

Now `CONVENTIONS.md` will be loaded to Aider automatically each time you start it.

:::{caution}
Do not forget to exclude the `CONVENTIONS.md` file from the MyST build process. See `myst.yml` file.
:::

+++

##### ❌ What **Not** to Do

+++

- **Do not add a "convention" telling aider to `git add notebook.ipynb`**—aider doesn't control staging logic directly; it relies on Git's changed-file detection.
- **Do not add human-style instructions** like "always commit both"—aider ignores narrative, and your automation already guarantees the outcome.

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
