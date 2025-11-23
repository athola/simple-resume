"""Public color utilities for simple-resume.

This module provides stable color manipulation functions for use in resume
styling and theming. All functions follow WCAG accessibility guidelines.

Stability: Stable
    All functions in this module are covered by the semantic versioning
    stability contract. Breaking changes require a major version bump.

Example:
    >>> from simple_resume.api import colors
    >>> colors.is_valid_color("#FF0000")
    True
    >>> colors.calculate_luminance("#808080")
    0.21586050011389926
    >>> colors.calculate_text_color("#000000")
    '#FFFFFF'

.. versionadded:: 0.1.0

"""

from simple_resume.core.colors import (
    calculate_contrast_ratio,
    calculate_luminance,
    darken_color,
    get_contrasting_text_color,
    hex_to_rgb,
    is_valid_color,
)

# Re-export with simplified names where appropriate
# calculate_text_color is an alias for get_contrasting_text_color
calculate_text_color = get_contrasting_text_color

__all__ = [
    # Core functions
    "calculate_luminance",
    "calculate_contrast_ratio",
    "calculate_text_color",
    "is_valid_color",
    "hex_to_rgb",
    "darken_color",
    # Canonical name (for advanced users)
    "get_contrasting_text_color",
]
