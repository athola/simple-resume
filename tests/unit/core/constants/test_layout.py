"""Tests for core/constants/layout.py - layout constants."""

from __future__ import annotations

from simple_resume.core.config import apply_config_defaults
from simple_resume.core.constants import layout


class TestLayoutConstants:
    """Test layout constant values."""

    def test_default_page_dimensions(self) -> None:
        """Test default page dimension constants (A4: 210x297mm)."""
        assert layout.DEFAULT_PAGE_WIDTH_MM == 210
        assert layout.DEFAULT_PAGE_HEIGHT_MM == 297

    def test_default_sidebar_width(self) -> None:
        """Test default sidebar width constant (A4 standard layout: 65mm)."""
        assert layout.DEFAULT_SIDEBAR_WIDTH_MM == 65

    def test_default_padding_values(self) -> None:
        """Test default padding constants."""
        assert layout.DEFAULT_PADDING == 12
        assert layout.DEFAULT_SIDEBAR_PADDING_ADJUSTMENT == -2
        assert layout.DEFAULT_SIDEBAR_PADDING == 12

    def test_frame_padding(self) -> None:
        """Test frame padding constant."""
        assert layout.DEFAULT_FRAME_PADDING == 10

    def test_cover_letter_padding(self) -> None:
        """Test cover letter padding constants."""
        assert layout.DEFAULT_COVER_PADDING_TOP == 10
        assert layout.DEFAULT_COVER_PADDING_BOTTOM == 20
        assert layout.DEFAULT_COVER_PADDING_HORIZONTAL == 25

    def test_validation_constraints_page_dimensions(self) -> None:
        """Test page dimension validation constraints."""
        assert layout.MIN_PAGE_WIDTH_MM == 100
        assert layout.MAX_PAGE_WIDTH_MM == 300
        assert layout.MIN_PAGE_HEIGHT_MM == 150
        assert layout.MAX_PAGE_HEIGHT_MM == 400

    def test_validation_constraints_sidebar(self) -> None:
        """Test sidebar validation constraints."""
        assert layout.MIN_SIDEBAR_WIDTH_MM == 30
        assert layout.MAX_SIDEBAR_WIDTH_MM == 100

    def test_validation_constraints_padding(self) -> None:
        """Test padding validation constraints."""
        assert layout.MIN_PADDING == 0
        assert layout.MAX_PADDING == 50

    def test_all_exports(self) -> None:
        """Test that __all__ contains all expected constants."""
        expected = [
            "DEFAULT_PAGE_WIDTH_MM",
            "DEFAULT_PAGE_HEIGHT_MM",
            "DEFAULT_SIDEBAR_WIDTH_MM",
            "DEFAULT_PADDING",
            "DEFAULT_SIDEBAR_PADDING_ADJUSTMENT",
            "DEFAULT_SIDEBAR_PADDING",
            "DEFAULT_FRAME_PADDING",
            "DEFAULT_COVER_PADDING_TOP",
            "DEFAULT_COVER_PADDING_BOTTOM",
            "DEFAULT_COVER_PADDING_HORIZONTAL",
            "MIN_PAGE_WIDTH_MM",
            "MAX_PAGE_WIDTH_MM",
            "MIN_PAGE_HEIGHT_MM",
            "MAX_PAGE_HEIGHT_MM",
            "MIN_SIDEBAR_WIDTH_MM",
            "MAX_SIDEBAR_WIDTH_MM",
            "MIN_PADDING",
            "MAX_PADDING",
        ]
        assert layout.__all__ == expected


class TestLayoutArithmetic:
    """Test that layout calculations are mathematically consistent."""

    def test_body_width_equals_page_minus_sidebar(self) -> None:
        """Test body_width = page_width - sidebar_width."""
        config: dict = {}
        apply_config_defaults(config)

        page_width = config["page_width"]
        sidebar_width = config["sidebar_width"]
        expected_body_width = page_width - sidebar_width

        # A4: 210mm - 65mm = 145mm
        assert expected_body_width == 145
        assert page_width == layout.DEFAULT_PAGE_WIDTH_MM
        assert sidebar_width == layout.DEFAULT_SIDEBAR_WIDTH_MM

    def test_sidebar_internal_width_calculation(self) -> None:
        """Test sidebar internal width = sidebar_width - left_padding - right_padding.

        This verifies the arithmetic for profile_width calculation.
        Previously there was an inconsistency using base padding (12mm) instead
        of actual sidebar padding (10mm each side).
        """
        config: dict = {}
        apply_config_defaults(config)

        sidebar_width = config["sidebar_width"]
        sidebar_padding_left = config["sidebar_padding_left"]
        sidebar_padding_right = config["sidebar_padding_right"]

        # Verify padding is derived from base padding - 2
        base_padding = config["padding"]
        assert sidebar_padding_left == base_padding - 2  # 12 - 2 = 10
        assert sidebar_padding_right == base_padding - 2  # 12 - 2 = 10

        # Calculate available internal width
        internal_width = sidebar_width - sidebar_padding_left - sidebar_padding_right

        # A4 layout: 65mm - 10mm - 10mm = 45mm (not 41mm with old incorrect formula)
        assert internal_width == 45

    def test_profile_width_fits_within_sidebar(self) -> None:
        """Test that profile width calculation respects sidebar bounds.

        When profile_width is not explicitly set, it should be calculated as:
        sidebar_width - sidebar_padding_left - sidebar_padding_right
        """
        config: dict = {}
        apply_config_defaults(config)

        sidebar_width = config["sidebar_width"]
        sidebar_padding_left = config["sidebar_padding_left"]
        sidebar_padding_right = config["sidebar_padding_right"]

        calculated_profile_width = (
            sidebar_width - sidebar_padding_left - sidebar_padding_right
        )

        # Must fit within sidebar (obvious sanity check)
        assert calculated_profile_width > 0
        assert calculated_profile_width < sidebar_width

        # Specific value for A4 defaults
        assert calculated_profile_width == 45

    def test_h2_width_calculation(self) -> None:
        """Test h2 heading width = body_width - h2_padding_left - icon_offset.

        The template uses: page_width - sidebar_width - h2_padding_left - 18
        where 18 is for the section icon spacing.
        """
        config: dict = {}
        apply_config_defaults(config)

        page_width = config["page_width"]
        sidebar_width = config["sidebar_width"]
        h2_padding_left = config["h2_padding_left"]
        icon_offset = 18  # Fixed spacing for section icons

        body_width = page_width - sidebar_width
        h2_width = body_width - h2_padding_left - icon_offset

        # A4 layout: (210 - 65) - 6 - 18 = 145 - 24 = 121mm
        assert h2_width == 121

    def test_padding_hierarchy_consistency(self) -> None:
        """Test that padding values maintain consistent hierarchy.

        Base padding should be larger than sidebar-specific padding adjustments.
        """
        config: dict = {}
        apply_config_defaults(config)

        base_padding = config["padding"]
        sidebar_padding_left = config["sidebar_padding_left"]
        sidebar_padding_right = config["sidebar_padding_right"]

        # Sidebar padding should be base - 2 (the adjustment factor)
        adjustment = layout.DEFAULT_SIDEBAR_PADDING_ADJUSTMENT
        expected_sidebar_padding = base_padding + adjustment
        assert sidebar_padding_left == expected_sidebar_padding
        assert sidebar_padding_right == expected_sidebar_padding

    def test_page_dimensions_are_valid_a4(self) -> None:
        """Test that default dimensions match standard A4 paper."""
        config: dict = {}
        apply_config_defaults(config)

        assert config["page_width"] == 210  # A4 width in mm
        assert config["page_height"] == 297  # A4 height in mm

        # Sidebar should be less than 1/3 of page width for good proportions
        assert config["sidebar_width"] < config["page_width"] / 3 + 5
