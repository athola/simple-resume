#!/usr/bin/env python3
"""Load and validate resume data from YAML files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from markdown import markdown
from oyaml import safe_load

from . import config as config_module
from .config import FILE_DEFAULT, Paths, resolve_paths

PATH_DATA = str(config_module.PATH_DATA)
PATH_INPUT = str(config_module.PATH_INPUT)
PATH_OUTPUT = str(config_module.PATH_OUTPUT)

__all__ = [
    "FILE_DEFAULT",
    "PATH_DATA",
    "PATH_INPUT",
    "PATH_OUTPUT",
    "get_content",
    "validate_config",
]


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


def validate_config(config: dict[str, Any], filename: str = "") -> None:
    """Validate resume configuration for common errors.

    Args:
        config: Configuration dict from YAML file
        filename: Name of the file being validated (for error messages)

    Raises:
        ValueError: If validation fails with descriptive error message

    """
    if not config:
        return  # No config to validate

    filename_prefix = f"{filename}: " if filename else ""

    # Validate dimensions
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

    # Validate colors
    color_fields = [
        "theme_color",
        "sidebar_color",
        "bar_background_color",
        "date2_color",
        "frame_color",
    ]

    for field in color_fields:
        if field in config:
            color = config[field]
            if not _is_valid_color(color):
                raise ValueError(
                    f"{filename_prefix}Invalid color format for '{field}': {color}. "
                    f"Expected hex color like '#0395DE' or '#FFF'"
                )


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


def get_content(name: str = "", *, paths: Paths | None = None) -> dict[str, Any]:
    """Read and parse a resume from a YAML file."""
    if not name:
        name = FILE_DEFAULT

    split_name = name.split(".")
    if split_name:
        name = split_name[0]

    if paths is None:
        base_paths = resolve_paths()
        resolved_paths = Paths(
            data=Path(PATH_DATA),
            input=Path(PATH_INPUT),
            output=Path(PATH_OUTPUT),
            content=base_paths.content,
            templates=base_paths.templates,
            static=base_paths.static,
        )
    else:
        resolved_paths = paths
    input_path = resolved_paths.input

    # Read data
    out = _read_yaml(input_path / f"{name}.yaml")

    # Validate config if present
    if "config" in out:
        validate_config(out["config"], filename=f"{name}.yaml")

    _transform_from_markdown(out)

    return out
