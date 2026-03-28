ai_engineering_book

prepare_prompt.py
- should be updated with the findings in ai_system/3_prompts/appendix_yaml_serializer_variance.ipynb 

bug
the pre-commit and GH actions should be checked for duplicate operations:
Check Broken Links.......................................................Passed
Check Link Format (ipynb priority).......................................Passed
Jupytext Sync............................................................Passed
Jupytext Verify Pair.....................................................Passed
Check API Keys...........................................................Passed
Check JSON Files.....................................(no files to check)Skipped
Check Script Suite (script + test + doc).............(no files to check)Skipped
Validate frontmatter (ADR-26042).........................................Passed
Validate evidence artifacts..........................(no files to check)Skipped
Check ADR Index......................................(no files to check)Skipped
Test Check Broken Links script.......................(no files to check)Skipped
Test Check Link Format script........................(no files to check)Skipped
Test Jupytext Sync script............................(no files to check)Skipped
Test Jupytext Verify Pair script.....................(no files to check)Skipped
Test Check API Keys script...........................(no files to check)Skipped
Test JSON validation script..........................(no files to check)Skipped
Test Prepare Prompt script...........................(no files to check)Skipped
Test Check Script Suite script.......................(no files to check)Skipped
Test Validate Commit Msg script......................(no files to check)Skipped
Test Generate Changelog script.......................(no files to check)Skipped
Test git utilities module............................(no files to check)Skipped
Test check_frontmatter...............................(no files to check)Skipped
Test check_evidence..................................(no files to check)Skipped
Test Check ADR Index script..........................(no files to check)Skipped
Validate Commit Body.....................................................Passed
Test Check Broken Links script.......................(no files to check)Skipped
Test Check Link Format script........................(no files to check)Skipped
Test Jupytext Sync script............................(no files to check)Skipped
Test Jupytext Verify Pair script.....................(no files to check)Skipped
Test Check API Keys script...........................(no files to check)Skipped
Test JSON validation script..........................(no files to check)Skipped
Test Prepare Prompt script...........................(no files to check)Skipped
Test Check Script Suite script.......................(no files to check)Skipped
Test Validate Commit Msg script......................(no files to check)Skipped
Test Generate Changelog script.......................(no files to check)Skipped
Test git utilities module............................(no files to check)Skipped
Test check_frontmatter...............................(no files to check)Skipped
Test check_evidence..................................(no files to check)Skipped
Test Check ADR Index script..........................(no files to check)Skipped
Changelog Preview........................................................Passed
- hook id: changelog-preview
- duration: 0.04s

...

Tip -- use git commit --amend if the output looks incorrect

Test Check Broken Links script.......................(no files to check)Skipped
Test Check Link Format script........................(no files to check)Skipped
Test Jupytext Sync script............................(no files to check)Skipped
Test Jupytext Verify Pair script.....................(no files to check)Skipped
Test Check API Keys script...........................(no files to check)Skipped
Test JSON validation script..........................(no files to check)Skipped
Test Prepare Prompt script...........................(no files to check)Skipped
Test Check Script Suite script.......................(no files to check)Skipped
Test Validate Commit Msg script......................(no files to check)Skipped
Test Generate Changelog script.......................(no files to check)Skipped
Test git utilities module............................(no files to check)Skipped
Test check_frontmatter...............................(no files to check)Skipped
Test check_evidence..................................(no files to check)Skipped
Test Check ADR Index script..........................(no files to check)Skipped

brainstorm
- We mark each document with options.type, so the evidence/analyses directory becomes obsolete - it more valuable to move analyses to the corresponding ai_systems/ dirs so the agents and human engineers get all the relevant information in one place. what consequences will we face in our infrastructure if we decide to make this refactoring?

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
