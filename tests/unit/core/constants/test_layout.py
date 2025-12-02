"""Tests for core/constants/layout.py - layout constants."""

from __future__ import annotations

from simple_resume.core.constants import layout


class TestLayoutConstants:
    """Test layout constant values."""

    def test_default_page_dimensions(self) -> None:
        """Test default page dimension constants."""
        assert layout.DEFAULT_PAGE_WIDTH_MM == 190
        assert layout.DEFAULT_PAGE_HEIGHT_MM == 270

    def test_default_sidebar_width(self) -> None:
        """Test default sidebar width constant."""
        assert layout.DEFAULT_SIDEBAR_WIDTH_MM == 60

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
