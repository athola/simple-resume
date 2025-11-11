"""Curate public API namespaces inspired by ``pandas.api``.

Only a subset of helpers are meant to be imported by downstream callers. The
`:mod:simple_resume.api` package groups those helpers into purpose-driven
namespaces (e.g., `:mod:simple_resume.api.colors`) while keeping the underlying
implementations private. Import from these modules when you need a stable
contract.
"""

from __future__ import annotations

from . import colors

__all__ = ["colors"]
