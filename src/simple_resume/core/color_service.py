"""Color calculation service to follow Law of Demeter principles.

This module provides a service layer for color calculations, encapsulating
color logic and preventing Law of Demeter violations through configuration
objects.
"""

from __future__ import annotations

from typing import Any

from simple_resume.constants import (
    DEFAULT_COLOR_SCHEME,
    ICON_CONTRAST_THRESHOLD,
    LUMINANCE_DARK,
    SIDEBAR_BOLD_DARKEN_FACTOR,
)

from .colors import (
    calculate_contrast_ratio,
    calculate_luminance,
    darken_color,
    get_contrasting_text_color,
    is_valid_color,
)


class ColorCalculationService:
    """Service for color calculations following Law of Demeter principles."""

    @staticmethod
    def calculate_sidebar_text_color(config: dict[str, Any]) -> str:
        """Calculate sidebar text color based on background color.

        Args:
            config: Configuration dictionary containing sidebar_color

        Returns:
            Calculated text color with proper contrast

        """
        sidebar_color = config.get("sidebar_color")
        if isinstance(sidebar_color, str) and is_valid_color(sidebar_color):
            return get_contrasting_text_color(sidebar_color)
        return DEFAULT_COLOR_SCHEME["sidebar_text_color"]

    @staticmethod
    def calculate_sidebar_bold_color(config: dict[str, Any]) -> str:
        """Calculate sidebar bold color for optimal contrast.

        Args:
            config: Configuration dictionary containing sidebar_color

        Returns:
            Calculated bold color with proper contrast against sidebar background

        """
        sidebar_color = config.get("sidebar_color")
        if isinstance(sidebar_color, str) and is_valid_color(sidebar_color):
            # For bold text, we want slightly darker than regular text for contrast
            # Use a darker variant by reducing luminance
            try:
                luminance = calculate_luminance(sidebar_color)

                # If sidebar is light, use darker bold text
                if luminance > LUMINANCE_DARK:
                    return darken_color(
                        get_contrasting_text_color(sidebar_color),
                        SIDEBAR_BOLD_DARKEN_FACTOR,
                    )
                # If sidebar is dark, use slightly lighter bold text
                else:
                    return get_contrasting_text_color(sidebar_color)
            except (ValueError, TypeError):
                # Fall back to regular contrasting text color
                return get_contrasting_text_color(sidebar_color)

        return DEFAULT_COLOR_SCHEME.get(
            "bold_color",
            DEFAULT_COLOR_SCHEME["sidebar_text_color"],
        )

    @staticmethod
    def calculate_heading_icon_color(config: dict[str, Any]) -> str:
        """Calculate heading icon color with proper contrast.

        Args:
            config: Configuration dictionary containing theme_color and sidebar_color

        Returns:
            Calculated icon color with WCAG contrast compliance

        """
        theme_color = config.get("theme_color", DEFAULT_COLOR_SCHEME["theme_color"])
        sidebar_color = config.get(
            "sidebar_color",
            DEFAULT_COLOR_SCHEME["sidebar_color"],
        )

        # If theme color has good contrast with sidebar, use it
        if isinstance(theme_color, str) and is_valid_color(theme_color):
            try:
                contrast_ratio = calculate_contrast_ratio(theme_color, sidebar_color)
                if contrast_ratio >= ICON_CONTRAST_THRESHOLD:
                    return theme_color
            except (ValueError, TypeError):
                pass  # Fall back to calculated color

        # Otherwise, calculate contrasting color
        return get_contrasting_text_color(sidebar_color)

    @staticmethod
    def calculate_sidebar_icon_color(config: dict[str, Any]) -> str:
        """Calculate sidebar icon color with proper contrast.

        Args:
            config: Configuration dictionary containing sidebar_color

        Returns:
            Calculated icon color with WCAG contrast compliance

        """
        return ColorCalculationService.calculate_sidebar_text_color(config)

    @staticmethod
    def ensure_color_contrast(
        background_color: str,
        text_color: str | None = None,
        *,
        contrast_threshold: float = ICON_CONTRAST_THRESHOLD,
    ) -> str:
        """Ensure text color has sufficient contrast with background.

        Args:
            background_color: Background hex color
            text_color: Optional text color to validate/adjust
            contrast_threshold: Minimum contrast ratio (default: WCAG AA)

        Returns:
            Text color with sufficient contrast

        """
        if text_color and is_valid_color(text_color):
            try:
                ratio = calculate_contrast_ratio(text_color, background_color)
                if ratio >= contrast_threshold:
                    return text_color
            except (ValueError, TypeError):
                pass

        return get_contrasting_text_color(background_color)
