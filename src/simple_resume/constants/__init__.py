"""Centralized constants for simple-resume.

This package splits the legacy monolithic constants module into domain-specific
submodules. Importing from ``simple_resume.constants`` remains backwards
compatible because the key symbols are re-exported from this package.
"""

from __future__ import annotations

from enum import Enum
from typing import Final

from .colors import (
    BOLD_DARKEN_FACTOR,
    COLOR_FIELD_ORDER,
    CONFIG_COLOR_FIELDS,
    CONFIG_DIRECT_COLOR_KEYS,
    DEFAULT_BOLD_COLOR,
    DEFAULT_COLOR_SCHEME,
    DIRECT_COLOR_KEYS,
    HEX_COLOR_FULL_LENGTH,
    HEX_COLOR_SHORT_LENGTH,
    ICON_CONTRAST_THRESHOLD,
    LUMINANCE_DARK,
    LUMINANCE_VERY_DARK,
    LUMINANCE_VERY_LIGHT,
    SIDEBAR_BOLD_DARKEN_FACTOR,
    WCAG_LINEARIZATION_DIVISOR,
    WCAG_LINEARIZATION_EXPONENT,
    WCAG_LINEARIZATION_OFFSET,
    WCAG_LINEARIZATION_THRESHOLD,
)
from .files import (
    BYTES_PER_KB,
    BYTES_PER_MB,
    DEFAULT_LATEX_TEMPLATE,
    FONTAWESOME_DEFAULT_SCALE,
    SUPPORTED_YAML_EXTENSIONS,
    SUPPORTED_YAML_EXTENSIONS_STR,
)
from .layout import (
    DEFAULT_COVER_PADDING_BOTTOM,
    DEFAULT_COVER_PADDING_HORIZONTAL,
    DEFAULT_COVER_PADDING_TOP,
    DEFAULT_FRAME_PADDING,
    DEFAULT_PADDING,
    DEFAULT_PAGE_HEIGHT_MM,
    DEFAULT_PAGE_WIDTH_MM,
    DEFAULT_SIDEBAR_PADDING,
    DEFAULT_SIDEBAR_PADDING_ADJUSTMENT,
    DEFAULT_SIDEBAR_WIDTH_MM,
    MAX_PADDING,
    MAX_PAGE_HEIGHT_MM,
    MAX_PAGE_WIDTH_MM,
    MAX_SIDEBAR_WIDTH_MM,
    MIN_PADDING,
    MIN_PAGE_HEIGHT_MM,
    MIN_PAGE_WIDTH_MM,
    MIN_SIDEBAR_WIDTH_MM,
)

# =============================================================================
# CLI Exit Codes
# =============================================================================

EXIT_SUCCESS: Final[int] = 0
EXIT_SIGINT: Final[int] = 130  # Ctrl+C cancellation
EXIT_FILE_SYSTEM_ERROR: Final[int] = 2
EXIT_INTERNAL_ERROR: Final[int] = 3
EXIT_RESOURCE_ERROR: Final[int] = 4
EXIT_INPUT_ERROR: Final[int] = 5
EXIT_GENERIC_ERROR: Final[int] = 1

# =============================================================================
# Error Messages
# =============================================================================

ERROR_UNKNOWN_COMMAND: Final[str] = "Unknown command"
ERROR_FILE_NOT_FOUND: Final[str] = "Resume file not found"
ERROR_INVALID_FORMAT: Final[str] = "Invalid format"
ERROR_PERMISSION_DENIED: Final[str] = "Permission denied"

# =============================================================================
# Process and Resource Limits
# =============================================================================

DEFAULT_PROCESS_TIMEOUT_SECONDS: Final[int] = 30
MAX_RESUME_SIZE_MB: Final[int] = 10
MAX_PALETTE_SIZE_MB: Final[int] = 1


class OutputFormat(str, Enum):
    """Define supported output formats for resume generation."""

    PDF = "pdf"
    HTML = "html"
    LATEX = "latex"

    @classmethod
    def values(cls) -> set[str]:
        """Return a set of all format values."""
        return {cls.PDF.value, cls.HTML.value, cls.LATEX.value}

    @classmethod
    def is_valid(cls, format_str: str) -> bool:
        """Check if a format string is valid."""
        return format_str.lower() in cls.values()

    @classmethod
    def normalize(
        cls, value: str | OutputFormat, *, param_name: str | None = None
    ) -> OutputFormat:
        """Convert arbitrary input into an `OutputFormat` enum member."""
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise TypeError(
                "Output format must be provided as string or OutputFormat, "
                f"got {type(value)}"
            )

        normalized = value.strip().lower()
        try:
            return cls(normalized)
        except ValueError as exc:  # pragma: no cover - defensive path
            label = f"{param_name} " if param_name else ""
            raise ValueError(
                f"Unsupported {label}format: {value}. "
                f"Supported formats: {', '.join(sorted(cls.values()))}"
            ) from exc


class TemplateType(str, Enum):
    """Define available resume templates."""

    NO_BARS = "resume_no_bars"
    WITH_BARS = "resume_with_bars"

    @classmethod
    def values(cls) -> set[str]:
        """Return a set of all template values."""
        return {cls.NO_BARS.value, cls.WITH_BARS.value}

    @classmethod
    def is_valid(cls, template_str: str) -> bool:
        """Check if a template string is valid."""
        return template_str in cls.values()


class RenderMode(str, Enum):
    """Define rendering modes for resume generation."""

    HTML = "html"
    LATEX = "latex"


# Additional file extensions (consolidated with earlier definitions)
PDF_EXTENSION: Final[str] = ".pdf"
HTML_EXTENSION: Final[str] = ".html"
TEX_EXTENSION: Final[str] = ".tex"

# Default values
DEFAULT_FORMAT: Final[str] = OutputFormat.PDF.value
DEFAULT_TEMPLATE: Final[str] = TemplateType.NO_BARS.value

# Configuration
MIN_FILENAME_PARTS: Final[int] = 2
ALLOWED_PATH_OVERRIDES: Final[set[str]] = {"content_dir", "templates_dir", "static_dir"}

# Validation
MAX_FILE_SIZE_MB: Final[int] = 50
SUPPORTED_FORMATS: Final[set[str]] = OutputFormat.values()
SUPPORTED_TEMPLATES: Final[set[str]] = TemplateType.values()


__all__ = [
    # General/global constants
    "EXIT_SUCCESS",
    "EXIT_SIGINT",
    "EXIT_FILE_SYSTEM_ERROR",
    "EXIT_INTERNAL_ERROR",
    "EXIT_RESOURCE_ERROR",
    "EXIT_INPUT_ERROR",
    "EXIT_GENERIC_ERROR",
    "ERROR_UNKNOWN_COMMAND",
    "ERROR_FILE_NOT_FOUND",
    "ERROR_INVALID_FORMAT",
    "ERROR_PERMISSION_DENIED",
    "DEFAULT_PROCESS_TIMEOUT_SECONDS",
    "MAX_RESUME_SIZE_MB",
    "MAX_PALETTE_SIZE_MB",
    "PDF_EXTENSION",
    "HTML_EXTENSION",
    "TEX_EXTENSION",
    "DEFAULT_FORMAT",
    "DEFAULT_TEMPLATE",
    "MIN_FILENAME_PARTS",
    "ALLOWED_PATH_OVERRIDES",
    "MAX_FILE_SIZE_MB",
    "SUPPORTED_FORMATS",
    "SUPPORTED_TEMPLATES",
    "OutputFormat",
    "TemplateType",
    "RenderMode",
    # Re-exported layout constants
    "DEFAULT_PAGE_WIDTH_MM",
    "DEFAULT_PAGE_HEIGHT_MM",
    "DEFAULT_SIDEBAR_WIDTH_MM",
    "DEFAULT_PADDING",
    "DEFAULT_SIDEBAR_PADDING_ADJUSTMENT",
    "DEFAULT_SIDEBAR_PADDING",
    "DEFAULT_FRAME_PADDING",
    "DEFAULT_COVER_PADDING_TOP",
    "DEFAULT_COVER_PADDING_BOTTOM",
    "DEFAULT_COVER_PADDING_HORIZONTAL",
    "MIN_PAGE_WIDTH_MM",
    "MAX_PAGE_WIDTH_MM",
    "MIN_PAGE_HEIGHT_MM",
    "MAX_PAGE_HEIGHT_MM",
    "MIN_SIDEBAR_WIDTH_MM",
    "MAX_SIDEBAR_WIDTH_MM",
    "MIN_PADDING",
    "MAX_PADDING",
    # Re-exported file constants
    "SUPPORTED_YAML_EXTENSIONS",
    "SUPPORTED_YAML_EXTENSIONS_STR",
    "DEFAULT_LATEX_TEMPLATE",
    "FONTAWESOME_DEFAULT_SCALE",
    "BYTES_PER_KB",
    "BYTES_PER_MB",
    # Re-exported color constants
    "DEFAULT_COLOR_SCHEME",
    "WCAG_LINEARIZATION_THRESHOLD",
    "WCAG_LINEARIZATION_DIVISOR",
    "WCAG_LINEARIZATION_EXPONENT",
    "WCAG_LINEARIZATION_OFFSET",
    "BOLD_DARKEN_FACTOR",
    "SIDEBAR_BOLD_DARKEN_FACTOR",
    "LUMINANCE_VERY_DARK",
    "LUMINANCE_DARK",
    "LUMINANCE_VERY_LIGHT",
    "ICON_CONTRAST_THRESHOLD",
    "HEX_COLOR_SHORT_LENGTH",
    "HEX_COLOR_FULL_LENGTH",
    "DEFAULT_BOLD_COLOR",
    "COLOR_FIELD_ORDER",
    "DIRECT_COLOR_KEYS",
    "CONFIG_COLOR_FIELDS",
    "CONFIG_DIRECT_COLOR_KEYS",
]
