#!/usr/bin/env python3
"""Provide a palette registry that aggregates multiple providers."""

from __future__ import annotations

import json
from functools import lru_cache

from .common import Palette, get_cache_dir
from .sources import (
    ensure_bundled_palettes_loaded,
    load_default_palettes,
    load_palettable_palette,
)


class PaletteRegistry:
    """Define an in-memory registry of named palettes."""

    def __init__(self) -> None:
        """Initialize an empty palette registry."""
        self._palettes: dict[str, Palette] = {}

    def register(self, palette: Palette) -> None:
        """Register or overwrite a palette."""
        key = palette.name.lower()
        self._palettes[key] = palette

    def get(self, name: str) -> Palette:
        """Return a palette by name."""
        key = name.lower()
        try:
            return self._palettes[key]
        except KeyError as exc:
            raise KeyError(f"Palette not found: {name}") from exc

    def list(self) -> list[Palette]:
        """Return all registered palettes sorted by name."""
        return [self._palettes[key] for key in sorted(self._palettes)]

    def to_json(self) -> str:
        """Serialize the registry to JSON."""
        return json.dumps([palette.to_dict() for palette in self.list()], indent=2)


_CACHE_ENV = "SIMPLE_RESUME_PALETTE_CACHE"


def _load_palettable(registry: PaletteRegistry) -> None:
    """Populate the registry with palettable palettes."""
    for record in ensure_bundled_palettes_loaded():
        palette = load_palettable_palette(record)
        if palette is not None:
            registry.register(palette)


@lru_cache(maxsize=1)
def get_palette_registry() -> PaletteRegistry:
    """Return a singleton registry populated with known sources."""
    registry = PaletteRegistry()
    for palette in load_default_palettes():
        registry.register(palette)
    _load_palettable(registry)
    return registry


def reset_palette_registry() -> None:
    """Clear the cached global registry (primarily for tests)."""
    get_palette_registry.cache_clear()


__all__ = [
    "Palette",
    "PaletteRegistry",
    "get_palette_registry",
    "reset_palette_registry",
    "get_cache_dir",
]
