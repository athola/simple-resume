#!/usr/bin/env python3
"""Provide a palette registry that aggregates multiple providers."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Callable

from .common import Palette, get_cache_dir
from .sources import (
    discover_palettable,
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
    for record in discover_palettable():
        palette = load_palettable_palette(record)
        if palette is not None:
            registry.register(palette)


@lru_cache(maxsize=1)
def get_palette_registry() -> PaletteRegistry:
    """Return a singleton registry populated with known sources."""
    # Import from shell to get actual I/O implementation
    from simple_resume.shell.palettes.loader import (  # noqa: PLC0415
        load_default_palettes as shell_load,
    )

    registry = PaletteRegistry()
    for palette in shell_load():
        registry.register(palette)
    _load_palettable(registry)
    return registry


def build_palette_registry(
    *,
    default_loader: Callable[[], list[Palette]] | None = None,
    palettable_loader: Callable[[], list[Palette]] | None = None,
) -> PaletteRegistry:
    """Build a palette registry with custom loader functions.

    Args:
        default_loader: Function to load default palettes
        palettable_loader: Function to load palettable palettes

    Returns:
        PaletteRegistry populated with palettes from the specified loaders

    """
    registry = PaletteRegistry()

    if default_loader:
        for palette in default_loader():
            registry.register(palette)

    if palettable_loader:
        for palette in palettable_loader():
            registry.register(palette)

    return registry


def reset_palette_registry() -> None:
    """Clear the cached global registry (primarily for tests)."""
    get_palette_registry.cache_clear()


__all__ = [
    "Palette",
    "PaletteRegistry",
    "get_palette_registry",
    "build_palette_registry",
    "reset_palette_registry",
    "get_cache_dir",
]
