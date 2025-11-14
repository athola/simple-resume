"""Provide pure configuration normalization helpers."""

from __future__ import annotations

from itertools import cycle
from typing import Any

from simple_resume.constants import (
    BOLD_DARKEN_FACTOR,
    CONFIG_COLOR_FIELDS,
    CONFIG_DIRECT_COLOR_KEYS,
    DEFAULT_BOLD_COLOR,
    DEFAULT_COLOR_SCHEME,
)
from simple_resume.palettes.common import PaletteSource
from simple_resume.palettes.exceptions import (
    PaletteError,
    PaletteGenerationError,
    PaletteLookupError,
)
from simple_resume.palettes.generators import generate_hcl_palette
from simple_resume.palettes.registry import get_palette_registry
from simple_resume.palettes.sources import ColourLoversClient

from .color_service import ColorCalculationService
from .colors import darken_color, get_contrasting_text_color, is_valid_color


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
    for field in CONFIG_COLOR_FIELDS:
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
    config["sidebar_text_color"] = ColorCalculationService.calculate_sidebar_text_color(
        config
    )


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

    config["sidebar_bold_color"] = ColorCalculationService.calculate_sidebar_bold_color(
        config
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

    config["heading_icon_color"] = ColorCalculationService.calculate_heading_icon_color(
        config
    )
    config["sidebar_icon_color"] = ColorCalculationService.calculate_sidebar_icon_color(
        config
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


# ============================================================================
# Configuration Processing (Consolidated from configuration_processor.py)
# ============================================================================


def _is_direct_color_block(block: dict[str, Any]) -> bool:
    """Check if block contains direct color definitions (not palette config)."""
    if not isinstance(block, dict):
        return False

    has_direct_colors = any(field in block for field in CONFIG_DIRECT_COLOR_KEYS)
    palette_block_keys = {
        "source",
        "name",
        "colors",
        "size",
        "seed",
        "hue_range",
        "luminance_range",
        "chroma",
        "keywords",
        "num_results",
        "order_by",
    }
    has_palette_config = any(key in block for key in palette_block_keys)
    return has_direct_colors and not has_palette_config


def _process_direct_colors(
    config: dict[str, Any],
    block: dict[str, Any],
) -> dict[str, Any] | None:
    """Process direct color definitions by merging into config."""
    # Direct color definitions: merge into config directly
    for field in CONFIG_DIRECT_COLOR_KEYS:
        if field in block:
            config[field] = block[field]

    # Automatically calculate sidebar text color based on sidebar background
    if config.get("sidebar_color"):
        config["sidebar_text_color"] = get_contrasting_text_color(
            config["sidebar_color"]
        )

    # Return metadata indicating a direct color definition
    return {
        "source": "direct",
        "fields": [f for f in CONFIG_DIRECT_COLOR_KEYS if f in block],
    }


def _resolve_palette_block(block: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    """Resolve palette block to color swatches and metadata."""
    RANGE_LENGTH = 2  # Moved from utilities.py

    try:
        source = PaletteSource.normalize(block.get("source"), param_name="palette")
    except (TypeError, ValueError) as exc:
        raise PaletteLookupError(
            f"Unsupported palette source: {block.get('source')}"
        ) from exc

    if source is PaletteSource.REGISTRY:
        name = block.get("name")
        if not name:
            raise PaletteLookupError("registry source requires 'name'")
        registry = get_palette_registry()
        palette = registry.get(str(name))
        metadata = {
            "source": source.value,
            "name": palette.name,
            "size": len(palette.swatches),
            "attribution": palette.metadata,
        }
        return list(palette.swatches), metadata

    if source is PaletteSource.GENERATOR:
        size = int(block.get("size", len(CONFIG_COLOR_FIELDS)))
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
            "source": source.value,
            "size": len(swatches),
            "seed": int(seed) if seed is not None else None,
            "hue_range": [float(hue_range[0]), float(hue_range[1])],
            "luminance_range": [float(luminance_range[0]), float(luminance_range[1])],
            "chroma": chroma,
        }
        return swatches, metadata

    if source is PaletteSource.REMOTE:
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
            "source": source.value,
            "name": palette.name,
            "attribution": palette.metadata,
            "size": len(palette.swatches),
        }
        return list(palette.swatches), metadata

    raise PaletteLookupError(f"Unsupported palette source: {source.value}")


def _process_palette_colors(
    config: dict[str, Any],
    block: dict[str, Any],
) -> dict[str, Any] | None:
    """Process palette block by resolving colors and applying to config."""
    try:
        swatches, palette_meta = _resolve_palette_block(block)
    except PaletteError:
        raise
    except (TypeError, ValueError, KeyError, AttributeError) as exc:
        # Common errors when palette configuration is malformed
        raise PaletteError(f"Invalid palette block: {exc}") from exc

    if not swatches:
        return None

    # Cycle through swatches to cover all required fields
    iterator = cycle(swatches)
    for field in CONFIG_COLOR_FIELDS:
        if field not in config or not config[field]:
            config[field] = next(iterator)

    # Automatically calculate sidebar text color based on sidebar background
    if config.get("sidebar_color"):
        config["sidebar_text_color"] = get_contrasting_text_color(
            config["sidebar_color"]
        )

    # Set color scheme name if provided
    if "color_scheme" not in config and "name" in block:
        config["color_scheme"] = str(block["name"])

    return palette_meta


def apply_palette_block(config: dict[str, Any]) -> dict[str, Any] | None:
    """Apply a palette block to the configuration using simplified logic."""
    block = config.get("palette")
    if not isinstance(block, dict):
        return None

    # Simple conditional logic instead of complex Strategy pattern
    if _is_direct_color_block(block):
        return _process_direct_colors(config, block)
    else:
        return _process_palette_colors(config, block)


__all__ = [
    "CONFIG_COLOR_FIELDS",
    "DEFAULT_BOLD_COLOR",
    "DEFAULT_COLOR_SCHEME",
    "CONFIG_DIRECT_COLOR_KEYS",
    "apply_palette_block",
    "finalize_config",
    "prepare_config",
    "_resolve_palette_block",
]
