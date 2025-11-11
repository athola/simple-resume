"""Provide internal helpers for advanced integrations.

These objects are *not* covered by the public stability guarantee. They exist
to allow power users to keep importing functionality that previously leaked from the
public namespace while we migrate toward a curated API surface. Expect breaking
changes between releases.
"""

from __future__ import annotations

from ..api.colors import calculate_luminance, calculate_text_color
from ..utilities import (
    get_content,
    normalize_config,
    render_markdown_content,
    validate_config,
)

__all__ = [
    "calculate_luminance",
    "calculate_text_color",
    "get_content",
    "normalize_config",
    "render_markdown_content",
    "validate_config",
]
