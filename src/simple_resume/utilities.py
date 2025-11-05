#!/usr/bin/env python3
"""Load and validate resume data from YAML files."""

from __future__ import annotations

import copy
import re
from itertools import cycle
from pathlib import Path
from typing import Any

from markdown import markdown
from oyaml import safe_load

from . import config as config_module
from .config import FILE_DEFAULT, Paths
from .palettes.exceptions import (
    PaletteError,
    PaletteGenerationError,
    PaletteLookupError,
)
from .palettes.generators import generate_hcl_palette
from .palettes.registry import get_global_registry
from .palettes.sources import ColourLoversClient

PATH_DATA = str(config_module.PATH_DATA)
PATH_INPUT = str(config_module.PATH_INPUT)
PATH_OUTPUT = str(config_module.PATH_OUTPUT)

# Color constants
HEX_COLOR_SHORT_LENGTH = 3
HEX_COLOR_FULL_LENGTH = 6

# Luminance constants for contrast ratio calculations
LINEARIZATION_THRESHOLD = 0.03928
LINEARIZATION_DIVISOR = 12.92
LINEARIZATION_EXPONENT = 2.4
LINEARIZATION_OFFSET = 0.055

# Luminance thresholds for text color selection
VERY_DARK_THRESHOLD = 0.15
DARK_THRESHOLD = 0.5
VERY_LIGHT_THRESHOLD = 0.8

# Color generation constants
RANGE_LENGTH = 2

__all__ = [
    "FILE_DEFAULT",
    "PATH_DATA",
    "PATH_INPUT",
    "PATH_OUTPUT",
    "normalize_config",
    "get_content",
    "validate_config",
    "render_markdown_content",
]


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == HEX_COLOR_SHORT_LENGTH:
        hex_color = "".join([c * 2 for c in hex_color])
    if len(hex_color) != HEX_COLOR_FULL_LENGTH:
        raise ValueError(f"Invalid hex color: {hex_color}")
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return r, g, b
    except ValueError as exc:
        raise ValueError(f"Invalid hex color: {hex_color}") from exc


def _calculate_luminance(rgb: tuple[int, int, int]) -> float:
    """Calculate relative luminance of RGB color using WCAG formula.

    Returns a value between 0 (darkest black) and 1 (lightest white).
    """
    r, g, b = rgb

    # Convert to linear RGB by applying gamma correction
    def _linearize(c: int) -> float:
        c_val = c / 255.0
        return (
            c_val / LINEARIZATION_DIVISOR
            if c_val <= LINEARIZATION_THRESHOLD
            else ((c_val + LINEARIZATION_OFFSET) / (1 + LINEARIZATION_OFFSET))
            ** LINEARIZATION_EXPONENT
        )

    r_linear = _linearize(r)
    g_linear = _linearize(g)
    b_linear = _linearize(b)

    # Calculate luminance using WCAG weights
    return 0.2126 * r_linear + 0.7152 * g_linear + 0.0722 * b_linear


def _get_contrasting_text_color(background_color: str) -> str:
    """Generate an appropriate text color for the given background color.

    Returns:
        - "#000000" (black) for light backgrounds (luminance > 0.5)
        - "#FFFFFF" (white) for dark backgrounds (luminance <= 0.5)
        - "#333333" (dark gray) for very light backgrounds (luminance > 0.8)
        - "#F5F5F5" (off-white) for very dark backgrounds (luminance <= 0.15)

    """
    try:
        rgb = _hex_to_rgb(background_color)
        luminance = _calculate_luminance(rgb)

        # Use different text colors based on background luminance
        if luminance <= VERY_DARK_THRESHOLD:
            # Very dark background - use off-white for less harsh contrast
            return "#F5F5F5"
        elif luminance <= DARK_THRESHOLD:
            # Dark background - use white
            return "#FFFFFF"
        elif luminance >= VERY_LIGHT_THRESHOLD:
            # Very light background - use dark gray for less harsh contrast
            return "#333333"
        else:
            # Light background - use black
            return "#000000"
    except (ValueError, TypeError):
        # If color parsing fails, default to black
        return "#000000"


def _read_yaml(uri: str | Path) -> dict[str, Any]:
    """Read a YAML file and return its content."""
    path = Path(uri)
    with open(str(path), encoding="utf-8") as file:
        content = safe_load(file)
        return content if content is not None else {}


def _is_valid_color(color: str) -> bool:
    """Check if a color string is a valid hex color code."""
    if not color:
        return False
    # Match #RGB or #RRGGBB format
    return bool(re.match(r"^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$", color))


def _coerce_number(value: Any, *, field: str, prefix: str) -> float | int | None:
    """Convert mixed numeric inputs (including strings) to floats."""
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{prefix}{field} must be numeric. Got bool value {value!r}")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            raise ValueError(f"{prefix}{field} must be numeric. Got empty string.")
        try:
            number = float(stripped)
            if number.is_integer():
                return int(number)
            return number
        except ValueError as exc:
            raise ValueError(f"{prefix}{field} must be numeric. Got {value!r}") from exc
    raise ValueError(f"{prefix}{field} must be numeric. Got {type(value).__name__}")


DEFAULT_COLOR_SCHEME = {
    "theme_color": "#0395DE",
    "sidebar_color": "#F6F6F6",
    "sidebar_text_color": "#000000",
    "bar_background_color": "#DFDFDF",
    "date2_color": "#616161",
    "frame_color": "#757575",
}

COLOR_FIELD_ORDER = [
    "theme_color",
    "sidebar_color",
    "sidebar_text_color",
    "bar_background_color",
    "date2_color",
    "frame_color",
]


def normalize_config(
    raw_config: dict[str, Any], filename: str = ""
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Return a normalized copy of the config and optional palette metadata."""
    working = copy.deepcopy(raw_config)
    palette_meta = _validate_config_inplace(working, filename=filename)
    return working, palette_meta


def validate_config(config: dict[str, Any], filename: str = "") -> None:
    """Validate resume configuration for common errors (legacy mutating API).

    Args:
        config: Configuration dict from YAML file
        filename: Name of the file being validated (for error messages)

    Raises:
        ValueError: If validation fails with descriptive error message

    """
    if not config:
        return  # No config to validate

    normalized, _ = normalize_config(config, filename=filename)
    config.clear()
    config.update(normalized)


def _apply_config_defaults(config: dict[str, Any]) -> None:
    """Apply default values for optional config parameters."""
    # Get base padding value for calculating derived defaults
    base_padding = config.get("padding", 12)

    # Sidebar padding defaults (derived from base padding if not specified)
    if "sidebar_padding_left" not in config:
        config["sidebar_padding_left"] = base_padding - 2
    if "sidebar_padding_right" not in config:
        config["sidebar_padding_right"] = base_padding - 2
    if "sidebar_padding_top" not in config:
        config["sidebar_padding_top"] = 0
    if "sidebar_padding_bottom" not in config:
        config["sidebar_padding_bottom"] = base_padding

    # Spacing defaults
    if "skill_container_padding_top" not in config:
        config["skill_container_padding_top"] = 3
    if "skill_spacer_padding_top" not in config:
        config["skill_spacer_padding_top"] = 3
    if "h3_padding_top" not in config:
        config["h3_padding_top"] = 7

    # Section heading spacing defaults
    if "h2_padding_top" not in config:
        config["h2_padding_top"] = 8
    if "section_heading_margin_top" not in config:
        config["section_heading_margin_top"] = 4
    if "section_heading_margin_bottom" not in config:
        config["section_heading_margin_bottom"] = 2


def _validate_dimensions(config: dict[str, Any], filename_prefix: str) -> None:
    """Validate and normalize dimension fields in config."""
    raw_page_width = config.get("page_width")
    raw_page_height = config.get("page_height")
    raw_sidebar_width = config.get("sidebar_width")

    page_width = _coerce_number(
        raw_page_width, field="page_width", prefix=filename_prefix
    )
    page_height = _coerce_number(
        raw_page_height, field="page_height", prefix=filename_prefix
    )
    sidebar_width = _coerce_number(
        raw_sidebar_width, field="sidebar_width", prefix=filename_prefix
    )

    if page_width is not None and page_width <= 0:
        raise ValueError(
            f"{filename_prefix}Invalid resume config: page_width must be positive. "
            f"Got page_width={raw_page_width}"
        )

    if page_height is not None and page_height <= 0:
        raise ValueError(
            f"{filename_prefix}Invalid resume config: page_height must be positive. "
            f"Got page_height={raw_page_height}"
        )

    if page_width is not None:
        config["page_width"] = page_width
    if page_height is not None:
        config["page_height"] = page_height
    if sidebar_width is not None:
        config["sidebar_width"] = sidebar_width

    if page_width is not None and page_height is not None:
        if page_width <= 0 or page_height <= 0:
            raise ValueError(
                f"{filename_prefix}Page dimensions must be positive. "
                f"Got page_width={raw_page_width}, page_height={raw_page_height}"
            )

    if sidebar_width is not None:
        if sidebar_width <= 0:
            raise ValueError(
                f"{filename_prefix}Sidebar width must be positive. "
                f"Got {raw_sidebar_width}"
            )
        if page_width is not None and sidebar_width >= page_width:
            message = (
                f"{filename_prefix}Sidebar width ({raw_sidebar_width}mm) must be less "
                f"than page width ({raw_page_width}mm)"
            )
            raise ValueError(message)


def _normalize_color_scheme(config: dict[str, Any]) -> None:
    """Normalize color scheme field in config."""
    raw_color_scheme = config.get("color_scheme", "")
    if isinstance(raw_color_scheme, str):
        trimmed_scheme = raw_color_scheme.strip()
    else:
        trimmed_scheme = ""

    if trimmed_scheme:
        config["color_scheme"] = trimmed_scheme
    else:
        config["color_scheme"] = "default"


def _validate_color_fields(config: dict[str, Any], filename_prefix: str) -> None:
    """Validate and fill default color fields."""
    color_fields = [
        "theme_color",
        "sidebar_color",
        "sidebar_text_color",
        "bar_background_color",
        "date2_color",
        "frame_color",
    ]

    for field in color_fields:
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
        if not _is_valid_color(value):
            raise ValueError(
                f"{filename_prefix}Invalid color format for '{field}': {value}. "
                f"Expected hex color like '#0395DE' or '#FFF'"
            )


def _auto_calculate_sidebar_text_color(config: dict[str, Any]) -> None:
    """Automatically calculate sidebar text color based on sidebar background."""
    sidebar_color = config.get("sidebar_color")
    if isinstance(sidebar_color, str) and _is_valid_color(sidebar_color):
        config["sidebar_text_color"] = _get_contrasting_text_color(sidebar_color)


def _handle_icon_color(config: dict[str, Any], filename_prefix: str) -> None:
    """Validate and set icon color."""
    icon_color = config.get("heading_icon_color")
    if not icon_color:
        config["heading_icon_color"] = config.get("sidebar_text_color", "#000000")
    else:
        if not isinstance(icon_color, str):
            raise ValueError(
                f"{filename_prefix}Invalid color format for 'heading_icon_color': "
                f"{icon_color}. Expected hex color string."
            )
        if not _is_valid_color(icon_color):
            raise ValueError(
                f"{filename_prefix}Invalid color format for 'heading_icon_color': "
                f"{icon_color}. Expected hex color like '#0395DE' or '#FFF'"
            )


def _validate_config_inplace(
    config: dict[str, Any], filename: str = ""
) -> dict[str, Any] | None:
    """Validate and normalize config in-place, return palette metadata."""
    filename_prefix = f"{filename}: " if filename else ""

    # Apply default values for optional parameters
    _apply_config_defaults(config)

    # Validate dimensions
    _validate_dimensions(config, filename_prefix)

    # Check if user provided sidebar text color before palette application
    user_sidebar_text_color = bool(config.get("sidebar_text_color"))

    # Apply palette block
    palette_metadata = _apply_palette_block(config)

    # Normalize color scheme
    _normalize_color_scheme(config)

    # Validate color fields
    _validate_color_fields(config, filename_prefix)

    # Auto-calculate sidebar text color if not user-provided
    if not user_sidebar_text_color:
        _auto_calculate_sidebar_text_color(config)

    # Handle icon color
    _handle_icon_color(config, filename_prefix)

    return palette_metadata


def _apply_palette_block(config: dict[str, Any]) -> dict[str, Any] | None:
    block = config.get("palette")
    if not isinstance(block, dict):
        return None

    try:
        swatches, palette_meta = _resolve_palette_block(block)
    except PaletteError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise PaletteGenerationError(f"Invalid palette block: {exc}") from exc

    if not swatches:
        return None

    # Cycle through swatches to cover all required fields
    iterator = cycle(swatches)
    for field in COLOR_FIELD_ORDER:
        if field not in config or not config[field]:
            config[field] = next(iterator)

    # Automatically calculate sidebar text color based on sidebar background
    if config.get("sidebar_color"):
        config["sidebar_text_color"] = _get_contrasting_text_color(
            config["sidebar_color"]
        )

    if "color_scheme" not in config and "name" in block:
        config["color_scheme"] = str(block["name"])

    return palette_meta


def _resolve_palette_block(block: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    source = str(block.get("source", "registry")).lower()

    if source == "registry":
        name = block.get("name")
        if not name:
            raise PaletteLookupError("registry source requires 'name'")
        registry = get_global_registry()
        palette = registry.get(str(name))
        metadata = {
            "source": "registry",
            "name": palette.name,
            "size": len(palette.swatches),
            "attribution": palette.metadata,
        }
        return list(palette.swatches), metadata

    if source == "generator":
        size = int(block.get("size", len(COLOR_FIELD_ORDER)))
        seed = block.get("seed")
        hue_range = tuple(block.get("hue_range", (0, 360)))
        luminance_range = tuple(block.get("luminance_range", (0.35, 0.85)))
        chroma = float(block.get("chroma", 0.12))
        if len(hue_range) != RANGE_LENGTH or len(luminance_range) != RANGE_LENGTH:
            raise PaletteGenerationError(
                "hue_range and luminance_range must have two values"
            )
        swatches = generate_hcl_palette(
            size,
            seed=int(seed) if seed is not None else None,
            hue_range=(float(hue_range[0]), float(hue_range[1])),
            chroma=chroma,
            luminance_range=(float(luminance_range[0]), float(luminance_range[1])),
        )
        metadata = {
            "source": "generator",
            "size": len(swatches),
            "seed": int(seed) if seed is not None else None,
            "hue_range": [float(hue_range[0]), float(hue_range[1])],
            "luminance_range": [float(luminance_range[0]), float(luminance_range[1])],
            "chroma": chroma,
        }
        return swatches, metadata

    if source == "remote":
        client = ColourLoversClient()
        palettes = client.fetch(
            keywords=block.get("keywords"),
            num_results=int(block.get("num_results", 1)),
            order_by=str(block.get("order_by", "score")),
        )
        if not palettes:
            raise PaletteLookupError("ColourLovers returned no palettes")
        palette = palettes[0]
        metadata = {
            "source": "remote",
            "name": palette.name,
            "attribution": palette.metadata,
            "size": len(palette.swatches),
        }
        return list(palette.swatches), metadata

    raise PaletteLookupError(f"Unsupported palette source: {source}")


def _coerce_items(value: Any) -> list[str]:
    """Return a list of trimmed string items from arbitrary input."""
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def format_skill_groups(value: Any) -> list[dict[str, list[str] | str | None]]:
    """Normalize skill data into titled groups with string entries."""
    groups: list[dict[str, list[str] | str | None]] = []

    if value is None:
        return groups

    def add_group(title: str | None, items: Any) -> None:
        normalized = [entry for entry in _coerce_items(items) if entry]
        if not normalized:
            return
        groups.append(
            {
                "title": str(title).strip() if title else None,
                "items": normalized,
            }
        )

    if isinstance(value, dict):
        for key, items in value.items():
            add_group(str(key), items)
        return groups

    if isinstance(value, (list, tuple, set)):
        # Check if all entries are simple strings (not dicts)
        all_simple = all(not isinstance(entry, dict) for entry in value)

        if all_simple:
            # Create a single group with all items
            add_group(None, list(value))
        else:
            # Mixed content: process each entry separately
            for entry in value:
                if isinstance(entry, dict):
                    for key, items in entry.items():
                        add_group(str(key), items)
                else:
                    add_group(None, entry)
        return groups

    add_group(None, value)
    return groups


def render_markdown_content(data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of the resume data with Markdown transformed to HTML."""
    cloned = copy.deepcopy(data)
    _transform_from_markdown(cloned)
    cloned["expertise_groups"] = format_skill_groups(cloned.get("expertise"))
    cloned["programming_groups"] = format_skill_groups(cloned.get("programming"))
    cloned["keyskills_groups"] = format_skill_groups(cloned.get("keyskills"))
    cloned["certification_groups"] = format_skill_groups(cloned.get("certification"))
    return cloned


def _transform_from_markdown(data: dict[str, Any]) -> None:
    """Convert Markdown fields in a resume data dictionary to HTML in-place."""
    # Markdown extensions for enhanced formatting
    extensions = [
        "fenced_code",  # For ```code blocks
        "tables",  # For pipe tables
        "codehilite",  # For syntax highlighting
        "nl2br",  # Convert newlines to breaks
        "attr_list",  # For attributes on elements
    ]

    if "description" in data:
        data["description"] = markdown(data["description"], extensions=extensions)

    if "body" in data:
        for block_data in data["body"].values():
            for element in block_data:
                if "description" in element:
                    element["description"] = markdown(
                        element["description"], extensions=extensions
                    )


def calculate_text_color(background_color: str) -> str:
    """Calculate appropriate text color for given background color.

    Args:
        background_color: Background color as hex string (e.g., "#FF0000")

    Returns:
        Text color as hex string that provides good contrast

    """
    return _get_contrasting_text_color(background_color)


def calculate_luminance(hex_color: str) -> float:
    """Calculate relative luminance of a hex color.

    Args:
        hex_color: Color as hex string (e.g., "#FF0000")

    Returns:
        Relative luminance value between 0.0 and 1.0

    """
    rgb = _hex_to_rgb(hex_color)
    return _calculate_luminance(rgb)


def get_content(
    name: str = "",
    *,
    paths: Paths | None = None,
    transform_markdown: bool = True,
) -> dict[str, Any]:
    """Read and parse a resume from a YAML file.

    Args:
        name: Resume identifier without extension.
        paths: Optional set of resolved content/input/output paths.
        transform_markdown: When True (default), convert Markdown fields to HTML.

    Returns:
        Parsed resume data dictionary.

    """
    from .hydration import hydrate_resume_data, load_resume_yaml  # noqa: PLC0415

    raw_data, filename, _ = load_resume_yaml(name, paths=paths)
    hydrated = hydrate_resume_data(
        raw_data,
        filename=filename,
        transform_markdown=transform_markdown,
    )
    return hydrated
