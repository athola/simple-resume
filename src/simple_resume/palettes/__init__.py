#!/usr/bin/env python3
"""Palette discovery utilities and registries."""

from __future__ import annotations

from .exceptions import (
    PaletteError,
    PaletteGenerationError,
    PaletteLookupError,
    PaletteRemoteDisabled,
    PaletteRemoteError,
)
from .generators import generate_hcl_palette
from .registry import Palette, PaletteRegistry, get_palette_registry
from .sources import (
    ColourLoversClient,
    ensure_bundled_palettes_loaded,
    load_default_palettes,
)

__all__ = [
    "Palette",
    "PaletteRegistry",
    "generate_hcl_palette",
    "get_palette_registry",
    "load_default_palettes",
    "ensure_bundled_palettes_loaded",
    "ColourLoversClient",
    "PaletteError",
    "PaletteLookupError",
    "PaletteGenerationError",
    "PaletteRemoteDisabled",
    "PaletteRemoteError",
]
