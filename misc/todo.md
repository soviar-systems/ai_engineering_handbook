ai_engineering_book



entire ecosystem description
- should be in hub, this is the entry point. brainstorm is needed

projects agents.md
- how to maintain the core architectural and validation decisions in such files? they should be independent (the user can isntall only one repo from the ecosystem), at the same time these files rely on the hub's decisions. vadocs look like a good choice for a distribution tools of these updates. The cenral agents.md file can be symlinked from other repos?

code design
- docstring contracts - see insights.md

TDD analysis
- https://t.me/turboproject/3505
- important question touching the code development workflow in the ecosystem

- The Security Implications section must be added as a required field for proposed and accepted ADRs.

Architectural docs in changelog
- ADRs deserve their own section in changelog and release notes
- architectural docs should have arch: commit prefix for special treatment (vadocs-git scope)

extract_html.py
- all new lines are broken, they must be kept as is or converted to markdown when possible
- see https://github.com/unclecode/crawl4ai

Development environment configuration
- when vadocs is installed, the developer's machine must be configured for the tools vadocs uses
- tools/scripts/configure_repo.py is the beginning, needs to evolve into vadocs-driven repo setup
- basis: personal JupyterLab configuration scripts to be generalized as ecosystem-standard dev environment setup
- related workflow docs to review:
    - ./4_orchestration/workflows/requirements_engineering
    - ./4_orchestration/workflows/release_notes_generation
    - ./mlops
    
    
DONE

Path constants stay in `tools/scripts/paths.py`
- this is non-standard way, and we should consider moving paths to the configs, like in .vadocs/conf.yaml so it can be moved then to the vadocs package distribution mechanism

ADR:
- should we use only one tag so we can change the adr_index to be sectioned, not the huge list of titles?
 - adr_index
    - can we move the check to git add stage, not post-commit?
    - divide History section into rejected and superseded
