"""Centralize constants and enums for Simple-Resume.

This module centralizes magic strings and constant values used throughout the codebase.
"""

from __future__ import annotations

from enum import Enum
from typing import Final


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
        """Convert arbitrary input into an `OutputFormat` enum member.

        Args:
            value: Input string or `OutputFormat` value.
            param_name: Optional name for error reporting.

        Returns:
            `OutputFormat` enum member.

        Raises:
            `ValueError`: If the value cannot be converted to a supported format.
            `TypeError`: If value is neither a string nor `OutputFormat`.

        """
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise TypeError(
                f"Output format must be provided as string or OutputFormat, "
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


# Exit codes
EXIT_SUCCESS: Final[int] = 0
EXIT_FAILURE: Final[int] = 1
EXIT_KEYBOARD_INTERRUPT: Final[int] = 130

# File extensions
YAML_EXTENSIONS: Final[tuple[str, ...]] = (".yaml", ".yml")
PDF_EXTENSION: Final[str] = ".pdf"
HTML_EXTENSION: Final[str] = ".html"
TEX_EXTENSION: Final[str] = ".tex"

# Default values
DEFAULT_FORMAT: Final[str] = OutputFormat.PDF.value
DEFAULT_TEMPLATE: Final[str] = TemplateType.NO_BARS.value
DEFAULT_PAGE_WIDTH_MM: Final[float] = 210.0
DEFAULT_PAGE_HEIGHT_MM: Final[float] = 297.0

# Configuration
MIN_FILENAME_PARTS: Final[int] = 2
ALLOWED_PATH_OVERRIDES: Final[set[str]] = {"content_dir", "templates_dir", "static_dir"}

# Validation
MAX_FILE_SIZE_MB: Final[int] = 50
SUPPORTED_FORMATS: Final[set[str]] = OutputFormat.values()
SUPPORTED_TEMPLATES: Final[set[str]] = TemplateType.values()
