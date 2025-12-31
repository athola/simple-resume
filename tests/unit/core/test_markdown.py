"""Tests for core/markdown.py - markdown processing functions."""

from __future__ import annotations

from simple_resume.core.markdown import derive_bold_color
from tests.bdd import Scenario


class TestDeriveBoldColor:
    """Tests for derive_bold_color function."""

    def test_darkens_valid_hex_color(self, story: Scenario) -> None:
        """Test that valid hex color is darkened."""
        story.given("a valid light hex color")
        story.when("deriving bold color")
        result = derive_bold_color("#F6F6F6")
        assert result.startswith("#")
        assert result != "#F6F6F6"  # Should be darker

    def test_returns_default_for_none(self, story: Scenario) -> None:
        """Test that None returns default bold color."""
        story.given("None as input")
        story.when("deriving bold color")
        result = derive_bold_color(None)
        assert result.startswith("#")

    def test_returns_default_for_invalid_color(self, story: Scenario) -> None:
        """Test that invalid color returns default."""
        story.given("an invalid color string")
        story.when("deriving bold color")
        result = derive_bold_color("not-a-color")
        assert result.startswith("#")

    def test_returns_default_for_non_string(self, story: Scenario) -> None:
        """Test that non-string input returns default."""
        story.given("a non-string input (integer)")
        story.when("deriving bold color")
        result = derive_bold_color(12345)  # type: ignore[arg-type]
        assert result.startswith("#")
