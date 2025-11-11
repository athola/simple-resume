#!/usr/bin/env python3
"""Load and validate resume data from YAML files."""

from __future__ import annotations

import copy
import importlib
import os
from itertools import cycle
from pathlib import Path
from typing import Any, Protocol, cast

from markdown import markdown
from oyaml import safe_load

from . import config as config_module
from .config import FILE_DEFAULT, Paths
from .core.color_utils import darken_color, get_contrasting_text_color, is_valid_color
from .core.config_core import (
    BOLD_DARKEN_FACTOR,
    COLOR_FIELD_ORDER,
    DEFAULT_BOLD_COLOR,
    DEFAULT_COLOR_SCHEME,
    DIRECT_COLOR_KEYS,
    finalize_config,
    prepare_config,
)
from .core.hydration_core import build_skill_group_payload
from .palettes.common import PaletteSource
from .palettes.exceptions import (
    PaletteError,
    PaletteGenerationError,
    PaletteLookupError,
)
from .palettes.generators import generate_hcl_palette
from .palettes.registry import get_palette_registry
from .palettes.sources import ColourLoversClient
from .skill_utils import format_skill_groups

PATH_DATA = str(config_module.PATH_DATA)
PATH_INPUT = str(config_module.PATH_INPUT)
PATH_OUTPUT = str(config_module.PATH_OUTPUT)

# Color constants
HEX_COLOR_SHORT_LENGTH = 3
HEX_COLOR_FULL_LENGTH = 6

# WCAG 2.1 relative luminance constants (see
# https://www.w3.org/TR/WCAG21/#dfn-relative-luminance). These values are used to
# linearize sRGB inputs before applying the standard luminance weights.
LINEARIZATION_THRESHOLD = 0.03928
LINEARIZATION_DIVISOR = 12.92
LINEARIZATION_EXPONENT = 2.4
LINEARIZATION_OFFSET = 0.055

# Empirical luminance buckets—derived from the WCAG contrast guidance—to decide
# which text color offers sufficient readability for a given background.
VERY_DARK_THRESHOLD = 0.15
DARK_THRESHOLD = 0.5
VERY_LIGHT_THRESHOLD = 0.8
ICON_CONTRAST_THRESHOLD = 3.0

# Color generation constants
RANGE_LENGTH = 2

__all__ = [
    "FILE_DEFAULT",
    "PATH_DATA",
    "PATH_INPUT",
    "PATH_OUTPUT",
    "DEFAULT_COLOR_SCHEME",
    "normalize_config",
    "get_content",
    "validate_config",
    "render_markdown_content",
    "apply_external_palette",
    "load_palette_from_file",
    "derive_bold_color",
    "format_skill_groups",
]


class _HydrationModule(Protocol):
    """Define a protocol for hydration module functions."""

    def load_resume_yaml(
        self,
        name: str | os.PathLike[str] = "",
        *,
        paths: Paths | None = None,
    ) -> tuple[dict[str, Any], str, Paths]: ...

    def hydrate_resume_data(
        self,
        source_yaml: dict[str, Any],
        *,
        filename: str = "",
        transform_markdown: bool = True,
    ) -> dict[str, Any]: ...


def derive_bold_color(frame_color: str | None) -> str:
    """Return a darkened variant of the frame color for bold emphasis."""
    if isinstance(frame_color, str) and is_valid_color(frame_color):
        return darken_color(frame_color, BOLD_DARKEN_FACTOR)
    return DEFAULT_COLOR_SCHEME.get("bold_color", DEFAULT_BOLD_COLOR)


def _read_yaml(uri: str | Path) -> dict[str, Any]:
    """Read a YAML file and return its content as a dictionary.

    Raises:
        `ValueError`: If the YAML file does not contain a dictionary at the root level.

    """
    path = Path(uri)
    with open(str(path), encoding="utf-8") as file:
        content = safe_load(file)

    if content is None:
        return {}

    if not isinstance(content, dict):
        raise ValueError(
            f"YAML file must contain a dictionary at the root level, "
            f"but found {type(content).__name__}: {path}"
        )

    return content


def normalize_config(
    raw_config: dict[str, Any], filename: str = ""
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Return a normalized copy of the config and optional palette metadata."""
    working = copy.deepcopy(raw_config)
    sidebar_locked = prepare_config(working, filename=filename)
    palette_meta = _apply_palette_block(working)
    finalize_config(
        working,
        filename=filename,
        sidebar_text_locked=sidebar_locked,
    )
    return working, palette_meta


def load_palette_from_file(palette_file: str | Path) -> dict[str, Any]:
    """Load and return palette configuration from an external YAML file."""
    path = Path(palette_file)

    if not path.exists():
        raise FileNotFoundError(f"Palette file not found: {path}")

    if path.suffix.lower() not in {".yaml", ".yml"}:
        raise ValueError("Palette file must be a YAML file")

    content = _read_yaml(path)

    palette_data: Any = content.get("palette", content)

    # Support palette files that wrap color settings under a `config` block
    # (common in legacy palette snippets and alternate format specs).
    if isinstance(palette_data, dict) and "config" in palette_data:
        config_block = palette_data["config"]
        if isinstance(config_block, dict):
            nested_palette = config_block.get("palette")
            if isinstance(nested_palette, dict):
                palette_data = nested_palette
            else:
                palette_data = config_block

    if not isinstance(palette_data, dict):
        raise ValueError("Palette configuration must be a dictionary")

    return {"palette": copy.deepcopy(palette_data)}


def apply_external_palette(
    config: dict[str, Any], palette_file: str | Path
) -> dict[str, Any]:
    """Return a new configuration dictionary with palette data applied."""
    palette_payload = load_palette_from_file(palette_file)
    updated = copy.deepcopy(config)
    updated["palette"] = palette_payload["palette"]
    return updated


def validate_config(config: dict[str, Any], filename: str = "") -> None:
    """Validate resume configuration for common errors (legacy mutating API).

    Args:
        config: Configuration dict from YAML file.
        filename: Name of the file being validated (for error messages).

    Raises:
        `ValueError`: If validation fails with a descriptive error message.

    """
    if not config:
        return  # No config to validate

    normalized, _ = normalize_config(config, filename=filename)
    config.clear()
    config.update(normalized)


def _apply_palette_block(config: dict[str, Any]) -> dict[str, Any] | None:
    """Apply a palette block to the configuration."""
    block = config.get("palette")
    if not isinstance(block, dict):
        return None

    # Check if this is a direct color definition block (contains color field keys)
    # versus a palette block (contains source/name/generator config).
    has_direct_colors = any(field in block for field in DIRECT_COLOR_KEYS)
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

    if has_direct_colors and not has_palette_config:
        # Direct color definitions: merge into config directly.
        for field in DIRECT_COLOR_KEYS:
            if field in block:
                config[field] = block[field]

        # Automatically calculate sidebar text color based on sidebar background.
        if config.get("sidebar_color"):
            config["sidebar_text_color"] = get_contrasting_text_color(
                config["sidebar_color"]
            )

        # Return metadata indicating a direct color definition.
        return {
            "source": "direct",
            "fields": [f for f in DIRECT_COLOR_KEYS if f in block],
        }

    # Otherwise, treat as a palette block requiring resolution.
    try:
        swatches, palette_meta = _resolve_palette_block(block)
    except PaletteError:
        raise
    except (TypeError, ValueError, KeyError, AttributeError) as exc:
        # Common errors when palette configuration is malformed.
        raise PaletteGenerationError(f"Invalid palette block: {exc}") from exc

    if not swatches:
        return None

    # Cycle through swatches to cover all required fields.
    iterator = cycle(swatches)
    for field in COLOR_FIELD_ORDER:
        if field not in config or not config[field]:
            config[field] = next(iterator)

    # Automatically calculate sidebar text color based on sidebar background.
    if config.get("sidebar_color"):
        config["sidebar_text_color"] = get_contrasting_text_color(
            config["sidebar_color"]
        )

    if "color_scheme" not in config and "name" in block:
        config["color_scheme"] = str(block["name"])

    return palette_meta


def _resolve_palette_block(block: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
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


def render_markdown_content(resume_data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of the resume data with Markdown transformed to HTML."""
    transformed_resume = copy.deepcopy(resume_data)

    # Extract palette colors for bold text styling (prefer explicit bold_color)
    config = transformed_resume.get("config", {})
    bold_color = config.get("bold_color")
    if not bold_color:
        bold_color = config.get("frame_color")
    if not bold_color:
        bold_color = config.get("heading_icon_color")
    if not bold_color:
        bold_color = config.get("theme_color", "#0395DE")

    _transform_from_markdown(transformed_resume, bold_color=bold_color)
    transformed_resume.update(build_skill_group_payload(transformed_resume))
    return transformed_resume


def _apply_bold_color(html: str, color: str) -> str:
    """Apply color styling to bold (`<strong>`) tags in HTML.

    Args:
        html: HTML string that may contain `<strong>` tags.
        color: Hex color code to apply (e.g., "#0395DE").

    Returns:
        HTML string with styled `<strong>` tags.

    """
    if not html:
        return html
    strong_style = f"color: {color}; font-weight: 700 !important;"
    replacements = {
        "<strong>": f'<strong class="markdown-strong" style="{strong_style}">',
        "<strong >": f'<strong class="markdown-strong" style="{strong_style}">',
    }
    if "<strong" not in html:
        return html
    for needle, replacement in replacements.items():
        html = html.replace(needle, replacement)
    return html


def _transform_from_markdown(
    data: dict[str, Any], bold_color: str = DEFAULT_BOLD_COLOR
) -> None:
    """Convert Markdown fields in a resume data dictionary to HTML in-place.

    Args:
        data: Resume data dictionary.
        bold_color: Hex color code for bold text (defaults to theme color).

    """
    # Markdown extensions for enhanced formatting.
    extensions = [
        "fenced_code",  # For ```code blocks
        "tables",  # For pipe tables
        "codehilite",  # For syntax highlighting
        "nl2br",  # Convert newlines to breaks
        "attr_list",  # For attributes on elements
    ]

    if "description" in data:
        html = markdown(data["description"], extensions=extensions)
        data["description"] = _apply_bold_color(html, bold_color)

    if "body" in data:
        for block_data in data["body"].values():
            for element in block_data:
                if "description" in element:
                    html = markdown(element["description"], extensions=extensions)
                    element["description"] = _apply_bold_color(html, bold_color)


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
        transform_markdown: When `True` (default), convert Markdown fields to HTML.

    Returns:
        Parsed resume data dictionary.

    """
    hydration_module = cast(
        _HydrationModule,
        importlib.import_module("simple_resume.hydration"),
    )
    raw_data, filename, _ = hydration_module.load_resume_yaml(name, paths=paths)
    hydrated = hydration_module.hydrate_resume_data(
        raw_data,
        filename=filename,
        transform_markdown=transform_markdown,
    )
    return hydrated
