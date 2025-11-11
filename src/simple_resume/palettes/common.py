#!/usr/bin/env python3
"""Define common types and utilities for palette modules."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

_CACHE_ENV = "SIMPLE_RESUME_PALETTE_CACHE_DIR"


@dataclass(frozen=True)
class Palette:
    """Define palette metadata and resolved swatches."""

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


class PaletteSource(str, Enum):
    """Define supported palette sources for resume configuration."""

    REGISTRY = "registry"
    GENERATOR = "generator"
    REMOTE = "remote"

    @classmethod
    def normalize(
        cls, value: str | PaletteSource | None, *, param_name: str | None = None
    ) -> PaletteSource:
        """Convert arbitrary input into a `PaletteSource` enum member."""
        if value is None:
            return cls.REGISTRY
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise TypeError(
                f"Palette source must be string or PaletteSource, got {type(value)}"
            )

        normalized = value.strip().lower()
        try:
            return cls(normalized)
        except ValueError as exc:
            label = f"{param_name} " if param_name else ""
            supported_sources = ", ".join(
                sorted(member.value for member in cls.__members__.values())
            )
            raise ValueError(
                f"Unsupported {label}source: {value}. Supported sources: "
                f"{supported_sources}"
            ) from exc


def get_cache_dir() -> Path:
    """Return palette cache directory."""
    custom = os.environ.get(_CACHE_ENV)
    if custom:
        return Path(custom).expanduser()
    return Path.home() / ".cache" / "simple-resume" / "palettes"
