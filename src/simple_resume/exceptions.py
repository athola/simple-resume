"""Define the exception hierarchy for simple-resume.

This module defines a structured exception hierarchy similar to pandas and requests
to provide clear error handling and debugging capabilities.

## Error Handling Pattern

`simple-resume` uses a two-tier error handling pattern:

**Tier 1: Inspection (returns results)**
- Use when you want to check validation status, log warnings, or collect errors.
- Methods: `Resume.validate()` → `ValidationResult`.
- Never raises exceptions, always returns a result object.
- Example: Check validation without stopping execution.
  ```python
  result = resume.validate()
  if result.warnings:
      log.warning(result.warnings)
  if not result.is_valid:
      print(f"Errors: {result.errors}")
  ```

**Tier 2: Action (raises on invalid)**
- Use when operations require valid data (fail-fast approach).
- Methods: `Resume.validate_or_raise()` → `None` or raises `ValidationError`.
- Used internally by `to_pdf()`, `to_html()`, and CLI commands.
- Example: Ensure data is valid before proceeding.
  ```python
  resume.validate_or_raise()  # Raises ValidationError if invalid
  resume.to_pdf("output.pdf")  # Only runs if validation passed
  ```

This pattern is similar to:
- **pandas**: `df.empty` (returns bool) vs operations that raise on empty DataFrames.
- **requests**: `response.status_code` vs `response.raise_for_status()`.

## Exception Hierarchy

All exceptions inherit from `SimpleResumeError`, allowing users to catch all
`simple-resume` errors with a single except clause:

```python
try:
    resume = Resume.read_yaml("resume.yaml")
    resume.to_pdf()
except SimpleResumeError as e:
    # Catches all simple-resume specific errors
    print(f"Error: {e}")
```

Exception classes should be raised directly (not through helper functions):

```python
# Correct
raise ValidationError("Invalid data", errors=["Missing field"], filename="resume.yaml")

# Correct
raise GenerationError("PDF generation failed", format_type="pdf", output_path="out.pdf")
```
"""

from __future__ import annotations

import os
from typing import Any


class SimpleResumeError(Exception):
    """Define the base exception for all simple-resume errors.

    All other exceptions in `simple-resume` inherit from this base class,
    allowing users to catch all `simple-resume`-specific errors with a single
    except clause.
    """

    def __init__(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        filename: str | None = None,
    ) -> None:
        """Initialize the exception with a message and optional context."""
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.filename = filename

    def __str__(self) -> str:
        """Return a formatted error message with filename and context."""
        base_msg = self.message
        if self.filename:
            base_msg = f"{self.filename}: {base_msg}"
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            base_msg = f"{base_msg} (context: {context_str})"
        return base_msg


class ValidationError(SimpleResumeError, ValueError):
    """Raise when resume data validation fails.

    This exception is raised when the provided resume data doesn't meet
    the required structure, contains invalid values, or fails validation rules.

    Inherits from both `SimpleResumeError` and `ValueError` for backwards compatibility.
    """

    def __init__(
        self,
        message: str,
        *,
        errors: list[str] | None = None,
        warnings: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize with message and optional error/warning lists."""
        super().__init__(message, **kwargs)
        self.errors = errors or []
        self.warnings = warnings or []


class ConfigurationError(SimpleResumeError):
    """Raise when configuration is invalid.

    This covers issues with resume configuration, color schemes, page dimensions,
    template settings, and other configuration-related problems.
    """

    def __init__(
        self,
        message: str,
        *,
        config_key: str | None = None,
        config_value: Any | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize with message and optional config details."""
        super().__init__(message, **kwargs)
        self.config_key = config_key
        self.config_value = config_value

    def __str__(self) -> str:
        """Return a formatted error message with the config key."""
        base_msg = super().__str__()
        if self.config_key:
            base_msg = f"{base_msg} (config_key={self.config_key})"
        return base_msg


class TemplateError(SimpleResumeError):
    """Raise when template processing fails.

    This exception covers issues with template loading, rendering, missing
    templates, and Jinja2 template errors.
    """

    def __init__(
        self,
        message: str,
        *,
        template_name: str | None = None,
        template_path: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize with message and optional template details."""
        super().__init__(message, **kwargs)
        self.template_name = template_name
        self.template_path = template_path


class GenerationError(SimpleResumeError):
    """Raise when PDF/HTML generation fails.

    This exception covers issues during the actual generation process,
    including WeasyPrint errors, file I/O problems, and rendering failures.
    """

    def __init__(
        self,
        message: str,
        *,
        output_path: str | os.PathLike[str] | None = None,
        format_type: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the generation error with a message and optional output details.

        Args:
            message: Error message.
            output_path: Output path (accepts str or Path objects).
            format_type: Format type (pdf, html, etc.).
            **kwargs: Additional context passed to base exception.

        """
        super().__init__(message, **kwargs)
        self.output_path = str(output_path) if output_path is not None else None
        self.format_type = format_type

    def __str__(self) -> str:
        """Return a formatted error message with the format type."""
        base_msg = super().__str__()
        if self.format_type:
            base_msg = f"{base_msg} (format={self.format_type})"
        return base_msg


class PaletteError(SimpleResumeError):
    """Raise when color palette operations fail.

    This exception covers issues with palette loading, generation, color
    validation, and palette-related errors.
    """

    def __init__(
        self,
        message: str,
        *,
        palette_name: str | None = None,
        color_values: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the palette error with a message and optional palette details."""
        super().__init__(message, **kwargs)
        self.palette_name = palette_name
        self.color_values = color_values


class FileSystemError(SimpleResumeError):
    """Raise when file system operations fail.

    This exception covers issues with file reading, writing, path resolution,
    and directory operations.
    """

    def __init__(
        self,
        message: str,
        *,
        path: str | os.PathLike[str] | None = None,
        operation: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the filesystem error with a message and optional path/operation.

        Args:
            message: Error message.
            path: File path (accepts str or Path objects).
            operation: Operation type (read, write, etc.).
            **kwargs: Additional context passed to base exception.

        """
        super().__init__(message, **kwargs)
        self.path = str(path) if path is not None else None
        self.operation = operation


class SessionError(SimpleResumeError):
    """Raise when session operations fail.

    This exception covers issues with `ResumeSession` operations, context
    management, and session-related errors.
    """

    def __init__(
        self, message: str, *, session_id: str | None = None, **kwargs: Any
    ) -> None:
        """Initialize the session error with a message and optional session ID."""
        super().__init__(message, **kwargs)
        self.session_id = session_id


__all__ = [
    # Base exception
    "SimpleResumeError",
    # Specific exception types
    "ValidationError",
    "ConfigurationError",
    "TemplateError",
    "GenerationError",
    "PaletteError",
    "FileSystemError",
    "SessionError",
]
