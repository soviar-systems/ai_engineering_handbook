"""Fixers for automatic documentation fixes."""

from vadocs.fixers.adr_fixer import AdrFixer
from vadocs.fixers.base import Fixer
from vadocs.fixers.sync_fixer import SyncFixer

__all__ = [
    "Fixer",
    "AdrFixer",
    "SyncFixer",
]
