#!/usr/bin/env python3
"""Exception types used by the palette subsystem.

.. deprecated::
   This module is deprecated. Import palette exceptions from
   ``simple_resume.core.exceptions`` instead. The palette exceptions
   are now part of the unified ``SimpleResumeError`` hierarchy per ADR-006.

   Migration:
       # Old (deprecated):
       from simple_resume.core.palettes.exceptions import PaletteError

       # New:
       from simple_resume.core.exceptions import PaletteError
"""

from __future__ import annotations

import warnings

# Import all palette exceptions from the main exceptions module
# This maintains backward compatibility while using the unified hierarchy
from simple_resume.core.exceptions import (
    PaletteError,
    PaletteGenerationError,
    PaletteLookupError,
    PaletteRemoteDisabled,
    PaletteRemoteError,
)

__all__ = [
    "PaletteError",
    "PaletteGenerationError",
    "PaletteLookupError",
    "PaletteRemoteDisabled",
    "PaletteRemoteError",
]

# Issue deprecation warning when module is imported
warnings.warn(
    "Importing from 'simple_resume.core.palettes.exceptions' is deprecated. "
    "Import from 'simple_resume.core.exceptions' instead. "
    "This module will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)
