"""Shared error handling for CLI subcommands.

Extracted from main.py to avoid circular imports between
main.py and the subcommand modules (_import.py, _tailor.py, _screen.py).
"""

from __future__ import annotations

import logging


def _handle_unexpected_error(exc: Exception, context: str) -> int:
    """Handle unexpected exceptions with proper logging and classification.

    Args:
        exc: The unexpected exception.
        context: Context where the error occurred (e.g., "generation", "validation").

    Returns:
        Appropriate exit code.

    """
    logger = logging.getLogger(__name__)

    # Classify the error type for better user experience.
    if isinstance(exc, (PermissionError, OSError)):
        error_type = "File System Error"
        exit_code = 2
        suggestion = "Check file permissions and disk space"
    elif isinstance(exc, (KeyError, AttributeError, TypeError)):
        error_type = "Internal Error"
        exit_code = 3
        suggestion = "This may be a bug - please report it"
    elif isinstance(exc, MemoryError):
        error_type = "Resource Error"
        exit_code = 4
        suggestion = "System ran out of memory"
    elif isinstance(exc, (ValueError, IndexError)):
        error_type = "Input Error"
        exit_code = 5
        suggestion = "Check your input files and parameters"
    else:
        error_type = "Unexpected Error"
        exit_code = 1
        suggestion = "Check logs for details"

    # Log the full error for debugging.
    logger.error(
        f"{error_type} in {context}: {exc}",
        exc_info=True,
        extra={
            "error_type": error_type,
            "context": context,
            "exception_type": type(exc).__name__,
        },
    )

    # Show user-friendly message.
    print(f"{error_type}: {exc}")
    if suggestion:
        print(f"Suggestion: {suggestion}")

    return exit_code


__all__ = ["_handle_unexpected_error"]
