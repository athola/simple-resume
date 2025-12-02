"""Unified generation helpers that orchestrate shell operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Callable, TypeVar, cast

import simple_resume.shell.session as session_mod
from simple_resume.core.constants import OutputFormat
from simple_resume.core.exceptions import (
    ConfigurationError,
    FileSystemError,
    ValidationError,
)
from simple_resume.core.generate.exceptions import (
    GenerationError,
)
from simple_resume.core.generate.plan import (
    CommandType,
    GeneratePlanOptions,
    GenerationCommand,
    build_generation_plan,
)
from simple_resume.core.models import GenerationConfig
from simple_resume.core.paths import Paths
from simple_resume.core.result import (
    BatchGenerationResult,
    GenerationResult,
)
from simple_resume.core.validation import validate_directory_path
from simple_resume.shell.generate import core as generate_core

T = TypeVar("T")


@dataclass(frozen=True)
class GenerateOptions:
    """Configuration for convenience helpers like `generate` and `preview`."""

    formats: tuple[OutputFormat | str, ...] = (OutputFormat.PDF,)
    preview: bool = False
    template: str | None = None
    browser: str | None = None
    open_after: bool = False
    overrides: dict[str, Any] = field(default_factory=dict)


def generate_pdf(
    config: GenerationConfig,
    **overrides: Any,
) -> GenerationResult | BatchGenerationResult:
    """Generate PDF output for one or more resumes."""

    def _runner(
        session: session_mod.ResumeSession,
    ) -> GenerationResult | BatchGenerationResult:
        if config.name:
            resume = session.resume(config.name)
            if overrides:
                resume = resume.with_config(**overrides)
            output_path = config.output_path if config.output_path is not None else None
            return generate_core.to_pdf(
                resume, output_path=output_path, open_after=config.open_after
            )
        return session.generate_all(
            format=OutputFormat.PDF,
            pattern=config.pattern,
            open_after=config.open_after,
            **overrides,
        )

    return _run_with_session(
        config,
        overrides=overrides,
        default_format=OutputFormat.PDF,
        runner=_runner,
    )


def generate_html(
    config: GenerationConfig,
    **overrides: Any,
) -> GenerationResult | BatchGenerationResult:
    """Generate HTML output for one or more resumes."""

    def _runner(
        session: session_mod.ResumeSession,
    ) -> GenerationResult | BatchGenerationResult:
        if config.name:
            resume = session.resume(config.name)
            if overrides:
                resume = resume.with_config(**overrides)
            output_path = config.output_path if config.output_path is not None else None
            return generate_core.to_html(
                resume,
                output_path=output_path,
                open_after=config.open_after,
                browser=config.browser,
            )
        return session.generate_all(
            format=OutputFormat.HTML,
            pattern=config.pattern,
            open_after=config.open_after,
            browser=config.browser,
            **overrides,
        )

    return _run_with_session(
        config,
        overrides=overrides,
        default_format=OutputFormat.HTML,
        runner=_runner,
    )


def generate_all(
    config: GenerationConfig,
    **overrides: Any,
) -> dict[str, BatchGenerationResult | GenerationResult]:
    """Generate multiple formats, returning a mapping of format -> result."""
    requested_formats = config.formats or (OutputFormat.PDF,)
    normalized_formats = _normalize_formats(requested_formats)
    if not normalized_formats:
        raise ValueError("Unsupported format configuration - no formats provided")

    def _runner(
        session: session_mod.ResumeSession,
    ) -> dict[str, BatchGenerationResult | GenerationResult]:
        results: dict[str, BatchGenerationResult | GenerationResult] = {}

        if config.name:
            resume = session.resume(config.name)
            if overrides:
                resume = resume.with_config(**overrides)
            for fmt in normalized_formats:
                if fmt is OutputFormat.PDF:
                    results[fmt.value] = generate_core.to_pdf(
                        resume,
                        output_path=config.output_path,
                        open_after=config.open_after,
                    )
                elif fmt is OutputFormat.HTML:
                    results[fmt.value] = generate_core.to_html(
                        resume,
                        output_path=config.output_path,
                        open_after=config.open_after,
                        browser=config.browser,
                    )
                else:
                    raise ValueError(f"Unsupported format: {fmt}")
            return results

        for fmt in normalized_formats:
            results[fmt.value] = session.generate_all(
                format=fmt,
                pattern=config.pattern,
                open_after=config.open_after,
                browser=config.browser if fmt is OutputFormat.HTML else None,
                **overrides,
            )
        return results

    return _run_with_session(
        config,
        overrides=overrides,
        default_format=normalized_formats[0],
        runner=_runner,
    )


def generate_resume(
    config: GenerationConfig,
    **overrides: Any,
) -> GenerationResult | BatchGenerationResult | dict[str, Any]:
    """Generate resumes according to the normalized plan output."""
    format_value = config.format or OutputFormat.PDF
    normalized_format = _normalize_format(format_value)
    output_path = Path(config.output_path) if config.output_path is not None else None

    plan_options = GeneratePlanOptions(
        name=config.name,
        data_dir=Path(config.data_dir)
        if isinstance(config.data_dir, str)
        else config.data_dir,
        template=config.template,
        output_path=output_path,
        output_dir=Path(config.output_dir)
        if isinstance(config.output_dir, str)
        else config.output_dir,
        preview=config.preview,
        open_after=config.open_after,
        browser=config.browser,
        formats=[normalized_format],
        overrides=overrides,
        paths=config.paths,
        pattern=config.pattern,
    )
    commands = build_generation_plan(plan_options)
    executions = execute_generation_commands(commands)
    return (
        cast(
            GenerationResult | BatchGenerationResult | dict[str, Any], executions[0][1]
        )
        if executions
        else {}
    )


def generate(
    source: str | Path,
    options: GenerateOptions | None = None,
) -> dict[str, GenerationResult | BatchGenerationResult]:
    """High-level convenience wrapper similar to requests-style helpers."""
    options = options or GenerateOptions()
    source_path = Path(source)
    formats = _normalize_formats(options.formats)

    if not formats:
        raise ValueError("GenerateOptions.formats must include at least one format")

    overrides = dict(options.overrides)

    if source_path.is_file():
        config = GenerationConfig(
            name=source_path.stem,
            data_dir=source_path.parent,
            template=options.template,
            preview=options.preview,
            open_after=options.open_after,
            browser=options.browser,
        )
    else:
        config = GenerationConfig(
            data_dir=source_path,
            template=options.template,
            preview=options.preview,
            open_after=options.open_after,
            browser=options.browser,
        )

    if len(formats) == 1:
        fmt = formats[0]
        if fmt is OutputFormat.PDF:
            return {"pdf": generate_pdf(config, **overrides)}
        if fmt is OutputFormat.HTML:
            return {"html": generate_html(config, **overrides)}
        raise ValueError(f"Unsupported format: {fmt}")

    # Create new config with formats
    # (GenerationConfig is frozen, so create new instance)
    updated_config = replace(config, formats=list(formats))
    return generate_all(updated_config, **overrides)


def preview(
    source: str | Path, **overrides: Any
) -> GenerationResult | BatchGenerationResult:
    """Render a single resume to HTML in preview mode."""
    source_path = Path(source)
    if not source_path.is_file():
        raise ValueError("preview requires a specific resume file path")

    config = GenerationConfig(
        name=source_path.stem,
        data_dir=source_path.parent,
        preview=True,
        browser=overrides.pop("browser", None),
    )
    return generate_html(config, **overrides)


def execute_generation_commands(
    commands: Sequence[GenerationCommand],
) -> list[tuple[GenerationCommand, object]]:
    """Execute normalized generation commands."""
    results: list[tuple[GenerationCommand, object]] = []
    for command in commands:
        overrides = command.overrides or {}
        if command.kind in (CommandType.SINGLE, CommandType.BATCH_SINGLE):
            format_type = command.format
            if format_type is None:
                raise ValueError("Missing format for generation command")
            executor = _FORMAT_EXECUTORS.get(format_type)
            if executor is None:
                raise ValueError(f"Unsupported format: {format_type}")
            result = executor(command.config, **overrides)
            results.append((command, result))
            continue

        if command.kind is CommandType.BATCH_ALL:
            result = generate_all(command.config, **overrides)
            results.append((command, result))
            continue

        raise ValueError(f"Unsupported command type: {command.kind}")
    return results


def _run_with_session(
    config: GenerationConfig,
    *,
    overrides: dict[str, Any],
    default_format: OutputFormat,
    runner: Callable[[session_mod.ResumeSession], T],
) -> T:
    """Execute a shell operation inside a managed ResumeSession."""
    session_config = _build_session_config(config, overrides, default_format)
    data_dir = _resolve_data_dir(config)

    try:
        with session_mod.ResumeSession(
            data_dir=data_dir,
            paths=config.paths,
            config=session_config,
        ) as session:
            return runner(session)
    except (ValidationError, ConfigurationError, FileSystemError, GenerationError):
        raise
    except Exception as exc:  # pragma: no cover - defensive
        label = default_format.value.upper()
        raise GenerationError(
            f"Failed to generate {label}s: {exc}",
            format_type=default_format.value,
        ) from exc


def _build_session_config(
    config: GenerationConfig,
    overrides: dict[str, Any],
    default_format: OutputFormat,
) -> session_mod.SessionConfig:
    """Return a SessionConfig derived from the generation config."""
    session_metadata = dict(overrides)
    return session_mod.SessionConfig(
        paths=config.paths if isinstance(config.paths, Paths) else None,
        default_template=config.template,
        default_format=default_format,
        auto_open=config.open_after,
        preview_mode=config.preview,
        output_dir=Path(config.output_dir) if config.output_dir else None,
        session_metadata=session_metadata,
    )


def _resolve_data_dir(config: GenerationConfig) -> Path | None:
    """Return a validated data directory if provided."""
    if config.paths is not None:
        return None
    if not config.data_dir:
        return None
    return validate_directory_path(
        config.data_dir, must_exist=False, create_if_missing=False
    )


def _normalize_formats(
    formats: Sequence[OutputFormat | str] | None,
) -> list[OutputFormat]:
    """Normalize a sequence of format strings or enums to `OutputFormat` enum values.

    Args:
        formats: A sequence of format strings (e.g., "pdf", "html") or
            `OutputFormat` enums.

    Returns:
        A list of normalized `OutputFormat` enum values.

    """
    if not formats:
        return []
    return [_normalize_format(value) for value in formats]


def _normalize_format(value: OutputFormat | str) -> OutputFormat:
    """Normalize a single format string or enum to an `OutputFormat` enum value.

    Args:
        value: The format string (e.g., "pdf", "html") or `OutputFormat` enum.

    Returns:
        A normalized `OutputFormat` enum value.

    Raises:
        ValueError: If the format is unsupported.

    """
    if isinstance(value, OutputFormat):
        return value
    normalized = value.strip().lower()
    try:
        return OutputFormat(normalized)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"Unsupported format: {value}") from exc


_FORMAT_EXECUTORS: dict[OutputFormat, Callable[..., object]] = {
    OutputFormat.PDF: generate_pdf,
    OutputFormat.HTML: generate_html,
}


__all__ = [
    "GenerateOptions",
    "execute_generation_commands",
    "generate",
    "generate_all",
    "generate_html",
    "generate_pdf",
    "generate_resume",
    "preview",
]
