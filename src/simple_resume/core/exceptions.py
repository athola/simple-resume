"""Core exception types for simple-resume."""

from __future__ import annotations

from typing import Any


class SimpleResumeError(Exception):
    """Raise for any simple-resume specific error."""

    def __init__(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        filename: str | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: The error message.
            context: Optional context for the error.
            filename: The name of the file being processed.

        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.filename = filename

    def __str__(self) -> str:
        """Return a formatted error message."""
        base_msg = self.message
        if self.filename:
            base_msg = f"{self.filename}: {base_msg}"
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            base_msg = f"{base_msg} (context: {context_str})"
        return base_msg


class ValidationError(SimpleResumeError, ValueError):
    """Raise when resume data validation fails."""

    def __init__(
        self,
        message: str,
        *,
        errors: list[str] | None = None,
        warnings: list[str] | None = None,
        context: dict[str, Any] | None = None,
        filename: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception.

        Args:
            message: The error message.
            errors: A list of validation errors.
            warnings: A list of validation warnings.
            context: Optional context for the error.
            filename: The name of the file being processed.
            **kwargs: Additional context (will be filtered).

        """
        # Filter out parameters that should be passed to parent
        filtered_kwargs = {
            k: v for k, v in kwargs.items() if k not in ["context", "filename"]
        }

        super().__init__(message, context=context, filename=filename, **filtered_kwargs)
        self.errors = errors or []
        self.warnings = warnings or []


class ConfigurationError(SimpleResumeError):
    """Raise when configuration is invalid."""

    def __init__(
        self,
        message: str,
        *,
        config_key: str | None = None,
        config_value: Any | None = None,
        context: dict[str, Any] | None = None,
        filename: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception.

        Args:
            message: The error message.
            config_key: The configuration key that caused the error.
            config_value: The value of the configuration key.
            context: Optional context for the error.
            filename: The name of the file being processed.
            **kwargs: Additional context (will be filtered).

        """
        # Filter out parameters that should be passed to parent
        filtered_kwargs = {
            k: v for k, v in kwargs.items() if k not in ["context", "filename"]
        }

        super().__init__(message, context=context, filename=filename, **filtered_kwargs)
        self.config_key = config_key
        self.config_value = config_value

    def __str__(self) -> str:
        """Return a formatted error message."""
        base_msg = super().__str__()
        if self.config_key:
            base_msg = f"{base_msg} (config_key={self.config_key})"
        return base_msg


class PaletteError(SimpleResumeError):
    """Raise when color palette operations fail."""

    def __init__(
        self,
        message: str,
        *,
        palette_name: str | None = None,
        color_values: list[str] | None = None,
        context: dict[str, Any] | None = None,
        filename: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception.

        Args:
            message: The error message.
            palette_name: The name of the palette.
            color_values: The color values that caused the error.
            context: Optional context for the error.
            filename: The name of the file being processed.
            **kwargs: Additional context (will be filtered).

        """
        # Filter out parameters that should be passed to parent
        filtered_kwargs = {
            k: v for k, v in kwargs.items() if k not in ["context", "filename"]
        }

        super().__init__(message, context=context, filename=filename, **filtered_kwargs)
        self.palette_name = palette_name
        self.color_values = color_values


class FileSystemError(SimpleResumeError):
    """Raise when file system operations fail."""

    def __init__(
        self,
        message: str,
        *,
        path: str | None = None,
        operation: str | None = None,
        **kwargs: Any,
    ):
        """Initialize the exception.

        Args:
            message: The error message.
            path: The file path.
            operation: The file system operation that failed.
            **kwargs: Additional context.

        """
        super().__init__(message, **kwargs)
        self.path = path
        self.operation = operation


class SessionError(SimpleResumeError):
    """Raise when session operations fail."""

    def __init__(
        self, message: str, *, session_id: str | None = None, **kwargs: Any
    ) -> None:
        """Initialize the exception.

        Args:
            message: The error message.
            session_id: The ID of the session.
            **kwargs: Additional context.

        """
        super().__init__(message, **kwargs)
        self.session_id = session_id


class GenerationError(SimpleResumeError):
    """Raise when PDF/HTML generation fails."""

    def __init__(self, message: str, **metadata: Any) -> None:
        """Initialize the exception with optional metadata.

        Args:
            message: The error message.
            **metadata: Optional metadata such as ``output_path``, ``format_type``,
                ``resume_name``, ``context`` and ``filename``.

        """
        output_path = metadata.pop("output_path", None)
        format_type = metadata.pop("format_type", None)
        resume_name = metadata.pop("resume_name", None)
        context = metadata.pop("context", None)
        filename = metadata.pop("filename", None)

        if filename is None and resume_name is not None:
            filename = resume_name

        super().__init__(message, context=context, filename=filename, **metadata)
        self.output_path = str(output_path) if output_path is not None else None
        self.format_type = format_type
        self.resume_name = resume_name

    def __str__(self) -> str:
        """Return a formatted error message."""
        base_msg = super().__str__()
        if self.format_type:
            base_msg = f"{base_msg} (format={self.format_type})"
        return base_msg


class TemplateError(SimpleResumeError):
    """Raise when template processing fails."""

    def __init__(self, message: str, **metadata: Any) -> None:
        """Initialize the exception with optional metadata.

        Args:
            message: The error message.
            **metadata: Optional metadata such as ``template_name``,
                ``template_path``, ``context`` and ``filename``.

        """
        template_name = metadata.pop("template_name", None)
        template_path = metadata.pop("template_path", None)
        context = metadata.pop("context", None)
        filename = metadata.pop("filename", None)

        super().__init__(message, context=context, filename=filename, **metadata)
        self.template_name = template_name
        self.template_path = template_path


__all__ = [
    # Base exception
    "SimpleResumeError",
    # Specific exception types
    "ConfigurationError",
    "FileSystemError",
    "GenerationError",
    "PaletteError",
    "SessionError",
    "TemplateError",
    "ValidationError",
]
