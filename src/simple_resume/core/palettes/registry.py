#!/usr/bin/env python3
"""Provide a palette registry that aggregates multiple providers."""

from __future__ import annotations

import json
from typing import Callable

from simple_resume.core.palettes.common import Palette


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


__all__ = [
    "Palette",
    "PaletteRegistry",
    "build_palette_registry",
]
