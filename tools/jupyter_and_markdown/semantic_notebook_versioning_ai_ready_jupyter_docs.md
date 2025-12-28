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
Version: 0.1.0  
Birth: 2025-12-28  
Last Modified: 2025-12-28

---

+++

## Purpose

+++

To enable clean Git diffs, prevent notebook metadata noise, and provide high-fidelity Markdown inputs for SLM/LLM assistants (e.g., `aider`) while preserving execution state.

:::{important}
It is supposed that you have already configured your environment for this repository with the [*environment configuration scripts*](helpers/scripts/environment_setup_scripts/).

* **Why:** The central JupyterLab server keeps your workspace stable. Even if a specific project's dependencies break, your "IDE" remains functional.
:::

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
~/venv/jupyter/bin/jupyter-lab -V
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

For Aider, the **Markdown file** is always the intended source of truth. To achieve full automation where **Aider** can perform auto-commits without being blocked, you must use the **active fix** pre-commit strategy which updates the files and continues.

Add a **local hook** that explicitly prioritizes the Markdown file if a conflict is detected.

`.pre-commit-config.yaml`:

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

* **Why this works for Aider:**

Since Aider modifies the `.md` file, its timestamp will be newer. This local hook runs via `uv` (using your established environment) and forces the `.ipynb` to match the `.md` before the commit finishes.

1. **Aider** writes to `notebook.md` and runs `git commit`.
2. **Pre-commit** interrupts and runs `jupytext --sync`.
3. **Jupytext** sees `notebook.md` is newer, so it updates the JSON in `notebook.ipynb`.
4. **Git** includes both the `.md` and the updated `.ipynb` in the final commit automatically.

+++

:::{seealso} Standard pre-commit-hook
:class: dropdown
:open: false
The default hook identifies the problem but doesn't "stage" the fixed file back into your commit. It is safer but it breaks the automation, i.e. aider will not be able to make auto-commits when editing markdown files, so implement it instead of the proposed method if you are really sure you will resolve conflicts manually.

Create a `.pre-commit-config.yaml` in your repository root to automate file synchronization.
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

### Activate

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

## **Phase 3: Git Attributes (The Diff Filter)**

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

### Real-World Example: "The Data Science Team Review"

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

File: `.github/workflows/verify-docs.yml`. Run the check **only on changed notebooks**:

```yaml
- name: Get changed notebooks
id: nb-changed
run: |
  echo "notebooks=$(git diff --name-only HEAD^ HEAD | grep '\.ipynb$' | tr '\n' ' ')" >> $GITHUB_OUTPUT

- name: Verify Notebook Synchronization
if: steps.nb-changed.outputs.notebooks != ''
run: |
  pip install "jupytext==1.16.0"
  jupytext --check --sync ${{ steps.nb-changed.outputs.notebooks }}
```

+++

### Why Pre-commit Alone Is Not Sufficient

#### 1. Pre-commit hooks can be bypassed
- `git commit --no-verify` skips all pre-commit hooks.
- New or rushed engineers may disable hooks temporarily.
- Automated scripts or IDE-based commits (e.g., VS Code Git UI) sometimes skip hooks if not properly configured.

> 🔒 **CI is the only enforcement point you can’t opt out of.**

#### 2. Merge conflicts break sync silently
- During a merge or rebase, `.ipynb` and `.md` may diverge **without any local edit**.
- Pre-commit only runs on *new commits*, not on *incoming changes* from `git pull` or PR merges.
- Only CI (or a dedicated merge check) can catch this **post-merge drift**.

#### 3. Team heterogeneity
- Not all contributors may run `pre-commit install` (e.g., external collaborators, CI-generated commits).
- A CI gate ensures **uniform enforcement**, regardless of local setup.

#### Best Practice Alignment

- **GitOps Principle**: *“Trust, but verify.”* Pre-commit is trust; CI is verification.
- **MLOps Standard**: Leading projects (e.g., Jupyter Book, MLflow, Hugging Face examples) **combine pre-commit + CI validation** for notebook workflows.
- **ISO 29148**: Ensures *verifiability* of documentation artifacts — a CI check provides **independent traceability**.

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

### Why this is "AI-Ready"

+++

If you are using an AI coding assistant like **Aider**, your workflow looks like this:

1. **AI Edit:** You tell Aider: *"Change the plotting colors in my_notebook.md to blue."*
2. **Aider saves the `.md`:** Aider only sees and edits the clean Markdown file.
3. **Git Sync:** When you go to commit, the **Sync Guard** (pre-commit) sees that the `.md` is newer than the `.ipynb`. It automatically pushes the AI's changes into the JSON of the `.ipynb`.
4. **Result:** Your notebook is now updated with the AI's code without you ever opening the JSON or manually syncing.

+++

### The Pull Request Experience

+++

When you push to GitHub, the workflow pays off for the **Reviewer**:

* **Reviewer opens the PR:** They see two files changed.
* **They click the `.md`:** They see a clean, line-by-line diff of your logic changes.
* **They ignore the `.ipynb`:** Because of your `.gitattributes`, GitHub collapses the `.ipynb` file. It's treated as an "artifact" (the execution state), while the `.md` is treated as the "source code."

+++

### Summary

+++

| File | Commit? | Why? |
| --- | --- | --- |
| **`.ipynb`** | **Yes** | Stores your execution results, plots, and metadata for other developers to run. |
| **`.md`** | **Yes** | Acts as the "Source of Truth" for Git diffs, Code Reviews, and AI assistants. |

| Task | Action | Result |
| --- | --- | --- |
| **Development** | Edit and execute `.ipynb` as usual. | Jupytext updates `.md` on save. |
| **Code Review** | Review the `.md` file in the PR. | Clean, semantic, line-based diffs. |
| **AI Assistance** | Feed the `.md` file to `aider`. | Token-efficient input; zero JSON noise. |
| **Onboarding** | Read `.md` files in the repository. | Instant understanding without a kernel. |

+++

### Semantic Notebook Versioning &  **Critical Maintenance Notes**

+++

* **Conflict Resolution**: If a merge conflict occurs, resolve it within the `.md` file. The pre-commit hook will then propagate those changes back to the `.ipynb`.
* **Sync Logic**: The `--sync` flag updates both files based on the **most recent timestamp**. Ensure your system clock is accurate when working across distributed environments.

+++

:::{iframe} https://www.youtube.com/embed/J5yW-NEJp5Q
:width: 100%
:::
