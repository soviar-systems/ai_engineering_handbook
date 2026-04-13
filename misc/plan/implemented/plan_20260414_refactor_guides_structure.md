# Guides Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure ai_agents/guides/ to remove numeric prefixes, separate vim-ollama from aider, and create a general terminal AI agents workflow guide.

**Architecture:** Extract general hybrid strategy content from vim-specific guide into a new parent-level guide. Rename directory and files to reflect actual content. Update all cross-references.

**Tech Stack:** MyST Markdown, Jupytext, git mv for history preservation

---

## Full Context

### Current Structure
```
ai_agents/guides/
├── 04_connect_to_capable_llms_using_api_keys.md    # General API keys guide (has numeric prefix)
├── aider/
│   └── 02_aider_commands_handout.md                # Aider commands reference (has numeric prefix)
├── claude/
│   ├── 2026_03_03_claude_code_memory_vs_claude_md.md  # Has date prefix instead of number
│   └── creating_consultant_skills.md               # No prefix (correct)
├── images/
│   └── gemini_limits_free_tier.png
├── kilocode/
│   └── 05_kilocode_cli_setup.md                    # Kilo-specific (has numeric prefix)
└── vim_and_aider/                                   # MISLEADING: contains only vim-ollama content
    ├── 01_vim_in_ai_era_hybrid_setup_with_ollama_and_aider.md  # PROBLEM: mixes general + vim-specific
    └── 03_vim_ollama_llm_tab_completion_nuances.md  # vim-ollama specific
```

### Content Breakdown of Problem File (01_vim_in_ai_era_*.md)

| Section | Content | Should Go To |
|---------|---------|--------------|
| Intro paragraph | Hybrid strategy thesis (Vim plugin + CLI agent) | General guide |
| **§1 Optimized AI Tooling Strategy** | Tool comparison table (llama.vim, vim-ollama, Aider), caution about FIM conflicts | General guide (make editor-agnostic) |
| **§2 Ollama: Setting Up the Foundation** | Install Ollama, pull 3 models | General guide |
| **§3 Aider: Set Up CLI Agent** | Install Aider, configure for Ollama | General guide (or reference aider guide) |
| **§4 gergap/vim-ollama: Set Up Vim Inline Agent** | vim-plug install, g:ollama_debug, key mappings, <Plug> mappings | Keep in vim guide |
| **§5 Workflow and Usage** | Two scenarios: in-vim plugin + terminal Aider | Split: general patterns to general guide, vim-specific stays |
| Bonus: Web Aider | `uv tool install aider-chat[browser]` | Reference aider guide |
| **§6 Troubleshooting** | ModuleNotFoundError fix, debug logging | Keep in vim guide (plugin-specific) |

### Cross-References to Fix (all point to .ipynb files that don't exist)

| File | Line | Current (broken) | Should Be |
|------|------|-------------------|-----------|
| `vim_ollama/03_vim_ollama_tab_completion.md` | 32 | `/ai_agents/guides/vim_and_aider/01_vim_in_ai_era_hybrid_setup_with_ollama_and_aider.ipynb` | `/ai_agents/guides/vim_ollama/vim_ollama_plugin_setup.md` |
| `aider/aider_commands_handout.md` | 32 | `/ai_agents/guides/vim_and_aider/01_vim_in_ai_era_hybrid_setup_with_ollama_and_aider.ipynb` | `/ai_agents/guides/terminal_ai_agents_workflow.md` |
| `0_intro/00_onboarding.md` | 88 | `/ai_agents/guides/vim_and_aider/01_vim_in_ai_era_hybrid_setup_with_ollama_and_aider.ipynb` | `/ai_agents/guides/terminal_ai_agents_workflow.md` |

### RELEASE_NOTES.md References
Lines 695 and 947 reference `/ai_agents/guides/aider/02_aider_commands_handout.ipynb` — these are **historical** (changelog entries). Do NOT change them. They document what was shipped at that time.

---

## Target Structure
```
ai_agents/guides/
├── terminal_ai_agents_workflow.md        # NEW: general strategy
├── connect_to_capable_llms_api_keys.md   # RENAMED: remove "04_"
├── aider/
│   └── aider_commands_handout.md         # RENAMED: remove "02_"
├── vim_ollama/                           # RENAMED: was vim_and_aider/
│   ├── vim_ollama_plugin_setup.md        # RENAMED: was 01_*, slimmed
│   └── vim_ollama_tab_completion.md      # RENAMED: was 03_*
├── claude/
│   ├── creating_consultant_skills.md
│   └── claude_code_memory_vs_claude_md.md  # RENAMED: remove date prefix
├── images/
│   └── gemini_limits_free_tier.png
└── kilocode/
    └── kilocode_cli_setup.md             # RENAMED: remove "05_"
```

---

### Task 1: Rename files (remove numeric prefixes)

**Rationale:** Directories provide structure; numeric prefixes are redundant and inconsistent.

- [ ] **Step 1.1: Rename aider commands handout**

```bash
git mv ai_agents/guides/aider/02_aider_commands_handout.md ai_agents/guides/aider/aider_commands_handout.md
```

- [ ] **Step 1.2: Rename API keys guide**

```bash
git mv ai_agents/guides/04_connect_to_capable_llms_using_api_keys.md ai_agents/guides/connect_to_capable_llms_api_keys.md
```

- [ ] **Step 1.3: Rename kilocode guide**

```bash
git mv ai_agents/guides/kilocode/05_kilocode_cli_setup.md ai_agents/guides/kilocode/kilocode_cli_setup.md
```

- [ ] **Step 1.4: Rename claude memory guide**

```bash
git mv ai_agents/guides/claude/2026_03_03_claude_code_memory_vs_claude_md.md ai_agents/guides/claude/claude_code_memory_vs_claude_md.md
```

- [ ] **Step 1.5: Commit**

```bash
git add ai_agents/guides/aider/aider_commands_handout.md ai_agents/guides/connect_to_capable_llms_api_keys.md ai_agents/guides/kilocode/kilocode_cli_setup.md ai_agents/guides/claude/claude_code_memory_vs_claude_md.md
git commit -m "refactor(guides): remove numeric prefixes from file names

Directories provide structure; prefixes are redundant and inconsistent.
- 02_aider_commands_handout.md → aider_commands_handout.md
- 04_connect_to_capable_llms... → connect_to_capable_llms_api_keys.md
- 05_kilocode_cli_setup.md → kilocode_cli_setup.md
- 2026_03_03_claude_code_memory... → claude_code_memory_vs_claude_md.md"
```

---

### Task 2: Rename vim_and_aider/ → vim_ollama/

**Rationale:** The directory contains only vim-ollama plugin guides. Aider has its own directory. The name is misleading.

- [ ] **Step 2.1: Rename directory**

```bash
git mv ai_agents/guides/vim_and_aider ai_agents/guides/vim_ollama
```

- [ ] **Step 2.2: Commit**

```bash
git add ai_agents/guides/vim_ollama/
git commit -m "refactor(guides): rename vim_and_aider/ to vim_ollama/

Directory contains only vim-ollama plugin guides. Aider has its own dir."
```

---

### Task 3: Create general terminal_ai_agents_workflow.md

**Rationale:** Extract general hybrid strategy and Ollama setup from the vim-specific guide into a tool-agnostic parent-level guide. This is needed because:
1. The hybrid philosophy applies to any editor (Vim, VS Code, Emacs)
2. Ollama is infrastructure, not vim-specific
3. New CLI agents (Claude Code, Kilo Code) need a general reference

- [ ] **Step 3.1: Create the file**

Write `ai_agents/guides/terminal_ai_agents_workflow.md` with this EXACT content:

```markdown
---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.1
kernelspec:
  name: python3
  display_name: Python 3 (ipykernel)
  language: python
---

# Terminal AI Agents Workflow

+++

The best way to work with AI tools in your development workflow is by adopting a hybrid strategy: use **editor plugins** for rapid, in-buffer tasks (like completion and single-file edits) and **CLI agents** for agentic, multi-file refactoring that leverages the power and stability of the terminal.

This guide covers the general philosophy and infrastructure setup. For tool-specific guides, see the cross-references below.

+++

## **1. Tool Categories and When to Use Them**

+++

| Tool Type | Examples | Core Function | Best For |
| :--- | :--- | :--- | :--- |
| **Editor Plugin** | `vim-ollama`, GitHub Copilot | **In-buffer completion, chat, single-file edits.** | Lowest latency, inline code completion, quick refactoring. |
| **CLI Agent** | Aider, Claude Code, Kilo Code | **Multi-file refactoring & committing.** Reads Git context and makes atomic changes. | Complex refactors, generating new files, fixing tests across the codebase. |

:::{caution}
Don't run multiple editor plugins with FIM (Fill-in-the-Middle) completion simultaneously. They aggressively intercept the same keystrokes, leading to unpredictable behavior.
:::

+++

## **2. Setting Up Local Model Infrastructure with Ollama**

+++

Install Ollama and pull models for different tasks:

1.  **Install Ollama:** Follow the [official guide](https://ollama.com/download) to install Ollama on your operating system and start the server.
2.  **Pull Models:** Pull high-quality models for different use cases.
    ```bash
    ollama pull qwen2.5-coder:3b   # fast enough for low-latency FIM/completion
    ollama pull qwen2.5-coder:14B  # better instruction following for complex editing and agentic tasks
    ollama pull gemma3n:e4b        # good for chat
    ```

+++

## **3. Choosing Your Tool Stack**

+++

:::{seealso} Tool-Specific Guides
> - [Aider Commands Handout](/ai_agents/guides/aider/aider_commands_handout.md)
> - [vim-ollama Plugin Setup](/ai_agents/guides/vim_ollama/vim_ollama_plugin_setup.md)
> - [Claude Code Memory](/ai_agents/guides/claude/claude_code_memory_vs_claude_md.md)
> - [Kilo Code CLI Setup](/ai_agents/guides/kilocode/kilocode_cli_setup.md)
> - [Connect to Cloud LLMs via API](/ai_agents/guides/connect_to_capable_llms_api_keys.md)
:::

+++

## **4. General Workflow Patterns**

+++

### Pattern 1: In-Editor Quick Edit (Editor Plugin)

+++

1.  **Select Code:** Use your editor's selection to highlight the code to refactor.
2.  **Ask Plugin:** Trigger the plugin's edit/chat command.
3.  **Prompt:** Type your instruction (e.g., "Rewrite using list comprehension").
4.  **Diff Review:** The plugin shows proposed changes. Accept or reject line-by-line.

This pattern works in Vim with `vim-ollama`, VS Code with Copilot Chat, or any editor with an AI plugin.

+++

### Pattern 2: Multi-File Feature Implementation (CLI Agent)

+++

1.  **Open Terminal:** Use a terminal session (standalone or split in your editor).
2.  **Start Agent:** Launch your CLI agent (e.g., `aider --model ollama_chat/qwen2.5-coder:14B`).
3.  **Add Files:** Tell the agent what to work on (e.g., `/add main.py utils.py tests/test_utils.py`).
4.  **Prompt:** Give a high-level instruction spanning multiple files.
5.  **Reload & Review:** The agent modifies files on disk. Your editor detects changes and prompts you to reload buffers. Review the diff.

This pattern applies to Aider, Claude Code, Kilo Code, and similar CLI-based agents.

+++

### Pattern 3: Hybrid Mode (Cloud + Local)

+++

For large-context planning tasks, use a capable cloud LLM (Gemini, Grok) via API as the architect model, while a local SLM handles execution:

- **Architect mode:** Cloud LLM for high-level planning and design
- **Editor model:** Local SLM for coding, testing, and fixing

:::{seealso}
> See [Connect to Cloud LLMs](/ai_agents/guides/connect_to_capable_llms_api_keys.md) for API key setup and model orchestration.
:::

+++

## **5. Data Privacy Considerations**

+++

When using cloud LLMs via API keys, be aware of the data privacy trade-offs:

- **Free-tier APIs** often use your prompts for model training and human review
- **Paid-tier accounts** (even within free usage limits) typically provide enterprise privacy agreements
- **Local models** (Ollama) never leave your machine

For server configs, IP addresses, and sensitive data, always use local models or mask credentials before sending to cloud APIs.

:::{seealso}
> See [Connect to Cloud LLMs](/ai_agents/guides/connect_to_capable_llms_api_keys.md) for the complete data classification table and sanitization workflow.
:::
```

- [ ] **Step 3.2: Commit**

```bash
git add ai_agents/guides/terminal_ai_agents_workflow.md
git commit -m "feat(guides): add general terminal AI agents workflow guide

Extracted from vim-specific guide. Covers hybrid strategy, Ollama setup,
workflow patterns, and cross-references to all tool-specific guides."
```

---

### Task 4: Slim vim_ollama_plugin_setup.md to plugin-only content

**Rationale:** The file `vim_ollama/01_vim_in_ai_era_hybrid_setup_with_ollama_and_aider.md` currently contains:
- ~40% general content (hybrid strategy, Ollama setup, Aider setup)
- ~60% vim-ollama plugin configuration

We need to remove the general content and replace it with a reference to the new general guide.

- [ ] **Step 4.1: Read the current file**

```bash
cat ai_agents/guides/vim_ollama/01_vim_in_ai_era_hybrid_setup_with_ollama_and_aider.md
```

- [ ] **Step 4.2: Replace ENTIRE file content**

Use `edit` tool to replace the full content. Keep the Jupytext frontmatter. Replace everything after it with:

```markdown
---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.1
kernelspec:
  name: python3
  display_name: Python 3 (ipykernel)
  language: python
---

# vim-ollama Plugin Setup

+++

:::{seealso}
See [Terminal AI Agents Workflow](/ai_agents/guides/terminal_ai_agents_workflow.md) for the general hybrid strategy, Ollama setup, and when to use editor plugins vs CLI agents.
:::

+++

This guide covers the installation and configuration of the `gergap/vim-ollama` plugin, which provides in-editor AI functionality for code completion, refactoring, and general chat.

+++

## **1. Plugin Installation (using `vim-plug`)**

+++

Add the following to your `~/.vimrc`:

```vim
call plug#begin()
Plug 'gergap/vim-ollama'
" ... other plugins
call plug#end()
```

Run `:PlugInstall` within Vim to download and install the plugin.

After installation, run in VIM:

```
:Ollama setup
```

General settings like context lines or model selection should be placed in this dedicated file.

+++

## **2. Initial Plugin Settings**

+++

To prevent potential errors upon startup, define the `g:ollama_debug` variable, which handles the plugin's internal logging level, to any integer value.

**In `~/.vim/config/ollama.vim`:**

```vim
" Define and initialize the debug variable to prevent E121/E116 errors.
" Set to 0 to disable logging.
let g:ollama_debug = 0
```

> - E121: Undefined variable: g:ollama_debug, and
> - E116: Invalid arguments for function ollama#logger#PythonLogLevel(g:ollama_debug).

+++

## **3. Configure Key Mappings**

+++

This section covers core commands (Normal/Visual Mode) and suggestion handling (Insert Mode). Read the official documentation for advanced options: `:help vim-ollama-maps`.

+++

### Define a `<Leader>` key

+++

Define your leader key (if you haven't already, **`<Space>`** is recommended):

```vimrc
" --- Vim Core Configuration ---
let mapleader = " "        " Set Leader key to Spacebar
```

+++

### Custom Mappings for Chat, Review, and Edit (Normal and Visual Modes)

+++

We will **disable default mappings** to prevent conflicts, then define custom ones (you can choose one keys).

**In your `~/.vimrc`:**

```vimrc
" --- Ollama Plugin Configuration ---

" !! IMPORTANT !! Disable all default plugin mappings
" This prevents conflicts and ensures only your custom mappings are used.
let g:ollama_no_maps = 1

" Normal Mode
" Use for general chat
nnoremap <Leader>c :OllamaChat<CR>
" Toggle FIM completion on/off (Mapped to default key)
nnoremap <Leader>t :Ollama toggle<CR>

" Visual Mode
" Use for refactoring selected code (Mapped to default key)
vnoremap <Leader>e :OllamaEdit
" Use for reviewing selected code
vnoremap <Leader>or :OllamaReview
```

+++

### Suggestion Mappings (Insert Mode)

+++

**Freeing the `<Tab>` Key**

The default behavior is for **`<Tab>`** to accept the full suggestion.

If you **must** use `<Tab>` for indenting instead, you need to explicitly disable the plugin's mapping:

**Add this line to your `~/.vimrc`:**

```vimrc
" Do not map <Tab> to accept the entire completion
" This restores <Tab> to its default function.
let g:ollama_no_tab_map = v:true
```

**Setting New Custom Acceptance Mappings**

If you disabled `<Tab>`, or if you prefer simpler keys for line/word acceptance, use the following official `<Plug>` mappings shown in the documentation:

```vimrc
" Accept Full Block Control-A
inoremap <C-a> <Plug>(ollama-tab-completion)

" Accept Next Line Control-J
inoremap <C-j> <Plug>(ollama-insert-line)

" Accept Next Word Control-L
inoremap <C-l> <Plug>(ollama-insert-word)

" Dismiss the current suggestion (Mapped to default Control-])
inoremap <C-]> <Plug>(ollama-dismiss)
```

By using these official `<Plug>` mappings, you are calling the internal plugin functions directly, guaranteeing stability and avoiding the unreliable terminal transmission of `<M-Right>` or `<M-C-Right>`.

+++

## **4. Workflow: In-Vim Refactoring**

+++

The typical vim-ollama workflow for single-file tasks:

1.  **Visual Select:** Use **`V`** or **`v`** to select the function block you want to change.
2.  **Execute Edit:** Press **`<Space>e`**.
3.  **Prompt:** A prompt appears. Type your instruction, e.g., `"Rewrite this function to use list comprehension for performance."` Press `<Enter>`.
4.  **Diff Review:** The plugin opens a split with the AI's proposed changes, allowing you to use `vimdiff` commands to accept or reject line-by-line.

For multi-file refactoring and git-aware commits, use a CLI agent like Aider instead.

:::{seealso}
> - [Terminal AI Agents Workflow](/ai_agents/guides/terminal_ai_agents_workflow.md) — general hybrid strategy
> - [Aider Commands Handout](/ai_agents/guides/aider/aider_commands_handout.md) — CLI agent reference
:::

+++

## **5. Troubleshooting: Python & Connection Errors**

+++

Common issues often stem from how Fedora/Linux handles Python virtual environments or how `localhost` resolves in the terminal.

+++

### **Issue: ModuleNotFoundError: No module named 'requests'**

+++

If you see this error in the Vim status line or logs, your virtual environment is either missing or "hollow" (missing internal management tools).

**The "Modern" Fix (using `uv`):**
The most reliable way to ensure a functional, isolated environment is using `uv`.
```bash
# 1. Remove the broken environment
rm -rf ~/.vim/venv/ollama

# 2. Create a fresh venv using uv
uv venv ~/.vim/venv/ollama

# 3. Install dependencies specifically into that path
uv pip install requests httpx jinja2 mistralai openai -p $HOME/.vim/venv/ollama
```

+++

### **Issue: Debugging and Logs**

+++

If the plugin is behaving unexpectedly, enable logging to see the raw communication between Vim and the Python helper scripts.

1. **Create the log directory:** `mkdir -p /tmp/logs`
2. **Enable logging in `~/.vim/config/ollama.vim`:**
   ```vim
   let g:ollama_debug = 4
   let g:ollama_logfile = '/tmp/logs/vim-ollama.log'
   ```
3. **Monitor the logs in a separate terminal:**
   ```bash
   tail -f /tmp/logs/vim-ollama.log
   ```
```

**What was removed from the original:**
- ✗ Intro paragraph about hybrid strategy → moved to general guide
- ✗ Section 1 "Optimized AI Tooling Strategy" table → moved to general guide
- ✗ Section 2 "Ollama: Setting Up the Foundation" → moved to general guide
- ✗ Section 3 "Aider: Set Up CLI Agent" → moved to general guide
- ✗ "Bonus: Web Aider" subsection → reference aider guide instead
- ✗ "Terminal Task (Aider)" workflow example → moved to general guide

**What was kept:**
- ✅ Plugin installation (vim-plug)
- ✅ Initial plugin settings (g:ollama_debug)
- ✅ Key mappings (all of section 4)
- ✅ In-Vim refactoring workflow (simplified from section 5)
- ✅ Troubleshooting (section 6)

- [ ] **Step 4.3: Commit**

```bash
git add ai_agents/guides/vim_ollama/01_vim_in_ai_era_hybrid_setup_with_ollama_and_aider.md
git commit -m "refactor(guides): slim vim guide to plugin-only content

Removed general hybrid strategy, Ollama setup, Aider setup sections
(now in terminal_ai_agents_workflow.md). Added cross-references to
general guide and aider handout."
```

---

### Task 5: Rename vim_ollama files (remove 01_, 03_ prefixes)

- [ ] **Step 5.1: Rename vim plugin setup file**

```bash
git mv ai_agents/guides/vim_ollama/01_vim_in_ai_era_hybrid_setup_with_ollama_and_aider.md ai_agents/guides/vim_ollama/vim_ollama_plugin_setup.md
```

- [ ] **Step 5.2: Rename tab completion guide**

```bash
git mv ai_agents/guides/vim_ollama/03_vim_ollama_llm_tab_completion_nuances.md ai_agents/guides/vim_ollama/vim_ollama_tab_completion.md
```

- [ ] **Step 5.3: Commit**

```bash
git add ai_agents/guides/vim_ollama/vim_ollama_plugin_setup.md ai_agents/guides/vim_ollama/vim_ollama_tab_completion.md
git commit -m "refactor(guides): remove numeric prefixes from vim_ollama files"
```

---

### Task 6: Update all cross-references

Three files contain broken references to old paths with `.ipynb` extension. Fix each one.

- [ ] **Step 6.1: Fix reference in vim_ollama_tab_completion.md**

Read the file first to confirm the line:
```bash
grep -n "01_vim_in_ai_era\|\.ipynb" ai_agents/guides/vim_ollama/vim_ollama_tab_completion.md
```

The file contains at line ~32 this exact text:
```markdown
:::{seealso}
> Setup vim-ollama: ["VIM in AI Era: Hybrid Setup with Ollama and Aider"](/ai_agents/guides/vim_and_aider/01_vim_in_ai_era_hybrid_setup_with_ollama_and_aider.ipynb)
:::
```

Replace it with:
```markdown
:::{seealso}
> Setup vim-ollama: [vim-ollama Plugin Setup](/ai_agents/guides/vim_ollama/vim_ollama_plugin_setup.md)
:::
```

Use the `edit` tool with this exact old_string (include 3 lines of context):
```
+++

This handbook explains the mechanics of LLM-based tab completion within Vim specifically for the `vim-ollama` plugin and why specific model-config alignment is required for it to function correctly.

:::{seealso}
> Setup vim-ollama: ["VIM in AI Era: Hybrid Setup with Ollama and Aider"](/ai_agents/guides/vim_and_aider/01_vim_in_ai_era_hybrid_setup_with_ollama_and_aider.ipynb)
:::

+++
```

New string:
```
+++

This handbook explains the mechanics of LLM-based tab completion within Vim specifically for the `vim-ollama` plugin and why specific model-config alignment is required for it to function correctly.

:::{seealso}
> Setup vim-ollama: [vim-ollama Plugin Setup](/ai_agents/guides/vim_ollama/vim_ollama_plugin_setup.md)
:::

+++
```

- [ ] **Step 6.2: Fix reference in aider_commands_handout.md**

The file `ai_agents/guides/aider/aider_commands_handout.md` contains at line ~32:
```markdown
:::{seealso} How to set up aider
> [VIM in AI Era: Hybrid Setup with Ollama and Aider](/ai_agents/guides/vim_and_aider/01_vim_in_ai_era_hybrid_setup_with_ollama_and_aider.ipynb)
```

Replace with:
```markdown
:::{seealso} How to set up aider
> [Terminal AI Agents Workflow](/ai_agents/guides/terminal_ai_agents_workflow.md)
```

Use the `edit` tool with context. The exact old_string (from the file content read earlier):
```
+++

Aider is an AI pair programmer that uses your code as context.

:::{seealso} How to set up aider
> [VIM in AI Era: Hybrid Setup with Ollama and Aider](/ai_agents/guides/vim_and_aider/01_vim_in_ai_era_hybrid_setup_with_ollama_and_aider.ipynb)

+++

## **1. Installation and Setup**
```

New string:
```
+++

Aider is an AI pair programmer that uses your code as context.

:::{seealso} How to set up aider
> [Terminal AI Agents Workflow](/ai_agents/guides/terminal_ai_agents_workflow.md)

+++

## **1. Installation and Setup**
```

- [ ] **Step 6.3: Fix reference in 00_onboarding.md**

Read the file to find the exact line:
```bash
grep -n "vim_and_aider\|01_vim_in_ai_era" 0_intro/00_onboarding.md
```

The reference at line ~88 is:
```markdown
1. ["VIM in AI Era: Hybrid Setup with Ollama and Aider"](/ai_agents/guides/vim_and_aider/01_vim_in_ai_era_hybrid_setup_with_ollama_and_aider.ipynb)
```

Replace with:
```markdown
1. [Terminal AI Agents Workflow](/ai_agents/guides/terminal_ai_agents_workflow.md)
```

Use the `edit` tool with surrounding context (read the file first to get the exact 3 lines before and after).

- [ ] **Step 6.4: Verify no other .ipynb references in guides**

```bash
grep -rn "\.ipynb" ai_agents/guides/
```

Expected: No output (all .ipynb references removed from guides directory)

If RELEASE_NOTES.md or misc/plan files show up — IGNORE them. Those are historical.

- [ ] **Step 6.5: Commit**

```bash
git add ai_agents/guides/vim_ollama/vim_ollama_tab_completion.md ai_agents/guides/aider/aider_commands_handout.md 0_intro/00_onboarding.md
git commit -m "fix(guides): update cross-references to new paths and .md extension

- vim_ollama_tab_completion.md: point to vim_ollama_plugin_setup.md
- aider_commands_handout.md: point to terminal_ai_agents_workflow.md
- 00_onboarding.md: point to terminal_ai_agents_workflow.md"
```

---

### Task 7: Final verification

- [ ] **Step 7.1: Check for broken links**

```bash
uv run tools/scripts/check_broken_links.py --pattern "*.md"
```

Expected: May show RELEASE_NOTES.md references (lines 695, 947) — those are historical and acceptable. All guides/ links must be valid.

- [ ] **Step 7.2: Verify final directory structure**

```bash
find ai_agents/guides/ -type f | sort
```

Expected output:
```
ai_agents/guides/aider/aider_commands_handout.md
ai_agents/guides/claude/claude_code_memory_vs_claude_md.md
ai_agents/guides/claude/creating_consultant_skills.md
ai_agents/guides/connect_to_capable_llms_api_keys.md
ai_agents/guides/images/gemini_limits_free_tier.png
ai_agents/guides/kilocode/kilocode_cli_setup.md
ai_agents/guides/terminal_ai_agents_workflow.md
ai_agents/guides/vim_ollama/vim_ollama_plugin_setup.md
ai_agents/guides/vim_ollama/vim_ollama_tab_completion.md
```

- [ ] **Step 7.3: Final git status**

```bash
git status
```

Expected: Working tree clean (all changes committed)

---

## Self-Review

**1. Spec coverage:**
- ✅ Remove numeric prefixes → Tasks 1, 5
- ✅ Rename vim_and_aider/ → vim_ollama/ → Task 2
- ✅ Create general terminal workflow guide → Task 3 (full content provided)
- ✅ Slim vim guide to plugin-only → Task 4 (full content provided, removal list documented)
- ✅ Update all cross-references → Task 6 (exact old_string/new_string for each file)
- ✅ Verify → Task 7 (commands with expected output)

**2. Placeholder scan:**
- No TBD, TODO, "implement later" found
- All file content is complete (Tasks 3, 4)
- All edit operations have exact old_string with context (Task 6)
- All commands include expected output

**3. Cross-reference map (final state):**
```
terminal_ai_agents_workflow.md
  → links to: aider/aider_commands_handout.md
  → links to: vim_ollama/vim_ollama_plugin_setup.md
  → links to: claude/claude_code_memory_vs_claude_md.md
  → links to: kilocode/kilocode_cli_setup.md
  → links to: connect_to_capable_llms_api_keys.md

vim_ollama/vim_ollama_plugin_setup.md
  → links to: terminal_ai_agents_workflow.md (top seealso)
  → links to: aider/aider_commands_handout.md (bottom seealso)

vim_ollama/vim_ollama_tab_completion.md
  → links to: vim_ollama/vim_ollama_plugin_setup.md (top seealso)

aider/aider_commands_handout.md
  → links to: terminal_ai_agents_workflow.md (top seealso)

0_intro/00_onboarding.md
  → links to: terminal_ai_agents_workflow.md
```

**4. Scope check:**
All tasks produce working, testable changes. Each commit is a complete step. No placeholders. Another agent can execute this without re-brainstorming because:
- Full file content is provided for new files (Task 3) and rewritten files (Task 4)
- Exact edit operations with old_string/new_string are provided for cross-references (Task 6)
- All commands and expected outputs are documented
- Context table shows what moves where and why
