ai_engineering_book

1. Analyze the Gemini discussion. Make a detailed report on the insights and main viable ideas based on this dialogue and save it to misc/plan/analysis.

Brainstorming. 
1. Read the misc/plan/analysis.
2. Revise the YAML frontmatter to be the same across all documentation. Now the ADRs have their own template and other docs have a different template. We need to align the frontmatter to the 
- MyST formatting,
- skills architecture (name, tags, description - essential fields)
- internal rules (version, birth and last modified dates).
Revise the existing ADRs to supersede outdated ones with the new standard. Update the existing *active* ADRs to follow the new frontmatter style, start versioning. The docs should be refined in a lazy manner (ADR-26023).

Brainstorming. 
1. The problem of hub-spoke ADRs (see ADR-26020). This documentation is considered interconnected but it is maintained in each repo respectively. There is no understanding on how to consolidate this knowledge base for cross-referencing especially from spoke to hub. 
Probably, we need a script that works both with the hub index and the spoke indices. The spoke indices should contain the section for the hub's only ACTIVE ADRs that are actual for this spoke repo. Do we need to add the spoke's tags to the hub's ADRs? Isn't it over-engineered solution? We try to transfer the context management from the LLM and the agent to the automated tools during the commit.
2. The validation script must be aligned with the new frontmatter style and be natively able to process the ADRs in each repo with the different prefixes. No hardcoded prefixes, the vadocs should be the instrument any organization can adopt through the config file - adr_config or pyproject.toml.

Brainstorming. 
1. Read the misc/plan/analysis.
2. Revise the ADRs since 26031.
3. Revision. Should we move these ADRs to the hub docs and keep only the references in spoke repos? 
/home/commi/Yandex.Disk/it_working/projects/soviar-systems/mentor_generator/docs/architecture/adr/adr_26003_instruction_budget_llm_context_limits.md
/home/commi/Yandex.Disk/it_working/projects/soviar-systems/vadocs/docs/adrs/adr_26001_dogfooding_self_documentation.md

Brainstorming
1. The initial repo template. The docs validated by vadocs should follow the structure the vadocs expects. Now this problem is not resolved.

