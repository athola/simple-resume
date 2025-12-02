"""Provide pure configuration normalization helpers."""

from __future__ import annotations

import atexit
import copy
from contextlib import ExitStack
from importlib import resources
from itertools import cycle
from typing import Any, Callable

from simple_resume.core.colors import (
    ColorCalculationService,
    darken_color,
    get_contrasting_text_color,
    is_valid_color,
)
from simple_resume.core.constants.colors import (
    BOLD_DARKEN_FACTOR,
    CONFIG_COLOR_FIELDS,
    CONFIG_DIRECT_COLOR_KEYS,
    DEFAULT_BOLD_COLOR,
    DEFAULT_COLOR_SCHEME,
)
from simple_resume.core.palettes import resolve_palette_config
from simple_resume.core.palettes.exceptions import (
    PaletteError,
    PaletteLookupError,
)
from simple_resume.core.palettes.fetch_types import PaletteFetchRequest
from simple_resume.core.palettes.registry import PaletteRegistry

# Keep an open handle to package resources so they're available even when the
# distribution is zipped (e.g., installed from a wheel).
_asset_stack = ExitStack()
PACKAGE_ROOT = _asset_stack.enter_context(
    resources.as_file(resources.files("simple_resume"))
)
atexit.register(_asset_stack.close)

PATH_CONTENT = PACKAGE_ROOT
TEMPLATE_LOC = PACKAGE_ROOT / "templates"
STATIC_LOC = PACKAGE_ROOT / "static"


def _coerce_number(value: Any, *, field: str, prefix: str) -> float | int | None:
    """Coerce a value to a number (float or int) or None.

    Args:
        value: The value to coerce.
        field: The name of the field being coerced, for error messages.
        prefix: A prefix for error messages.

    Returns:
        The coerced numeric value, or None if the input is None.

    Raises:
        ValueError: If the value cannot be coerced to a number.

    """
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
    """Apply default padding and font weight settings to the configuration.

    Args:
        config: The configuration dictionary to modify in-place.

    """
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

    # Set default bold font weight
    config.setdefault("bold_font_weight", 600)


def validate_dimensions(config: dict[str, Any], filename_prefix: str) -> None:
    """Validate page and sidebar dimensions in the configuration.

    Ensures that width and height are positive, and sidebar width is less
    than page width.

    Args:
        config: The configuration dictionary containing dimension settings.
        filename_prefix: A prefix for error messages, typically the source filename.

    Raises:
        ValueError: If any dimension is invalid.

    """
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
    """Normalize the 'color_scheme' field in the configuration.

    Ensures 'color_scheme' is a string and defaults to "default" if empty or
    not a string.

    Args:
        config: The configuration dictionary to modify in-place.

    """
    raw_scheme = config.get("color_scheme", "")
    if isinstance(raw_scheme, str):
        config["color_scheme"] = raw_scheme.strip() or "default"
    else:
        config["color_scheme"] = "default"


def _validate_color_fields(config: dict[str, Any], filename_prefix: str) -> None:
    """Validate and set default values for color-related fields in the configuration.

    Args:
        config: The configuration dictionary to modify in-place.
        filename_prefix: A prefix for error messages, typically the source filename.

    Raises:
        ValueError: If a color value is invalid or not a hex string.

    """
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
    """Automatically calculate and set the sidebar text color for contrast.

    Args:
        config: The configuration dictionary to modify in-place.

    """
    config["sidebar_text_color"] = ColorCalculationService.calculate_sidebar_text_color(
        config
    )


def _handle_sidebar_bold_color(config: dict[str, Any], filename_prefix: str) -> None:
    """Handle explicit or automatically calculated sidebar bold color.

    If 'sidebar_bold_color' is explicitly set, validates it.
    Otherwise, calculates it using ColorCalculationService.

    Args:
        config: The configuration dictionary to modify in-place.
        filename_prefix: A prefix for error messages.

    Raises:
        ValueError: If an explicitly set color is invalid.

    """
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
    """Handle explicit or automatically calculated icon colors.

    If 'heading_icon_color' is explicitly set, validates it.
    Otherwise, calculates heading and sidebar icon colors using ColorCalculationService.

    Args:
        config: The configuration dictionary to modify in-place.
        filename_prefix: A prefix for error messages.

    Raises:
        ValueError: If an explicitly set heading icon color is invalid.

    """
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
    """Handle explicit or automatically calculated bold text color.

    If 'bold_color' is explicitly set, validates it.
    Otherwise, derives it from 'frame_color' or uses a default.

    Args:
        config: The configuration dictionary to modify in-place.
        filename_prefix: A prefix for error messages.

    Raises:
        ValueError: If an explicitly set bold color is invalid.

    """
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


def _resolve_palette_block(
    block: dict[str, Any],
    *,
    registry: PaletteRegistry,
    palette_fetcher: Callable[[PaletteFetchRequest], tuple[list[str], dict[str, Any]]]
    | None = None,
) -> tuple[list[str] | None, dict[str, Any]]:
    """Resolve palette block to color swatches and metadata.

    This function uses dependency injection for both registry lookup and
    network operations. The registry is required for local palette lookups.
    If a palette_fetcher is provided, it will be used for remote palettes.

    Args:
        block: Palette configuration block.
        registry: Palette registry for looking up named palettes (required).
        palette_fetcher: Optional callable that executes PaletteFetchRequest.

    Returns:
        Tuple of (colors, metadata).

    Raises:
        PaletteLookupError: If palette cannot be resolved.
        PaletteError: If palette configuration is invalid.

    """
    # Use the new pure resolution system with injected registry
    resolution = resolve_palette_config(block, registry=registry)

    if resolution.has_colors:
        # Local sources (registry, generator) - already have colors
        return resolution.colors, resolution.metadata or {}

    elif resolution.needs_fetch:
        # Remote source - need to execute fetch request via injected dependency
        if palette_fetcher is None:
            raise PaletteLookupError(
                "Remote palette fetching requires palette_fetcher parameter. "
                "Provide a fetch function from the shell layer."
            )

        # Execute the network operation using the injected fetcher
        if resolution.fetch_request is None:
            raise PaletteLookupError(
                "Internal error: fetch_request is None despite needs_fetch being True"
            )
        return palette_fetcher(resolution.fetch_request)

    else:
        raise PaletteLookupError(f"Unable to resolve palette: {block}")


def _process_palette_colors(
    config: dict[str, Any],
    block: dict[str, Any],
    *,
    registry: PaletteRegistry,
    palette_fetcher: Callable[[PaletteFetchRequest], tuple[list[str], dict[str, Any]]]
    | None = None,
) -> dict[str, Any] | None:
    """Process palette block by resolving colors and applying to config."""
    try:
        swatches, palette_meta = _resolve_palette_block(
            block, registry=registry, palette_fetcher=palette_fetcher
        )
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


def apply_palette_block(
    config: dict[str, Any],
    *,
    registry: PaletteRegistry,
    palette_fetcher: Callable[[PaletteFetchRequest], tuple[list[str], dict[str, Any]]]
    | None = None,
) -> dict[str, Any] | None:
    """Apply a palette block to the configuration using simplified logic.

    Args:
        config: Configuration dictionary to modify.
        registry: Palette registry for looking up named palettes (required).
        palette_fetcher: Optional callable to handle remote palette fetching.

    """
    block = config.get("palette")
    if not isinstance(block, dict):
        return None

    # Simple conditional logic instead of complex Strategy pattern
    if _is_direct_color_block(block):
        return _process_direct_colors(config, block)
    else:
        return _process_palette_colors(
            config, block, registry=registry, palette_fetcher=palette_fetcher
        )


def normalize_config(
    raw_config: dict[str, Any],
    filename: str = "",
    *,
    registry: PaletteRegistry,
    palette_fetcher: Callable[[PaletteFetchRequest], tuple[list[str], dict[str, Any]]]
    | None = None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Return a normalized copy of the configuration.

    Args:
        raw_config: Raw configuration dictionary.
        filename: Source filename for error messages.
        registry: Palette registry for looking up named palettes (required).
        palette_fetcher: Optional callable to handle remote palette fetching.

    Returns:
        Tuple of (normalized_config, palette_metadata).

    """
    working = copy.deepcopy(raw_config)
    sidebar_locked = prepare_config(working, filename=filename)
    palette_meta = apply_palette_block(
        working,
        registry=registry,
        palette_fetcher=palette_fetcher,
    )
    finalize_config(
        working,
        filename=filename,
        sidebar_text_locked=sidebar_locked,
    )
    return working, palette_meta


def validate_config(
    config: dict[str, Any],
    filename: str = "",
    *,
    registry: PaletteRegistry,
    palette_fetcher: Callable[[PaletteFetchRequest], tuple[list[str], dict[str, Any]]]
    | None = None,
) -> None:
    """Normalize the configuration in-place if present (pure operation).

    Args:
        config: Configuration dictionary to normalize in-place.
        filename: Source filename for error messages.
        registry: Palette registry for looking up named palettes (required).
        palette_fetcher: Optional callable to handle remote palette fetching.

    """
    if not config:
        return
    normalized, _ = normalize_config(
        config,
        filename=filename,
        registry=registry,
        palette_fetcher=palette_fetcher,
    )
    config.clear()
    config.update(normalized)


__all__ = [
    "CONFIG_COLOR_FIELDS",
    "DEFAULT_BOLD_COLOR",
    "DEFAULT_COLOR_SCHEME",
    "CONFIG_DIRECT_COLOR_KEYS",
    "apply_palette_block",
    "finalize_config",
    "prepare_config",
    "_resolve_palette_block",
    "normalize_config",
    "validate_config",
]
