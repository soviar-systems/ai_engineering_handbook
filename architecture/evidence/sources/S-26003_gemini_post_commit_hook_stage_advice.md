---
id: S-26003
title: "Gemini 3 Flash — Post-Commit Hook Stage Advice"
date: 2026-03-03
model: gemini-3.0-flash
extracted_into: A-26004
---

User:
I use post-commit hook to verify the correct structure of the commit body so the AI agent's work is validated

Gemini-3-Flash:
That is a bold strategy, but I have a quick "architectural" reality check for you: using `post-commit` to verify structure is like checking if a letter is addressed correctly **after** you've already dropped it in the mailbox.

While it technically works, there are a few reasons why shifting that "skill" slightly earlier in the timeline will save your AI agent (and you) a lot of headache.

---

## The Hook Timeline: Why `post-commit` is Risky

The `post-commit` hook runs after the commit hash has been created and the `HEAD` has moved.

| Hook Stage | Timing | Outcome if it Fails |
| --- | --- | --- |
| **pre-commit** | Before the message is even written. | Commit stops; no history created. |
| **commit-msg** | After writing, before saving. | Commit stops; user/AI can fix the text. |
| **post-commit** | **After the commit is saved.** | **The "bad" commit is already in your history.** |

### The Problem with `post-commit` for Validation:

1. **Orphaned Commits:** If your `post-commit` script finds an error and tries to "fix" it (e.g., by running `git commit --amend`), it creates a new commit hash.
2. **Notification Loops:** If the hook fails, the commit still exists. You then have to manually (or via agent) go back and fix a commit that technically already happened.
3. **Non-Blocking:** A failure in `post-commit` does **not** undo the commit. It just exits with an error code while the bad data stays in your local branch.

---

## The Better Way: `commit-msg` Hook

If your goal is to **validate the structure** (e.g., checking for a specific body format, Jira links, or character limits), you should use the **`commit-msg`** hook.

This hook receives the path to a temporary file containing the message. If your script exits with a non-zero status (fails), **Git aborts the commit entirely.**

### Example: The "Structure Validator" Skill

Here is how you would set up a "Skill-Gate" in your `.pre-commit-config.yaml` to ensure your AI agent (or humans) didn't forget the "Body" of the commit:

```yaml
-   repo: local
    hooks:
    -   id: validate-commit-body
        name: Check Commit Body Structure
        entry: python3 ./scripts/check_body.py
        language: python
        stages: [commit-msg]

```

**The Logic (`check_body.py`):**

```python
import sys

with open(sys.argv[1], 'r') as f:
    lines = f.readlines()
    # Check if there is a blank line and then a body
    if len(lines) < 3 or not lines[2].strip():
        print("Error: AI Agent failed to provide a detailed commit body.")
        sys.exit(1) # This stops the commit!

```

---

## How to give the AI Agent the "Self-Correction" Skill

If you want the AI agent to be truly autonomous, you don't just want it to hit a wall (the hook); you want it to **anticipate** the wall.

1. **The Pre-computation:** Tell the Agent: *"Before calling the commit tool, verify your message matches the regex `^\[PROJ-\d+\] .+\n\n[\s\S]+$`."*
2. **The Error Handler:** If the Agent calls the commit tool and the **hook** rejects it, the Agent will receive the error message from your script.
3. **The Skill:** Give the Agent a "Retry Logic" where it reads the hook's error message, fixes the body, and tries the commit again.

---

### Summary for your Workflow

* **Move the logic** from `post-commit` to `commit-msg`. This makes the validation "blocking" so bad commits never enter your history.
* **Feed the Hook errors back to the AI.** AI agents are surprisingly good at fixing their own formatting if the error message is clear (e.g., "Missing Jira Ticket in Header").

**Would you like me to show you how to configure your AI agent's system prompt so it understands how to read and fix these Git hook errors?**
