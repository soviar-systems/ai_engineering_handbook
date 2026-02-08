When you implemented a plan in /architect mode and handle it to editor, save this plan to misc/plan/plan_<date_hash>.md. This is needed to save the history of the decisions made between context switch. 

The repo is configured for working with uv
    when you run tests or Python scripts, use uv run command,
    when your need to install a new Python dependency, use uv add command.

When working with an .md file
    You are editing a MyST Markdown notebook paired with Jupytext,
    never convert ```{code-cell} blocks to standard ```bash or ```python,
    always preserve the exact syntax: ```{code-cell}[optional-kernel],
    never alter, remove, or reformat MyST directive syntax.

When coding
    always prefer Path from pathlib in Python; NEVER use os library,
    always follow top-down design in coding: main function at the top as the entry point.

When editing configuration files
    always use placeholders like <IP_ADDRESS> or <DOMAIN> instead of real values.

When you commit changes
    Prefer atomic commits - each task should have its own commit so if it contains a bug it can be reverted as a whole feature or fix in one git revert command,
    Always commit telegram posts in the dedicated commit with pr prefix, they must be filtered during the release notes generation.

Save chat history to the .aider.chat.history/ directory - each new session you start a new history file with the name of form "<date_hash>_<time_hash>.md"
