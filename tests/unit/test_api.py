"""Tests for the public API namespace module."""

from __future__ import annotations

from simple_resume.api import colors


class TestApiNamespace:
    """Test the public API namespace module."""

    def test_api_colors_import(self) -> None:
        """Test that api.colors can be imported."""
        assert colors is not None

    def test_api_colors_all_exports_available(self) -> None:
        """Test that all exported symbols are available."""
        # Verify all exports from __all__ are available
        assert hasattr(colors, "calculate_luminance")
        assert hasattr(colors, "calculate_contrast_ratio")
        assert hasattr(colors, "calculate_text_color")
        assert hasattr(colors, "is_valid_color")
        assert hasattr(colors, "hex_to_rgb")
        assert hasattr(colors, "darken_color")
        assert hasattr(colors, "get_contrasting_text_color")

    def test_api_colors_calculate_text_color_is_alias(self) -> None:
        """Test that calculate_text_color is alias for get_contrasting_text_color."""
        assert colors.calculate_text_color is colors.get_contrasting_text_color

    def test_api_colors_functions_work(self) -> None:
        """Test that imported functions work correctly."""
        # Test is_valid_color
        assert colors.is_valid_color("#FF0000") is True
        assert colors.is_valid_color("invalid") is False

        # Test calculate_text_color - returns a valid hex color
        result = colors.calculate_text_color("#000000")
        assert colors.is_valid_color(result) is True

        # Test calculate_luminance
        luminance = colors.calculate_luminance("#808080")
        assert isinstance(luminance, float)
        assert 0 <= luminance <= 1
