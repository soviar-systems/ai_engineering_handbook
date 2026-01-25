---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.0
kernelspec:
  name: python3
  display_name: Python 3 (ipykernel)
  language: python
---

# Layer 3: Prompts as Infrastructure

+++

This directory is under initial development. Currently here are the monolithic prompts that must be refactored to the block prompts.

The prompts are stored and transported via JSON format which is natively machine-readable and highly testable for errors. Before pass it to the LLM it is very advised to convert them into YAML format with minimum markup symbols which is noise for the transformer. Use the [`prepare_prompt.py`](/tools/scripts/prepare_prompt.py) script for this cleaning.

```bash
uv run tools/scripts/prepare_prompt.py ai_system/3_prompts/consultants/devops_consultant.json
```
