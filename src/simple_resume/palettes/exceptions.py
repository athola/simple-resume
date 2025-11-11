#!/usr/bin/env python3
"""Exception types used by the palette subsystem."""

from __future__ import annotations


class PaletteError(RuntimeError):
    """Base class for palette-related failures."""


class PaletteLookupError(PaletteError):
    """Raised when a named palette cannot be located."""


class PaletteGenerationError(PaletteError):
    """Raised when a generator cannot produce the requested swatches."""


class PaletteRemoteDisabled(PaletteError):
    """Raised when remote palette access is disabled by configuration."""


class PaletteRemoteError(PaletteError):
    """Raised when a remote palette provider returns an error."""


__all__ = [
    "PaletteError",
    "PaletteGenerationError",
    "PaletteLookupError",
    "PaletteRemoteDisabled",
    "PaletteRemoteError",
]
