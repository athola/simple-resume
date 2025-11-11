"""Provide color helpers shared between shell and core modules."""

from __future__ import annotations

import re

HEX_COLOR_SHORT_LENGTH = 3
HEX_COLOR_FULL_LENGTH = 6

LINEARIZATION_THRESHOLD = 0.03928
LINEARIZATION_DIVISOR = 12.92
LINEARIZATION_EXPONENT = 2.4
LINEARIZATION_OFFSET = 0.055

VERY_DARK_THRESHOLD = 0.15
DARK_THRESHOLD = 0.5
VERY_LIGHT_THRESHOLD = 0.8
ICON_CONTRAST_THRESHOLD = 3.0


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    processed = hex_color.lstrip("#")
    if len(processed) == HEX_COLOR_SHORT_LENGTH:
        processed = "".join([char * 2 for char in processed])
    if len(processed) != HEX_COLOR_FULL_LENGTH:
        raise ValueError(f"Invalid hex color: {hex_color}")
    try:
        r = int(processed[0:2], 16)
        g = int(processed[2:4], 16)
        b = int(processed[4:6], 16)
        return r, g, b
    except ValueError as exc:
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
    r, g, b = rgb

    def _linearize(component: int) -> float:
        value = component / 255.0
        return (
            value / LINEARIZATION_DIVISOR
            if value <= LINEARIZATION_THRESHOLD
            else ((value + LINEARIZATION_OFFSET) / (1 + LINEARIZATION_OFFSET))
            ** LINEARIZATION_EXPONENT
        )

    r_linear = _linearize(r)
    g_linear = _linearize(g)
    b_linear = _linearize(b)

    # Calculate relative luminance using sRGB BT.709 coefficients
    # These coefficients represent human eye sensitivity to different color wavelengths:
    # - 0.2126: Red channel contribution (humans are least sensitive to red)
    # - 0.7152: Green channel contribution (humans are most sensitive to green)
    # - 0.0722: Blue channel contribution (humans are least sensitive to blue)
    # Formula from WCAG 2.0 and ITU-R BT.709 standards for accessibility calculations
    return 0.2126 * r_linear + 0.7152 * g_linear + 0.0722 * b_linear


def calculate_luminance(hex_color: str) -> float:
    """Return the relative luminance for ``hex_color``."""
    rgb = hex_to_rgb(hex_color)
    return _calculate_luminance_from_rgb(rgb)


def calculate_contrast_ratio(color1: str, color2: str) -> float:
    """Return WCAG contrast ratio between two hex colors."""
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    lum1 = _calculate_luminance_from_rgb(rgb1)
    lum2 = _calculate_luminance_from_rgb(rgb2)
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)


def get_contrasting_text_color(background_color: str) -> str:
    """Return a readable text color for the given background."""
    try:
        luminance = calculate_luminance(background_color)
        if luminance <= VERY_DARK_THRESHOLD:
            return "#F5F5F5"
        if luminance <= DARK_THRESHOLD:
            return "#FFFFFF"
        if luminance >= VERY_LIGHT_THRESHOLD:
            return "#333333"
        return "#000000"
    except (ValueError, TypeError):
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


__all__ = [
    "calculate_contrast_ratio",
    "calculate_icon_contrast_color",
    "calculate_luminance",
    "darken_color",
    "get_contrasting_text_color",
    "hex_to_rgb",
    "is_valid_color",
]
