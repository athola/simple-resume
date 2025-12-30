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
from tests.bdd import Scenario


class TestColorCalculationService:
    def test_sidebar_text_color_respects_contrast(self, story: Scenario) -> None:
        story.given("a config with a dark sidebar color (#000000)")
        story.when("calculating sidebar text color")
        config = {"sidebar_color": "#000000"}
        assert ColorCalculationService.calculate_sidebar_text_color(config) == "#F5F5F5"

    def test_sidebar_text_color_falls_back_to_default(self, story: Scenario) -> None:
        story.given("a config with an invalid sidebar color")
        story.when("calculating sidebar text color")
        config = {"sidebar_color": "not-a-color"}
        assert (
            ColorCalculationService.calculate_sidebar_text_color(config)
            == DEFAULT_COLOR_SCHEME["sidebar_text_color"]
        )

    def test_heading_icon_color_prefers_theme_with_contrast(
        self, story: Scenario
    ) -> None:
        story.given("a config with light sidebar and contrasting theme color")
        story.when("calculating heading icon color")
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
        self, text_color: str, background: str, story: Scenario
    ) -> None:
        story.given(f"a {text_color} text on {background} background")
        story.when("ensuring color contrast")
        assert (
            ColorCalculationService.ensure_color_contrast(
                background,
                text_color,
                contrast_threshold=ICON_CONTRAST_THRESHOLD,
            )
            == text_color
        )

    def test_ensure_color_contrast_generates_fallback(self, story: Scenario) -> None:
        story.given("a nearly white color on white background (low contrast)")
        story.when("ensuring color contrast")
        # Very low contrast user color should be replaced.
        result = ColorCalculationService.ensure_color_contrast("#FFFFFF", "#FFFFFE")
        assert result == "#333333"

    def test_ensure_color_contrast_with_invalid_color(self, story: Scenario) -> None:
        story.given("an invalid color string")
        story.when("ensuring color contrast")
        # Invalid colors should return default fallback.
        result = ColorCalculationService.ensure_color_contrast("not-a-color", "#FFFFFF")
        assert result == "#333333"

    def test_calculate_sidebar_bold_color_with_valid_sidebar(
        self, story: Scenario
    ) -> None:
        """Test calculate_sidebar_bold_color with valid sidebar color."""
        story.given("a config with a light sidebar color")
        story.when("calculating sidebar bold color")
        config = {"sidebar_color": "#F6F6F6"}
        result = ColorCalculationService.calculate_sidebar_bold_color(config)
        assert result.startswith("#")
        # Should be darker than the original
        assert result != "#F6F6F6"

    def test_calculate_sidebar_bold_color_fallback(self, story: Scenario) -> None:
        """Test calculate_sidebar_bold_color without valid sidebar color."""
        story.given("an empty config without sidebar color")
        story.when("calculating sidebar bold color")
        config: dict[str, Any] = {}
        result = ColorCalculationService.calculate_sidebar_bold_color(config)
        assert result == "#000000"

    def test_calculate_heading_icon_color_with_frame_fallback(
        self, story: Scenario
    ) -> None:
        """Test heading icon color falls back to frame_color."""
        story.given("a config with only frame_color defined")
        story.when("calculating heading icon color")
        config = {"frame_color": "#757575"}
        result = ColorCalculationService.calculate_heading_icon_color(config)
        assert result == "#757575"

    def test_calculate_sidebar_icon_color_fallback(self, story: Scenario) -> None:
        """Test sidebar icon color with invalid sidebar color."""
        story.given("a config with an invalid sidebar color")
        story.when("calculating sidebar icon color")
        config = {"sidebar_color": "invalid"}
        result = ColorCalculationService.calculate_sidebar_icon_color(config)
        assert result == "#FFFFFF"


class TestHexToRgb:
    """Tests for hex_to_rgb function."""

    def test_short_hex_color(self, story: Scenario) -> None:
        """Test converting short hex color (3 digits)."""
        story.given("a short hex color string (#FFF)")
        story.when("converting to RGB tuple")
        result = hex_to_rgb("#FFF")
        assert result == (255, 255, 255)

    def test_short_hex_without_hash(self, story: Scenario) -> None:
        """Test converting short hex color without #."""
        story.given("a short hex color without hash prefix (F00)")
        story.when("converting to RGB tuple")
        result = hex_to_rgb("F00")
        assert result == (255, 0, 0)

    def test_invalid_hex_length(self, story: Scenario) -> None:
        """Test invalid hex color length raises ValueError."""
        story.given("an invalid hex color with wrong length (#FFFF)")
        story.when("attempting to convert to RGB")
        with pytest.raises(ValueError, match="Invalid hex color"):
            hex_to_rgb("#FFFF")


class TestDarkenColor:
    """Tests for darken_color function."""

    def test_darken_with_invalid_color(self, story: Scenario) -> None:
        """Test darken_color with invalid hex returns fallback."""
        story.given("an invalid color string")
        story.when("attempting to darken the color")
        result = darken_color("not-a-color", 0.8)
        assert result == "#585858"


class TestCalculateIconContrastColor:
    """Tests for calculate_icon_contrast_color function."""

    def test_with_valid_user_color_and_contrast(self, story: Scenario) -> None:
        """Test calculate_icon_contrast_color with valid user color."""
        story.given("a black user color on white background (high contrast)")
        story.when("calculating icon contrast color")
        result = calculate_icon_contrast_color(
            user_color="#000000",
            background_color="#FFFFFF",
            contrast_threshold=4.5,
        )
        assert result == "#000000"

    def test_with_invalid_user_color(self, story: Scenario) -> None:
        """Test calculate_icon_contrast_color with invalid user color."""
        story.given("an invalid user color string")
        story.when("calculating icon contrast color")
        result = calculate_icon_contrast_color(
            user_color="invalid",
            background_color="#FFFFFF",
        )
        # Should return contrasting color
        assert result.startswith("#")

    def test_with_low_contrast_user_color(self, story: Scenario) -> None:
        """Test calculate_icon_contrast_color with insufficient contrast."""
        story.given("a light gray user color on white background (low contrast)")
        story.when("calculating icon contrast color")
        result = calculate_icon_contrast_color(
            user_color="#EEEEEE",
            background_color="#FFFFFF",
            contrast_threshold=4.5,
        )
        # Should return contrasting color, not the user color
        assert result != "#EEEEEE"
