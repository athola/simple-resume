"""Tests for core/palettes/generators.py - palette generation functions."""

from __future__ import annotations

import pytest

from simple_resume.core.palettes.generators import generate_hcl_palette
from tests.bdd import Scenario


class TestGenerateHclPalette:
    """Tests for generate_hcl_palette function."""

    def test_generates_single_color(self, story: Scenario) -> None:
        """Test generating a single color palette."""
        story.given("a request for a single color palette")
        story.when("generating HCL palette with size 1")
        colors = generate_hcl_palette(1, seed=42)
        assert len(colors) == 1
        assert all(c.startswith("#") for c in colors)

    def test_generates_multiple_colors(self, story: Scenario) -> None:
        """Test generating multiple colors."""
        story.given("a request for multiple colors")
        story.when("generating HCL palette with size 5")
        colors = generate_hcl_palette(5, seed=42)
        assert len(colors) == 5
        assert all(c.startswith("#") for c in colors)

    def test_deterministic_with_seed(self, story: Scenario) -> None:
        """Test that same seed produces same colors."""
        story.given("two generation requests with the same seed")
        story.when("generating palettes")
        colors1 = generate_hcl_palette(3, seed=123)
        colors2 = generate_hcl_palette(3, seed=123)
        assert colors1 == colors2

    def test_different_seeds_different_colors(self, story: Scenario) -> None:
        """Test that different seeds produce different colors."""
        story.given("two generation requests with different seeds")
        story.when("generating palettes")
        colors1 = generate_hcl_palette(3, seed=123)
        colors2 = generate_hcl_palette(3, seed=456)
        assert colors1 != colors2

    def test_custom_hue_range(self, story: Scenario) -> None:
        """Test generating with custom hue range."""
        story.given("a custom hue range of 0 to 60")
        story.when("generating HCL palette")
        colors = generate_hcl_palette(3, seed=42, hue_range=(0, 60))
        assert len(colors) == 3

    def test_custom_luminance_range(self, story: Scenario) -> None:
        """Test generating with custom luminance range."""
        story.given("a custom luminance range of 0.5 to 0.9")
        story.when("generating HCL palette")
        colors = generate_hcl_palette(3, seed=42, luminance_range=(0.5, 0.9))
        assert len(colors) == 3

    def test_returns_valid_hex_colors(self, story: Scenario) -> None:
        """Test that returned colors are valid hex format."""
        story.given("a palette generation request")
        story.when("checking the generated color format")
        colors = generate_hcl_palette(5, seed=42)
        for color in colors:
            assert color.startswith("#")
            assert len(color) == 7  # #RRGGBB format

    def test_raises_error_for_zero_size(self, story: Scenario) -> None:
        """Test that size <= 0 raises ValueError."""
        story.given("size parameter of 0")
        story.when("attempting to generate palette")
        with pytest.raises(ValueError, match="size must be a positive integer"):
            generate_hcl_palette(0)

    def test_raises_error_for_negative_size(self, story: Scenario) -> None:
        """Test that negative size raises ValueError."""
        story.given("negative size parameter")
        story.when("attempting to generate palette")
        with pytest.raises(ValueError, match="size must be a positive integer"):
            generate_hcl_palette(-1)
