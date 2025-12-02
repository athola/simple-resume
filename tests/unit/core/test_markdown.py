"""Tests for core/markdown.py - markdown processing functions."""

from __future__ import annotations

from simple_resume.core.markdown import derive_bold_color


class TestDeriveBoldColor:
    """Tests for derive_bold_color function."""

    def test_darkens_valid_hex_color(self) -> None:
        """Test that valid hex color is darkened."""
        result = derive_bold_color("#F6F6F6")
        assert result.startswith("#")
        assert result != "#F6F6F6"  # Should be darker

    def test_returns_default_for_none(self) -> None:
        """Test that None returns default bold color."""
        result = derive_bold_color(None)
        assert result.startswith("#")

    def test_returns_default_for_invalid_color(self) -> None:
        """Test that invalid color returns default."""
        result = derive_bold_color("not-a-color")
        assert result.startswith("#")

    def test_returns_default_for_non_string(self) -> None:
        """Test that non-string input returns default."""
        result = derive_bold_color(12345)  # type: ignore[arg-type]
        assert result.startswith("#")
