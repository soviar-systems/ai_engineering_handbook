# nbdiff: "git diff" for Jupyter Notebooks Version Control

---

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.1.0  
Birth: 2025-12-28  
Last Modified: 2025-12-28

---

This guide will walk you through using `nbdime` (specifically `nbdiff`) to manage Jupyter Notebooks. Standard git diffs are notoriously difficult to read because notebooks are stored as dense JSON files containing metadata and execution counts that obscure actual logic changes.

## 1. What is `nbdiff` and Why We Use It

Jupyter Notebooks (.ipynb) are JSON documents. When you change a single line of code or simply re-run a cell, a standard `git diff` shows a mess of structural changes, "id" updates, and metadata shifts.

We use `nbdiff` because it is **content-aware**. It understands the notebook structure and filters out the "noise" to show you only what matters:

* **Markdown Changes:** Clear text diffs of documentation and math.
* **Code Changes:** Logical changes to Python inputs.
* **Ignore Metadata:** It can ignore execution counts and cell IDs so you don't see diffs just because you clicked "Run".

## 2. Installation with `uv`

We use `uv` for fast, reliable Python tool management. To install the `nbdime` suite (which includes `nbdiff`) as a globally accessible tool:

```bash
uv tool install nbdime
```

This installs the following CLI tools:

* `nbdiff`: Terminal-based notebook comparison.
* `nbdiff-web`: Opens a side-by-side visual diff in your browser.
* `nbmerge`: Tools for resolving notebook merge conflicts.

## 3. How to Use `nbdiff`

### In a Git-like Manner

You can use `nbdiff` similarly to how you use `git diff` to compare commits or branches.

| Command | Explanation | Description |
|---------|---------|-------------|
| `nbdiff HEAD path/to/notebook.ipynb` | Compare a file to your last commit |
| `nbdiff 351b33e HEAD path/to/notebook.ipynb` | Compare two specific commits |
| `nbdiff-web 351b33e HEAD path/to/notebook.ipynb` | View changes visually (Recommended for Math/LaTeX) |

### Integrating with `aider`

[`aider`](/tools/ai_agents/handout_aider.md) is a pair-programming tool that works best when it can see clean diffs. To ensure your AI partner isn't confused by Jupyter JSON structure, follow these steps:

When you are in an `aider` session, the AI will now receive much cleaner diffs when it suggests changes to your notebooks. You can also explicitly ask `aider` to check the diff using the tool by running:

```bash
/run nbdiff HEAD path/to/notebook.ipynb
```

**Pro-tip:** If Aider struggles to edit a specific cell, use `nbdiff-web` to identify the specific "Cell Index" and tell Aider: *"In cell index 14, please update the LaTeX formula to include the bias term."*

## 4. Advanced Setup: Aliases & Configuration

### Default "Clean" Profiles

If you find that `nbdiff` still shows too much information (like `id` changes or large output blobs from print statements), you can configure it to always be "documentation-first."

Add these flags to your commands or aliases:

* `--ignore-metadata`: Hides changes to cell IDs and notebook-level metadata.
* `--ignore-outputs`: Hides changes in the `outputs` and `execution_count` fields.

**The "Clean Documentation" Command:**

```bash
nbdiff --ignore-metadata --ignore-outputs 351b33e HEAD path/to/notebook.ipynb
```

### Create a `nb-diff` alias

To make this behaviour default, create an alias in your `~/.bashrc` file:

```bash
vi ~/.bashrc
alias nbdiff="nbdiff --ignore-metadata --ignore-outputs"
:wq
```

## Summary Table for Quick Reference

| Task | Command |
| --- | --- |
| **Install** |  `uv tool install nbdime` |
| **Simple Diff** | `nbdiff old.ipynb new.ipynb` |
| **Git Commit Diff** | `nbdiff <hash> HEAD <file>` |
| **Visual/Web Diff** | `nbdiff-web <hash> HEAD <file>` |
