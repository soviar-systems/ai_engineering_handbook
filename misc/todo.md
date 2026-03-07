ai_engineering_book

ADR index
- divide History section into rejected and superseded
- restructure the dir to active/rfc/rejected/superseded for easier navigation
- each ADR in the index should contain title and description so the index is a reference (progressive disclosure for agents)

generate_changelog.py
- if all lines of a commit body are excluded, the commit itself should also be excluded

Architectural docs in changelog
- ADRs deserve their own section in changelog and release notes
- architectural docs should have arch: commit prefix for special treatment (vadocs-git scope)

check_adr.py
- input("Apply merge? [Y/n]") crashes with EOFError in non-interactive contexts (pre-commit hooks)
- fix: inform the user without requiring interaction, or detect non-interactive mode

extract_html.py
- all new lines are broken, they must be kept as is or converted to markdown when possible
- see https://github.com/unclecode/crawl4ai

TDD analysis
- https://t.me/turboproject/3505
- important question touching the code development workflow in the ecosystem

Development environment configuration
- when vadocs is installed, the developer's machine must be configured for the tools vadocs uses
- tools/scripts/configure_repo.py is the beginning, needs to evolve into vadocs-driven repo setup
- basis: personal JupyterLab configuration scripts to be generalized as ecosystem-standard dev environment setup
- related workflow docs to review:
    - ./4_orchestration/workflows/requirements_engineering
    - ./4_orchestration/workflows/release_notes_generation
    - ./mlops
