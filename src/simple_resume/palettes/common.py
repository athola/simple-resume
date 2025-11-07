#!/usr/bin/env python3
"""Common types and utilities for palette modules."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

_CACHE_ENV = "SIMPLE_RESUME_PALETTE_CACHE_DIR"


@dataclass(frozen=True)
class Palette:
    """Palette metadata and resolved swatches."""

    name: str
    swatches: tuple[str, ...]
    source: str
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Serialize palette to a JSON-friendly structure."""
        return {
            "name": self.name,
            "swatches": list(self.swatches),
            "source": self.source,
            "metadata": dict(self.metadata),
        }


def get_cache_dir() -> Path:
    """Return palette cache directory."""
    custom = os.environ.get(_CACHE_ENV)
    if custom:
        return Path(custom).expanduser()
    return Path.home() / ".cache" / "simple-resume" / "palettes"
