---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.0
kernelspec:
  name: python3
  display_name: Python 3 (ipykernel)
  language: python
---

# Kilo Code CLI: Installation and Setup

+++

---
title: "Kilo Code CLI: Installation and Setup"
author: Vadim Rudakov, rudakow.wadim@gmail.com
description: "Step-by-step setup guide for Kilo Code CLI (Roo Code/Cline fork, 500+ models): npm install, Ollama local models, DashScope/Qwen cloud, and multi-provider BYOK setup."
tags: [cli_agents, tooling, installation]
date: 2026-03-15
options:
  type: guide
  birth: 2026-03-15
  version: 1.0.0
---

+++

Kilo Code is an open-source AI coding agent for the terminal (and VS Code). It is a fork of Roo Code / Cline, supports 500+ models, and works with both cloud APIs and local models via Ollama — a strong alternative to aider when you want an interactive TUI agent.

+++

## **1. Install Kilo Code CLI**

+++

### Prerequisites

+++

Make sure Node.js 18+ is installed:

```bash
node --version
npm --version
```

+++

### Install via npm (user-local, no sudo)

+++

Installing to `~/.local` avoids permission issues on Fedora/Linux systems where `/usr/local/lib` is root-owned:

```bash
npm install -g @kilocode/cli --prefix ~/.local
```

+++

:::{note}
**Behind a corporate/Squid proxy?**
npm does not automatically pick up `HTTPS_PROXY` from the environment. Pass it explicitly:
```bash
npm install -g @kilocode/cli --prefix ~/.local \
  --proxy http://<username>:<password>@<proxy-host>:<port>
```
Or set it permanently so you never need the flag again:
```bash
npm config set proxy http://<username>:<password>@<proxy-host>:<port>
npm config set https-proxy http://<username>:<password>@<proxy-host>:<port>
```
Replace `<username>`, `<password>`, `<proxy-host>`, `<port>` with your actual proxy credentials.
:::

+++

### Add `~/.local/bin` to PATH

+++

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
```

Verify:

```bash
kilo --version
```

+++

## **2. Launch Kilo Code**

+++

### Interactive TUI (default)

+++

Navigate to your project directory and run:

```bash
cd /path/to/my/project
kilo
```

This opens the full terminal UI where you can chat with the agent, approve file edits, and run shell commands interactively.

+++

### One-off task (non-interactive)

+++

```bash
kilo run "add input validation to the signup form"
```

+++

### Key CLI flags

+++

| Flag | Description |
| :--- | :--- |
| `-m provider/model` | Set the model (e.g. `-m ollama/qwen2.5-coder:14b`) |
| `-c` | Continue the last session |
| `-s <session-id>` | Resume a specific session |
| `--prompt "<text>"` | Pass an initial prompt non-interactively |

+++

## **3. Authenticate with Kilo Platform**

+++

Kilo offers its own hosted models, including free-tier ones, at [kilo.ai](https://kilo.ai). To use them, log in:

```bash
kilo auth login
```

This opens a browser-based OAuth flow. Credentials are stored in `~/.local/share/kilo/auth.json`.

```bash
kilo auth list    # show stored credentials
kilo auth logout  # log out
```

List available Kilo-hosted models (including free ones):

```bash
kilo models
```

+++

:::{note}
**No account needed** to use your own API keys or a local Ollama instance — skip this section entirely if you prefer BYOK or local models.
:::

+++

## **4. Connect to Local Ollama + Qwen**

+++

Kilo Code supports Ollama as a local model provider. This lets you run Qwen (or any other model) entirely on your own hardware with no API costs and full data privacy.

+++

### Pull the model and start Ollama

+++

```bash
ollama pull qwen2.5-coder:14b    # recommended for agentic tasks
ollama pull qwen2.5-coder:3b     # lighter, fast edits
ollama serve                     # starts server at http://localhost:11434
```

+++

### Launch Kilo with a local model

+++

```bash
kilo -m ollama/qwen2.5-coder:14b
```

Or for a one-off run:

```bash
kilo run -m ollama/qwen2.5-coder:14b "refactor the auth module to use JWT"
```

+++

:::{tip}
**Recommended models by task:**

| Model | Use case |
| :--- | :--- |
| `qwen2.5-coder:14b` | Multi-file edits, complex instructions |
| `qwen2.5-coder:3b` | Fast single-file edits, low VRAM |
| `qwen3-coder:30b` | Best quality (requires 24GB+ VRAM) |
:::

+++

:::{note}
**Context window:** Ollama's default `num_ctx` can be too small for agentic tasks. Set it to at least 32k in your `Modelfile` or via `OLLAMA_NUM_CTX=32768` environment variable before starting `ollama serve`.
:::

+++

## **5. Connect to Qwen Cloud (DashScope API)**

+++

To use Qwen's cloud models (larger, more capable than local ones) you authenticate via the **DashScope API key**.

+++

:::{important}
**Qwen OAuth (regular account login) is not supported in Kilo Code.**

[Qwen Code](https://github.com/QwenLM/qwen-code) has a special `/auth → Qwen OAuth` flow that lets you log in with a regular [qwen.ai](https://qwen.ai) account and get **1,000 free requests/day** without any API key. This feature is built into Qwen Code only — it does not exist in Kilo Code.

If you want that free tier with zero setup, use Qwen Code instead. In Kilo Code, Qwen cloud access requires a DashScope API key.
:::

+++

### Get a DashScope API key

+++

1. Sign up or log in at [Alibaba Cloud Model Studio](https://bailian.console.aliyun.com/)
2. Go to **API Keys** and create a new key
3. For international users (outside China): use [international.aliyuncs.com](https://bailian.console.aliyun.com/?tab=api#/api-key)

+++

### Set the key as an environment variable

+++

```bash
export DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
# add to ~/.bashrc to make it permanent
```

+++

### Launch Kilo with Qwen Cloud via OpenAI-compatible endpoint

+++

Kilo Code supports any OpenAI-compatible provider. Use the `-m` flag with the `openai-compatible` provider and set the base URL:

```bash
OPENAI_API_KEY=$DASHSCOPE_API_KEY \
OPENAI_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1 \
kilo -m openai-compatible/qwen-plus
```

Available Qwen cloud model IDs:

| Model | Notes |
| :--- | :--- |
| `qwen-turbo` | Fast, cheap, good for simple tasks |
| `qwen-plus` | Balanced capability and cost |
| `qwen-max` | Best quality, highest cost |
| `qwen2.5-coder-32b-instruct` | Best for code tasks |

+++

:::{seealso}
- [DashScope OpenAI-compatible API docs](https://www.alibabacloud.com/help/en/model-studio/compatibility-of-openai-with-dashscope)
- [Qwen model list](https://www.alibabacloud.com/help/en/model-studio/getting-started/models)
:::

+++

## **6. Connect to Cloud Providers (Gemini, Claude, OpenRouter, Groq)**

+++

Kilo Code supports all major cloud providers via **BYOK (Bring Your Own Key)**. You can register your key through the Kilo platform web UI, or pass it directly via environment variables for a provider-agnostic approach.

+++

### Get API keys

+++

| Provider | Where to get the key | Free tier |
| :--- | :--- | :--- |
| **Gemini** | [Google AI Studio](https://aistudio.google.com/api-keys) | Yes, 20 RPD on flash models |
| **Claude (Anthropic)** | [Anthropic Console](https://console.anthropic.com/settings/keys) | No (pay-as-you-go) |
| **OpenRouter** | [OpenRouter Settings](https://openrouter.ai/settings/keys) | Yes, 50 free req/day |
| **Groq** | [Groq Console](https://console.groq.com/keys) | Yes |

+++

### Register your key via Kilo web UI (recommended)

+++

After logging in with `kilo auth login`:

1. Go to [kilo.ai/dashboard](https://kilo.ai/dashboard)
2. Navigate to **Account → Bring Your Own Key (BYOK)**
3. Click **Add Your First Key**, select the provider, and paste your API key

From this point your key is used automatically when you select a model from that provider in Kilo.

+++

### Or pass the key via environment variable

+++

For a simpler, login-free workflow — set the standard environment variable and launch:

```bash
# Gemini
export GEMINI_API_KEY=AIzaSy...
kilo -m gemini/gemini-2.5-flash

# Claude
export ANTHROPIC_API_KEY=sk-ant-...
kilo -m anthropic/claude-sonnet-4-5

# OpenRouter
export OPENROUTER_API_KEY=sk-or-...
kilo -m openrouter/qwen/qwen3-coder:free

# Groq
export GROQ_API_KEY=gsk_...
kilo -m groq/llama-3.3-70b-versatile
```

+++

:::{tip}
Add your keys to `~/.bashrc` to avoid re-exporting them each session:
```bash
export GEMINI_API_KEY=AIzaSy...
export ANTHROPIC_API_KEY=sk-ant-...
```
:::

+++

:::{seealso}
- [Kilo Code AI Providers docs](https://kilo.ai/docs/ai-providers)
- [Kilo BYOK docs](https://kilo.ai/docs/getting-started/byok)
:::

+++

## **7. Useful Commands Reference**

+++

```bash
kilo                        # launch interactive TUI
kilo run "<task>"           # run a one-off task
kilo models                 # list all available models
kilo session list           # list past sessions
kilo export <session-id>    # export session as JSON
kilo auth login             # log in to Kilo platform
kilo auth list              # show stored credentials
kilo auth logout            # log out
kilo mcp                    # manage MCP (Model Context Protocol) servers
kilo upgrade                # upgrade to the latest version
kilo stats                  # show token usage and cost statistics
kilo uninstall              # uninstall kilo and remove config files
```

+++

:::{seealso}
- [Kilo Code GitHub](https://github.com/Kilo-Org/kilocode)
- [Kilo Code Documentation](https://kilo.ai/docs)
- [Kilo Code Getting Started](https://kilo.ai/docs/getting-started)
:::
