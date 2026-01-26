---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.0
kernelspec:
  name: bash
  display_name: Bash
  language: bash
---

# Layer 3: Prompts-as-Infrastructure

+++

---

Owner: Vadim Rudakov, rudakow.wadim@gmail.com  
Version: 0.1.1  
Birth: 2026-01-26  
Last Modified: 2026-01-26

---

+++

This directory contains structured prompt files and tooling for the AI Engineering Book project.

The directory is under initial development. Currently here are the monolithic prompts that must be refactored to the block prompts.

The prompts are stored and transported via JSON format which is natively machine-readable and highly testable for errors. Before pass it to the LLM it is very advised to convert them into YAML format with minimum markup symbols which is noise for the transformer. Use the [`prepare_prompt.py`](#prepare-prompt-section) script for this cleaning.

+++

## **1. Directory Structure**

```{code-cell}
tree . --gitignore -I "*.md"
```

## **2. Tools**

+++

(prepare-prompt-section)=
### Prepare Prompt Suite

+++

The [`prepare_prompt.py`](/tools/scripts/prepare_prompt.py) script converts JSON prompt files to LLM-friendly formats.

**Location:** `tools/scripts/prepare_prompt.py`, verify:

```{code-cell}
ls ../../tools/scripts/prepare_prompt.py
```

**Usage:**

```bash
# Basic usage (YAML-like output)
uv run tools/scripts/prepare_prompt.py consultants/devops_consultant.json

# Plain text output
uv run tools/scripts/prepare_prompt.py consultants/devops_consultant.json --format plain

# From stdin
cat consultants/devops_consultant.json | uv run tools/scripts/prepare_prompt.py --stdin
```

**What it does:**
- Removes the `metadata` field (version info, dates, etc.)
- Strips special characters (`*`, `'`, `"`, `` ` ``, `#`)
- Converts JSON to YAML-like readable format

**Full documentation:** [prepare_prompt_py_script.ipynb](/tools/docs/scripts_instructions/prepare_prompt_py_script.ipynb)

+++

## **3. Consultant Prompt Files**

+++

Each consultant JSON file follows a standard structure:

```json
{
  "metadata": { ... },           // Version info (stripped by prepare_prompt.py)
  "input_protocol": { ... },     // How the consultant handles input
  "consultant_persona": { ... }, // Role, tone, principles
  "target": { ... },             // Audience and user profile
  "consulting_protocol": { ... }, // Methodology and verification
  "output_protocol": { ... },    // Response structure
  "USER_INPUT": "..."            // Placeholder for user input
}
```
