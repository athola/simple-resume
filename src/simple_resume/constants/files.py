"""Filesystem and file-format constants for simple-resume."""

from __future__ import annotations

from typing import Final

# Supported file extensions
SUPPORTED_YAML_EXTENSIONS: Final[set[str]] = {".yaml", ".yml"}
SUPPORTED_YAML_EXTENSIONS_STR: Final[str] = "yaml"  # For CLI usage

# Default template paths
DEFAULT_LATEX_TEMPLATE: Final[str] = "latex/basic.tex"

# Font scaling constants
FONTAWESOME_DEFAULT_SCALE: Final[float] = 0.72

# Byte conversion constants
BYTES_PER_KB: Final[int] = 1024
BYTES_PER_MB: Final[int] = 1024 * 1024

__all__ = [
    "SUPPORTED_YAML_EXTENSIONS",
    "SUPPORTED_YAML_EXTENSIONS_STR",
    "DEFAULT_LATEX_TEMPLATE",
    "FONTAWESOME_DEFAULT_SCALE",
    "BYTES_PER_KB",
    "BYTES_PER_MB",
]
