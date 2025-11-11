from __future__ import annotations

from simple_resume.core.config_core import finalize_config, prepare_config


def test_prepare_config_coerces_numeric_fields() -> None:
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


def test_finalize_config_populates_default_colors() -> None:
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
