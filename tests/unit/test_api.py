"""Tests for the core color utilities."""

from __future__ import annotations

from simple_resume.core import colors
from tests.bdd import Scenario


class TestCoreColors:
    """Test the core color utilities module."""

    def test_colors_module_import(self, story: Scenario) -> None:
        """Test that core.colors can be imported."""
        story.given("the colors module is part of the public API")
        story.when("importing the module")
        assert colors is not None

    def test_colors_all_exports_available(self, story: Scenario) -> None:
        """Test that all exported symbols are available."""
        story.given("__all__ defines expected color helpers")
        story.when("inspecting the module attributes")
        # Verify all exports from __all__ are available
        assert hasattr(colors, "calculate_luminance")
        assert hasattr(colors, "calculate_contrast_ratio")
        assert hasattr(colors, "get_contrasting_text_color")
        assert hasattr(colors, "is_valid_color")
        assert hasattr(colors, "hex_to_rgb")
        assert hasattr(colors, "darken_color")

    def test_colors_functions_work(self, story: Scenario) -> None:
        """Test that imported functions work correctly."""
        story.given("the color helper functions are invoked with sample values")
        story.when("validating luminance and contrast helpers")
        # Test is_valid_color
        assert colors.is_valid_color("#FF0000") is True
        assert colors.is_valid_color("invalid") is False

        # Test get_contrasting_text_color - returns a valid hex color
        result = colors.get_contrasting_text_color("#000000")
        assert colors.is_valid_color(result) is True

        # Test calculate_luminance
        luminance = colors.calculate_luminance("#808080")
        assert isinstance(luminance, float)
        assert 0 <= luminance <= 1
