"""Exception types used by the generation subsystem."""

from __future__ import annotations

from typing import Any

from simple_resume.core.exceptions import SimpleResumeError


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
    "GenerationError",
    "TemplateError",
]
