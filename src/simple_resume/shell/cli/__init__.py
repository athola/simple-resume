"""Command-line interface for simple-resume."""

from __future__ import annotations

# Import the module itself to maintain test functionality
from simple_resume.shell.cli import main as main_module

# Import the main functions directly from the module
from simple_resume.shell.cli.main import (
    _build_config_overrides,
    _handle_unexpected_error,
    _run_session_generation,
    create_parser,
    handle_generate_command,
    handle_session_command,
    handle_validate_command,
)

# Import main as a different name to avoid conflict
from simple_resume.shell.cli.main import main as main_entry

# Make the main module available for import flexibility
main = main_module

__all__ = [
    "_build_config_overrides",
    "_handle_unexpected_error",
    "_run_session_generation",
    "create_parser",
    "handle_generate_command",
    "handle_session_command",
    "handle_validate_command",
    "main",
    "main_entry",
]
