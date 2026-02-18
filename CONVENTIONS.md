When you implemented a plan in /architect mode and handle it to editor, save this plan to misc/plan/plan_<date_hash>_<short_description>.md. This is needed to save the history of the decisions made between context switch. 

The repo is configured for working with uv
- when you run tests or Python scripts, use uv run command,
- when you need to install a new Python dependency, use uv add command.

When working with an .md file
- You are editing a MyST Markdown notebook paired with Jupytext,
- never convert ```{code-cell} blocks to standard ```bash or ```python,
- always preserve the exact syntax: ```{code-cell}[optional-kernel],
- never alter, remove, or reformat MyST directive syntax.

When coding
- always prefer Path from pathlib in Python; NEVER use os library,
- always follow top-down design in coding: main function at the top as the entry point.

When editing configuration files
- always use placeholders like <IP_ADDRESS> or <DOMAIN> instead of real values.

When you generate a commit title and body, follow this convention:
Commit Conventions architecture/adr/adr_26024_structured_commit_bodies_for_automated_changelog.md:
- Use conventional commits with prefixes from pyproject.toml [tool.commit-convention] section:
- `pr:` prefix is for promotional/announcement posts
- Keep commit subjects concise (50 chars max), focusing on the "what"
- Commit bodies MUST contain structured bullets: - <Verb>: <file-path> — <what and why>
- <file-path> is relative to repo root (e.g., tools/scripts/check_adr.py). No abstract targets — every change lives in a file
- One bullet = one line, no line length limit
- Verbs: Created, Updated, Renamed, Fixed, Moved, Added, Removed, Refactored, Configured
