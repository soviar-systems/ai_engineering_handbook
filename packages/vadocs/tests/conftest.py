"""Shared test fixtures for vadoc tests."""

from pathlib import Path

import pytest


@pytest.fixture
def tmp_file(tmp_path: Path) -> Path:
    """Create a temporary file path."""
    return tmp_path / "test_doc.md"


@pytest.fixture
def sample_frontmatter_content() -> str:
    """Sample markdown content with YAML frontmatter."""
    return """---
id: 26001
title: Test Document
date: 2024-01-15
status: accepted
tags: [architecture]
---

# ADR-26001: Test Document

## Status

Accepted

## Context

Some context here.
"""


@pytest.fixture
def sample_no_frontmatter_content() -> str:
    """Sample markdown content without frontmatter."""
    return """# ADR-26001: Test Document

## Status

Accepted

## Context

Some context here.
"""
