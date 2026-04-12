# Consultant Prompts

System prompts for AI architecture consultants — JSON files designed to be sent as system prompts during agent sessions.

## Usage

These `.json` files are the **authoritative source** for consultant personas. They are not skills, not plugins — they are system prompt definitions.

**Daily workflow:** Copy the file content and paste it as the system prompt in your agent session. No installation, no symlinks, no tool-specific convention required.

**Sharing with colleagues:** Send the `.json` file directly. The JSON is self-contained — it works with any LLM agent that accepts system prompts (Claude, Qwen, GPT, local models via Ollama, etc.).

## Available Consultants

| File | Specialty |
| :--- | :--- |
| `ai_systems_consultant.json` | General AI systems architecture — local and cloud LLM/SLM design, methodology comparison, WRC scoring |
| `devops_consultant.json` | DevOps and infrastructure — CI/CD, IaC, automation, deployment architecture |
| `ai_brainstorming_colleague.json` | Unconstrained ideation and exploration — "what-if" scenarios, architectural discussion |
| `handbook_consultant.json` | Documentation and handbook review — structure, consistency, content quality |

## Why JSON, Not Skills?

Skills (Claude Code's `SKILL.md` convention) add a thin wrapper (description + usage hints) but introduce tool-specific dependencies and symlink fragility — every directory rename breaks the links. The JSON files are the canonical artifact; skills are optional convenience wrappers for specific tools.

For sharing and daily use, **the JSON is enough**.
