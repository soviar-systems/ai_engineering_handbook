---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.18.1
kernelspec:
  name: python3
  display_name: Python 3 (ipykernel)
  language: python
---

# vim-ollama: LLM Tab Completion Nuances

+++

---

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.1.0  
Birth: 2026-01-13  
Last Modified: 2026-01-13

---

+++

This handbook explains the mechanics of LLM-based tab completion within Vim specifically for the `vim-ollama` plugin and why specific model-config alignment is required for it to function correctly.

:::{seealso}
> Setup vim-ollama: ["VIM in AI Era: Hybrid Setup with Ollama and Aider"](/tools/docs/ai_agents/01_vim_in_ai_era_hybrid_setup_with_ollama_and_aider.ipynb)
:::

+++

## **Understanding the Model-to-Config Relationship**

+++

### 1. The Core Logic: FIM (Fill-In-the-Middle)

+++

Unlike a standard chat interface, tab completion uses a technique called **FIM**. For the model to provide a seamless completion, it must receive the code surrounding your cursor in a very specific format:

* **Prefix:** Everything before the cursor.
* **Suffix:** Everything after the cursor.
* **Sentinels:** Special tokens (e.g., `<|fim_prefix|>`, `<|fim_suffix|>`) that tell the model where the gap is.

```{code-cell} ipython3
cat ~/.vim/plugged/vim-ollama/python/configs/qwen3-coder.json
```

### 2. The Role of JSON Configs

+++

In `vim-ollama`, the files located in `~/.vim/plugged/vim-ollama/python/configs/` act as **translation layers**.

If you set `g:ollama_model = 'qwen3:4b-instruct'` in your `~/.vim/config/ollama.vim` which sets the tab completion model, the plugin searches these JSON files to find a matching template. If no match is found:

1. The plugin may fail to send the correct "Sentinel" tokens.
2. The model will receive raw text and likely try to "continue" the file as a chat or a blog post rather than completing the logic.
3. You will often see empty suggestions or "prose" comments appearing in your code.

+++

### 3. Coder vs. Instruct Models

+++

| Model Type | Purpose | Behavior in Tab Completion |
| --- | --- | --- |
| **Coder** | Trained on raw code & FIM patterns. | **Best.** Understands the gap between prefix and suffix. |
| **Instruct** | Trained to follow conversational prompts. | **Poor.** Often tries to "explain" the code or chat with the user. |

:::{important} **The Golden Rule**
For Tab Completion to work, your `g:ollama_model` name must have a corresponding configuration file that defines its specific FIM tokens.
:::

+++

## **Troubleshooting & Best Practices**

+++

### Scenario: "I have the model, but completion isn't working"

+++

* **Check the Filename:** Ensure the string in your `.vimrc` matches the prefix of a JSON file in the `configs/` directory.
* **Check the Model Type:** If you are using an `instruct` model for completion, the plugin may not have a template for it because instruct models generally do not support FIM tokens natively.

+++

### Recommended Team Setup

+++

To ensure consistency across the team, everyone should use a model that has a verified config file:

```vim
" In .vimrc
" Use a 'coder' variant for specialized FIM support
let g:ollama_model = 'qwen2.5-coder:7b' 
```

+++

### How to Add a New Model

+++

If the team moves to a new model (e.g., `qwen3`) that isn't yet supported:

1. Identify the model's FIM tokens from its official documentation.
2. Create a new JSON file in `.../python/configs/` (e.g., `qwen3-coder.json`).
3. Define the `prefix`, `suffix`, and `middle` tokens within that file.

+++

## **Summary for the Team**

+++

* **Tab completion is not "plug and play"** for every model.
* **Consistency matters:** The model name in Vim must match a JSON config.
* **Model Choice:** Always prefer `-coder` models over `-instruct` models for the `g:ollama_model` variable used for completion.
