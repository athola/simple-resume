from __future__ import annotations

import pytest

from simple_resume.api import colors
from tests.bdd import Scenario


class TestApiColors:
    def test_calculate_text_color_namespace(self, story: Scenario) -> None:
        story.case(
            given="a light and a dark background color",
            when="calculate_text_color is invoked through the public API namespace",
            then="the helper returns contrasting text colors",
        )
        assert colors.calculate_text_color("#FFFFFF") == "#000000"
        assert colors.calculate_text_color("#000000") == "#FFFFFF"

    def test_calculate_luminance_namespace(self, story: Scenario) -> None:
        story.case(
            given="solid black and white colors",
            when="calculate_luminance is called via simple_resume.api.colors",
            then="the helper reports 0.0 for black and 1.0 for white",
        )
        assert colors.calculate_luminance("#000000") == pytest.approx(0.0)
        assert colors.calculate_luminance("#FFFFFF") == pytest.approx(1.0)

    def test_is_valid_color_namespace(self, story: Scenario) -> None:
        story.case(
            given="valid and invalid color candidates",
            when="is_valid_color runs through the curated namespace",
            then="valid hex values pass while invalid strings are rejected",
        )
        assert colors.is_valid_color("#FFF")
        assert not colors.is_valid_color("not-a-color")

    def test_calculate_text_color_light_background(self, story: Scenario) -> None:
        story.case(
            given="a light background color",
            when="calculate_text_color determines contrasting text",
            then="black or dark gray is returned for readability",
        )
        light_bg = "#FFFFFF"
        text_color = colors.calculate_text_color(light_bg)
        assert text_color in ["#000000", "#333333"]

    def test_calculate_text_color_dark_background(self, story: Scenario) -> None:
        story.case(
            given="a dark background color",
            when="calculate_text_color determines contrasting text",
            then="white or off-white is returned for readability",
        )
        dark_bg = "#000000"
        text_color = colors.calculate_text_color(dark_bg)
        assert text_color in ["#FFFFFF", "#F5F5F5"]

    def test_calculate_text_color_medium_background(self, story: Scenario) -> None:
        story.case(
            given="a medium gray background color",
            when="calculate_text_color determines contrasting text",
            then="either black or white is returned based on luminance",
        )
        medium_bg = "#808080"
        text_color = colors.calculate_text_color(medium_bg)
        assert text_color in ["#000000", "#FFFFFF"]

    def test_is_valid_color_valid_formats(self, story: Scenario) -> None:
        story.case(
            given="various valid hex color formats",
            when="is_valid_color is called on each format",
            then="all valid formats are accepted",
        )
        valid_colors = ["#FFF", "#FFFFFF", "#abc", "#ABCDEF", "#123", "#123456"]
        for color in valid_colors:
            assert colors.is_valid_color(color) is True

    def test_is_valid_color_invalid_formats(self, story: Scenario) -> None:
        story.case(
            given="various invalid color formats",
            when="is_valid_color is called on each format",
            then="all invalid formats are rejected",
        )
        invalid_colors = [
            "",
            "FFF",
            "white",
            "rgb(255,255,255)",
            "#GGGGGG",
            "#12",
            "#12345",
        ]
        for color in invalid_colors:
            assert colors.is_valid_color(color) is False

    def test_calculate_luminance_ranges(self, story: Scenario) -> None:
        story.case(
            given="white, black, and gray colors",
            when="calculate_luminance computes relative luminance",
            then="values fall in expected ranges",
        )
        white_luminance = colors.calculate_luminance("#FFFFFF")
        assert white_luminance > 0.9

        black_luminance = colors.calculate_luminance("#000000")
        assert black_luminance < 0.1

        gray_luminance = colors.calculate_luminance("#808080")
        assert 0.2 < gray_luminance < 0.8

    def test_calculate_luminance_invalid_color(self, story: Scenario) -> None:
        story.case(
            given="an invalid color string",
            when="calculate_luminance attempts calculation",
            then="a ValueError is raised",
        )
        with pytest.raises(ValueError):
            colors.calculate_luminance("invalid")

    @pytest.mark.parametrize(
        "color",
        [
            "#000000",
            "#FFFFFF",
            "#808080",
            "#FF0000",
            "#00FF00",
            "#0000FF",
            "#123456",
            "#ABCDEF",
            "#888",
            "#FFF",
            "#000",
            "#F0F",
        ],
    )
    def test_is_valid_color_hex_formats_parametrized(
        self,
        color: str,
        story: Scenario,
    ) -> None:
        story.case(
            given=f"a valid hex color format: {color}",
            when="is_valid_color is called",
            then="the validation returns True",
        )
        result = colors.is_valid_color(color)
        assert isinstance(result, bool)
        assert result is True
