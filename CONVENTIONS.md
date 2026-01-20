You are editing a MyST Markdown notebook paired with Jupytext.
NEVER convert ```{code-cell} blocks to standard ```bash or ```python.
ALWAYS preserve the exact syntax: ```{code-cell}[optional-kernel].
NEVER alter, remove, or reformat MyST directive syntax.

ALWAYS prefer Path from pathlib in Python; NEVER use os library.

ALWAYS follow top-down design in coding: main function at the top as the entry point.

When editing configuration files, always use placeholders like [IP_ADDRESS] or [DOMAIN] instead of real values.

Always write a plan to misc/plan.md before you start any actual implementation.
