"""Command-line interface for simple-resume."""

from __future__ import annotations

from .main import (
    _build_config_overrides,
    _handle_unexpected_error,
    _run_session_generation,
    create_parser,
    handle_generate_command,
    handle_session_command,
    handle_validate_command,
    main,
)

__all__ = [
    "_build_config_overrides",
    "_handle_unexpected_error",
    "_run_session_generation",
    "create_parser",
    "handle_generate_command",
    "handle_session_command",
    "handle_validate_command",
    "main",
]
