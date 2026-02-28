release v2.6.0
* New Features:
    - Add evidence artifact validation tooling
        - Created: tools/scripts/check_evidence.py — validates evidence artifacts against evidence.config.yaml schema
        - Created: tools/tests/test_check_evidence.py — 75 config-driven tests with SSoT chain resolution
        - Created: tools/docs/scripts_instructions/check_evidence_py_script.md — ADR-26011 script instruction doc
        - Updated: architecture/evidence/evidence.config.yaml — added common_required_fields and date_format as SSoT
        - Updated: .pre-commit-config.yaml — added check-evidence and test-check-evidence hooks
        - Updated: .github/workflows/quality.yml — added evidence-validation job with logic/docs triggers
        - Fixed: architecture/adr/adr_26036_config_file_location_and_naming_conventions.md — link format (.md → .ipynb)
    - Architecture — add ADR-26030 for stateless JIT context injection
        - Created: architecture/adr/adr_26030_stateless_jit_context_injection.md — formalized the stateless observer pattern to eliminate context accumulation and reduce token costs.
        - Updated: pyproject.toml — added initial placeholders for commit-convention tool configuration to support JIT prompt assembly.
        - Updated: architecture/adr/adr_index.md — indexed ADR-26030 under Evolutionary Proposals to maintain the documentation registry.
* Bug Fixes:
    - Update format_string.py and docs
        - Updated: tools/scripts/format_string.py — Add — symbol to special symbols to replace
        - Updated: tools/docs/scripts_instructions/format_string_py_script.ipynb — Add —symbol to list of removed special symbols in documentation
* Documentation:
    - Add A-26002 analysis — Agentic OS, Tiered Memory, Package Infrastructure
        - Created: architecture/evidence/analyses/A-26002_agentic_os_skills_tiered_memory_package_infra.md — comprehensive analysis extracting 11 architectural insights from Gemini dialogue S-26001: Agentic OS paradigm, three-tier cognitive memory, tag-filtered skill discovery, package-driven virtual monorepo, builder/runtime separation, researcher agent alternatives, DSPy evaluation, industry alternatives landscape, and evolution from prompt engineering to software engineering
    - Add S-26001 Gemini dialogue on skills architecture
        - Created: architecture/evidence/sources/S-26001_gemini_dialogue_skills_architectures.md — full extracted transcript of Gemini 3.0 Flash consultation covering Agentic OS paradigm, tiered cognitive memory, and package-driven infrastructure
* Architectural Decisions:
    - Add Architecture Knowledge Base taxonomy and config conventions
        - Created: architecture/adr/adr_26035_architecture_knowledge_base_taxonomy.md — taxonomy for evidence artifacts (analyses, retrospective, sources)
        - Created: architecture/adr/adr_26036_config_file_location_and_naming_conventions.md — <domain>.config.yaml naming,
        - Created: architecture/evidence/analyses/A-26001_architecture_knowledge_base_taxonomy.md — inaugural analysis documenting
        - Created: architecture/evidence/evidence.config.yaml — evidence artifact validation spec with naming patterns, required
        - Created: architecture/architecture.config.yaml — shared architectural vocabulary (tags) as parent config
        - Created: architecture/evidence/sources/README.md — source lifecycle and git archaeology guide
        - Updated: architecture/adr_index.md — auto-generated entries for ADR-26035 and ADR-26036
        - Updated: pyproject.toml — added [tool.check-adr] and [tool.check-evidence] config pointer registry
    - Propose new ADR taxonomy
        - Added: architecture/adr/adr_26031_prefixed_namespace_system_for_architectural_records.md - propose adding prefixes for ADR in different repos of the ecosystem so their ids do not overlap and confuse the consumer of these ADRs
    - Add skills architecture ADRs
        - Added: architecture/adr/adr_26032_tiered_cognitive_memory_procedural_skills.md - skills plus RAG architecture inspired by Claude talk
        - Added: architecture/adr/adr_26033_virtual_monorepo_via_package_driven_dependency_management.md - how to interconnect projects in the ecosystem without real monorepo
        - Added: architecture/adr/adr_26034_agentic_os_paradigm_skills_as_composable_applications.md -  the 3 Tier Architecture of LLM, Agent, Skills
* Maintenance:
    - Remove backtick requirement and make commit config SSoT
        - Updated: architecture/adr/adr_26024_structured_commit_bodies_for_automated_changelog.md — removed backtick wrapping from bullet format spec and examples
        - Updated: tools/docs/git/01_production_git_workflow_standards.md — removed backtick requirement from body convention rules and examples
        - Updated: tools/docs/scripts_instructions/validate_commit_msg_py_script.md — removed backticks from examples, replaced hardcoded type list with pyproject.toml reference
        - Updated: tools/docs/scripts_instructions/generate_changelog_py_script.md — removed backticks from CHANGELOG format examples
        - Updated: pyproject.toml — added adr type, removed test type from commit-convention
        - Updated: tools/scripts/validate_commit_msg.py — removed backticks from error message
        - Refactored: tools/tests/test_validate_commit_msg.py — parametrize lists derive from VALID_TYPES/ARCHTAG_REQUIRED_TYPES instead of hardcoded values
        - Refactored: tools/tests/test_generate_changelog.py — parametrize lists derive from TYPE_TO_SECTION instead of hardcoded values

release 2.5.0
* New Features:
    - Add MHTML support to extract_html_text.py
        - Updated: `tools/scripts/extract_html_text.py` — added is_mhtml() detection, extract_html_from_mhtml() with quoted-printable decoding, SVG skip tag, auto-detection in main()
        - Updated: `tools/tests/test_extract_html_text.py` — added 22 new tests for MHTML parsing, SVG/base64 stripping, and integration (36 total, 85% coverage)
        - Updated: `tools/docs/scripts_instructions/extract_html_text_py_script.md` — documented MHTML support, SVG stripping, new test classes
        - Updated: `tools/docs/scripts_instructions/extract_html_text_py_script.ipynb` — synced via jupytext
    - Enforce ADR section whitelist with conditional and code-fence support
        - Updated: `architecture/adr/adr_config.yaml` — added `allowed_sections` (10 items) and `conditional_sections` (Rejection Rationale → rejected only)
        - Updated: `tools/scripts/check_adr.py` — added `ALLOWED_SECTIONS`, `CONDITIONAL_SECTIONS` constants; `CODE_FENCE_PATTERN` to strip fenced code blocks before section extraction; extended `validate_sections()` with whitelist + conditional checks
        - Refactored: `tools/tests/test_check_adr.py` — replaced hardcoded test config with `shutil.copy2` from real `adr_config.yaml` (SSoT); added 5 tests across `TestSectionWhitelist`, `TestConditionalSections`, `TestCodeFencedSectionsIgnored`
        - Updated: `tools/docs/scripts_instructions/check_adr_py_script.md` — documented `unexpected_section` and `conditional_section_violation` error types, new test classes, version bump to 0.6.0
    - Add validate_commit_msg.py and generate_changelog.py with full script suites
        - Created: `tools/scripts/validate_commit_msg.py` — commit-msg hook enforcing CC format, structured body bullets, and ArchTag rules
        - Created: `tools/scripts/generate_changelog.py` — release-time CHANGELOG generator from git history with hierarchical formatting
        - Created: `tools/tests/test_validate_commit_msg.py` — 68 non-brittle tests covering subject, body, ArchTag, skip logic, and CLI
        - Created: `tools/tests/test_generate_changelog.py` — 56 non-brittle tests covering parsing, grouping, formatting, and CLI
        - Created: `tools/docs/scripts_instructions/validate_commit_msg_py_script.md` — script documentation with ADR-26023 frontmatter
        - Created: `tools/docs/scripts_instructions/generate_changelog_py_script.md` — script documentation with ADR-26023 frontmatter
        - Updated: `pyproject.toml` — added [tool.commit-convention] config as single source of truth for types and section mappings
        - Updated: `.pre-commit-config.yaml` — registered validate-commit-msg hook and test hooks for both scripts
        - Updated: `.github/workflows/quality.yml` — added CI jobs for validate-commit-msg and generate-changelog test suites
        - Updated: `tools/docs/git/01_production_git_workflow_standards.md` — added pyproject.toml config tips and script doc cross-references
        - Updated: `tools/docs/git/03_precommit_ci_validation_system.md` — unified validation matrix, expression injection prevention section
    - Formalize RFC→ADR workflow (ADR-26025) with promotion gate
        - architecture/adr/adr_26025_rfc_adr_workflow_formalization.md — Fat ADR
        - tools/scripts/check_adr.py — validate_promotion_gate() added, detects
        - tools/tests/test_check_adr.py — 14 new promotion gate tests
        - architecture/adr_index.md — ADR-26025 added via --fix (dogfooded)
        - architecture/what_is_an_adr.md — rewritten: no hardcoded rules,
    - Add HTML text extraction script (extract_html_text.py)
        - tools/scripts/extract_html_text.py — stdlib-only HTML text extractor (85% coverage)
        - tools/tests/test_extract_html_text.py — 22 tests (unit + in-process CLI)
        - tools/docs/scripts_instructions/extract_html_text_py_script.md + .ipynb
    - Annotate superseded entries in generated index
* Bug Fixes:
    - Install commit-msg hook in configure_repo.py setup
        - Updated: `tools/scripts/configure_repo.py` — added `run_precommit_install_commit_msg()` to install commit-msg stage hook via `--hook-type commit-msg`
        - Updated: `tools/tests/test_configure_repo.py` — added tests for commit-msg hook install success/failure and mid-chain failure paths
        - Updated: `tools/docs/git/02_pre_commit_hooks_and_staging_instruction_for_devel.md` — added commit-msg install command and warning about hook stage installation
        - Updated: `tools/docs/git/03_precommit_ci_validation_system.md` — added commit-msg install command and cross-reference to article 02; migrated frontmatter to ADR-26023
        - Updated: `tools/docs/scripts_instructions/configure_repo_py_script.md` — added commit-msg hook row to operations table; migrated frontmatter to ADR-26023
    - Remove is_skip_commit() bypass from commit validator
        - Updated: `tools/scripts/validate_commit_msg.py` — removed is_skip_commit() function and skip check in run(); all commits now go through all three validation layers (subject, body, ArchTag)
        - Updated: `tools/tests/test_validate_commit_msg.py` — removed TestIsSkipCommit class (7 tests) and 2 CLI skip tests; added TestFormerlySkippedCommitsFail (4 tests) asserting WIP/Merge/fixup/squash → exit 1
        - Updated: `tools/docs/scripts_instructions/validate_commit_msg_py_script.(md|ipynb)` — removed Skip Logic section and is_skip_commit() references; added Section 7 post-mortem documenting root cause (input/output policy coupling) and principles extracted
        - Updated: `tools/docs/git/01_production_git_workflow_standards.(md|ipynb)` — removed WIP: from valid commit types table; renamed section to "Local Checkpoint Commits"; replaced WIP guidance with --no-verify as the only escape hatch; removed CI PR Status Check for WIP
    - Close pre-commit/CI desync gap and gate deploy to main
        - Updated: `tools/scripts/check_adr.py` — detect duplicate `##` sections in validate_sections() (set → counter), add fix_duplicate_sections() with interactive prompt, run promotion gate in --fix mode
        - Updated: `tools/tests/test_check_adr.py` — add TestDuplicateSections, TestFixDuplicateSections, TestPromotionGateInFixMode (10 new tests, 154 total, 96% coverage)
        - Fixed: `architecture/adr/adr_26026_dedicated_research_monorepo_for_volatile.md` — merge duplicate ## Participants headers
        - Updated: `.github/workflows/deploy.yml` — gate build-deploy job to main branch with if: github.ref == 'refs/heads/main'
        - Updated: `tools/docs/website/01_github_pages_deployment.md` — add deployment rejection pitfall to Common Pitfalls table
        - Updated: `tools/docs/scripts_instructions/check_adr_py_script.md` — add duplicate_section error type, fix step, desync admonition, bump to v0.5.0
* Documentation:
    - Adopt MyST-aligned frontmatter standard (ADR-26023)
    - Prefer .md over .ipynb for reading notebooks
        - Updated: `CLAUDE.md` — added instruction to always read `.md` Jupytext pairs instead of `.ipynb` JSON, which is expensive to parse
    - Convert generate_changelog instruction examples to executable cells
        - Updated: `tools/docs/scripts_instructions/generate_changelog_py_script.md` — replaced static bash examples with executable `{code-cell}` blocks using dry-run output; bumped version to 1.0.1
    - Integrate AI Code Generation Engineer insights into Gherkin analysis
        - Updated: `misc/gherkin_tmp/analysis_summary.md` — added Source 3, Section G (verification & execution infrastructure), peer reviews for G2-G6, devil's advocate section, ADR Candidate 4, renamed RFC→ADR candidates, expanded AST/CST relevance, added "Crafting Interpreters" to reading list
        - Created: `misc/gherkin_tmp/new_profession_description.md` — AI Code Generation Engineer role definition based on real European bank vacancy, structured by Qwen3-Max
    - Add Gherkin/BDD/DDD conversation analysis and plan
        - Created: `misc/gherkin_tmp/analysis_summary.md` — analytical summary with 30 ideas inventoried, peer review of 8 key claims, 3 RFC candidates
        - Created: `misc/gherkin_tmp/code_generation_from_specifications_v2.txt` — clean extraction from MHTML source
        - Created: `misc/gherkin_tmp/ddd_bdd_and_tdd_explained_v2.txt` — clean extraction from HTML source
    - Rewrite README.md to v2.5.0 with Documentation-as-Code framing
        - Updated: `README.md` — full structural rewrite: new mission (documentation as AI input), Documentation-as-Code section, Architectural Governance, Hub-and-Spoke Ecosystem, tool-agnostic Methodology, corrected directory tree, Toolchain & CI/CD section; removed Research & Foundations, Motivation, and all tool/model name references
        - Created: `architecture/manifesto.md` — declaration of the Documentation-as-Code principle with structural analogy (repo structure = code architecture)
        - Created: `misc/pr/tg_channel_ai_learning/2026_02_16_documentation_as_source_code_manifesto.md` — Telegram post about the manifesto
    - Promote 6 ADRs from proposed to accepted
        - Updated: `architecture/adr/adr_26015_mandatory_sync_guard_and_diff_suppression.md` — status proposed → accepted
        - Updated: `architecture/adr/adr_26017_adr_format_validation_workflow.md` — status proposed → accepted
        - Updated: `architecture/adr/adr_26020_hub_spoke_ecosystem_documentation.md` — status proposed → accepted
        - Updated: `architecture/adr/adr_26021_content_lifecycle_policy_for_rag_consumed.md` — status proposed → accepted
        - Updated: `architecture/adr/adr_26022_standardization_of_public_documentation_hosting.md` — status proposed → accepted
        - Updated: `architecture/adr/adr_26025_rfc_adr_workflow_formalization.md` — status proposed → accepted
        - Updated: `architecture/adr_index.md` — regenerated index to reflect status changes (6 ADRs moved from Evolutionary Proposals to Active Architecture)
        - Updated: `tools/docs/scripts_instructions/check_adr_py_script.(md|ipynb)` — version bump 0.6.0 → 0.6.1
    - Update CLAUDE.md with ADR workflow, new scripts, and tool config conventions
        - Updated: `CLAUDE.md` — added check_adr.py, validate_commit_msg.py, generate_changelog.py to Common Commands
        - Updated: `CLAUDE.md` — added Tool Configuration (ADR-26029) and ADR index management conventions
        - Updated: `CLAUDE.md` — de-emphasized Aider as primary editor, made workflow tool-agnostic
    - Add ADR-26029 formalizing pyproject.toml as tool config hub
        - Created: `architecture/adr/adr_26029_pyproject_toml_as_tool_config_hub.md` — formalizes `[tool.X]` sections as canonical location for machine-readable tool configuration
        - Updated: `architecture/adr_index.md` — added ADR-26029 to Active Architecture section via `check_adr.py --fix`
    - Expand Format-as-Architecture article to v0.2.0 with empirical token measurements
        - Created: `ai_system/3_prompts/format_as_architecture_signal_noise_in_prompt_delivery.md` — added Minified JSON (2.4), YAML Literal Block Scalar (2.5), BPE Tokenizer Mechanics (2.7), Practical Measurement section (5) with runnable {code-cell} bash blocks, Security Considerations section (7), expanded Decision Framework and Summary
        - Updated: `ai_system/3_prompts/format_as_architecture_signal_noise_in_prompt_delivery.ipynb` — jupytext sync of all new content including 7 executable code cells measuring token cost across 4 formats with cl100k_base and o200k_base tokenizers
    - Add commit convention guidelines to CONVENTIONS.md
    - Mandate file paths in structured commit body bullets
        - Updated: architecture/adr/adr_26024_structured_commit_bodies_for_automated_changelog.md — defined <target> as
        - Updated: tools/docs/git/01_production_git_workflow_standards.md — aligned Body Convention template and added Rule 4
        - Updated: CLAUDE.md — aligned commit conventions bullet with new format; added <file-path> definition; added
    - Expand ADR-26024 plan with foundational decisions and Gemini alternatives analysis
        - Created: gemini_20260209_changelog_alternatives_analysis.md — full Gemini session transcript with WRC scoring, hypothesis evaluation, and validation gap analysis
        - Updated: plan_20260209_structured_commit_bodies_automated_changelog.md — added foundational architectural decisions (bisect deprioritization, Rich-Body Squash, Ingredients-First pattern, dch rejection, LLM supersession), split into Phase A (analytical) and Phase B (implementation), expanded ADR-26024 spec with WRC scores and alternatives pointers
    - Establish structured commit body convention and automated CHANGELOG foundation (ADR-26024 Phase A)
        - Created:  — codifies the Rich-Body Squash
        - Refactored:  — resolved 8 contradictions (ff-only vs
        - Updated:  — added Section 4 (Commit Message
        - Updated:  — commit conventions now mandate structured body bullets, Squash-and-Merge policy, and
        - Added: usage: git [-v | --version] [-h | --help] [-C <path>] [-c <name>=<value>]
        - Updated: ADR-26001, ADR-26002, ADR-26003 — added usage: git [-v | --version] [-h | --help] [-C <path>] [-c <name>=<value>]
        - Updated:  — registered ADR-26024 under Evolutionary Proposals
    - Update CLAUDE.md with frontmatter standard and deploy target
        - Added: Content Frontmatter section under Critical Conventions — documents ADR-26023 rules: use `title/author/date/options.version/options.birth` fields, correct author email (`rudakow.wadim@gmail.com`), and `1.0.0`+ versioning for production docs
        - Fixed: deploy.yml description — "deploys to server" → "deploys to GitHub Pages" (per ADR-26022)
    - Update Plan 2 with real commit example
        - Updated: complex commit example in structured commit bodies plan — replaced draft bullets with actual commit `3e652bc` (8 detailed bullets)
        - Updated: CHANGELOG output example — aligned hierarchical sub-items with the real commit structure
    - Restructure website deployment documentation
        - Created: `tools/docs/website/01_github_pages_deployment.(md|ipynb)` — canonical GitHub Pages guide with MyST init, myst.yml config, local testing, Pages enablement, deploy workflow, and troubleshooting (309 lines)
        - Renamed: `mystmd_website_deployment_instruction.(md|ipynb)` → `02_self_hosted_deployment.(md|ipynb)` — with `:::{warning}` deprecation notice linking to the new guide
        - Refactored: `02_self_hosted_deployment.md` — replaced duplicated MyST init/config/local-testing sections (1.1, 1.2, 4) with cross-references to the GitHub Pages guide; added superseded notice inside deploy.yml dropdown
        - Deleted: `tools/docs/git/github_pages_setup.md` — content fully absorbed into `01_github_pages_deployment`
        - Updated: `architecture/adr/adr_26022...md` — fixed self-hosted link path, replaced single reference with two entries (GitHub Pages guide + deprecated self-hosted)
        - Updated: `architecture/packages/README.md` — GitHub Pages setup link now points to `01_github_pages_deployment.ipynb`
        - Updated: `architecture/packages/creating_spoke_packages.md` — same link fix in Next Steps section
        - Fixed: `configs/mutli-site/` → `configs/multi-site/` directory typo (nginx.conf + play_nginx.yml)
    - Add GitHub org transfer and Pages setup guides
    - Add spoke package extraction guide and vadocs POC
    - Add decision plan for superseded annotation feature
* CI/CD & Quality:
    - Migrate deploy.yml from SSH/rsync to GitHub Pages
* Refactoring:
    - Move research projects to dedicated monorepo
        - Created: `architecture/adr/adr_26026_dedicated_research_monorepo_for_volatile.md` — Added ADR documenting the decision to move
        - Deleted: `misc/research/slm_from_scratch/` — Removed the `slm_from_scratch` research project and its associated files (notebooks,
        - Modified: `myst.yml` — Added "DVC: Data Version Control" to the acronyms list.
    - Replace aidx article with tool-agnostic Multi-Phase AI Pipeline
        - Created: ai_system/4_orchestration/workflows/multi_phase_ai_pipeline.md — Research-Apply pipeline and namespace partitioning for RAG
        - Deleted: ai_system/4_orchestration/workflows/aidx_industrial_ai_orchestration_framework.md — tool-coupled original
        - Deleted: ai_system/4_orchestration/workflows/aidx_industrial_ai_orchestration_framework.ipynb — paired notebook
        - Updated: 0_intro/00_onboarding.md — link to new pipeline article
        - Updated: ai_system/2_model/selection/choosing_model_size.md — replaced 5 aidx refs with tool-agnostic language and cross-links
        - Updated: ai_system/2_model/selection/general_purpose_vs_agentic_models.md — replaced 3 aidx refs, fixed gemini-3-flash version string
    - Rename BROKEN_LINKS_EXCLUDE_DIRS to VALIDATION_EXCLUDE_DIRS
        - Refactored: `tools/scripts/paths.py` — rename to VALIDATION_EXCLUDE_DIRS, remove JUPYTEXT_EXCLUDE_DIRS alias
        - Updated: `tools/scripts/check_broken_links.py` — use VALIDATION_EXCLUDE_DIRS
        - Updated: `tools/scripts/check_link_format.py` — use VALIDATION_EXCLUDE_DIRS
        - Updated: `tools/scripts/check_adr.py` — use VALIDATION_EXCLUDE_DIRS, remove historical comment
        - Updated: `tools/tests/test_check_broken_links.py` — align with renamed variable
        - Updated: `tools/tests/test_check_link_format.py` — align with renamed variable
        - Updated: `tools/docs/git/03_precommit_ci_validation_system.md` — update code example
        - Updated: `tools/docs/scripts_instructions/check_adr_py_script.md` — fix frontmatter format
        - Updated: `tools/docs/scripts_instructions/check_broken_links_py_script.md` — update variable name in docs
        - Updated: `tools/docs/scripts_instructions/check_link_format_py_script.md` — update variable name in docs
        - Updated: `tools/docs/scripts_instructions/format_string_py_script.md` — migrate to YAML frontmatter
        - Updated: `tools/docs/scripts_instructions/extract_html_text_py_script.md` — fix frontmatter whitespace
        - Updated: `ai_system/3_prompts/format_as_architecture_signal_noise_in_prompt_delivery.md` — bump to v0.1.1
    - Triage ADR-26004..26008 from tool-specific to tool-agnostic
        - Updated: `architecture/adr/adr_26004_implementation_of_agentic_rag_for_autonom.md` — rejected with rejection rationale (tool-agnostic shift)
        - Updated: `architecture/adr/adr_26005_formalization_of_aider_as_primary_agentic.md` — rejected with rejection rationale (tool-agnostic shift)
        - Updated: `architecture/adr/adr_26006_agentic_class_models_for_architect_phase.md` — superseded by ADR-26027
        - Updated: `architecture/adr/adr_26007_formalization_of_phase_0_intent_synthesi.md` — superseded by ADR-26028
        - Updated: `architecture/adr/adr_26008_reasoning_class_models_for_abstract_synt.md` — superseded by ADR-26027
        - Created: `architecture/adr/adr_26027_model_taxonomy_reasoning_vs_agentic_class.md` — tool-agnostic model selection heuristic (accepted)
        - Created: `architecture/adr/adr_26028_tool_agnostic_phase_0_intent_synthesis.md` — tool-agnostic Phase 0 intent synthesis (accepted)
        - Updated: `architecture/adr/adr_template.md` — added conditional Rejection Rationale section
        - Updated: `architecture/adr_index.md` — regenerated via check_adr.py --fix
        - Updated: `ai_system/2_model/selection/general_purpose_vs_agentic_models.md` — replaced ADR-26006/26008 refs with ADR-26027
        - Updated: `ai_system/2_model/selection/choosing_model_size.md` — replaced ADR-26005/26006 refs with ADR-26027
        - Fixed: `architecture/adr/adr_26015_mandatory_sync_guard_and_diff_suppression.md` — typo in gitattributes formatting
        - Fixed: `architecture/adr/adr_26022_standardization_of_public_documentation_hosting.md` — missing EOF newline
* Public Relations:
    - Add 2026_02_15_architecture_of_context_building_a_central_brain.md
    - Add Telegram post on Format-as-Architecture token analysis
        - Created: `misc/pr/tg_channel_ai_learning/2026_02_15_format_as_architecture_token_cost.md` — educational post explaining how serialization format affects LLM attention budget, with BPE mechanics and measured token costs across 4 formats
    - Update release post

release 2.4.0
* ADR Validation Toolchain:
    - `check_adr_index.py` renamed to `check_adr.py` with expanded scope: config-driven
      validation of required frontmatter fields, date format, tag allowlist, required sections,
      hyphen-format standardization (ADR-NNNNN), legacy migration (`--migrate`), partitioned
      index by status. 110 tests, 98% coverage.
    - Term reference validation added (`--check-terms`, `--fix-terms`) — detects and fixes
      broken `{term}` cross-references (e.g. `ADR 26001` → `ADR-26001`).
    - New `adr_config.yaml` as single source of truth for required sections, term reference
      patterns, and tag allowlists.
* Architecture Decisions (ADRs) added:
    - ADR-26016: Metadata-Driven Architectural Records Lifecycle.
    - ADR-26017: ADR Format Validation Workflow.
    - ADR-26018: Universal YAML Frontmatter Adoption for Machine-Readable Documentation.
    - ADR-26019: Mirroring YAML Metadata to Document Body for Human Verification.
    - ADR-26020: Hub-and-Spoke Ecosystem Documentation Architecture.
    - ADR-26021: Content Lifecycle Policy for RAG-Consumed Repositories.
    - ADR-26022: Standardization of Public Documentation Hosting on GitHub Pages.
* ADR Migration:
    - All 17 pre-existing ADRs (26001–26016) migrated to standardized format with YAML
      frontmatter (`id`, `title`, `date`, `status`, `tags`), hyphen-style headers, and
      Title/Date/Status body sections.
    - ADR index reorganized into Active Architecture / Evolutionary Proposals partitions.
* Hub-Spoke Ecosystem:
    - `architecture/packages/` directory created for ecosystem-wide package specifications.
    - vadocs package specification added (`architecture/packages/vadocs.md`).
    - Ecosystem development workflow guide added
      (`tools/docs/packages/ecosystem_package_development_workflow.md`).
* vadocs Package Lifecycle (v0.1.0):
    - Scaffolded as `vadoc` with core models, validators (ADR, Frontmatter, MystGlossary),
      fixers (ADR, Sync), 26 tests passing.
    - Renamed `vadoc` → `vadocs`, added config module, integration tests, PoC docs.
    - Extracted to dedicated repository (github.com/lefthand67/vadocs) after successful PoC;
      all package sources removed from monorepo.
* New Articles:
    - ai_system/5_context/reflected_metadata_pattern.md — reflected-metadata pattern
      explaining why `myst build --html` ignores custom YAML fields.
    - ai_system/5_context/yaml_frontmatter_for_ai_enabled_engineering.md — YAML frontmatter
      guide with real `aidx` examples and corrected MyST-build framing.
* Rewritten Articles:
    - ai_system/2_model/selection/choosing_model_size.md rewritten as VRAM budgeting guide —
      KV Cache, quantization, production patterns (Verifier Cascade, Hybrid Routing),
      `aidx` pipeline roles, Jan 2026 model zoo.
* Deleted Articles:
    - ai_system/4_orchestration/patterns/llm_usage_patterns.md deleted per ADR-26021 —
      superseded by `aidx` framework; 101-level taxonomy below repo quality bar.
* Bug Fixes:
    - MyST term references fixed across 11 ADR files and 3 content files
      (`{term}\`ADR 26001\`` → `{term}\`ADR-26001\``).
    - ADR-26019: dropped phantom HTML-anchor mechanism (never implemented), corrected
      CLI-invisibility claim to the actual gap (myst build ignoring custom YAML fields).
* CI/CD & Quality:
    - `quality.yml` and `.pre-commit-config.yaml` updated for `check_adr.py`.
    - `misc/` added to broken-links exclusion list in `paths.py`.
    - ADR template updated with Date/Status sections and YAML frontmatter schema.
* Development Workflow (CLAUDE.md):
    - TDD approach clarified (Red → Green → Refactor, tests-first emphasis).
    - Non-brittle test quality standards added (test contracts, semantic assertions).
* Documentation:
    - Onboarding (`00_onboarding.md`) updated with metadata conventions section.

release 2.3.0
* Architecture Decisions (ADRs) added:
    - ADR 26011: Formalization of Mandatory Script Suite (Script + Test + Doc).
    - ADR 26012: Extraction of Docs Validation Engine.
    - ADR 26013: Just-in-Time Prompt Transformation.
    - ADR 26014: Semantic Notebook Pairing Strategy (Jupytext).
    - ADR 26015: Mandatory Sync Guard and Diff Suppression.
* Tooling Ecosystem Overhaul:
    - New `check_script_suite.py` enforces the 1:1:1 convention (Script, Test, Documentation).
    - New `check_adr_index.py` validates ADR index synchronization.
    - New `check_link_format.py` ensures links point to `.ipynb` in paired files.
    - `prepare_prompt` refactored to Python (`prepare_prompt.py`) with multi-format support (JSON, YAML, TOML, Markdown) and JIT transformation.
    - `configure_repo` refactored to Python (`configure_repo.py`) for better cross-platform support.
    - `jupytext_sync` and `jupytext_verify_pair` updated for Semantic Notebook Pairing.
* Documentation & Standards:
    - `CONVENTIONS.md` and `CLAUDE.md` updated with MyST, Jupytext, and Script Suite guidelines.
    - Onboarding instructions updated to use `configure_repo.py`.
    - Documentation for all scripts centralized in `tools/docs/scripts_instructions/`.
* Content Organization:
    - Password management handbooks moved to `misc/in_progress`.
    - Prompts directory (`ai_system/3_prompts`) restructured for Prompts-as-Infrastructure.
* CI/CD & Quality:
    - Pre-commit hooks updated for new tools and Python-based scripts.
    - CI now checks all Markdown files for broken links.
    - API Key scanning improved with file exclusion lists.
* New articles added:
    - 1_execution/hybrid_cpu_gpu_execution_and_kv_cache_offloading.md

release 1.3.0
* New articles added:
  - mlops/workflows/git_three_major_workflows.md
  - tools/vim/ai_tools_in_vim.md
  - tools/vim/handout_aider.md
* Articles moved
  - 2_model/training/python314_parallelism_game_changer.md -> tools/python314_parallelism_game_changer.md
  - 2_model/training/right_tool_for_right_layer.md -> tools/right_tool_for_right_layer.md
  - 2_model/training/why_rust_for_tokenizers.md -> tools/why_rust_for_tokenizers.md
  - 4_orchestration/patterns/llm_usage_patterns_p1.md -> 4_orchestration/patterns/llm_usage_patterns.md
  - 4_orchestration/patterns/llm_usage_patterns_p2.md -> 2_model/selection/choosing_model_size.md
* Release Notes created

release 1.2.0
* New articles added:
  - 0_intro/ai_systems_multilayer_approach.md
  - 4_orchestration/patterns/llm_usage_patterns_p1.md
  - 4_orchestration/patterns/llm_usage_patterns_p2.md
* New directory added - `0_intro` - with all general and introductory materials
  - ./ai_further_reading.md moved there

release 1.1.0
* New articles added:
  - 2_model/training/custom_tokenizer_and_embedding.md
  - 2_model/training/why_rust_for_tokenizers.md
  - 2_model/training/right_tool_for_right_layer.md added - Python, Rust, and C++ in AI stack
  - 2_model/training/python314_parallelism_game_changer.md

release 1.0.0
* Tree structure prepared for new articles.
* New articles added:
  - 1_execution/nvidia_gpu_optimization.md,
  - 2_model/embeddings_for_small_llms.md.
