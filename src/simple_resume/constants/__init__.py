"""Centralized constants for simple-resume.

This package contains core constants and enums for resume generation.
Domain-specific constants are organized in separate submodules.
"""

from __future__ import annotations

from enum import Enum
from typing import Final

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

# =============================================================================
# File Extensions
# =============================================================================

PDF_EXTENSION: Final[str] = ".pdf"
HTML_EXTENSION: Final[str] = ".html"
TEX_EXTENSION: Final[str] = ".tex"

# =============================================================================
# Default Values
# =============================================================================

# Default values will be set after enum definitions
DEFAULT_FORMAT: str
DEFAULT_TEMPLATE: str

# =============================================================================
# Configuration
# =============================================================================

MIN_FILENAME_PARTS: Final[int] = 2
ALLOWED_PATH_OVERRIDES: Final[set[str]] = {"content_dir", "templates_dir", "static_dir"}

# =============================================================================
# Validation
# =============================================================================

MAX_FILE_SIZE_MB: Final[int] = 50


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


# Set defaults using enum values
DEFAULT_FORMAT = OutputFormat.PDF.value
DEFAULT_TEMPLATE = TemplateType.NO_BARS.value
SUPPORTED_FORMATS: Final[set[str]] = OutputFormat.values()
SUPPORTED_TEMPLATES: Final[set[str]] = TemplateType.values()


__all__ = [
    # Exit codes
    "EXIT_SUCCESS",
    "EXIT_SIGINT",
    "EXIT_FILE_SYSTEM_ERROR",
    "EXIT_INTERNAL_ERROR",
    "EXIT_RESOURCE_ERROR",
    "EXIT_INPUT_ERROR",
    "EXIT_GENERIC_ERROR",
    # Error messages
    "ERROR_UNKNOWN_COMMAND",
    "ERROR_FILE_NOT_FOUND",
    "ERROR_INVALID_FORMAT",
    "ERROR_PERMISSION_DENIED",
    # Process and resource limits
    "DEFAULT_PROCESS_TIMEOUT_SECONDS",
    "MAX_RESUME_SIZE_MB",
    "MAX_PALETTE_SIZE_MB",
    "MAX_FILE_SIZE_MB",
    # File extensions
    "PDF_EXTENSION",
    "HTML_EXTENSION",
    "TEX_EXTENSION",
    # Defaults and configuration
    "DEFAULT_FORMAT",
    "DEFAULT_TEMPLATE",
    "MIN_FILENAME_PARTS",
    "ALLOWED_PATH_OVERRIDES",
    "SUPPORTED_FORMATS",
    "SUPPORTED_TEMPLATES",
    # Enums
    "OutputFormat",
    "TemplateType",
    "RenderMode",
]
