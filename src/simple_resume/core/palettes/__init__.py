#!/usr/bin/env python3
"""Palette discovery utilities and registries (pure core)."""

from __future__ import annotations

from simple_resume.core.palettes.exceptions import (
    PaletteError,
    PaletteGenerationError,
    PaletteLookupError,
    PaletteRemoteDisabled,
    PaletteRemoteError,
)
from simple_resume.core.palettes.fetch_types import (
    PaletteFetchRequest,
    PaletteResolution,
)
from simple_resume.core.palettes.generators import generate_hcl_palette
from simple_resume.core.palettes.registry import (
    Palette,
    PaletteRegistry,
    build_palette_registry,
)
from simple_resume.core.palettes.resolution import resolve_palette_config

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
