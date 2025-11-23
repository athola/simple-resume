#!/usr/bin/env python3
"""Palette discovery utilities and registries (pure core)."""

from __future__ import annotations

from .exceptions import (
    PaletteError,
    PaletteGenerationError,
    PaletteLookupError,
    PaletteRemoteDisabled,
    PaletteRemoteError,
)
from .fetch_types import PaletteFetchRequest, PaletteResolution
from .generators import generate_hcl_palette
from .registry import Palette, PaletteRegistry, build_palette_registry
from .resolution import resolve_palette_config

__all__ = [
    "Palette",
    "PaletteRegistry",
    "build_palette_registry",
    "generate_hcl_palette",
    "PaletteError",
    "PaletteLookupError",
    "PaletteGenerationError",
    "PaletteRemoteDisabled",
    "PaletteRemoteError",
    "PaletteFetchRequest",
    "PaletteResolution",
    "resolve_palette_config",
]
