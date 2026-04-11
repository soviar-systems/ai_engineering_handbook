ai_engineering_book

- Formalize commit body standard in a single config place — currently spread across 01_production_git_workflow_standards.md, AGENTS.md, QWEN.md, validate_commit_msg.py, generate_changelog.py. Need a SSoT config (e.g., .vadocs/commit-body.conf.json or pyproject.toml section) that all docs and scripts reference. All contracts should be written to scripts and configs, not prose docs.
- Move BROKEN_LINKS_EXCLUDE_LINK_STRINGS from paths.py to pyproject.toml — check_broken_links.py already follows the pattern of loading changelog-exclude-patterns and valid-types from [tool.commit-convention].
- Add pyproject.toml to the consumers list for external-repos.conf.json — when a repo directory is relocated via manage_external_repos.py, the pyproject.toml exclusion patterns should update alongside .gitignore.
