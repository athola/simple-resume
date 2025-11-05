from __future__ import annotations

import pytest

from simple_resume.palettes.generators import generate_hcl_palette


def test_generate_hcl_palette_deterministic(story) -> None:
    story.given("two palette generations with the same seed and hue range")
    colors_one = generate_hcl_palette(5, seed=42, hue_range=(210, 260))
    colors_two = generate_hcl_palette(5, seed=42, hue_range=(210, 260))

    story.then("the colour sequences are identical for reproducibility")
    assert colors_one == colors_two


def test_generate_hcl_palette_positive_size(story) -> None:
    story.given("a request for zero colours")
    with pytest.raises(ValueError):
        generate_hcl_palette(0)

    story.then("a ValueError is raised to signal invalid size")


def test_generate_hcl_palette_respects_size(story) -> None:
    story.given("a request for three colours within a hue range")
    colors = generate_hcl_palette(3, seed=7, hue_range=(0, 120))

    story.then("the palette returns the requested count of hex colours")
    assert len(colors) == 3
    assert all(color.startswith("#") and len(color) == 7 for color in colors)
