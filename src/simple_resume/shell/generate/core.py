"""Core generation functions with immediate imports.

This module provides high-level functions for generating resumes with immediate
import loading. These functions are ideal for:
- Applications that will definitely use generation functionality
- Situations where predictability is preferred over optimization
- Web applications where import time is less critical than request time

For lazy-loaded versions with better startup performance, see `generate.lazy`.
"""

from __future__ import annotations

import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from simple_resume.core.constants import DEFAULT_FORMAT, OutputFormat
from simple_resume.core.exceptions import (
    ConfigurationError,
    FileSystemError,
    GenerationError,
    ValidationError,
)
from simple_resume.core.generate.plan import (
    CommandType,
    GeneratePlanOptions,
    GenerationCommand,
    build_generation_plan,
)
from simple_resume.core.models import GenerationConfig
from simple_resume.core.result import BatchGenerationResult, GenerationResult
from simple_resume.core.validation import (
    validate_directory_path,
    validate_format,
    validate_template_name,
)
from simple_resume.shell import session as session_mod
from simple_resume.shell.resume_extensions import to_html, to_pdf

_YAML_SUFFIXES = {".yaml", ".yml"}
CommandResult = (
    GenerationResult
    | BatchGenerationResult
    | dict[str, GenerationResult | BatchGenerationResult]
)


def _to_optional_path(value: str | Path | None) -> Path | None:
    """Convert value to optional `Path` object."""
    if value is None:
        return None
    return value if isinstance(value, Path) else Path(value)


def _normalize_format_sequence(
    formats: Sequence[OutputFormat | str],
) -> list[OutputFormat]:
    """Normalize a sequence of format strings to `OutputFormat` enums."""
    return [OutputFormat.normalize(fmt, param_name="format") for fmt in formats]


def _plan_options_from_config(
    config: GenerationConfig,
    overrides: dict[str, Any],
    *,
    formats: Sequence[OutputFormat],
) -> GeneratePlanOptions:
    """Create `GeneratePlanOptions` from `GenerationConfig` and overrides."""
    return GeneratePlanOptions(
        name=config.name,
        data_dir=_to_optional_path(config.data_dir),
        template=config.template,
        output_path=_to_optional_path(config.output_path),
        output_dir=_to_optional_path(config.output_dir),
        preview=config.preview,
        open_after=config.open_after,
        browser=config.browser,
        formats=formats,
        overrides=overrides,
        paths=config.paths,
        pattern=config.pattern,
    )


def _build_plan_for_config(
    config: GenerationConfig,
    overrides: dict[str, Any],
    *,
    formats: Sequence[OutputFormat],
) -> list[GenerationCommand]:
    """Build a list of `GenerationCommand` objects from config."""
    options = _plan_options_from_config(config, overrides, formats=formats)
    return build_generation_plan(options)


def _generate_with_format(
    config: GenerationConfig,
    *,
    format_type: OutputFormat,
    browser: str | None = None,
    overrides: dict[str, Any] | None = None,
) -> GenerationResult | BatchGenerationResult:
    """Generate output in the requested format using a unified pipeline."""
    # Touch time() to ensure monotonic clock import is kept (for parity with previous
    # implementation that relied on time for side effects).
    time.time()
    format_type = OutputFormat.normalize(format_type, param_name="format_type")

    normalized_overrides: dict[str, Any] = dict(overrides or {})

    try:
        # Validate inputs using configuration object.
        template = config.template
        if template:
            template = validate_template_name(template)

        if config.data_dir and config.paths is None:
            validate_directory_path(config.data_dir, must_exist=False)

        if config.output_dir and config.paths is None:
            validate_directory_path(
                config.output_dir,
                must_exist=False,
                create_if_missing=False,
            )

        # Create session with consistent configuration.
        session_config = session_mod.SessionConfig(
            default_template=template,
            default_format=format_type,
            auto_open=config.open_after,
            preview_mode=config.preview,
            output_dir=Path(config.output_dir) if config.output_dir else None,
            session_metadata=normalized_overrides,
        )

        with session_mod.ResumeSession(
            data_dir=config.data_dir,
            paths=config.paths,
            config=session_config,
        ) as session:
            if config.name:
                # Generate single resume.
                resume = session.resume(config.name)
                if normalized_overrides:
                    resume = resume.with_config(**normalized_overrides)

                if format_type is OutputFormat.PDF:
                    return to_pdf(resume, open_after=config.open_after)

                if format_type is OutputFormat.HTML:
                    return to_html(
                        resume,
                        open_after=config.open_after,
                        browser=browser,
                    )

                raise GenerationError(
                    f"Unsupported format requested: {format_type}",
                    format_type=format_type,
                )

            # Generate multiple resumes.
            batch_kwargs = dict(normalized_overrides)
            if format_type is OutputFormat.HTML and browser is not None:
                batch_kwargs.setdefault("browser", browser)

            return session.generate_all(
                format=format_type,
                pattern=config.pattern,
                open_after=config.open_after,
                **batch_kwargs,
            )

    except Exception as exc:
        if isinstance(
            exc, (GenerationError, ValidationError, ConfigurationError, FileSystemError)
        ):
            raise

        error_label = (
            "PDFs" if format_type is OutputFormat.PDF else format_type.value.upper()
        )
        raise GenerationError(
            f"Failed to generate {error_label}: {exc}",
            format_type=format_type,
        ) from exc


def _generate_single_format(
    session: session_mod.ResumeSession,
    config: GenerationConfig,
    format_type: OutputFormat,
    overrides: dict[str, Any],
) -> GenerationResult | BatchGenerationResult:
    """Generate a single format for a batch operation."""
    if not config.name:
        return session.generate_all(
            format=format_type,
            pattern=config.pattern,
            open_after=config.open_after,
            **overrides,
        )

    resume = session.resume(config.name)
    if format_type is OutputFormat.PDF:
        return to_pdf(resume, open_after=config.open_after)
    return to_html(resume, open_after=config.open_after, browser=config.browser)


def _execute_batch_all(
    config: GenerationConfig,
    overrides: dict[str, Any],
) -> dict[str, GenerationResult | BatchGenerationResult]:
    """Execute a multi-format batch command."""
    formats = config.formats or [OutputFormat.PDF, OutputFormat.HTML]
    normalized_formats = _normalize_format_sequence(formats)

    template = validate_template_name(config.template) if config.template else None
    if config.data_dir and config.paths is None:
        validate_directory_path(config.data_dir, must_exist=False)
    if config.output_dir and config.paths is None:
        validate_directory_path(
            config.output_dir, must_exist=False, create_if_missing=False
        )

    results: dict[str, GenerationResult | BatchGenerationResult] = {}
    default_fmt = normalized_formats[0] if normalized_formats else OutputFormat.PDF

    try:
        session_config = session_mod.SessionConfig(
            default_template=template,
            default_format=default_fmt,
            auto_open=config.open_after,
            preview_mode=config.preview,
            output_dir=_to_optional_path(config.output_dir),
            session_metadata=overrides,
        )

        with session_mod.ResumeSession(
            data_dir=config.data_dir,
            paths=config.paths,
            config=session_config,
        ) as session:
            for format_type in normalized_formats:
                results[format_type.value] = _generate_single_format(
                    session, config, format_type, overrides
                )

    except (GenerationError, ValidationError, ConfigurationError, FileSystemError):
        raise
    except Exception as exc:
        raise GenerationError(
            f"Failed to generate resumes: {exc}",
            format_type=", ".join(fmt.value for fmt in normalized_formats),
        ) from exc

    return results


def execute_generation_commands(
    commands: Sequence[GenerationCommand],
) -> list[tuple[GenerationCommand, CommandResult]]:
    """Execute planner commands and return their results."""
    executed: list[tuple[GenerationCommand, CommandResult]] = []
    for command in commands:
        result: CommandResult
        if command.kind is CommandType.BATCH_ALL:
            result = _execute_batch_all(command.config, command.overrides)
        else:
            format_type = command.format
            if format_type is None:
                raise GenerationError("Planner command missing required format")
            result = _generate_with_format(
                command.config,
                format_type=format_type,
                browser=command.config.browser,
                overrides=command.overrides,
            )
        executed.append((command, result))
    return executed


def _execute_plan_for_formats(
    config: GenerationConfig,
    overrides: dict[str, Any],
    formats: Sequence[OutputFormat],
) -> list[tuple[GenerationCommand, CommandResult]]:
    plan = _build_plan_for_config(config, dict(overrides), formats=formats)
    return execute_generation_commands(plan)


def _unwrap_generation_result(
    result: CommandResult,
) -> GenerationResult | BatchGenerationResult:
    """Unwrap a single `GenerationResult` from a `CommandResult`."""
    if isinstance(result, dict):
        raise TypeError(
            "Planner returned batch-all result where single output was expected"
        )
    return result


def _collect_generate_all_results(
    executions: Iterable[tuple[GenerationCommand, CommandResult]],
) -> dict[str, GenerationResult | BatchGenerationResult]:
    aggregated: dict[str, GenerationResult | BatchGenerationResult] = {}
    for command, result in executions:
        if command.kind is CommandType.BATCH_ALL:
            if not isinstance(result, dict):
                raise TypeError("Batch-all command must return a dictionary result")
            aggregated.update(result)
            continue

        if command.format is None:
            raise GenerationError("Planner command missing format information")
        aggregated[command.format.value] = _unwrap_generation_result(result)
    return aggregated


def generate_pdf(
    config: GenerationConfig,
    **config_overrides: Any,
) -> GenerationResult | BatchGenerationResult:
    """Generate PDF resumes using a configuration object.

    Args:
        config: Configuration describing what to render and where to write output.
        **config_overrides: Keyword overrides applied to the resume configuration.

    Returns:
        A generation result for a single resume or a batch when multiple
        files are rendered.

    Raises:
        `ConfigurationError`: Raised on invalid path configuration.
        `GenerationError`: Raised when PDF rendering fails.
        `ValidationError`: Raised when resume data fails validation.
        `FileSystemError`: Raised on filesystem errors during rendering.

    Examples:
        Generate all resumes in a directory::

            cfg = GenerationConfig(data_dir="my_resumes")
            results = generate_pdf(cfg)

        Render a single resume with overrides::

            cfg = GenerationConfig(
                name="casey",
                template="resume_with_bars",
                open_after=True,
            )
            result = generate_pdf(cfg, theme_color="#0066CC")

    """
    executions = _execute_plan_for_formats(
        config,
        config_overrides,
        formats=[OutputFormat.PDF],
    )
    if not executions:
        raise GenerationError("Planner produced no commands for generate_pdf")
    return _unwrap_generation_result(executions[0][1])


def generate_html(
    config: GenerationConfig,
    **config_overrides: Any,
) -> GenerationResult | BatchGenerationResult:
    """Generate HTML resumes using a configuration object.

    Args:
        config: Configuration describing what to render and where to write output.
        **config_overrides: Keyword overrides applied to the resume configuration.

    Returns:
        A generation result for a single resume or a batch when multiple
        files are rendered.

    Raises:
        `ConfigurationError`: Raised on invalid path configuration.
        `GenerationError`: Raised when HTML rendering fails.
        `ValidationError`: Raised when resume data fails validation.
        `FileSystemError`: Raised on filesystem errors during rendering.

    Examples:
        Generate HTML with preview enabled::

            cfg = GenerationConfig(data_dir="my_resumes", preview=True)
            results = generate_html(cfg)

        Render a single resume in the browser of choice::

            cfg = GenerationConfig(
                name="casey",
                template="resume_no_bars",
                browser="firefox",
            )
            result = generate_html(cfg)

    """
    executions = _execute_plan_for_formats(
        config,
        config_overrides,
        formats=[OutputFormat.HTML],
    )
    if not executions:
        raise GenerationError("Planner produced no commands for generate_html")
    return _unwrap_generation_result(executions[0][1])


def generate_all(
    config: GenerationConfig,
    **config_overrides: Any,
) -> dict[str, GenerationResult | BatchGenerationResult]:
    """Generate resumes in all specified formats.

    Generates resumes in multiple formats (e.g., PDF and HTML) from a single
    configuration.

    Args:
        config: Configuration describing what to render and which formats to include.
        **config_overrides: Keyword overrides applied to individual resume renders.

    Returns:
        Dictionary mapping format names to `GenerationResult` or
        `BatchGenerationResult`.

    Raises:
        `ValueError`: If any requested format is not supported.
        `ConfigurationError`: If path configuration is invalid.
        `GenerationError`: If generation fails for any format.

    Examples:
        # Generate all resumes in both PDF and HTML formats
        results = generate_all("my_resumes")

        # Generate specific resume in multiple formats
        results = generate_all(
            GenerationConfig(
                name="my_resume",
                formats=["pdf", "html"],
                template="professional",
            )
        )

    """
    target_formats = config.formats or [OutputFormat.PDF, OutputFormat.HTML]
    normalized_formats = _normalize_format_sequence(target_formats)
    executions = _execute_plan_for_formats(
        config,
        config_overrides,
        formats=normalized_formats,
    )
    return _collect_generate_all_results(executions)


def generate_resume(
    config: GenerationConfig,
    **config_overrides: Any,
) -> GenerationResult:
    """Generate a single resume.

    This function is designed for generating a single resume file, as opposed
    to batch operations.

    Args:
        config: Configuration describing the resume to render.
        **config_overrides: Keyword overrides applied to the resume configuration.

    Returns:
        `GenerationResult` with metadata and operations.

    Examples:
        # Simple generation
        result = generate_resume(GenerationConfig(name="my_resume"))

        # With template and output path
        result = generate_resume(
            GenerationConfig(
                name="my_resume",
                format="pdf",
                template="professional",
                output_path="output/my_resume.pdf",
            )
        )

    """
    format_enum = validate_format(config.format, param_name="format")
    plan_config = GenerationConfig(
        data_dir=config.data_dir,
        output_dir=config.output_dir,
        output_path=config.output_path,
        paths=config.paths,
        template=config.template,
        format=format_enum,
        open_after=config.open_after,
        preview=config.preview,
        name=config.name,
        pattern=config.pattern,
        browser=config.browser,
    )

    executions = _execute_plan_for_formats(
        plan_config,
        config_overrides,
        formats=[format_enum],
    )
    if not executions:
        raise GenerationError("Planner produced no commands for generate_resume")
    result = _unwrap_generation_result(executions[0][1])
    if isinstance(result, BatchGenerationResult):
        raise GenerationError(
            "Planner returned batch output when generate_resume expected a single "
            "resume"
        )
    return result


def _infer_data_dir_and_name(
    source: str | Path,
    data_dir: str | Path | None,
) -> tuple[Path, str | None]:
    """Infer a data directory and optional resume name from user-friendly inputs."""
    source_path = Path(source)

    if data_dir is not None:
        base_dir = Path(data_dir)
        if source_path.exists() and source_path.is_dir():
            return source_path, None
        if source_path.suffix.lower() in _YAML_SUFFIXES:
            return base_dir, source_path.stem
        return base_dir, str(source)

    if source_path.exists():
        if source_path.is_dir():
            return source_path, None
        if source_path.suffix.lower() in _YAML_SUFFIXES:
            return source_path.parent, source_path.stem

    raise ValueError(
        "Unable to infer data_dir from source. Provide a YAML path, directory, "
        "or set data_dir explicitly."
    )


@dataclass
class GenerateOptions:
    """Configuration options for resume generation."""

    formats: Sequence[str | OutputFormat] | None = None
    data_dir: str | Path | None = None
    output_dir: str | Path | None = None
    template: str | None = None
    preview: bool = False
    open_after: bool = False
    browser: str | None = None


def generate(
    source: str | Path,
    options: GenerateOptions | None = None,
    **overrides: Any,
) -> dict[str, GenerationResult | BatchGenerationResult]:
    """Render one or more formats for the same source."""
    opts = options or GenerateOptions()

    target_formats = tuple(opts.formats or (DEFAULT_FORMAT,))
    normalized_targets = tuple(
        validate_format(fmt, param_name="format") for fmt in target_formats
    )
    base_dir, resume_name = _infer_data_dir_and_name(source, opts.data_dir)

    if len(normalized_targets) == 1:
        fmt = normalized_targets[0]
        cfg = GenerationConfig(
            data_dir=base_dir,
            name=resume_name,
            output_dir=opts.output_dir,
            template=opts.template,
            open_after=opts.open_after,
            preview=opts.preview or (fmt is OutputFormat.HTML),
            browser=opts.browser if fmt is OutputFormat.HTML else None,
        )

        if fmt is OutputFormat.PDF:
            return {fmt.value: generate_pdf(cfg, **overrides)}

        if fmt is OutputFormat.HTML:
            return {fmt.value: generate_html(cfg, **overrides)}

        raise ValueError(f"Unsupported format requested: {fmt.value}")

    cfg = GenerationConfig(
        data_dir=base_dir,
        name=resume_name,
        output_dir=opts.output_dir,
        template=opts.template,
        formats=list(normalized_targets),
        open_after=opts.open_after,
        preview=opts.preview,
    )

    return generate_all(cfg, **overrides)


def preview(
    source: str | Path,
    *,
    data_dir: str | Path | None = None,
    template: str | None = None,
    browser: str | None = None,
    open_after: bool = True,
    **overrides: Any,
) -> GenerationResult | BatchGenerationResult:
    """Render a single resume to HTML with preview defaults."""
    base_dir, resume_name = _infer_data_dir_and_name(source, data_dir)
    if resume_name is None:
        raise ValueError("preview() requires a specific resume name or YAML path.")

    cfg = GenerationConfig(
        data_dir=base_dir,
        name=resume_name,
        template=template,
        browser=browser,
        preview=True,
        open_after=open_after,
    )

    return generate_html(cfg, **overrides)


__all__ = [
    "GenerationConfig",
    "execute_generation_commands",
    "generate_pdf",
    "generate_html",
    "generate_all",
    "generate_resume",
    "generate",
    "preview",
    "to_pdf",
    "to_html",
]
