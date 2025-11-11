"""Provide pure configuration normalization helpers."""

from __future__ import annotations

from typing import Any

from .color_utils import (
    calculate_icon_contrast_color,
    darken_color,
    get_contrasting_text_color,
    is_valid_color,
)

DEFAULT_BOLD_COLOR = "#585858"
DEFAULT_COLOR_SCHEME = {
    "theme_color": "#0395DE",
    "sidebar_color": "#F6F6F6",
    "sidebar_text_color": "#000000",
    "bar_background_color": "#DFDFDF",
    "date2_color": "#616161",
    "frame_color": "#757575",
    "heading_icon_color": "#0395DE",
    "bold_color": DEFAULT_BOLD_COLOR,
}

COLOR_FIELD_ORDER = [
    "theme_color",
    "sidebar_color",
    "sidebar_text_color",
    "bar_background_color",
    "date2_color",
    "frame_color",
    "heading_icon_color",
]

DIRECT_COLOR_KEYS = COLOR_FIELD_ORDER + ["bold_color", "sidebar_bold_color"]
BOLD_DARKEN_FACTOR = 0.75


def _coerce_number(value: Any, *, field: str, prefix: str) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{prefix}{field} must be numeric. Got bool value {value!r}")
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            raise ValueError(f"{prefix}{field} must be numeric. Got empty string.")
        try:
            number = float(stripped)
            return int(number) if number.is_integer() else number
        except ValueError as exc:
            raise ValueError(f"{prefix}{field} must be numeric. Got {value!r}") from exc
    raise ValueError(f"{prefix}{field} must be numeric. Got {type(value).__name__}")


def apply_config_defaults(config: dict[str, Any]) -> None:
    base_padding = config.get("padding", 12)

    config.setdefault("sidebar_padding_left", base_padding - 2)
    config.setdefault("sidebar_padding_right", base_padding - 2)
    config.setdefault("sidebar_padding_top", 0)
    config.setdefault("sidebar_padding_bottom", base_padding)

    config.setdefault("skill_container_padding_top", 3)
    config.setdefault("skill_spacer_padding_top", 3)
    config.setdefault("h3_padding_top", 7)

    config.setdefault("h2_padding_top", 8)
    config.setdefault("section_heading_margin_top", 4)
    config.setdefault("section_heading_margin_bottom", 2)


def validate_dimensions(config: dict[str, Any], filename_prefix: str) -> None:
    page_width = _coerce_number(
        config.get("page_width"), field="page_width", prefix=filename_prefix
    )
    page_height = _coerce_number(
        config.get("page_height"), field="page_height", prefix=filename_prefix
    )
    sidebar_width = _coerce_number(
        config.get("sidebar_width"), field="sidebar_width", prefix=filename_prefix
    )

    if page_width is not None and page_width <= 0:
        raise ValueError(
            f"{filename_prefix}Invalid resume config: page_width must be positive. "
            f"Got page_width={config.get('page_width')}"
        )

    if page_height is not None and page_height <= 0:
        raise ValueError(
            f"{filename_prefix}Invalid resume config: page_height must be positive. "
            f"Got page_height={config.get('page_height')}"
        )

    if page_width is not None:
        config["page_width"] = page_width
    if page_height is not None:
        config["page_height"] = page_height
    if sidebar_width is not None:
        config["sidebar_width"] = sidebar_width

    if sidebar_width is not None:
        if sidebar_width <= 0:
            raise ValueError(
                f"{filename_prefix}Sidebar width must be positive. "
                f"Got {config.get('sidebar_width')}"
            )
        if page_width is not None and sidebar_width >= page_width:
            raise ValueError(
                f"{filename_prefix}Sidebar width ({config.get('sidebar_width')}mm) "
                f"must be less than page width ({config.get('page_width')}mm)"
            )


def _normalize_color_scheme(config: dict[str, Any]) -> None:
    raw_scheme = config.get("color_scheme", "")
    if isinstance(raw_scheme, str):
        config["color_scheme"] = raw_scheme.strip() or "default"
    else:
        config["color_scheme"] = "default"


def _validate_color_fields(config: dict[str, Any], filename_prefix: str) -> None:
    for field in COLOR_FIELD_ORDER:
        value = config.get(field)
        if not value:
            default_value = DEFAULT_COLOR_SCHEME.get(field)
            if default_value:
                config[field] = default_value
            value = config.get(field)
        if value is None:
            continue
        if not isinstance(value, str):
            raise ValueError(
                f"{filename_prefix}Invalid color format for '{field}': {value}. "
                "Expected hex color string."
            )
        if not is_valid_color(value):
            raise ValueError(
                f"{filename_prefix}Invalid color format for '{field}': {value}. "
                "Expected hex color like '#0395DE' or '#FFF'"
            )


def _auto_calculate_sidebar_text_color(config: dict[str, Any]) -> None:
    sidebar_color = config.get("sidebar_color")
    if isinstance(sidebar_color, str) and is_valid_color(sidebar_color):
        config["sidebar_text_color"] = get_contrasting_text_color(sidebar_color)


def _handle_sidebar_bold_color(config: dict[str, Any], filename_prefix: str) -> None:
    explicit_color = config.get("sidebar_bold_color")
    if explicit_color:
        if not isinstance(explicit_color, str):
            raise ValueError(
                f"{filename_prefix}Invalid color format for 'sidebar_bold_color': "
                f"{explicit_color}. Expected hex color string."
            )
        if not is_valid_color(explicit_color):
            raise ValueError(
                f"{filename_prefix}Invalid color format for 'sidebar_bold_color': "
                f"{explicit_color}. Expected hex color like '#0395DE' or '#FFF'"
            )
        return

    sidebar_color = config.get("sidebar_color")
    if isinstance(sidebar_color, str) and is_valid_color(sidebar_color):
        config["sidebar_bold_color"] = get_contrasting_text_color(sidebar_color)
        return

    sidebar_text_color = config.get("sidebar_text_color")
    if isinstance(sidebar_text_color, str) and is_valid_color(sidebar_text_color):
        config["sidebar_bold_color"] = sidebar_text_color
        return

    config["sidebar_bold_color"] = DEFAULT_COLOR_SCHEME.get(
        "sidebar_bold_color", DEFAULT_COLOR_SCHEME["sidebar_text_color"]
    )


def _handle_icon_color(config: dict[str, Any], filename_prefix: str) -> None:
    heading_icon_color = config.get("heading_icon_color")
    if heading_icon_color:
        if not isinstance(heading_icon_color, str):
            raise ValueError(
                f"{filename_prefix}Invalid color format for 'heading_icon_color': "
                f"{heading_icon_color}. Expected hex color string."
            )
        if not is_valid_color(heading_icon_color):
            raise ValueError(
                f"{filename_prefix}Invalid color format for 'heading_icon_color': "
                f"{heading_icon_color}. Expected hex color like '#0395DE' or '#FFF'"
            )

    sidebar_color = config.get("sidebar_color", "#FFFFFF")
    theme_color = config.get("theme_color", "#0395DE")

    config["heading_icon_color"] = calculate_icon_contrast_color(
        heading_icon_color,
        theme_color,
    )
    config["sidebar_icon_color"] = calculate_icon_contrast_color(
        None,
        sidebar_color,
    )


def _handle_bold_color(config: dict[str, Any], filename_prefix: str) -> None:
    bold_color = config.get("bold_color")
    if bold_color:
        if not isinstance(bold_color, str):
            raise ValueError(
                f"{filename_prefix}Invalid color format for 'bold_color': "
                f"{bold_color}. Expected hex color string."
            )
        if not is_valid_color(bold_color):
            raise ValueError(
                f"{filename_prefix}Invalid color format for 'bold_color': "
                f"{bold_color}. Expected hex color like '#0395DE' or '#FFF'"
            )
        return

    frame_color = config.get("frame_color")
    if isinstance(frame_color, str) and is_valid_color(frame_color):
        config["bold_color"] = darken_color(frame_color, BOLD_DARKEN_FACTOR)
        return
    config["bold_color"] = DEFAULT_COLOR_SCHEME.get("bold_color", DEFAULT_BOLD_COLOR)


def prepare_config(config: dict[str, Any], *, filename: str = "") -> bool:
    """Apply defaults and validate dimensions prior to palette resolution."""
    filename_prefix = f"{filename}: " if filename else ""
    apply_config_defaults(config)
    validate_dimensions(config, filename_prefix)
    return bool(config.get("sidebar_text_color"))


def finalize_config(
    config: dict[str, Any],
    *,
    filename: str = "",
    sidebar_text_locked: bool = False,
) -> None:
    """Finalize color fields after palette resolution."""
    filename_prefix = f"{filename}: " if filename else ""
    _normalize_color_scheme(config)
    _validate_color_fields(config, filename_prefix)
    if not sidebar_text_locked:
        _auto_calculate_sidebar_text_color(config)
    _handle_icon_color(config, filename_prefix)
    _handle_bold_color(config, filename_prefix)
    _handle_sidebar_bold_color(config, filename_prefix)


__all__ = [
    "COLOR_FIELD_ORDER",
    "DEFAULT_BOLD_COLOR",
    "DEFAULT_COLOR_SCHEME",
    "DIRECT_COLOR_KEYS",
    "finalize_config",
    "prepare_config",
]
