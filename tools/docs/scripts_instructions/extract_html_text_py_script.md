---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.0
kernelspec:
  name: bash
  display_name: Bash
  language: bash
---

# Instruction on extract_html_text.py script

+++

---
title: "Instruction on extract_html_text.py script"
author: rudakow.wadim@gmail.com
date: 2026-02-10
options:
  version: 1.0.0
  birth: 2026-02-10
---

+++

This [script](/tools/scripts/extract_html_text.py) extracts readable plain text from HTML files by stripping all markup, scripts, styles, and non-content elements.

It uses only the Python standard library (`html.parser`), requiring zero external dependencies.

+++

## Synopsis

+++

```bash
# Extract to stdout
extract_html_text.py INPUT_FILE

# Extract to file
extract_html_text.py INPUT_FILE --output OUTPUT_FILE
```

| Argument | Description | Default |
|----------|-------------|---------|
| `INPUT_FILE` | Path to the HTML file to extract text from | Required |
| `--output` | Write output to file instead of stdout | stdout |

**Exit Codes:**
- `0` = Extraction successful
- `1` = File not found or read error

+++

## Extraction Logic

+++

The script processes HTML using a SAX-style parser that:

1. **Discards non-content tags**: `<script>`, `<style>`, `<noscript>` tags and all their nested content are stripped completely.
2. **Preserves text from all other elements**: Paragraph text, headings, list items, table cells, and inline elements are collected.
3. **Decodes HTML entities**: `&amp;` → `&`, `&lt;` → `<`, character references like `&#8212;` → `—`.
4. **Normalizes whitespace**: Collapses runs of 3+ blank lines into 2.

+++

## Examples

+++

1. Extract text from an HTML file to stdout:

```{code-cell}
cd ../../../
echo '<html><body><p>Hello world</p><script>alert("hidden")</script></body></html>' > /tmp/test_extract.html
env -u VIRTUAL_ENV uv run tools/scripts/extract_html_text.py /tmp/test_extract.html
```

2. Extract to a file:

```{code-cell}
env -u VIRTUAL_ENV uv run tools/scripts/extract_html_text.py /tmp/test_extract.html --output /tmp/extracted.txt && cat /tmp/extracted.txt
```

## Test Suite

+++

The [test suite](/tools/tests/test_extract_html_text.py) covers the full extraction contract:

| Test Class | Coverage |
|------------|----------|
| `TestExtractText` | Unit tests: tag stripping, entity decoding, Unicode, nested tags, empty input |
| `TestCLISuccessPath` | Integration: stdout output, file output, empty files, Unicode files |
| `TestCLIErrorPath` | Error handling: missing files, no arguments, directories |

Run tests with:

```bash
uv run pytest tools/tests/test_extract_html_text.py -v
```

```{code-cell}
env -u VIRTUAL_ENV uv run pytest tools/tests/test_extract_html_text.py -q
```
