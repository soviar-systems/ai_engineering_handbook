ai_engineering_book

Brainstorming
1. architecture/evidence/sources/ - when removing the sources we lose the number. we need to either change the taxonomy for sources or maintain an index for all the sources we had, so it is a reference. but do we really need such an index?
2. Should we keep all analysis files without cleaning the dir from time to time or it should be governed the same way the sources governed - removing after we are sure all the valuable information is extracted to ADR?

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


Brainstorming
- The docs validation scripts are so different but they solve one common goal - they are the docs quality gates. We need to assess all the scripts for solving common tasks and extract such functionality to the dedicated "parent" module and leave only the specific functionality for each doc type. More over, it looks like we need to elaborate the docs taxonomy - we already have the architectural docs, but we also have handbooks, scripts instructions, etc. Can we create some classification and build the validation gates around this docs system? We can consider the docs types as the interface in programming or the file types in UNIX/Linux systems. This interface should provide the uniform design for any new repo in the ecosystem.
- The scripts when using git or discovery tools should use one common module for such operations (agentic tools?). For example, check_evidence.py script uses _detect_repo_root(), resolve_config_path(), 
- This interface can lead us to the rethinking the repo structure, for example:
    - docs/ - 0_intro, ai_system, architecture, mlops, security
    - tools/

I do not have answers, I have questions. We need to research the best real world production level practices, existing standards, and elaborate the concept of the uniform design for the new AI era where the docs is the source code.

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


changelog generator:
- add a new line after the end of prepend
- ADRs should be validated as having the adr commit prefix so we can manage them as a special case in changelog and release notes. the ADRs are the strategic backbone, they deserve their own section.
- the list of exclusion strings - containing CLAUDE.md, aider, misc/plan, pr/

adr_index:
- consider divide History section to rejected and superseded

repo configuration
- vadocs
- git validation package
- configure repo script - in vadocs?




DONE

Brainstorming
Extract architecture/evidence/sources/2026_02_28_gemini_dialogue_skills_new_architectures.html using tools/scripts/extract_html.py. Read the result carefully and step by step extract all the important and valuable insights, ideas, clarifications. This is not only the documentation discussion, this is the new architectural patterns for building ai systems, so we need to finalize results in the architecture/evidence/analyses dir. 
https://gemini.google.com/share/10c1438e1c05

