"""Command-line interface for simple-resume."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, TypeVar, cast

from simple_resume.core.resume import Resume
from simple_resume.generate.core import execute_generation_commands
from simple_resume.session.config import SessionConfig
from simple_resume.session.session import ResumeSession

from . import main as _main_module

if TYPE_CHECKING:  # pragma: no cover - type checking helper only
    from .main import (
        _build_config_overrides,
        _handle_unexpected_error,
        _run_session_generation,
        create_parser,
        handle_generate_command,
        handle_session_command,
        handle_validate_command,
    )
    from .main import (
        main as _main_entry,
    )
else:
    _main_entry = _main_module.main

TMainCallable = TypeVar("TMainCallable", bound=Callable[..., int])


def _attach_cli_namespace(func: TMainCallable) -> TMainCallable:
    """Expose CLI helpers via attributes for legacy patching hooks."""
    namespace_func = cast(Any, func)
    namespace_func.execute_generation_commands = execute_generation_commands
    namespace_func.SessionConfig = SessionConfig
    namespace_func.ResumeSession = ResumeSession
    namespace_func.Resume = Resume
    namespace_func.create_parser = _main_module.create_parser
    namespace_func.handle_generate_command = _main_module.handle_generate_command
    namespace_func.handle_session_command = _main_module.handle_session_command
    namespace_func.handle_validate_command = _main_module.handle_validate_command
    namespace_func._build_config_overrides = _main_module._build_config_overrides
    namespace_func._run_session_generation = _main_module._run_session_generation
    namespace_func._handle_unexpected_error = _main_module._handle_unexpected_error
    return func


main = _attach_cli_namespace(_main_entry)

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
