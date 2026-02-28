ai_engineering_book

1. changelog generator:
- add a new line after the end of prepend
- add md bold for the level 1 bullets, like **New Features:** so the main sections are visually distinct from other sections
- the list of exclusion for changelog - strings containing CLAUDE.md, aider, all the misc/ changes, jupytext sync operations. should it be a config for such exclusions or we will use pyproject.yaml?

Brainstorming
1. git policy
- I need the central point to start with understanding how the git policy is governed in the repo. this knowledge is smeared within the repo and when I want to see what types of branches, commit prefixes are allowed, how to work with the commit bodies, etc. I do not understand where to go to make any changes - what configs, scripts, docs I should change. 
2. I am tending to extract this functionality either to vadocs or to the specialized package for git policy governance. The vadocs looks good because it governs the docs validation and these git scripts also are the validation gates for the docs so I can control the process from within one package. The vados looks not a good choice because git operations, hooks, and CI are specific operations with their own goals and maintaining them in the vadocs package will make mess. The UNIX philosophy is about making one tool for one task, and then you pipe these tools as lego blocks into the new tools.
The result should be the analysis file.

Brainstorming
1. We haven't finished the architecture dir restructuring. See ADR-26035 - we only created evidence dir, but we need to align the structure to the Conceptual Taxonomy.
2. The question 1 leads to the problem of vadocs package as the production level, a given-repo-agnostic tool. The docs validation scripts in tools/scripts are so different but they solve one common goal - they are the docs quality gates. We need to assess all the scripts for solving common tasks and extract such functionality to the dedicated "parent" module and leave only the specific functionality for each doc type. More over, it looks like we need to elaborate the more sophisticated docs taxonomy - we already have the architectural docs, but we also have handbooks, scripts instructions, etc. We need to elaborate some classification and build the validation gates around this docs system. I think, we need to leverage the UNIX design approach where the syscalls are the interfaces, and our docs types can also be interfaces and the given logic is hidden behind them. These interfaces should provide the uniform design for any new repo in the ecosystem. Thus the validation scripts are behind these interfaces and can use any tools (git or bash commands) or shared modules when they govern their doc type. This is much closer to the concept of Docs-as-Code. This interface approach will conduct how the repos structure should look like.
The interface (docs types classification) will also should define the tags system we can use for our git policy, ADRs, skills to let the agents filter the information in a stable manner complementing the RAG system. This hypothesis needs to be discussed.
I do not have answers, I have questions. We need to research the best real world production level practices, existing standards, and elaborate the concept of the uniform design for the new AI era where the docs is the source code.
The result of this session is the analysis file, not the pure plan. 

Brainstorming - clean up ephemeral and working files.
1. architecture/evidence/sources/ - when removing the sources we lose the number. we need to either change the taxonomy for sources or maintain an index for all the sources we had, so it is a reference. but do we really need such an index?
2. Should we keep all analysis files without cleaning the dir from time to time or it should be governed the same way the sources governed - removing after we are sure all the valuable information is extracted to ADR?
3. The implemented plans should be also cleaned up from time to time. 
So, we need to elaborate some cleaning up policy:
- the list of ephemeral files that should be removed and stayed only in the git history
- the period when the cleaning up should happen, for example with the new release.
This policy should be governed by some script like, when we commit the changelog - the script checks the existence of the ephemeral files, their presence in git history, and then tells the user to remove them. The script is like check_broken_links, but check_ephemeral_files.
The result of the session is the analysis file.

Shared module approach:
For example, check_evidence.py script uses _detect_repo_root(), resolve_config_path(), 

Brainstorming
1. Architectural docs should be validated as having the arch or whatever commit prefix so we can manage them as a special case in changelog and release notes. the ADRs are the strategic backbone, they deserve their own section.

Brainstorming. 
1. Read the architecture/evidence/analyses.
2. What other ADRs can we extract from this analysis?

Brainstorming. 
1. Read the architecture/evidence/analyses.
2. Revise the YAML frontmatter standard to be the same across all documentation (the problem mentioned in misc/plan/techdebt.md). Now the ADRs have their own template and other docs have a different template. We need to align the frontmatter to the 
- MyST formatting,
- skills architecture (name, tags, description - essential fields) - so the agents while getting the context can walk through these frontmatters instead of reading the entire docs and save tokens; I tend to adopt this approach to all documentation in the repos, so the agents need to read the frontmatters to get understanding whether they need to read the files in full,
- internal rules (version, birth and last modified dates) are also should be included to the frontmatter standard.
Revise the existing ADRs to supersede outdated ones with the new standard. Update the existing *active* ADRs to follow the new frontmatter style, start versioning. The docs should be refined in a lazy manner (ADR-26023).
We need to revise all the existing configs to use the new general frontmatter config instead of hard-coding general required fields.

Brainstorming. 
1. Read the architecture/evidence/analyses.
2. We need to get the decision on the problem of the docs taxonomy on the ecosystem level discussed in the analysis. I have no the final opinion yet.
3. Known tech debt must be traced officially to be resolved as soon as possible. This type of the documentation is to note all the tech debt we cannot resolve at that moment but we should remember and not lose. How is this done in the mature dev commands? And how can we implement it in our ecosystem? We need an ADR for this. See misc/plan/techdebt.md as the temporary solution.

extract_html
- all new lines are broken, they must be kept as is or even converted to markdown when possible, see https://github.com/unclecode/crawl4ai

1. tools/scripts/check_adr.py - Duplicate resolution error, try to add ## Decision and commit the ADR. Looks like we need just to inform the user, no interaction.
Apply merge? [Y/n]: Traceback (most recent call last):
File "/home/commi/Yandex.Disk/it_working/projects/soviar-systems/ai_engineering_book/tools/scripts/check_adr.py", line 1542, in <module>
sys.exit(main())
~~~~^^
File "/home/commi/Yandex.Disk/it_working/projects/soviar-systems/ai_engineering_book/tools/scripts/check_adr.py", line 1416, in main
if fix_duplicate_sections(adr_files):
~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
File "/home/commi/Yandex.Disk/it_working/projects/soviar-systems/ai_engineering_book/tools/scripts/check_adr.py", line 529, in fix_duplicate_sections
response = input("Apply merge? [Y/n]: ").strip().lower()
~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
EOFError: EOF when reading a line

Brainstorming. 
1. The problem of hub-spoke ADRs (see ADR-26020). This documentation is considered interconnected but it is maintained in each repo respectively. There is no understanding on how to consolidate this knowledge base for cross-referencing especially from spoke to hub. 
Probably, we need a script that works both with the hub index and the spoke indices. The spoke indices should contain the section for the hub's only ACTIVE ADRs that are actual for this spoke repo. Do we need to add the spoke's tags to the hub's ADRs? Isn't it over-engineered solution? We try to transfer the context management from the LLM and the agent to the automated tools during the commit.
2. The validation script must be aligned with the new frontmatter style and be natively able to process the ADRs in each repo with the different prefixes. No hardcoded prefixes, the vadocs should be the instrument any organization can adopt through the config file - adr_config or pyproject.toml.

Brainstorming. 
1. Read the misc/plan/analysis.
2. Revise the ADRs 26031-2634.
3. Revision. Should we move these ADRs to the hub docs and keep only the references in spoke repos? 
/home/commi/Yandex.Disk/it_working/projects/soviar-systems/mentor_generator/docs/architecture/adr/adr_26003_instruction_budget_llm_context_limits.md
/home/commi/Yandex.Disk/it_working/projects/soviar-systems/vadocs/docs/adrs/adr_26001_dogfooding_self_documentation.md

Brainstorming
1. The initial repo template. The docs validated by vadocs should follow the structure the vadocs expects. Now this problem is not resolved.



1. Configure JupyterLab, linters, etc. ./helpers/scripts/environment_setup_scripts
2. Read workflow docs:
    - ./4_orchestration/workflows/requirements_engineering
    - ./4_orchestration/workflows/release_notes_generation
    - ./mlops


adr_index:
- consider divide History section to rejected and superseded

repo configuration
- vadocs
- git validation package
- configure repo script - in vadocs?

Add validation of the version and date change in YAML frontmatters using script. 


ADR required fields:
- Status
- Tags
- Context
- Decision
- Consequences
- Alternatives
- References
- Participants
Title, date are not needed because they're rendered by MyST. We need to add ADR-YYNNN to the MyST rendered title somehow - the adr number is not shown in the table contents

DONE
