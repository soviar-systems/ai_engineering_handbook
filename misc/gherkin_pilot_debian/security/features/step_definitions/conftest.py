"""
pytest-bdd conftest for security feature tests.

Registers the shared `context` fixture so it is available to all step
definitions without explicit import. pytest-bdd resolves fixtures by name.
"""

import pytest


@pytest.fixture
def context() -> dict:
    """Mutable dict for sharing state between Given/When/Then steps."""
    return {}
