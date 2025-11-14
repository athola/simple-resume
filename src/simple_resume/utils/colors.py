"""Backwards-compatible shim for color helpers.

Color math now lives in :mod:`simple_resume.core.colors`. This module re-exports
those helpers so existing imports keep working while callers migrate to the
core namespace. Importing from this module emits a ``DeprecationWarning`` to
make the boundary move explicit.
"""

from __future__ import annotations

import warnings

from simple_resume.core.colors import (
    calculate_contrast_ratio,
    calculate_icon_contrast_color,
    calculate_luminance,
    darken_color,
    get_contrasting_text_color,
    hex_to_rgb,
    is_valid_color,
)

warnings.warn(
    "simple_resume.utils.colors is deprecated; import from "
    "simple_resume.core.colors instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "calculate_contrast_ratio",
    "calculate_icon_contrast_color",
    "calculate_luminance",
    "darken_color",
    "get_contrasting_text_color",
    "hex_to_rgb",
    "is_valid_color",
]
