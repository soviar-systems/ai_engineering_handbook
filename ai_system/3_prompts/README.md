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

# Prompts-as-Infrastructure

This directory contains structured prompt files and tooling for the AI Engineering Book project.

## Directory Structure

```{code-cell}
tree .
```

## Tools

### Prepare Prompt Script

The `prepare_prompt.py` script converts JSON prompt files to LLM-friendly formats.

**Location:** `tools/scripts/prepare_prompt.py`

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

## Consultant Prompt Files

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
