"""Exception hierarchy for simple-resume.

This module defines a structured exception hierarchy similar to pandas and requests
to provide clear error handling and debugging capabilities.
"""

from __future__ import annotations

from typing import Any, NoReturn


class SimpleResumeError(Exception):
    """Base exception for all simple-resume errors.

    All other exceptions in simple-resume inherit from this base class,
    allowing users to catch all simple-resume-specific errors with a single
    except clause.
    """

    def __init__(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        filename: str | None = None,
    ) -> None:
        """Initialize exception with message and optional context."""
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.filename = filename

    def __str__(self) -> str:
        """Return formatted error message with filename and context."""
        base_msg = self.message
        if self.filename:
            base_msg = f"{self.filename}: {base_msg}"
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            base_msg = f"{base_msg} (context: {context_str})"
        return base_msg


class ValidationError(SimpleResumeError, ValueError):
    """Raised when resume data validation fails.

    This exception is raised when the provided resume data doesn't meet
    the required structure, contains invalid values, or fails validation rules.

    Inherits from both SimpleResumeError and ValueError for backwards compatibility.
    """

    def __init__(
        self,
        message: str,
        *,
        errors: list[str] | None = None,
        warnings: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize validation error with message and optional error/warning lists."""
        super().__init__(message, **kwargs)
        self.errors = errors or []
        self.warnings = warnings or []


class ConfigurationError(SimpleResumeError):
    """Raised when configuration is invalid.

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
        """Initialize configuration error with message and optional config details."""
        super().__init__(message, **kwargs)
        self.config_key = config_key
        self.config_value = config_value

    def __str__(self) -> str:
        """Return formatted error message with config key."""
        base_msg = super().__str__()
        if self.config_key:
            base_msg = f"{base_msg} (config_key={self.config_key})"
        return base_msg


class TemplateError(SimpleResumeError):
    """Raised when template processing fails.

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
        """Initialize template error with message and optional template details."""
        super().__init__(message, **kwargs)
        self.template_name = template_name
        self.template_path = template_path


class GenerationError(SimpleResumeError):
    """Raised when PDF/HTML generation fails.

    This exception covers issues during the actual generation process,
    including WeasyPrint errors, file I/O problems, and rendering failures.
    """

    def __init__(
        self,
        message: str,
        *,
        output_path: str | None = None,
        format_type: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize generation error with message and optional output details."""
        super().__init__(message, **kwargs)
        self.output_path = output_path
        self.format_type = format_type

    def __str__(self) -> str:
        """Return formatted error message with format type."""
        base_msg = super().__str__()
        if self.format_type:
            base_msg = f"{base_msg} (format={self.format_type})"
        return base_msg


class PaletteError(SimpleResumeError):
    """Raised when color palette operations fail.

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
        """Initialize palette error with message and optional palette details."""
        super().__init__(message, **kwargs)
        self.palette_name = palette_name
        self.color_values = color_values


class FileSystemError(SimpleResumeError):
    """Raised when file system operations fail.

    This exception covers issues with file reading, writing, path resolution,
    and directory operations.
    """

    def __init__(
        self,
        message: str,
        *,
        path: str | None = None,
        operation: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize filesystem error with message and optional path/operation."""
        super().__init__(message, **kwargs)
        self.path = path
        self.operation = operation


class SessionError(SimpleResumeError):
    """Raised when session operations fail.

    This exception covers issues with ResumeSession operations, context
    management, and session-related errors.
    """

    def __init__(
        self, message: str, *, session_id: str | None = None, **kwargs: Any
    ) -> None:
        """Initialize session error with message and optional session ID."""
        super().__init__(message, **kwargs)
        self.session_id = session_id


# Convenience functions for common error patterns
def raise_validation_error(
    message: str, *, errors: list[str] | None = None, filename: str | None = None
) -> NoReturn:
    """Raise ValidationError with consistent format."""
    raise ValidationError(message, errors=errors, filename=filename)


def raise_configuration_error(
    message: str, *, config_key: str, config_value: Any, filename: str | None = None
) -> NoReturn:
    """Raise ConfigurationError with consistent format."""
    raise ConfigurationError(
        message, config_key=config_key, config_value=config_value, filename=filename
    )


def raise_template_error(
    message: str, *, template_name: str, filename: str | None = None
) -> NoReturn:
    """Raise TemplateError with consistent format."""
    raise TemplateError(message, template_name=template_name, filename=filename)


def raise_generation_error(
    message: str,
    *,
    format_type: str,
    output_path: str | None = None,
    filename: str | None = None,
) -> NoReturn:
    """Raise GenerationError with consistent format."""
    raise GenerationError(
        message, format_type=format_type, output_path=output_path, filename=filename
    )


def raise_filesystem_error(
    message: str, *, path: str, operation: str, filename: str | None = None
) -> NoReturn:
    """Raise FileSystemError with consistent format."""
    raise FileSystemError(message, path=path, operation=operation, filename=filename)


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
    # Convenience functions
    "raise_validation_error",
    "raise_configuration_error",
    "raise_template_error",
    "raise_generation_error",
    "raise_filesystem_error",
]
