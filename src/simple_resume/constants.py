"""Constants and enums for Simple-Resume.

This module centralizes magic strings and constant values used throughout the codebase.
"""

from enum import Enum
from typing import Final


class OutputFormat(str, Enum):
    """Supported output formats for resume generation."""

    PDF = "pdf"
    HTML = "html"
    LATEX = "latex"

    @classmethod
    def values(cls) -> set[str]:
        """Return set of all format values."""
        return {cls.PDF.value, cls.HTML.value, cls.LATEX.value}

    @classmethod
    def is_valid(cls, format_str: str) -> bool:
        """Check if format string is valid."""
        return format_str.lower() in cls.values()


class TemplateType(str, Enum):
    """Available resume templates."""

    NO_BARS = "resume_no_bars"
    WITH_BARS = "resume_with_bars"

    @classmethod
    def values(cls) -> set[str]:
        """Return set of all template values."""
        return {cls.NO_BARS.value, cls.WITH_BARS.value}

    @classmethod
    def is_valid(cls, template_str: str) -> bool:
        """Check if template string is valid."""
        return template_str in cls.values()


class RenderMode(str, Enum):
    """Rendering modes for resume generation."""

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
