---
name: convert-qwen-export
description: Convert Qwen chat export JSON to S-YYNNN evidence source markdown. Handles content_list phases, thread reconstruction, and frontmatter generation.
argument-hint: <path-to-qwen-json> [--id <S-YYNNN>] [--title "..."] [--output-dir <path>] [--dry-run]
---

Convert a Qwen/Open WebUI chat export JSON file into a standard S-YYNNN evidence source artifact.

**Never read the raw JSON directly — Qwen exports are 50-100K+ tokens. The script parses it into LLM-friendly markdown. Always work with the generated `.md`.**

## Usage

!`uv run python -m tools.scripts.convert_qwen_json_export_to_md $ARGUMENTS`

## CLI

```
convert_qwen_json_export_to_md.py <input.json> [options]

  --id S-YYNNN        Artifact ID (auto-detected from git history if omitted)
  --title "..."        Override chat title from the JSON
  --output-dir <path>  Output directory (default: architecture/evidence/sources/)
  --dry-run            Print to stdout, do not write file
```

## Output

Generates `S-YYNNN_<slug>.md` with frontmatter (`id`, `title`, `date`, `model`, `extracted_into`) and `### User` / `### Assistant` dialogue sections. Attachments rendered as `> Attached: name (type)`.

## After Conversion

1. `rm <path-to-json>` — Evidence Source Hygiene: raw JSON must not coexist with S-YYNNN
2. Read the generated `.md` to review — this is the working format
3. Set `extracted_into: [A-YYNNN]` when creating an analysis
4. Run `check_evidence.py` to validate
