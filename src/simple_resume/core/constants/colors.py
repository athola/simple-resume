"""Color-related constants for simple-resume."""

from __future__ import annotations

from typing import Final

DEFAULT_COLOR_SCHEME: Final[dict[str, str]] = {
    "theme_color": "#0395DE",
    "sidebar_color": "#F6F6F6",
    "sidebar_text_color": "#000000",
    "bar_background_color": "#DFDFDF",
    "date2_color": "#616161",
    "frame_color": "#757575",
    "heading_icon_color": "#0395DE",
    "bold_color": "#585858",
}

# WCAG 2.1 relative luminance formula constants
# Reference: https://www.w3.org/TR/WCAG21/#dfn-relative-luminance
# These constants implement the standard relative luminance calculation
# for determining color contrast and accessibility compliance.
WCAG_LINEARIZATION_THRESHOLD: Final[float] = 0.03928
WCAG_LINEARIZATION_DIVISOR: Final[float] = 12.92
WCAG_LINEARIZATION_EXPONENT: Final[float] = 2.4
WCAG_LINEARIZATION_OFFSET: Final[float] = 0.055

# Color manipulation constants
BOLD_DARKEN_FACTOR: Final[float] = 0.75
SIDEBAR_BOLD_DARKEN_FACTOR: Final[float] = 0.8

# Luminance thresholds for color contrast calculations
LUMINANCE_VERY_DARK: Final[float] = 0.15
LUMINANCE_DARK: Final[float] = 0.5
LUMINANCE_VERY_LIGHT: Final[float] = 0.8
ICON_CONTRAST_THRESHOLD: Final[float] = 3.0

# Color Format Constants
HEX_COLOR_SHORT_LENGTH: Final[int] = 3
HEX_COLOR_FULL_LENGTH: Final[int] = 6

# UI Element Constants
DEFAULT_BOLD_COLOR: Final[str] = "#585858"

# Define color field ordering for palette application
COLOR_FIELD_ORDER: Final[tuple[str, ...]] = (
    "accent_color",
    "sidebar_color",
    "text_color",
    "emphasis_color",
    "link_color",
)

# Direct color keys that can be specified in configuration
DIRECT_COLOR_KEYS: Final[set[str]] = {
    "accent_color",
    "sidebar_color",
    "text_color",
    "emphasis_color",
    "link_color",
    "sidebar_text_color",
}

# Resume configuration color ordering (used by palette normalization)
CONFIG_COLOR_FIELDS: Final[tuple[str, ...]] = (
    "theme_color",
    "sidebar_color",
    "sidebar_text_color",
    "bar_background_color",
    "date2_color",
    "frame_color",
    "heading_icon_color",
)

CONFIG_DIRECT_COLOR_KEYS: Final[tuple[str, ...]] = CONFIG_COLOR_FIELDS + (
    "bold_color",
    "sidebar_bold_color",
)

__all__ = [
    "DEFAULT_COLOR_SCHEME",
    "WCAG_LINEARIZATION_THRESHOLD",
    "WCAG_LINEARIZATION_DIVISOR",
    "WCAG_LINEARIZATION_EXPONENT",
    "WCAG_LINEARIZATION_OFFSET",
    "BOLD_DARKEN_FACTOR",
    "SIDEBAR_BOLD_DARKEN_FACTOR",
    "LUMINANCE_VERY_DARK",
    "LUMINANCE_DARK",
    "LUMINANCE_VERY_LIGHT",
    "ICON_CONTRAST_THRESHOLD",
    "HEX_COLOR_SHORT_LENGTH",
    "HEX_COLOR_FULL_LENGTH",
    "DEFAULT_BOLD_COLOR",
    "COLOR_FIELD_ORDER",
    "DIRECT_COLOR_KEYS",
    "CONFIG_COLOR_FIELDS",
    "CONFIG_DIRECT_COLOR_KEYS",
]
