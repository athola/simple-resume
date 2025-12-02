"""Pure helpers for transforming resume Markdown into HTML."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any

from markdown import markdown

from simple_resume.core.colors import darken_color, is_valid_color
from simple_resume.core.constants.colors import (
    BOLD_DARKEN_FACTOR,
    DEFAULT_BOLD_COLOR,
    DEFAULT_COLOR_SCHEME,
)
from simple_resume.core.hydration import build_skill_group_payload


def derive_bold_color(frame_color: str | None) -> str:
    """Return a darkened color for bold text."""
    if isinstance(frame_color, str) and is_valid_color(frame_color):
        return darken_color(frame_color, BOLD_DARKEN_FACTOR)
    return DEFAULT_COLOR_SCHEME.get("bold_color", DEFAULT_BOLD_COLOR)


def _apply_bold_color(html: str, color: str, font_weight: int = 600) -> str:
    """Apply color styling to `<strong>` tags in an HTML string."""
    if not html or "<strong" not in html:
        return html

    strong_style = f"color: {color}; font-weight: {font_weight} !important;"
    replacements = {
        "<strong>": f'<strong class="markdown-strong" style="{strong_style}">',
        "<strong >": f'<strong class="markdown-strong" style="{strong_style}">',
    }
    for needle, replacement in replacements.items():
        html = html.replace(needle, replacement)
    return html


def transform_markdown_blocks(
    data: dict[str, Any],
    *,
    bold_color: str = DEFAULT_BOLD_COLOR,
    bold_font_weight: int = 600,
) -> None:
    """Convert Markdown fields in-place."""
    extensions = [
        "fenced_code",
        "tables",
        "codehilite",
        "nl2br",
        "attr_list",
    ]

    description = data.get("description")
    if isinstance(description, str):
        data["description"] = _apply_bold_color(
            markdown(description, extensions=extensions),
            bold_color,
            bold_font_weight,
        )

    body = data.get("body")
    if isinstance(body, dict):
        for block_data in body.values():
            for element in block_data:
                if isinstance(element, dict):
                    desc = element.get("description")
                    if isinstance(desc, str):
                        element["description"] = _apply_bold_color(
                            markdown(desc, extensions=extensions),
                            bold_color,
                            bold_font_weight,
                        )


def _determine_bold_color(config: Mapping[str, Any] | None) -> str:
    """Derive the effective bold color from configuration data."""
    if not config:
        return DEFAULT_COLOR_SCHEME.get("bold_color", DEFAULT_BOLD_COLOR)

    # First check for explicit bold_color
    bold_color = config.get("bold_color")
    if isinstance(bold_color, str) and is_valid_color(bold_color):
        return bold_color

    # Fall back to frame_color (use directly, not derived)
    frame_color = config.get("frame_color")
    if isinstance(frame_color, str) and is_valid_color(frame_color):
        return frame_color

    # Check other color candidates
    color_candidates = [
        config.get("heading_icon_color"),
        config.get("theme_color"),
    ]
    for candidate in color_candidates:
        if isinstance(candidate, str) and is_valid_color(candidate):
            return candidate

    return DEFAULT_COLOR_SCHEME.get("bold_color", DEFAULT_BOLD_COLOR)


def render_markdown_content(resume_data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of resume data with Markdown converted to HTML."""
    transformed_resume = copy.deepcopy(resume_data)

    config = transformed_resume.get("config")
    bold_color = _determine_bold_color(config if isinstance(config, Mapping) else None)
    bold_font_weight = 600  # default
    if isinstance(config, Mapping):
        bold_font_weight = int(config.get("bold_font_weight", 600))

    transform_markdown_blocks(
        transformed_resume, bold_color=bold_color, bold_font_weight=bold_font_weight
    )
    transformed_resume.update(build_skill_group_payload(transformed_resume))
    return transformed_resume


__all__ = [
    "derive_bold_color",
    "render_markdown_content",
    "transform_markdown_blocks",
]
