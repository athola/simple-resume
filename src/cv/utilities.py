#!/usr/bin/env python3
"""Load data from YAML files as ordered dicts."""

from typing import Any

from markdown import markdown
from oyaml import safe_load

from .config import FILE_DEFAULT
from .config import PATH_INPUT as CONFIG_PATH_INPUT

PATH_INPUT: str = CONFIG_PATH_INPUT

__all__ = [
    "FILE_DEFAULT",
    "PATH_INPUT",
    "get_content",
]


def _read_yaml(uri: str) -> dict[str, Any]:
    """Auxilary function to read a yaml file."""
    with open(uri, encoding="utf-8") as file:
        content = safe_load(file)
        return content if content is not None else {}


def _transform_from_markdown(data: dict[str, Any]) -> None:
    """Transform markdown text to html with support for code blocks and tables."""
    # Markdown extensions for enhanced formatting
    extensions = [
        "fenced_code",  # For ```code blocks
        "tables",  # For pipe tables
        "codehilite",  # For syntax highlighting
        "nl2br",  # Convert newlines to breaks
        "attr_list",  # For attributes on elements
    ]

    # Main description of CV
    if "description" in data:
        data["description"] = markdown(data["description"], extensions=extensions)

    # Descriptions in body
    if "body" in data:
        for block_data in data["body"].values():
            for element in block_data:
                if "description" in element:
                    element["description"] = markdown(
                        element["description"], extensions=extensions
                    )


def get_content(name: str = "") -> dict[str, Any]:
    """Return content of the CV."""
    if not name:
        name = FILE_DEFAULT

    split_name = name.split(".")
    if split_name:
        name = split_name[0]

    # Read data
    out = _read_yaml(f"{PATH_INPUT}{name}.yaml")
    _transform_from_markdown(out)

    return out
