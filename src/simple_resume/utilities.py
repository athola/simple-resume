#!/usr/bin/env python3
"""Load and validate resume data from YAML files."""

from __future__ import annotations

import copy
import importlib
import os
from pathlib import Path
from typing import Any, Protocol, cast

from markdown import markdown

from simple_resume.constants import (
    BOLD_DARKEN_FACTOR,
    DEFAULT_BOLD_COLOR,
    DEFAULT_COLOR_SCHEME,
)

from . import config as config_module
from .config import FILE_DEFAULT, Paths
from .core.colors import darken_color, is_valid_color
from .core.config_core import apply_palette_block, finalize_config, prepare_config
from .core.hydration_core import build_skill_group_payload
from .utils.io import read_yaml_file
from .utils.skills import format_skill_groups

PATH_DATA = str(config_module.PATH_DATA)
PATH_INPUT = str(config_module.PATH_INPUT)
PATH_OUTPUT = str(config_module.PATH_OUTPUT)


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
    """Darken the frame color for bold text."""
    if isinstance(frame_color, str) and is_valid_color(frame_color):
        return darken_color(frame_color, BOLD_DARKEN_FACTOR)
    return DEFAULT_COLOR_SCHEME.get("bold_color", DEFAULT_BOLD_COLOR)


def normalize_config(
    raw_config: dict[str, Any], filename: str = ""
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Return a normalized copy of the config and optional palette metadata."""
    working = copy.deepcopy(raw_config)
    sidebar_locked = prepare_config(working, filename=filename)
    palette_meta = apply_palette_block(working)
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

    content = read_yaml_file(path)

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
