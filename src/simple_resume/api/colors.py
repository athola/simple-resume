"""Provide a color utility API mirroring ``pandas.api.colors``.

This module re-exports supported color helpers backed by internal
`:mod:simple_resume.core.colors` implementations. This provides callers
a stable import path that follows semantic-version guarantees.
"""

from __future__ import annotations

from ..core.colors import calculate_luminance, is_valid_color

_TEXT_LUMINANCE_THRESHOLD = 0.5

__all__ = ["calculate_luminance", "calculate_text_color", "is_valid_color"]


def calculate_text_color(background_color: str) -> str:
    """Return black for light backgrounds and white for dark ones."""
    try:
        luminance = calculate_luminance(background_color)
    except ValueError:
        return "#000000"
    return "#FFFFFF" if luminance <= _TEXT_LUMINANCE_THRESHOLD else "#000000"
