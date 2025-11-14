"""Unit tests for the color calculation service boundaries."""

from __future__ import annotations

import pytest

from simple_resume.constants import DEFAULT_COLOR_SCHEME, ICON_CONTRAST_THRESHOLD
from simple_resume.core.color_service import ColorCalculationService


class TestColorCalculationService:
    def test_sidebar_text_color_respects_contrast(self) -> None:
        config = {"sidebar_color": "#000000"}
        assert ColorCalculationService.calculate_sidebar_text_color(config) == "#F5F5F5"

    def test_sidebar_text_color_falls_back_to_default(self) -> None:
        config = {"sidebar_color": "not-a-color"}
        assert (
            ColorCalculationService.calculate_sidebar_text_color(config)
            == DEFAULT_COLOR_SCHEME["sidebar_text_color"]
        )

    def test_heading_icon_color_prefers_theme_with_contrast(self) -> None:
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
        self, text_color: str, background: str
    ) -> None:
        assert (
            ColorCalculationService.ensure_color_contrast(
                background,
                text_color,
                contrast_threshold=ICON_CONTRAST_THRESHOLD,
            )
            == text_color
        )

    def test_ensure_color_contrast_generates_fallback(self) -> None:
        # Very low contrast user color should be replaced.
        result = ColorCalculationService.ensure_color_contrast("#FFFFFF", "#FFFFFE")
        assert result == "#333333"
