# nbdiff: "git diff" for Jupyter Notebooks Version Control

---

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.2.0  
Birth: 2025-12-28  
Last Modified: 2025-12-28

---

This guide explains how to use `nbdime` (specifically `nbdiff`) to manage Jupyter Notebooks effectively. Standard git diffs are notoriously difficult to read because notebooks are stored as dense JSON files containing metadata, cell IDs, and execution counts that obscure actual logic changes.

## 1. What is `nbdiff` and Why We Use It

Jupyter Notebooks (.ipynb) are JSON documents. When you change a single line of code or simply re-run a cell, a standard `git diff` shows a mess of structural changes. 

We use `nbdiff` because it is **content-aware**. It understands the notebook structure and filters out the "noise" to show you only what matters:

* **Markdown Changes:** Clear text diffs of documentation and rendered math.
* **Code Changes:** Logical changes to Python inputs, ignoring the JSON wrapper.
* **Ignore Metadata:** It can ignore execution counts so you don't see diffs just because you clicked "Run."

## 2. Installation with `uv`

We use `uv` for fast, reliable Python tool management. To install the `nbdime` suite (which includes `nbdiff`) as a globally accessible tool:

```bash
uv tool install nbdime
```

This installs the following CLI tools:

* `nbdiff`: Terminal-based notebook comparison.
* `nbdiff-web`: Opens a side-by-side visual diff in your browser (best for Math/LaTeX).
* `nbmerge`: Tools for resolving notebook merge conflicts.

## 3. Configuration: Native Git Integration

Instead of running a separate command, you can configure Git to use `nbdiff` automatically whenever you run `git diff` on a `.ipynb` file.

**To enable global Git integration:**

```bash
nbdime config-git --enable --global
```

Now, a standard `git diff` will output a clean, readable notebook summary instead of raw JSON.

## 4. How to Use `nbdiff`

### Common CLI Commands

| Command | Description |
| --- | --- |
| `nbdiff HEAD path/to/notebook.ipynb` | Compare current changes to the last commit. |
| `nbdiff 351b33e HEAD path/to/nb.ipynb` | Compare two specific commits. |
| `nbdiff-web 351b33e HEAD path/to/nb.ipynb` | View changes in a rich browser UI (Highly Recommended). |

### Integrating with `aider`

`aider` is a pair-programming tool that works best when it can see clean diffs. To ensure your AI partner isn't confused by Jupyter's JSON structure, use the following workflow:

1. **Check the diff:** If you want the AI to review your work, run:
```bash
/run nbdiff --ignore-metadata HEAD path/to/notebook.ipynb
```

2. **Targeted Edits:** If Aider struggles to find a cell, use `nbdiff-web` to find the **Cell Index** and prompt:

> *"In cell index 14, please update the LaTeX formula to include the bias term ."*

## 5. Advanced Setup: "Documentation-First" Aliases

If you are working on a research paper or documentation, you likely want to hide all code execution noise (output blobs and run counts) to focus on the text and logic.

### Create a "Clean" Alias

Add a "clean" version of nbdiff to your `~/.bashrc` or `~/.zshrc`:

```bash
# Add the alias
echo 'alias nbdiff-clean="nbdiff --ignore-metadata --ignore-outputs"' >> ~/.bashrc
# Refresh your shell
source ~/.bashrc
```

Now, running `nbdiff-clean` will hide all image data and execution numbers, showing only the code and markdown changes.

Or, if you want to integrate this behaviour to git, create a git alias:

```bash
git config --global alias.nbclean "nbdiff --ignore-metadata --ignore-outputs"
```

:::{caution} Be aware!
:class: dropdown
:open: false
Sometimes the output *is* the point of the commit (e.g., a final loss curve or a summary table). If you ignore outputs during the diff, you might miss that a code change broke the resulting data.

Also, if you ignore metadata during a merge, you might accidentally overwrite important kernel specifications required to run the notebook on another machine.
:::

## Summary Reference

| Task | Command |
| --- | --- |
| **Install** | `uv tool install nbdime` |
| **Simple Diff** | `nbdiff old.ipynb new.ipynb` |
| **Visual/Web Diff** | `nbdiff-web <hash> HEAD <file>` |
| **Ignore Noise** | `nbdiff --ignore-metadata --ignore-outputs` |
| **Git Integration** | `nbdime config-git --enable` |
