---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.18.1
kernelspec:
  name: bash
  display_name: Bash
  language: bash
---

# Aider Commands Handout

+++

---

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.2.0  
Birth: 2025-11-18  
Last Modified: 2026-01-13

---

+++

Aider is an AI pair programmer that uses your code as context.

:::{seealso} How to set up aider
> [VIM in AI Era: Hybrid Setup with Ollama and Aider](/tools/docs/ai_agents/01_vim_in_ai_era_hybrid_setup_with_ollama_and_aider.ipynb)

+++

## **1. Installation and Setup**

+++

command|description
-|-
**Installation**|
`uv tool install aider-chat`|install aider with uv (faster)
`pipx install aider-chat`|install aider with pipx (traditional way)
`uv tool install aider-chat[browser]`|install browser extension (experimental feature)
`aider -h`|show help message and exit
`aider --version`|Show the version number and exit
**Configuration files**|
`/path/to/project/.aider.conf.yml`|poject level file
`$HOME/.aider.conf.yml`|user level file
`-c /path/to/.aider.conf.yml`|specific file, i.e. project level
**Essential Configuration Flags**|
`--model MODEL`|Specify the LLM to use
`--light-mode`|Use colors suitable for a light terminal background (default: False), env var: `AIDER_LIGHT_MODE`
`--auto-commits`, `--no-auto-commits`|Enable/disable auto commit of LLM changes (default: True) env var: `AIDER_AUTO_COMMITS`

Args that start with `--` can be set in a config file. The config file uses YAML syntax and must represent a YAML 'mapping' (for details, see http://learn.getgrav.org/advanced/yaml). 

:::{important} **Precedence**
In general, command-line values override environment variables which override config file values which override defaults.
:::

+++

## **2. Using proxy**

+++

If your organization requires all external traffic to be routed through the proxy, you can set these environment variables and pass them to the terminal session before starting the aider:

```bash
export HTTPS_PROXY="http://[user:password]@proxy_ip_address:port"
export https_proxy="http://[user:password]@proxy_ip_address:port"
```

You should NOT set `HTTP_PROXY` variable because it breaks the connection between the aider and local ollama through `http://127.0.0.1:11434`.

You can wrap this configuration into a script wrapper `aider_proxy.sh`:

```bash
#!/bin/bash
set -euo pipefail


main() {

    export HTTPS_PROXY="http://[user:password]@proxy_ip_address:port"
    export https_proxy="http://[user:password]@proxy_ip_address:port"

    exec aider "$@"
}


main "$@"
```

Make this [script executable](/tools/docs/scripts_instructions/how_to_use_scripts_on_gnu_linux.ipynb) and add it to your PATH. Now you can run aider simply:

```bash
$ aider_proxy.sh --model gemini/gemini-3-flash
```

Avoid using proxy if it's not necessary for it adds complexity to the aider configuration.

+++

## **3. Running & Basic Usage**

+++

### Launching aider

+++

command|description
-|-
`aider --model ollama_chat/<model_name>`|run a local model in terminal (get name from `ollama ls`)
`--gui`, `--no-gui`, `--browser`, `--no-browser`|Run aider in your browser (default: False); env var: `AIDER_GUI`
`aider --list-models gemini/`| list available models

+++

(aider-conf-yaml)=
### Core File Management

+++

| Command | Description |
| :--- | :--- |
`--file FILE`|specify a file to edit (can be used multiple times); env var: `AIDER_FILE`
`--read FILE`|specify a read-only file (can be used multiple times); env var: `AIDER_READ`
`/add`|Add files to the chat so aider can edit them or review them in detail.
`/tokens`|Report on the number of tokens used by the current chat context

:::{tip}
Use `/add` to tell Aider a file exists and is available for modification. This way aider knows this file exists and **will write to it**. Otherwise, aider might write the changes to an existing file; [source](https://aider.chat/docs/usage/tips.html)
:::

+++

### Using the Repository Map

+++

command|description
| :--- | :--- |
| `--map-tokens NUM` | **Limit the size** of the Repository Map in tokens (e.g., `aider --map-tokens 500`). |
| `/map` | **Display** the current Repository Map summary. |

The **Repository Map** provides a structural overview (file/function) of your project, helping the AI understand context without loading the entire codebase, thus saving tokens. Use `--map-tokens` to manage this resource (default is 1024 tokens).

+++

### In-Chat Commands

+++

command|description
| :--- | :--- |
| `/help` | Ask questions about Aider's features and usage. Aider's help is context-aware, i.e. it can answer questions about itself.|
| `/clear` | **Clear the chat history** (saves tokens). |
| `/run COMMAND` | Run an **arbitrary shell command** and share the output with the LLM. |
| `/undo` | **Undo the last Git commit** (only works for Aider's auto-commits). |
| `/web URL` | **Scrape a webpage**, convert to markdown and send in a message. |
| `/diff` | Show the **difference** between the current files and the last Aider commit. |
| `/commit MESSAGE` | Manually commit the current changes with a specific message. |
| `/exit` or `/quit` | Exit Aider. |

+++

## **4. Aider Integration with LLMs Using API Keys**

+++

Connect your aider to the capable LLMs, like Gemini, Grok, etc. with the free or paid teer. This allows you to work with much bigger context windows than the local LMs provide.

+++

### 4.1 Obtain an API Key

+++

#### Gemini

+++

Get it in the [Google AI studio](https://aistudio.google.com/api-keys), free tier is enough for start.

+++

:::{seealso}
> [Gemini API quickstart](https://ai.google.dev/gemini-api/docs/quickstart)
:::

+++

#### GROQ

+++

Groq currently offers free API access to the models they host. Obtain your API key here: https://console.groq.com/keys

+++

#### OpenRouter

+++

https://openrouter.ai/settings/keys

+++

### 4.2 Add API to aider

+++

You can pass an API key using either the command line or the config file: 

```bash
$ aider --model gemini/gemini-3-flash --api-key gemini=<your_api_key>
```

Using your LOCAL `~/.aider.conf.yml`. Set Gemini as the main (architect) model and save the API key:

```bash
$ ~/.aider.conf.yml

model: gemini/gemini-3-flash

api-key:
  - gemini=<your_api_key>
  - groq=<your_api_key>
  - openrouter=<your_api_key>
```

Now you can launch it like this, the Gemini model will be used as a main model.

```bash
$ aider
```

Launch other models with `--model` flag, like this:

```bash
$ aider --model openrouter/openai/gpt-oss-120b
```

See how to get the list of models in the [{name}](#list-models-section) section below.

:::{seealso} See aider documentation for details
https://aider.chat/docs/llms.html
:::

+++

### 4.3 Limits

+++

But it is a better idea to choose a model via command line because each model you request via API has its limit:

```bash
$ aider --model gemini/gemini-3-flash
```

+++

**Gemini Free tier limits**

You can control the usage [here](https://aistudio.google.com/app/usage):

:::{important} How Gemini rate limits work
:class: dropdown
Rate limits are usually measured across three dimensions:

Requests per minute (RPM)
Tokens per minute (input) (TPM)
Requests per day (RPD)
Your usage is evaluated against each limit, and exceeding any of them will trigger a rate limit error. For example, if your RPM limit is 20, making 21 requests within a minute will result in an error, even if you haven't exceeded your TPM or other limits.

Rate limits are applied per project, not per API key. Requests per day (RPD) quotas reset at midnight Pacific time.
> --- [Gemini API: Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)

```{figure} ./images/gemini_limits_free_tier.png
Free tier rate limits by model. Peak usage per model compared to its limit over the last 28 days
```
:::

+++

### 4.3 Combining different models

+++

(list-models-section)=
#### List models

+++

You can list available models with this command:

```bash
$ aider --list-models gemini/

$ aider --list-models groq/
```

On 13 Jan 2026, the free API keys of Google, GROQ, OpenRouter support these models with limits:

| Model (Free‑Tier)        | Token Per Request| Token Per Minute |
|--------------------------|-------------|----------------------|
|**GROQ**|||
|groq/gemma-7b-it|||
|groq/llama-3.1-8b-instant|||
|**groq/llama-3.3-70b-versatile**|  12K ||
|groq/meta-llama/llama-4-maverick-17b-128e-instruct|||
|groq/meta-llama/llama-4-scout-17b-16e-instruct|||
|groq/meta-llama/llama-guard-4-12b|||
|groq/moonshotai/kimi-k2-instruct-0905|||
|**groq/openai/gpt-oss-120b**||8K|
|groq/openai/gpt-oss-20b|||
|**groq/qwen/qwen3-32b**| 6K ||
|**Gemini**|||
|gemini/gemini-3-flash-preview| ||
|gemini/gemini-3-flash | | 250K |
|gemini/gemini-2.5-flash | | 250K |
|gemini/gemini-2.5-flash-preview-09-2025 | |
|gemini/gemini-2.5-flash-lite | | 250K | |
|gemini/gemma-3-27b-it | | 15K|
| **OpenRouter** | | |
|openrouter/qwen/qwen3-coder:free|||
|openrouter/qwen/qwen3-next-80b-a3b-instruct|||
|openrouter/qwen/qwen3-235b-a22b|||
|openrouter/qwen/qwen-plus|||
|openrouter/qwen/qwen-turbo|||
|openrouter/deepseek/deepseek-r1-0528:free|||
|openrouter/deepseek/deepseek-v3.2|||
|openrouter/google/gemini-2.5-flash-lite|||
|openrouter/google/gemini-2.0-flash-lite-001|||
|openrouter/google/gemini-2.0-flash-001|||
|openrouter/x-ai/grok-4.1-fast|||
|openrouter/x-ai/grok-4-fast|||
|openrouter/x-ai/grok-code-fast-1|||
|openrouter/x-ai/grok-3-mini|||
|openrouter/meta-llama/llama-3.3-70b-instruct:free|||
|openrouter/meta-llama/llama-3.1-405b-instruct|||

+++

#### Switch between models during session

+++

In the `/architect` mode the capable LLM can act as the main model to help you prepare the plan based on the large context while the local or the cheaper model set as `editor-model` can do the coding, testing, and fixing, saving you tokens.

Edit your local, NOT the repo's [`.aider.conf.yml`](#aider-conf-yaml):

```bash
$ ~/.aider.conf.yml

editor-model: ollama_chat/qwen2.5-coder:14b-instruct-q4_K_M
```

Now in the `/architect` mode the Gemini model will send tasks to the local Qwen model on your local GPU.

+++

## **5. Upgrading**

+++

command|description
| :--- | :--- |
`uv tool --upgrade aider-chat aider-chat[browser]`||
`aider --install-main-branch`|Install the latest version from the main branch; env var: `AIDER_INSTALL_MAIN_BRANCH`. Use for beta features only.
`aider --upgrade, --update`|Upgrade aider to the latest version from PyPI; env var: `AIDER_UPGRADE`
