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
Version: 0.3.1  
Birth: 2025-12-28  
Last Modified: 2025-12-29

---

+++

## **Introduction**

+++

### Purpose

+++

To enable clean Git diffs, prevent notebook metadata noise, and provide high-fidelity Markdown inputs for SLM/LLM assistants (e.g., `aider`) while preserving execution state.

:::{important}
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
- CI integrity validation**

is classified as **Production-Ready** because it:  

- ✅ **Runs fully on CPU/local stack** (uv, JupyterLab, Jupytext CLI)  
- ✅ **Introduces zero vendor lock-in** (open formats: MyST Markdown, standard Jupyter)  
- ✅ **Integrates into GitOps/CI pipelines** (pre-commit + GitHub Actions)  
- ✅ **Produces version-controllable, LLM-efficient inputs** (clean `.md` for aider/SLMs)  

All components are **traceable to ISO/IEC/IEEE 29148** requirements for *unambiguous, verifiable, and maintainable specification artifacts*, and comply with **SWEBOK Quality-2.1** (verifiability of development artifacts). It is a **minimal, auditable, and enforceable workflow** for AI engineering teams operating at the edge.

+++

## **Phase 1: Environment Provisioning**

+++

The repository comes with all files configured. But we reproduce some configuration steps so you understand what happens under the hood.

After cloning the repo run from within the repo's root directory:

```bash
uv sync
```

All the needed dependencies will be installed to the project's `.venv`, for this configuration they are:

- `jupytext`,
- `pre-commit`.

:::{important}
Restart your JupyterLab server after installation for the pairing commands to appear in the palette.
:::

The configuration described in this instruction was tested in this environment:

```{code-cell}
grep -i 'pretty' /etc/os-release
```

```{code-cell}
uv -V
```

## **Phase 2: Mandatory Pairing & Automation**

+++

To ensure the LLM assistant can read the semantic content of your work, every engineer must initialize notebook [pairing](https://github.com/mwouts/jupytext/blob/main/docs/paired-notebooks.md).

+++

### Automate Jupytext Defaulting

+++

Add to the `pyproject.toml` file in the **root of your repo**:

```toml
[tool.jupytext]
formats = "ipynb,md:myst"
```

Now, when you open a notebook inside this folder using the central JupyterLab, Jupytext looks "up" the directory tree. It finds this file and automatically applies the "Pair with MyST" setting.

+++

:::{tip} Manual Alternative
:class: dropdown
:open: false
If you ever need to do this operation manually (which is discouraged by our philosophy), in JupyterLab session open the Command Palette (`Ctrl+Shift+C`) and select:

```
Pair with myst md
```
:::{figure} ./images/Screenshot_20251228_194236.png
:width: 100%
:::
:::

+++

### Pre-commit hook: Sync Guard

+++

> "Jupyter keeps paired `.py` and `.ipynb` files in sync, but the synchronization happens only when you save the notebook in Jupyter. If you edit the `.py` file manually, then the `.ipynb` file will be outdated until you reload and save the notebook in Jupyter, or execute `jupytext --sync`."
> 
> -- [Documentation](https://github.com/mwouts/jupytext/blob/main/docs/using-pre-commit.md)

The standard [`jupytext` hook](https://github.com/mwouts/jupytext/blob/main/docs/using-pre-commit.md) is designed to be **safe rather than aggressive**. When it detects that *both* the `.ipynb` and the `.md` have changed (or are both staged), it stops and asks you to choose a side to avoid accidentally overwriting your work.

For Aider, the **Markdown file** is always the intended source of truth. Add a **local hook** that that leverages our existing `uv` environment and explicitly prioritizes the Markdown file if a conflict is detected.

Create a `.pre-commit-config.yaml` in your repository root to automate file synchronization.

```yaml
repos:
  - repo: local
    hooks:
      - id: jupytext-sync
        name: Jupytext Sync (Auto-Fix)
        entry: uv run jupytext --sync
        language: system
        files: \.(ipynb|md)$
        pass_filenames: true
```

**Why we use a `local` hook instead of the official one**

Since Aider modifies the `.md` file, its timestamp will be newer. This local hook runs via `uv` (using your established environment) and forces the `.ipynb` to match the `.md` before the commit finishes.

1. **Aider** writes to `notebook.md` and runs `git commit`.
1. **Pre-commit** interrupts and runs `jupytext --sync`.
1. **Jupytext** sees `notebook.md` is newer, so it updates the JSON in `notebook.ipynb`.
1. **Git** includes both the `.md` and the updated `.ipynb` in the final commit automatically.

+++

:::{seealso} Standard Pre-Commit-Hook Problem
:class: dropdown
:open: false
The official `jupytext` hook from their GitHub repository often fails because it runs in an isolated environment that ignores your local settings and can "hallucinate" formatting differences (like `kernelspec` indentation) that don't actually exist on your disk failing to pass the commit. The conflict becomes unresolvable. Reasons for this behavior are:

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

:::{hint} Aider Integration Hint
:class: dropdown
:class: false
For users of the `aider` AI assistant, this hook is critical. When Aider modifies a `.md` file, this hook ensures the `.ipynb` execution artifact is updated before the commit is finalized, maintaining repository integrity automatically.
:::

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

### Why the automated approach is the correct behavior

+++

Most developers treat `pre-commit` as a "fix-it" tool, but it was architected as a "gatekeeper."

This approach represents the "gold standard" for a synchronized documentation workflow.

* **Safety via Stashing**: The `pre-commit` tool stashed your unstaged changes to ensure the hook ran against a clean state.
* **Successful Sync**: "Jupytext Sync (Auto-Fix).....Passed" indicates that the hook successfully reconciled the `.ipynb` and `.md` files before the commit was finalized.
* **Unified Commit**: Note the line `2 files changed`. Even if Aider (or you) only specifically targeted one file, the hook ensured that **both** the execution state (`.ipynb`) and the semantic source (`.md`) were committed together.
* **Zero Manual Intervention**: This is the key to "Aider-readiness." The automation resolved the metadata inconsistencies that blocked you previously.

+++

### Pre-commit work real example

+++

Let's change the md file, add it to index without its ipynb pair, and try to commit. We get this:

```bash
$ git commit -m "WIP: test pre-commit hook on md file"
[WARNING] Unstaged files detected.
[INFO] Stashing unstaged files to /home/user/.cache/pre-commit/patch1766964037-81260.
Jupytext Sync (Auto-Fix).................................................Failed
- hook id: jupytext-sync
- files were modified by this hook

[jupytext] Reading tools/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.md in format md
[jupytext] Loading tools/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.ipynb
[jupytext] Unchanged tools/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.ipynb
[jupytext] Updating tools/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.md

[INFO] Restored changes from /home/user/.cache/pre-commit/patch1766964037-81260.
```

This failure is actually the "Sync Guard" working exactly as intended. The hook acts as a **gatekeeper**, ensuring you explicitly resolve the inconsistency before the files are permanently recorded in Git history.

**The Final Resolution**

To clear this error and complete your commit, follow these steps:

1. **Re-stage the files** now that they are perfectly aligned:
    ```bash
    $ git add tools/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.ipynb tools/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.md
    ```

3. **Commit again**:
    ```bash
    $ git commit -m "WIP: test pre-commit hook on md file"
    [WARNING] Unstaged files detected.
    [INFO] Stashing unstaged files to /home/user/.cache/pre-commit/patch1766964182-81431.
    Jupytext Sync (Auto-Fix).................................................Passed
    [INFO] Restored changes from /home/user/.cache/pre-commit/patch1766964182-81431.
    [feature/blas-article ddcad31] WIP: test pre-commit hook on md file
    2 files changed, 35 insertions(+), 65 deletions(-)
    ```

Your commit was successful, and the "Gatekeeper" has officially cleared your changes.

To see exactly what the automation did "under the hood," you can run:

```bash
$ git show --name-only
```

You will see that both files were included in the commit. This confirms that your "Source of Truth" (`.md`) is perfectly mirrored in your "Execution Artifact" (`.ipynb`).

+++

## **Phase 3: Git Attributes (The Diff Filter)**

+++

### .gitattributes configuration

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

+++

### Why it is important

+++

In a standard setup, Git treats every file equally, but for Jupyter Notebooks, this creates a problem because `.ipynb` files are massive JSON objects filled with metadata, execution counts, and base64-encoded images that make code reviews impossible.

By using these `.gitattributes`, you are telling Git to **ignore the noise** and focus on the **human-readable** part of your work.

+++

### Real-World Example: The Data Science Team Review

+++

Imagine you are a Data Engineer working on a project called `data_cleaning.ipynb`. You change one line of code: you change `drop_na()` to `fillna(0)`.

| Aspect | Without Git Attributes | With Git Attributes |
|--------|------------------------|----------------------|
| **Pull Request Diff** | 500+ lines of changes showing mostly JSON metadata (execution counts, cell IDs, binary strings) | Clean text-only diff showing only actual code changes |
| **Code Change Visibility** | Actual code change (e.g., `fillna(0)`) buried in middle of JSON block | Exact line highlighted: `- drop_na()` and `+ fillna(0)` |
| **Reviewer Experience** | Reviewer fatigue - must scroll through pages of noise to find logic changes | Clean document view - immediately sees semantic changes |
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

+++

## **Phase 4: CI Validation (The Safety Net)**

+++

To prevent out-of-sync pushes from bypassing local hooks, add this check to your CI pipeline (e.g., GitHub Actions).

File: `.github/workflows/verify-docs.yml`:

```yaml
      # --- 1. INTEGRITY CHECK (Enforced on all branches) ---
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Verify Notebook Synchronization
        run: |
          pip install "jupytext==1.18.1"

          # Find all notebooks excluding hidden and venv dirs
          NOTEBOOKS=$(find . -type f -name "*.ipynb" \
            ! -path "*/.*" \
            ! -path "*/venv/*" \
            ! -path "*/.venv/*" \
            ! -path "*/pr/*" \
            ! -path "*/old/*")

          if [ -n "$NOTEBOOKS" ]; then
            echo "Checking synchronization for: $NOTEBOOKS"
            # --test is the professional standard for CI:
            # It fails with a non-zero exit code if the .ipynb and .md are
            # out of sync.
            jupytext --test --to md $NOTEBOOKS
          else
            echo "No active notebooks found. Skipping."
          fi
```

:::{caution} Caution: Version drift
:class: dropdown
:open: false
Make sure your local Jupytext version (`/pyproject.toml`) and the CI version (`1.18.1`) stay matched to avoid tiny metadata format differences that could trigger false negatives.
:::

This provides:

1. **Immediate Feedback for Aider:** When you are in a feature branch, Aider will often auto-commit. If it fails to sync properly, GitHub will notify you immediately. You can fix the sync drift on the spot before the branch history gets too messy.
2. **No "Double" Maintenance:** Since you are solo, you don't need separate "CI" and "CD" files. This single file acts as both your quality gatekeeper and your delivery driver.
3. **The `if` Guard:** By using `if: github.ref == 'refs/heads/main'`, you effectively "turn off" the expensive and destructive steps (Building and Rsyncing to production) when you are just experimenting in a side branch.

:::{important} The "Aider" Connection
If you keep this Action in place, Aider (or any other AI tool) will be forced to play by the rules. If Aider makes a mistake and only edits the Markdown, the CI will fail, providing a clear signal that a `jupytext --sync` is required.
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

## **Phase 5: Workflow for AI Engineering**

+++

In a real-world project, your workflow transitions from **active coding** to **version control** using the automation you have built.

- Keep both `.ipynb` and `.md` in Git
- Use `.md` for diffs, PRs, and `aider` input
- Use `.ipynb` as the source for `myst build` (so outputs appear)
- Ensure `.ipynb` outputs are up-to-date before merge (via team discipline or CI execution)

This gives you:
- Clean diffs ✅  
- LLM-friendly input ✅  
- Rich, output-inclusive published docs ✅

Here is exactly what happens when you decide to commit your changes.

+++

### The "Single-Save" Workflow

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
    git commit -m "Refactor data cleaning logic"
    ```

    * **Pre-commit Trigger:** Your `pre-commit` hook kicks in. It runs `jupytext --sync`. If you accidentally edited the `.md` file with another tool (like VS Code or `aider`) and forgot to sync it back to the `.ipynb`, the hook ensures they are identical before the commit is finalized.

+++

### AI-Assisted Workflow (e.g., Aider)

+++

If you are using an AI coding assistant like **Aider**, your workflow looks like this:

1. **AI Edit:** You tell Aider: *"Change the plotting colors in my_notebook.**md** to blue."*

1. **Aider saves the `.md`:** Aider modifies the clean Markdown file and usually attempts to commit.

1. **The Sync Check:**
    * **If you have the Jupytext plugin active:** Your local editor will likely sync the `.ipynb` immediately.
    * **If not:** The **Sync Guard** (pre-commit) will stop the commit and warn you that the files are out of alignment.

1. **Manual Alignment (The "Standard" Way):**
    If the commit is rejected, simply run:
    ```bash
    uv run jupytext --sync my_notebook.md
    git add my_notebook.ipynb
    git commit
    ```

1. **Result:** Your repository remains high-integrity. The AI’s logic is captured in the `.md` for easy review, and the `.ipynb` is updated and ready for execution.

:::{tip} Pro-Tip for Aider Users
:class: dropdown
:class: false
To make this even smoother, you can add a "hint" to your `.aider.conf.yml` or your system prompt:

> *"After editing any .md file, always run 'jupytext --sync <file>' to ensure the paired notebook is updated."*

To make this seamless, we can use Aider's `scripts` or `lint` functionality. By adding this to your configuration, Aider will treat a desynced notebook as a "linting error" and fix it automatically before it even attempts to commit.

**The `.aider.conf.yml` Snippet**

Place `.aider.conf.yml` file in your project root. This configuration tells Aider to run the sync command whenever it modifies a file that has a notebook pair.

```yaml
# .aider.conf.yml

# Run Jupytext sync as a 'lint' step after Aider makes changes
lint-cmd:
  - "md: uv run jupytext --sync"
  - "ipynb: uv run jupytext --sync"

# This ensures Aider only commits once the files are perfectly aligned
auto-lint: true
```

The workflow is now fully hands-off:

1. **AI Edit:** You tell Aider: *"Update the loss function in foundations.md."*
2. **Auto-Sync:** Aider finishes the edit. Because of our `lint-cmds` config, Aider automatically runs `jupytext --sync` behind the scenes.
3. **Atomic Commit:** Aider sees that both the `.md` and the `.ipynb` have changed. It stages **both** and commits them together.
4. **Sync Guard Approval:** The pre-commit hook runs, sees that the files are already perfectly in sync, and allows the commit to pass instantly.
:::

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

## **Final Setup Checklist**

+++

To wrap up this entire "Engineering Foundation" phase, ensure these four files are in your root:

1. **`.pre-commit-config.yaml`**: With the official Jupytext hook.
2. **`.github/workflows/build-and-deploy.yml`**: With the `--test --sync` integrity check.
3. **`pyproject.toml`** (or `jupytext.toml`): With `formats = "ipynb,md:myst"`.
4. **`.aider.conf.yml`**: With the `lint-cmds` sync automation.

+++

:::{iframe} https://www.youtube.com/embed/J5yW-NEJp5Q
:width: 100%
:::
