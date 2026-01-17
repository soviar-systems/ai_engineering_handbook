---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.18.1
kernelspec:
  name: python3
  display_name: Python 3 (ipykernel)
  language: python
---

# Layer 3: Prompts as Infrastructure

+++

This directory is under initial development. Currently here are the monolithic prompts that must be refactored to the block prompts.

The prompts are stored and transported via JSON format which is natively machine-readable and highly testable for errors. Before pass it to the LLM it is very advised to convert them into YAML format with minimum markup symbols which is noise for the transformer. Use our [`prepare_prompt.sh`](/ai_system/3_prompts/prepare_prompt.sh) PoC-only script for this cleaning. 

:::{warning}
Beware, the script uses `jq` and `yq` tools under the hood, so install them via `apt` or `dnf` to the system before usage. 

This is script is going to be refactored to Python production level script when its time comes.
:::
