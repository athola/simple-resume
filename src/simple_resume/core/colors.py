"""Color calculation helpers that belong to the core domain layer.

This module centralizes hex parsing, luminance math, and contrast helpers so
domain services (and utility shims) do not need to re-implement
workarounds to avoid circular imports.
"""

from __future__ import annotations

import re
from typing import Any

from simple_resume.core.constants.colors import (
    BOLD_DARKEN_FACTOR,
    DEFAULT_COLOR_SCHEME,
    HEX_COLOR_FULL_LENGTH,
    HEX_COLOR_SHORT_LENGTH,
    ICON_CONTRAST_THRESHOLD,
    LUMINANCE_DARK,
    LUMINANCE_VERY_DARK,
    LUMINANCE_VERY_LIGHT,
    WCAG_LINEARIZATION_DIVISOR,
    WCAG_LINEARIZATION_EXPONENT,
    WCAG_LINEARIZATION_OFFSET,
    WCAG_LINEARIZATION_THRESHOLD,
)

__all__ = [
    "calculate_contrast_ratio",
    "calculate_icon_contrast_color",
    "calculate_luminance",
    "ColorCalculationService",
    "darken_color",
    "get_contrasting_text_color",
    "hex_to_rgb",
    "is_valid_color",
]


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to an RGB tuple."""
    processed = hex_color.lstrip("#")
    if len(processed) == HEX_COLOR_SHORT_LENGTH:
        processed = "".join(char * 2 for char in processed)
    if len(processed) != HEX_COLOR_FULL_LENGTH:
        raise ValueError(f"Invalid hex color: {hex_color}")
    try:
        r = int(processed[0:2], 16)
        g = int(processed[2:4], 16)
        b = int(processed[4:6], 16)
        return r, g, b
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"Invalid hex color: {hex_color}") from exc


def darken_color(hex_color: str, factor: float) -> str:
    """Return a darker variant of the provided hex color."""
    try:
        rgb = hex_to_rgb(hex_color)
    except ValueError:
        return "#585858"

    darkened = tuple(max(0, min(255, round(component * factor))) for component in rgb)
    return "#{:02X}{:02X}{:02X}".format(*darkened)


def _calculate_luminance_from_rgb(rgb: tuple[int, int, int]) -> float:
    """Calculate relative luminance from an RGB tuple using WCAG 2.1 formula.

    Args:
        rgb: An RGB color tuple (e.g., (255, 255, 255)).

    Returns:
        The relative luminance (0.0 to 1.0).

    """
    r, g, b = rgb

    def _linearize(component: int) -> float:
        value = component / 255.0
        return (
            value / WCAG_LINEARIZATION_DIVISOR
            if value <= WCAG_LINEARIZATION_THRESHOLD
            else ((value + WCAG_LINEARIZATION_OFFSET) / (1 + WCAG_LINEARIZATION_OFFSET))
            ** WCAG_LINEARIZATION_EXPONENT
        )

    r_linear = _linearize(r)
    g_linear = _linearize(g)
    b_linear = _linearize(b)

    return 0.2126 * r_linear + 0.7152 * g_linear + 0.0722 * b_linear


def calculate_luminance(hex_color: str) -> float:
    """Return the relative luminance for ``hex_color``."""
    rgb = hex_to_rgb(hex_color)
    return _calculate_luminance_from_rgb(rgb)


def calculate_contrast_ratio(color1: str, color2: str) -> float:
    """Return the WCAG contrast ratio between two hex colors."""
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    lum1 = _calculate_luminance_from_rgb(rgb1)
    lum2 = _calculate_luminance_from_rgb(rgb2)
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)


def get_contrasting_text_color(background_color: str) -> str:
    """Return a readable text color for the provided background."""
    try:
        luminance = calculate_luminance(background_color)
        if luminance <= LUMINANCE_VERY_DARK:
            return "#F5F5F5"
        if luminance <= LUMINANCE_DARK:
            return "#FFFFFF"
        if luminance >= LUMINANCE_VERY_LIGHT:
            return "#333333"
        return "#000000"
    except (ValueError, TypeError):  # pragma: no cover - defensive
        return "#000000"


def calculate_icon_contrast_color(
    user_color: str | None,
    background_color: str,
    *,
    contrast_threshold: float = ICON_CONTRAST_THRESHOLD,
) -> str:
    """Return an icon color that respects the WCAG AA contrast threshold."""
    if user_color and is_valid_color(user_color):
        ratio = calculate_contrast_ratio(user_color, background_color)
        if ratio >= contrast_threshold:
            return user_color
    return get_contrasting_text_color(background_color)


def is_valid_color(color: str) -> bool:
    """Check if a color string is a valid hex color code."""
    if not color:
        return False
    return bool(re.match(r"^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$", color))


class ColorCalculationService:
    """Service for calculating various color values based on configuration."""

    @staticmethod
    def calculate_sidebar_text_color(config: dict[str, Any]) -> str:
        """Calculate sidebar text color based on sidebar background."""
        sidebar_color = config.get("sidebar_color")
        if sidebar_color and is_valid_color(sidebar_color):
            return get_contrasting_text_color(sidebar_color)
        return DEFAULT_COLOR_SCHEME.get("sidebar_text_color", "#000000")

    @staticmethod
    def calculate_sidebar_bold_color(config: dict[str, Any]) -> str:
        """Calculate sidebar bold color based on sidebar background."""
        sidebar_color = config.get("sidebar_color")
        if sidebar_color and is_valid_color(sidebar_color):
            # Make the bold color slightly darker than the background
            return darken_color(sidebar_color, BOLD_DARKEN_FACTOR)
        return "#000000"  # Default black

    @staticmethod
    def calculate_heading_icon_color(config: dict[str, Any]) -> str:
        """Calculate heading icon color based on configuration."""
        user_icon_color = config.get("heading_icon_color")
        frame_color = config.get("frame_color", "#000000")

        if isinstance(user_icon_color, str) and is_valid_color(user_icon_color):
            return user_icon_color
        theme_color = config.get("theme_color")
        if isinstance(theme_color, str) and is_valid_color(theme_color):
            return theme_color
        return str(frame_color)

    @staticmethod
    def calculate_sidebar_icon_color(config: dict[str, Any]) -> str:
        """Calculate sidebar icon color based on configuration."""
        sidebar_color = config.get("sidebar_color")
        if sidebar_color and is_valid_color(sidebar_color):
            return get_contrasting_text_color(sidebar_color)
        return "#FFFFFF"  # Default white icon

    @staticmethod
    def ensure_color_contrast(
        background: str,
        text_color: str,
        *,
        contrast_threshold: float = 3.0,
    ) -> str:
        """Ensure text color has sufficient contrast against background.

        Args:
            background: Background color in hex format
            text_color: Text color in hex format
            contrast_threshold: Minimum contrast ratio required

        Returns:
            Original text color if contrast is sufficient, otherwise a fallback color

        """
        if not is_valid_color(background) or not is_valid_color(text_color):
            return "#333333"  # Default fallback color

        contrast = calculate_contrast_ratio(text_color, background)
        if contrast >= contrast_threshold:
            return text_color

        # Return fallback color with better contrast
        return get_contrasting_text_color(background)
