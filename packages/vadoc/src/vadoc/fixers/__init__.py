"""Fixers for automatic documentation fixes."""

from vadoc.fixers.adr_fixer import AdrFixer
from vadoc.fixers.base import Fixer
from vadoc.fixers.sync_fixer import SyncFixer

__all__ = [
    "Fixer",
    "AdrFixer",
    "SyncFixer",
]
