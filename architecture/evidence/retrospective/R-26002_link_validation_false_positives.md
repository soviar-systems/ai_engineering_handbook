---
id: R-26002
title: Link Validation False Positives in Source Code
authors:
- name: Qwen Code
  email: agent@qwen.ai
description: A markdown-oriented link checker was applied to Python files, flagging
  regex patterns and intentional test fixtures as broken links until the extractor
  became file-type aware.
tags:
- ci
- development
- testing
date: 2026-06-27
options:
  type: retrospective
  birth: 2026-06-27
  version: 1.0.0
  status: resolved
  severity: medium
  token_size: 1092
---
# Retrospective: Link Validation False Positives in Source Code

## Executive Summary

The `check-broken-links` hook began blocking commits on Python files, even when the change had nothing to do with documentation. The cause was scope: a validator built for markdown was applied to source code without asking what a "link" means in that context.

Three classes of false positive appeared — regex patterns used to *find* links, test fixtures that contain deliberately broken paths, and an over-broad hook that forwarded every staged file to the script.

The resolution was to make the extractor context-aware rather than to weaken the rule: exclude the test suite, filter known pattern strings, and keep validating links in script comments where agents actually navigate by them.

## Introduction

This retrospective was written on 2026-06-27, after the `check-broken-links` hook began failing on `.py` files during unrelated commits. It records the false positives, their cause, and the tiered resolution.

The scope is link extraction and the hook scope that fed it.

## Technical Diagnosis

### Symptom

The hook reported `[BLOCKING]` broken links inside Python files. The reported "links" were not navigation references at all.

### False Positive Classes

1. **Regex patterns.** The validator identified regex patterns used to *find* links (for example `r"```\{include\}([^`\n]+)"`) as links themselves, then attempted to resolve them as paths.
2. **Deliberate test data.** Tests in `tools/tests/` intentionally use broken paths (for example `/architecture/adr/adr_999.md`) to verify the validator's own failure logic. The tool reported them as project defects.
3. **Over-broad hook scope.** The pre-commit hook forwarded every staged file to the script, and the script added all supplied files to the scan list regardless of extension.

## Root Cause

The tool applied documentation link rules to source code without distinguishing between a functional link and a code artifact.

A `.md` file and a `.py` file both contain strings that look like paths. In markdown, such a string is almost always a navigation target. In Python, it is frequently a pattern, a fixture, or a message. The extractor treated the two the same because it had no notion of file type; it only knew how to match a path-shaped string.

The over-broad hook made this visible sooner and more often, but it was not the root cause. The root cause was that "what counts as a link" was never defined per file type.

## Impact Assessment

Commits unrelated to documentation were blocked, which is the same failure mode as a global gate: the validator's failure condition was not a property of the change under review.

The cost was not only time. Each false positive required an agent or developer to decide whether a real defect existed, so the signal-to-noise ratio of the hook degraded exactly where it was most needed — in a repository where links are the navigation mechanism.

## Corrective Actions

A tiered strategy was implemented to balance production link safety against developer velocity:

- **Test exclusion.** `tools/tests/` was excluded from the `check-broken-links` hook. Test suites must contain broken examples to verify validator contracts.
- **Pattern filtering.** Specific regex patterns that trigger false positives were added to `BROKEN_LINKS_EXCLUDE_LINK_STRINGS` in `tools/scripts/paths.py`.
- **AI-facing link preservation.** Validation was retained for `.py` files in `tools/scripts/`, so references to ADRs and guides that agents use to navigate the codebase remain valid.

## Preventive Measures

- **Source code is documentation too.** In AI-engineered projects, links in comments are functional navigation assets. They must be validated — but not with the same blanket rules as markdown.
- **Test data is not production debt.** A validator must know what environment it is scanning. A broken link in a test is usually a correct test case.
- **Tiered constraints beat blanket ones.** When a tool's scope expands (for example from `.md` to `.py`), its matching logic must evolve from literal matching to context-aware matching.
- **Prefer context awareness over configuration silencers.** An exclusion list that names a tool's own regex patterns couples configuration to implementation. The durable fix is for the extractor to understand file type and comment syntax.

## References

- [AI Engineering Book — README](/README.md)
- [Post-Mortem: Sunset of the AI Engineering Book](/architecture/post-mortems/post_mortem_sunset_of_the_ai_engineering_book.md)
