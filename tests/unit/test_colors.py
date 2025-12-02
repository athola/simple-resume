"""Unit tests for the color calculation service and helpers."""

from __future__ import annotations

from typing import Any

import pytest

from simple_resume.core.colors import (
    ColorCalculationService,
    calculate_icon_contrast_color,
    darken_color,
    hex_to_rgb,
)
from simple_resume.core.constants.colors import (
    DEFAULT_COLOR_SCHEME,
    ICON_CONTRAST_THRESHOLD,
)


class TestColorCalculationService:
    def test_sidebar_text_color_respects_contrast(self) -> None:
        config = {"sidebar_color": "#000000"}
        assert ColorCalculationService.calculate_sidebar_text_color(config) == "#F5F5F5"

    def test_sidebar_text_color_falls_back_to_default(self) -> None:
        config = {"sidebar_color": "not-a-color"}
        assert (
            ColorCalculationService.calculate_sidebar_text_color(config)
            == DEFAULT_COLOR_SCHEME["sidebar_text_color"]
        )

    def test_heading_icon_color_prefers_theme_with_contrast(self) -> None:
        config = {
            "sidebar_color": "#F6F6F6",
            "theme_color": "#0000FF",
        }
        assert (
            ColorCalculationService.calculate_heading_icon_color(config)
            == config["theme_color"]
        )

    @pytest.mark.parametrize(
        "text_color,background",
        [
            ("#000000", "#FFFFFF"),
            ("#FFFFFF", "#000000"),
        ],
    )
    def test_ensure_color_contrast_preserves_valid_colors(
        self, text_color: str, background: str
    ) -> None:
        assert (
            ColorCalculationService.ensure_color_contrast(
                background,
                text_color,
                contrast_threshold=ICON_CONTRAST_THRESHOLD,
            )
            == text_color
        )

    def test_ensure_color_contrast_generates_fallback(self) -> None:
        # Very low contrast user color should be replaced.
        result = ColorCalculationService.ensure_color_contrast("#FFFFFF", "#FFFFFE")
        assert result == "#333333"

    def test_ensure_color_contrast_with_invalid_color(self) -> None:
        # Invalid colors should return default fallback.
        result = ColorCalculationService.ensure_color_contrast("not-a-color", "#FFFFFF")
        assert result == "#333333"

    def test_calculate_sidebar_bold_color_with_valid_sidebar(self) -> None:
        """Test calculate_sidebar_bold_color with valid sidebar color."""
        config = {"sidebar_color": "#F6F6F6"}
        result = ColorCalculationService.calculate_sidebar_bold_color(config)
        assert result.startswith("#")
        # Should be darker than the original
        assert result != "#F6F6F6"

    def test_calculate_sidebar_bold_color_fallback(self) -> None:
        """Test calculate_sidebar_bold_color without valid sidebar color."""
        config: dict[str, Any] = {}
        result = ColorCalculationService.calculate_sidebar_bold_color(config)
        assert result == "#000000"

    def test_calculate_heading_icon_color_with_frame_fallback(self) -> None:
        """Test heading icon color falls back to frame_color."""
        config = {"frame_color": "#757575"}
        result = ColorCalculationService.calculate_heading_icon_color(config)
        assert result == "#757575"

    def test_calculate_sidebar_icon_color_fallback(self) -> None:
        """Test sidebar icon color with invalid sidebar color."""
        config = {"sidebar_color": "invalid"}
        result = ColorCalculationService.calculate_sidebar_icon_color(config)
        assert result == "#FFFFFF"


class TestHexToRgb:
    """Tests for hex_to_rgb function."""

    def test_short_hex_color(self) -> None:
        """Test converting short hex color (3 digits)."""
        result = hex_to_rgb("#FFF")
        assert result == (255, 255, 255)

    def test_short_hex_without_hash(self) -> None:
        """Test converting short hex color without #."""
        result = hex_to_rgb("F00")
        assert result == (255, 0, 0)

    def test_invalid_hex_length(self) -> None:
        """Test invalid hex color length raises ValueError."""
        with pytest.raises(ValueError, match="Invalid hex color"):
            hex_to_rgb("#FFFF")


class TestDarkenColor:
    """Tests for darken_color function."""

    def test_darken_with_invalid_color(self) -> None:
        """Test darken_color with invalid hex returns fallback."""
        result = darken_color("not-a-color", 0.8)
        assert result == "#585858"


class TestCalculateIconContrastColor:
    """Tests for calculate_icon_contrast_color function."""

    def test_with_valid_user_color_and_contrast(self) -> None:
        """Test calculate_icon_contrast_color with valid user color."""
        result = calculate_icon_contrast_color(
            user_color="#000000",
            background_color="#FFFFFF",
            contrast_threshold=4.5,
        )
        assert result == "#000000"

    def test_with_invalid_user_color(self) -> None:
        """Test calculate_icon_contrast_color with invalid user color."""
        result = calculate_icon_contrast_color(
            user_color="invalid",
            background_color="#FFFFFF",
        )
        # Should return contrasting color
        assert result.startswith("#")

    def test_with_low_contrast_user_color(self) -> None:
        """Test calculate_icon_contrast_color with insufficient contrast."""
        result = calculate_icon_contrast_color(
            user_color="#EEEEEE",
            background_color="#FFFFFF",
            contrast_threshold=4.5,
        )
        # Should return contrasting color, not the user color
        assert result != "#EEEEEE"
