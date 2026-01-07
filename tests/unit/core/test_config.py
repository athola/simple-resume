from __future__ import annotations

import pytest

from simple_resume.core.config import (
    apply_config_defaults,
    finalize_config,
    prepare_config,
)
from tests.bdd import Scenario


def test_prepare_config_coerces_numeric_fields(story: Scenario) -> None:
    story.given("a config with string numeric values")
    story.when("preparing the config")
    config = {
        "page_width": "210",
        "page_height": "297",
        "sidebar_width": "50",
    }

    sidebar_locked = prepare_config(config, filename="resume.yaml")

    assert sidebar_locked is False
    width = config["page_width"]
    height = config["page_height"]
    sidebar = config["sidebar_width"]
    assert isinstance(width, int) and width == 210
    assert isinstance(height, int) and height == 297
    assert isinstance(sidebar, int) and sidebar == 50


def test_finalize_config_populates_default_colors(story: Scenario) -> None:
    story.given("a config with basic theme colors")
    story.when("finalizing the config")
    config = {
        "theme_color": "#111111",
        "sidebar_color": "#FFFFFF",
        "frame_color": "#222222",
    }

    finalize_config(config, filename="resume.yaml", sidebar_text_locked=False)

    assert config["color_scheme"] == "default"
    assert config["sidebar_text_color"] in {"#000000", "#333333"}
    assert config["heading_icon_color"]
    assert config["sidebar_bold_color"]
    assert config["bold_color"]


class TestApplyConfigDefaults:
    """Tests for apply_config_defaults() ensuring all defaults are centralized."""

    def test_page_dimensions_default(self, story: Scenario) -> None:
        """Verify page dimensions are set to A4 defaults."""
        story.given("an empty config dictionary")
        story.when("applying config defaults")
        config: dict = {}
        apply_config_defaults(config)

        assert config["page_width"] == 210
        assert config["page_height"] == 297
        assert config["sidebar_width"] == 65

    def test_base_padding_default(self, story: Scenario) -> None:
        """Verify base padding is set to 12mm."""
        story.given("an empty config dictionary")
        story.when("applying config defaults")
        config: dict = {}
        apply_config_defaults(config)

        assert config["padding"] == 12

    def test_sidebar_padding_derived_from_base(self, story: Scenario) -> None:
        """Verify sidebar padding is derived from base padding."""
        story.given("an empty config dictionary")
        story.when("applying config defaults")
        config: dict = {}
        apply_config_defaults(config)

        # With base_padding=12, sidebar_padding_left/right should be 10
        assert config["sidebar_padding_left"] == 10
        assert config["sidebar_padding_right"] == 10
        assert config["sidebar_padding_top"] == 0
        assert config["sidebar_padding_bottom"] == 12

    def test_sidebar_padding_with_custom_base(self, story: Scenario) -> None:
        """Verify sidebar padding uses custom base padding."""
        story.given("a config with custom base padding of 16")
        story.when("applying config defaults")
        config: dict = {"padding": 16}
        apply_config_defaults(config)

        # With base_padding=16, sidebar_padding_left/right should be 14
        assert config["sidebar_padding_left"] == 14
        assert config["sidebar_padding_right"] == 14
        assert config["sidebar_padding_bottom"] == 16

    def test_pitch_padding_defaults(self, story: Scenario) -> None:
        """Verify pitch section padding defaults."""
        story.given("an empty config dictionary")
        story.when("applying config defaults")
        config: dict = {}
        apply_config_defaults(config)

        assert config["pitch_padding_top"] == 10
        assert config["pitch_padding_bottom"] == 8
        assert config["pitch_padding_left"] == 6

    def test_heading_padding_defaults(self, story: Scenario) -> None:
        """Verify heading padding defaults."""
        story.given("an empty config dictionary")
        story.when("applying config defaults")
        config: dict = {}
        apply_config_defaults(config)

        assert config["h2_padding_left"] == 6
        assert config["h2_padding_top"] == 8
        assert config["h3_padding_top"] == 7

    def test_section_layout_defaults(self, story: Scenario) -> None:
        """Verify section layout defaults match template expectations."""
        story.given("an empty config dictionary")
        story.when("applying config defaults")
        config: dict = {}
        apply_config_defaults(config)

        assert config["section_heading_margin_top"] == 7
        assert config["section_heading_margin_bottom"] == 1
        assert config["section_heading_text_margin"] == -6
        assert config["section_icon_design_scale"] == 1
        assert config["entry_margin_bottom"] == 4
        assert config["tech_stack_margin_bottom"] == 2

    def test_section_icon_defaults(self, story: Scenario) -> None:
        """Verify section icon settings defaults."""
        story.given("an empty config dictionary")
        story.when("applying config defaults")
        config: dict = {}
        apply_config_defaults(config)

        assert config["section_icon_circle_size"] == 7.8
        assert config["section_icon_circle_x_offset"] == 0
        assert config["section_icon_design_size"] == 3.5
        assert config["section_icon_design_x_offset"] == 0
        assert config["section_icon_design_y_offset"] == 0

    def test_container_width_defaults(self, story: Scenario) -> None:
        """Verify container width and padding defaults."""
        story.given("an empty config dictionary")
        story.when("applying config defaults")
        config: dict = {}
        apply_config_defaults(config)

        assert config["date_container_width"] == 15
        assert config["description_container_padding_left"] == 4
        assert config["skill_container_padding_top"] == 3
        assert config["skill_spacer_padding_top"] == 3
        assert config["profile_image_padding_bottom"] == 8

    def test_frame_padding_default(self, story: Scenario) -> None:
        """Verify frame (preview mode) padding default."""
        story.given("an empty config dictionary")
        story.when("applying config defaults")
        config: dict = {}
        apply_config_defaults(config)

        assert config["frame_padding"] == 15

    def test_cover_page_padding_defaults(self, story: Scenario) -> None:
        """Verify cover page padding defaults."""
        story.given("an empty config dictionary")
        story.when("applying config defaults")
        config: dict = {}
        apply_config_defaults(config)

        assert config["cover_padding_top"] == 15
        assert config["cover_padding_bottom"] == 15
        assert config["cover_padding_h"] == 20

    def test_contact_section_defaults(self, story: Scenario) -> None:
        """Verify contact section styling defaults."""
        story.given("an empty config dictionary")
        story.when("applying config defaults")
        config: dict = {}
        apply_config_defaults(config)

        assert config["contact_icon_size"] == 5
        assert config["contact_icon_margin_top"] == 0.5
        assert config["contact_text_padding_left"] == 2

    def test_font_settings_default(self, story: Scenario) -> None:
        """Verify font settings defaults."""
        story.given("an empty config dictionary")
        story.when("applying config defaults")
        config: dict = {}
        apply_config_defaults(config)

        assert config["bold_font_weight"] == 600
        assert config["description_font_size"] == 8.5
        assert config["date_font_size"] == 9
        assert config["sidebar_font_size"] == 8.5

    def test_existing_values_not_overwritten(self, story: Scenario) -> None:
        """Verify that existing config values are not overwritten."""
        story.given("a config with pre-existing custom values")
        story.when("applying config defaults")
        config: dict = {
            "page_width": 180,
            "page_height": 260,
            "sidebar_width": 55,
            "padding": 10,
            "section_heading_margin_top": 8,
            "frame_padding": 20,
            "description_font_size": 10,
            "date_font_size": 11,
            "sidebar_font_size": 9,
        }
        apply_config_defaults(config)

        # Existing values should be preserved
        assert config["page_width"] == 180
        assert config["page_height"] == 260
        assert config["sidebar_width"] == 55
        assert config["padding"] == 10
        assert config["section_heading_margin_top"] == 8
        assert config["frame_padding"] == 20

        # Font size values should be preserved
        assert config["description_font_size"] == 10
        assert config["date_font_size"] == 11
        assert config["sidebar_font_size"] == 9

        # Derived values should use the custom padding
        assert config["sidebar_padding_left"] == 8  # 10 - 2
        assert config["sidebar_padding_bottom"] == 10


class TestNormalizationCompleteness:
    """Tests to verify normalization populates all expected keys."""

    # Define all expected layout/styling keys that should be set by normalization
    EXPECTED_DIMENSION_KEYS = {
        "page_width",
        "page_height",
        "sidebar_width",
    }

    EXPECTED_PADDING_KEYS = {
        "padding",
        "sidebar_padding_left",
        "sidebar_padding_right",
        "sidebar_padding_top",
        "sidebar_padding_bottom",
        "pitch_padding_top",
        "pitch_padding_bottom",
        "pitch_padding_left",
        "h2_padding_left",
        "h2_padding_top",
        "h3_padding_top",
        "frame_padding",
        "cover_padding_top",
        "cover_padding_bottom",
        "cover_padding_h",
    }

    EXPECTED_SECTION_KEYS = {
        "section_heading_margin_top",
        "section_heading_margin_bottom",
        "section_heading_text_margin",
        "section_icon_design_scale",
        "entry_margin_bottom",
        "tech_stack_margin_bottom",
        "section_icon_circle_size",
        "section_icon_circle_x_offset",
        "section_icon_design_size",
        "section_icon_design_x_offset",
        "section_icon_design_y_offset",
    }

    EXPECTED_CONTAINER_KEYS = {
        "date_container_width",
        "description_container_padding_left",
        "skill_container_padding_top",
        "skill_spacer_padding_top",
        "profile_image_padding_bottom",
    }

    EXPECTED_CONTACT_KEYS = {
        "contact_icon_size",
        "contact_icon_margin_top",
        "contact_text_padding_left",
    }

    EXPECTED_FONT_KEYS = {
        "bold_font_weight",
        "description_font_size",
        "date_font_size",
        "sidebar_font_size",
    }

    @pytest.fixture
    def all_expected_keys(self) -> set:
        """Return the complete set of expected keys."""
        return (
            self.EXPECTED_DIMENSION_KEYS
            | self.EXPECTED_PADDING_KEYS
            | self.EXPECTED_SECTION_KEYS
            | self.EXPECTED_CONTAINER_KEYS
            | self.EXPECTED_CONTACT_KEYS
            | self.EXPECTED_FONT_KEYS
        )

    def test_all_expected_keys_populated(
        self, all_expected_keys: set, story: Scenario
    ) -> None:
        """Verify that normalization populates ALL expected layout/styling keys."""
        story.given("an empty config and a set of expected keys")
        story.when("applying config defaults")
        config: dict = {}
        apply_config_defaults(config)

        missing_keys = all_expected_keys - set(config.keys())
        assert not missing_keys, f"Missing keys after normalization: {missing_keys}"

    def test_no_none_values(self, all_expected_keys: set, story: Scenario) -> None:
        """Verify that no expected keys have None values."""
        story.given("an empty config and a set of expected keys")
        story.when("applying config defaults")
        config: dict = {}
        apply_config_defaults(config)

        none_keys = {k for k in all_expected_keys if config.get(k) is None}
        assert not none_keys, f"Keys with None values: {none_keys}"

    def test_all_numeric_values(self, all_expected_keys: set, story: Scenario) -> None:
        """Verify that all layout/styling values are numeric (int or float)."""
        story.given("an empty config and a set of expected keys")
        story.when("applying config defaults and checking value types")
        config: dict = {}
        apply_config_defaults(config)

        non_numeric_keys = {
            k: type(config[k]).__name__
            for k in all_expected_keys
            if not isinstance(config.get(k), (int, float))
        }
        assert not non_numeric_keys, f"Non-numeric values: {non_numeric_keys}"
