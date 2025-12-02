"""Provide a command-line interface for simple-resume, backed by the generation API."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable, Iterable
from os import PathLike
from pathlib import Path
from typing import Any, Protocol, cast

from simple_resume import __version__
from simple_resume.core.constants import OutputFormat
from simple_resume.core.exceptions import SimpleResumeError, ValidationError
from simple_resume.core.generate.exceptions import GenerationError
from simple_resume.core.generate.plan import (
    CommandType,
    GeneratePlanOptions,
    GenerationCommand,
    build_generation_plan,
)
from simple_resume.core.result import BatchGenerationResult, GenerationResult
from simple_resume.core.resume import Resume
from simple_resume.shell.config import resolve_paths
from simple_resume.shell.resume_extensions import to_html, to_pdf
from simple_resume.shell.runtime.generate import execute_generation_commands
from simple_resume.shell.services import register_default_services
from simple_resume.shell.session import ResumeSession, SessionConfig


class GenerationResultProtocol(Protocol):
    """A protocol for objects representing generation results."""

    @property
    def exists(self) -> bool:
        """Check if the generated output exists and is valid."""
        ...


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


def main() -> int:
    """Run the CLI entry point."""
    # Register default services for CLI operations
    register_default_services()

    parser = create_parser()
    try:
        args = parser.parse_args()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 130

    handlers = {
        "generate": handle_generate_command,
        "session": handle_session_command,
        "validate": handle_validate_command,
    }

    try:
        command = getattr(args, "command", "")
        handler = handlers.get(command)
        if handler is None:
            print(f"Error: Unknown command {command}")
            parser.print_help()
            return 1
        return handler(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 130
    except Exception as exc:  # pragma: no cover - safety net
        return _handle_unexpected_error(exc, "main command execution")


MIN_GENERATE_ARGS = 2


def create_parser() -> argparse.ArgumentParser:
    """Create and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="simple-resume",
        description="Generate professional resumes from YAML data",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"simple-resume {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # generate subcommand
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate resume(s) in the chosen format(s)",
    )
    generate_parser.add_argument(
        "name",
        nargs="?",
        help="Resume name when generating a specific file",
    )
    generate_parser.add_argument(
        "--format",
        "-f",
        choices=["pdf", "html"],
        default="pdf",
        help="Output format for single-format operations (default: pdf)",
    )
    generate_parser.add_argument(
        "--formats",
        nargs="+",
        choices=["pdf", "html"],
        help="Generate in multiple formats (only valid when name is supplied)",
    )
    generate_parser.add_argument(
        "--template",
        "-t",
        help="Template name to apply",
    )
    generate_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Destination file or directory",
    )
    generate_parser.add_argument(
        "--data-dir",
        "-d",
        type=Path,
        help="Directory containing resume input files",
    )
    generate_parser.add_argument(
        "--open",
        action="store_true",
        help="Open generated files after completion",
    )
    generate_parser.add_argument(
        "--preview",
        action="store_true",
        help="Enable preview mode",
    )
    generate_parser.add_argument(
        "--browser",
        help="Browser command for opening HTML output",
    )
    generate_parser.add_argument("--theme-color", help="Override theme color (hex)")
    generate_parser.add_argument("--palette", help="Palette name or YAML file path")
    generate_parser.add_argument(
        "--page-width",
        type=int,
        help="Page width in millimetres",
    )
    generate_parser.add_argument(
        "--page-height",
        type=int,
        help="Page height in millimetres",
    )

    # session subcommand
    session_parser = subparsers.add_parser(
        "session",
        help="Interactive session for batch operations",
    )
    session_parser.add_argument(
        "--data-dir",
        "-d",
        type=Path,
        help="Directory containing resume input files",
    )
    session_parser.add_argument(
        "--template",
        "-t",
        help="Default template applied during the session",
    )
    session_parser.add_argument(
        "--preview",
        action="store_true",
        help="Toggle preview mode for the session",
    )

    # validate subcommand
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate resume data without generating output",
    )
    validate_parser.add_argument(
        "name",
        nargs="?",
        help="Optional resume name (omit to validate all files)",
    )
    validate_parser.add_argument(
        "--data-dir",
        "-d",
        type=Path,
        help="Directory containing resume input files",
    )

    return parser


def handle_generate_command(args: argparse.Namespace) -> int:
    """Handle the generate subcommand using generation helpers."""
    overrides = _build_config_overrides(args)
    try:
        formats = _resolve_cli_formats(args)
        plan_options = _build_plan_options(args, overrides, formats)
        commands = build_generation_plan(plan_options)
        return _execute_generation_plan(commands)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 130
    except SimpleResumeError as exc:
        print(f"Error: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - safety net
        return _handle_unexpected_error(exc, "resume generation")


def handle_session_command(args: argparse.Namespace) -> int:
    """Handle the session subcommand using the session API."""
    session_config = SessionConfig(
        default_template=getattr(args, "template", None),
        preview_mode=getattr(args, "preview", False),
    )
    data_dir = _to_path_or_none(getattr(args, "data_dir", None))

    try:
        with ResumeSession(data_dir=data_dir, config=session_config) as session:
            print("Starting Simple-Resume Session")
            print("=" * 40)
            print(f"Data directory : {session.paths.input}")
            print(f"Output directory: {session.paths.output}")
            print()

            while True:
                try:
                    command = input("simple-resume> ").strip()
                except EOFError:
                    print()
                    break

                if not command:
                    continue

                lower = command.lower()
                if lower in {"exit", "quit"}:
                    break
                if lower in {"help", "?"}:
                    _print_session_help()
                    continue
                if lower == "list":
                    _session_list_resumes(session)
                    continue
                if command.startswith("generate"):
                    parts = command.split()
                    if len(parts) >= MIN_GENERATE_ARGS:
                        resume_name = parts[1]
                        _session_generate_resume(
                            session,
                            resume_name,
                            session_config.default_template,
                        )
                    else:
                        print("Usage: generate <resume_name>")
                    continue

                print(f"Unknown command: {command}")
            print("Session ended.")
            return 0
    except KeyboardInterrupt:
        print("\nSession cancelled by user.")
        return 130
    except SimpleResumeError as exc:
        print(f"Session error: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - safety net
        return _handle_unexpected_error(exc, "session management")


def handle_validate_command(args: argparse.Namespace) -> int:
    """Validate one or more resumes without generating output."""
    data_dir = _to_path_or_none(getattr(args, "data_dir", None))

    try:
        if args.name:
            return _validate_single_resume_cli(args.name, data_dir)
        return _validate_all_resumes_cli(data_dir)
    except SimpleResumeError as exc:
        print(f"Validation error: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - safety net
        return _handle_unexpected_error(exc, "resume validation")


def _resolve_cli_formats(args: argparse.Namespace) -> list[OutputFormat]:
    """Normalize format arguments to `OutputFormat` values with safe defaults."""
    raw_formats = getattr(args, "formats", None)
    candidates: Iterable[OutputFormat | str | None]
    if raw_formats:
        candidates = raw_formats
    else:
        candidates = [getattr(args, "format", OutputFormat.PDF.value)]

    resolved: list[OutputFormat] = []
    for value in candidates:
        resolved.append(_coerce_output_format(value))
    return resolved


def _coerce_output_format(value: OutputFormat | str | None) -> OutputFormat:
    """Convert CLI-provided format values to `OutputFormat` with helpful errors."""
    if isinstance(value, OutputFormat):
        return value
    if isinstance(value, str):
        try:
            return OutputFormat(value)
        except ValueError as exc:
            raise ValidationError(
                f"{value!r} is not a supported output format",
                context={"format": value},
            ) from exc
    # Argparse guarantees a string, but unit tests often rely on bare mocks.
    # Default to PDF format so patches still exercise the code path.
    return OutputFormat.PDF


def _summarize_batch_result(
    result: GenerationResult | BatchGenerationResult,
    format_type: OutputFormat | str,
) -> int:
    """Summarize batch generation results for CLI output.

    Args:
        result: The batch generation result object.
        format_type: The format type (e.g., PDF, HTML).

    Returns:
        An exit code (0 for success, 1 for partial failure).

    """
    label = format_type.value if isinstance(format_type, OutputFormat) else format_type
    if isinstance(result, BatchGenerationResult):
        latex_skips: list[str] = []
        other_failures: list[tuple[str, Exception]] = []

        for name, error in (result.errors or {}).items():
            if isinstance(error, GenerationError) and "LaTeX" in str(error):
                latex_skips.append(name)
            else:
                other_failures.append((name, error))

        print(f"{label.upper()} generation summary")
        print(f"Successful: {result.successful}")
        print(f"Failed: {len(other_failures)}")
        if latex_skips:
            print(f"Skipped (LaTeX): {len(latex_skips)}")
            info_icon = "\N{INFORMATION SOURCE}\N{VARIATION SELECTOR-16}"
            templates = ", ".join(sorted(latex_skips))
            print(f"{info_icon} Skipped LaTeX template(s): {templates}")

        for name, error in other_failures:
            print(f"{name}: {error}")

        return 0 if not other_failures else 1

    return 0 if _did_generation_succeed(result) else 1


def _did_generation_succeed(result: GenerationResult) -> bool:
    """Check if generation succeeded.

    Args:
        result: Generation result with `exists` property.

    Returns:
        `True` if generation succeeded (output file exists), `False` otherwise.

    """
    return result.exists


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------


def _session_generate_resume(
    session: ResumeSession,
    resume_name: str,
    default_template: str | None = None,
) -> None:
    """Generate a single resume within an interactive session.

    Args:
        session: The active `ResumeSession`.
        resume_name: The name of the resume to generate.
        default_template: Default template to apply if not specified in resume.

    """
    try:
        resume = session.resume(resume_name)
    except (KeyError, FileNotFoundError, ValueError) as exc:
        # Expected errors when resume doesn't exist or has invalid data.
        print(f"Resume not found: {resume_name} ({exc})")
        return
    except Exception as exc:  # pragma: no cover - unexpected error
        logger = logging.getLogger(__name__)
        msg = f"Unexpected error loading resume {resume_name}: {exc}"
        logger.warning(msg, exc_info=True)
        print(f"Resume not found: {resume_name} ({exc})")
        return

    if default_template:
        resume = resume.with_template(default_template)

    session_format = getattr(session.config, "default_format", OutputFormat.PDF)
    formats = [_coerce_output_format(session_format)]
    overrides = session.config.session_metadata.get("overrides", {})
    overrides_dict = dict(overrides) if isinstance(overrides, dict) else {}

    plan_options = GeneratePlanOptions(
        name=resume_name,
        data_dir=session.paths.input,
        template=default_template or session.config.default_template,
        output_path=None,
        output_dir=None,
        preview=session.config.preview_mode,
        open_after=session.config.auto_open,
        browser=session.config.session_metadata.get("browser"),
        formats=formats,
        overrides=overrides_dict,
    )

    commands = build_generation_plan(plan_options)
    _run_session_generation(resume, session, commands)


def _session_list_resumes(session: ResumeSession) -> None:
    files = list(_iter_yaml_files(session))
    if not files:
        print("No resumes found.")
        return

    print("Available resumes:")
    for file_path in sorted(files):
        print(f"  - {Path(file_path).stem}")


def _iter_yaml_files(session: ResumeSession) -> Iterable[Path]:
    finder: Callable[[], Iterable[Path]] | None = getattr(
        session, "_find_yaml_files", None
    )
    if callable(finder):
        for candidate in finder():
            yield Path(candidate)
        return

    yield from session.paths.input.glob("*.yaml")
    yield from session.paths.input.glob("*.yml")


def _print_session_help() -> None:
    print("Available commands:")
    print("  generate <name>  Generate resume with the provided name")
    print("  list             List available resumes")
    print("  help, ?          Show this help message")
    print("  exit, quit       Exit the session")


def _run_session_generation(
    resume: Resume, session: ResumeSession, commands: list[GenerationCommand]
) -> None:
    """Execute planner commands inside an active `ResumeSession`."""
    output_dir = session.paths.output
    resume_label = getattr(resume, "_name", "resume")

    for command in commands:
        if command.kind is not CommandType.SINGLE:
            print("Session generate only supports single-resume commands today.")
            continue

        format_type = command.format or OutputFormat.PDF
        output_path = command.config.output_path
        if output_path is None:
            suffix = ".pdf" if format_type is OutputFormat.PDF else ".html"
            output_path = output_dir / f"{resume_label}{suffix}"

        try:
            if format_type is OutputFormat.PDF:
                result = to_pdf(
                    resume,
                    output_path=output_path,
                    open_after=command.config.open_after,
                )
            elif format_type is OutputFormat.HTML:
                result = to_html(
                    resume,
                    output_path=output_path,
                    open_after=command.config.open_after,
                    browser=command.config.browser,
                )
            else:
                print(f"Unsupported format: {format_type}")
                continue
        except SimpleResumeError as exc:
            print(f"Generation error for {resume_label}: {exc}")
            continue

        label = format_type.value.upper()
        if _did_generation_succeed(result):
            output_label = getattr(result, "output_path", output_path)
            print(f"{label} generated: {output_label}")
        else:
            print(f"Failed to generate {label}")


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _log_validation_result(name: str, validation: Any) -> bool:
    if validation.is_valid:
        warnings = _normalize_warnings(getattr(validation, "warnings", []))
        if warnings:
            for warning in warnings:
                print(f"Warning - {name}: {warning}")
        else:
            print(f"{name} is valid")
        return True

    print(f"Error - {name}: {'; '.join(validation.errors)}")
    return False


def _normalize_warnings(warnings: Any) -> list[str]:
    if not warnings:
        return []
    if isinstance(warnings, (list, tuple, set)):
        return [str(warning) for warning in warnings if warning]
    return [str(warnings)]


def _normalize_errors(errors: Any, default: list[str]) -> list[str]:
    """Normalize errors to a list of strings, with a default if empty."""
    if isinstance(errors, (list, tuple, set)):
        return [str(error) for error in errors if error]
    if errors:
        return [str(errors)]
    return default


def _validate_single_resume_cli(name: str, data_dir: Path | None) -> int:
    paths = resolve_paths(data_dir=data_dir) if data_dir else None
    resume = Resume.read_yaml(name, paths=paths)
    try:
        validation = resume.validate_or_raise()
    except ValidationError as exc:
        errors = _normalize_errors([], exc.errors)
        print(f"Error - {name}: {'; '.join(errors)}")
        return 1

    # Use the validation result from validate_or_raise() - no redundant calls
    warnings = _normalize_warnings(validation.warnings)
    if warnings:
        for warning in warnings:
            print(f"Warning - {name}: {warning}")
    else:
        print(f"{name} is valid")
    return 0


def _validate_all_resumes_cli(data_dir: Path | None) -> int:
    session_config = SessionConfig(default_template=None)
    with ResumeSession(data_dir=data_dir, config=session_config) as session:
        yaml_files = list(_iter_yaml_files(session))
        if not yaml_files:
            print("No resumes found to validate.")
            return 0

        valid = 0
        for file_path in yaml_files:
            resume_name = Path(file_path).stem
            resume = session.resume(resume_name)
            try:
                validation = resume.validate_or_raise()
            except ValidationError as exc:
                errors = _normalize_errors([], exc.errors)
                print(f"Error - {resume_name}: {'; '.join(errors)}")
                continue

            # Use the validation result from validate_or_raise() - no redundant calls
            warnings = _normalize_warnings(validation.warnings)
            if warnings:
                for warning in warnings:
                    print(f"Warning - {resume_name}: {warning}")
            else:
                print(f"{resume_name} is valid")
            valid += 1

    print(f"\nValidation complete: {valid}/{len(yaml_files)} resumes are valid")
    return 0 if valid == len(yaml_files) else 1


def _to_path_or_none(value: Any) -> Path | None:
    """Convert value to `Path` or `None`."""
    if value in (None, "", False):
        return None
    if isinstance(value, Path):
        return value
    if isinstance(value, str):
        return Path(value)
    fspath = getattr(value, "__fspath__", None)
    if callable(fspath):
        fspath_result = fspath()
        if isinstance(fspath_result, (str, Path)):
            return Path(fspath_result)
        if isinstance(fspath_result, PathLike):
            return Path(fspath_result)
    return None


def _select_output_path(output: Path | None) -> Path | None:
    if isinstance(output, Path):
        return output if output.is_file() or output.suffix else output
    return None


def _select_output_dir(output: Path | None) -> Path | None:
    if isinstance(output, Path):
        return output if output.is_dir() else output.parent
    return None


def _looks_like_palette_file(palette: str | Path) -> bool:
    """Check if palette argument looks like a YAML palette path."""
    path = Path(palette)
    return path.suffix.lower() in {".yaml", ".yml"}


def _build_config_overrides(args: argparse.Namespace) -> dict[str, Any]:
    """Construct a dictionary of configuration overrides from CLI arguments.

    Args:
        args: The parsed command-line arguments.

    Returns:
        A dictionary of configuration overrides.

    """
    overrides: dict[str, Any] = {}
    theme_color = getattr(args, "theme_color", None)
    palette = getattr(args, "palette", None)
    page_width = getattr(args, "page_width", None)
    page_height = getattr(args, "page_height", None)

    if isinstance(theme_color, str) and theme_color:
        overrides["theme_color"] = theme_color

    if isinstance(palette, (str, Path)) and palette:
        if _looks_like_palette_file(palette):
            palette_path = Path(palette)
            if palette_path.is_file():
                overrides["palette_file"] = str(palette_path)
            else:
                print(
                    f"Palette file '{palette_path}' not found. "
                    "Defaulting to resume or preset colors already configured."
                )
        else:
            overrides["color_scheme"] = str(palette)

    if isinstance(page_width, (int, float)):
        overrides["page_width"] = page_width
    if isinstance(page_height, (int, float)):
        overrides["page_height"] = page_height

    return overrides


def _build_plan_options(
    args: argparse.Namespace,
    overrides: dict[str, Any],
    formats: list[OutputFormat],
) -> GeneratePlanOptions:
    """Build `GeneratePlanOptions` from CLI arguments and overrides."""
    data_dir = _to_path_or_none(getattr(args, "data_dir", None))
    output_value = _to_path_or_none(getattr(args, "output", None))

    if getattr(args, "name", None):
        output_path = _select_output_path(output_value)
        output_dir = None
    else:
        output_path = None
        output_dir = _select_output_dir(output_value)

    return GeneratePlanOptions(
        name=getattr(args, "name", None),
        data_dir=data_dir,
        template=getattr(args, "template", None),
        output_path=output_path,
        output_dir=output_dir,
        preview=_bool_flag(getattr(args, "preview", False)),
        open_after=_bool_flag(getattr(args, "open", False)),
        browser=getattr(args, "browser", None),
        formats=formats,
        overrides=overrides,
    )


def _execute_generation_plan(commands: list[GenerationCommand]) -> int:
    """Execute a list of generation commands and summarize their results for CLI output.

    Args:
        commands: A list of `GenerationCommand` objects to execute.

    Returns:
        An exit code (0 for full success, non-zero for any failures).

    """
    exit_code = 0
    executions = execute_generation_commands(commands)
    for command, result in executions:
        if command.kind is CommandType.SINGLE:
            label = command.format.value.upper() if command.format else "OUTPUT"
            single_result = cast(GenerationResult, result)
            if _did_generation_succeed(single_result):
                output = getattr(result, "output_path", "generated")
                print(f"{label} generated: {output}")
            else:
                print(f"Failed to generate {label}")
                exit_code = max(exit_code, 1)
            continue

        if command.kind is CommandType.BATCH_SINGLE:
            format_type = command.format
            if format_type is None:
                print("Error: Missing format for batch command")
                exit_code = max(exit_code, 1)
                continue
            batch_payload = cast(GenerationResult | BatchGenerationResult, result)
            result_code = _summarize_batch_result(batch_payload, format_type)
            exit_code = max(exit_code, result_code)
            continue

        if not isinstance(result, dict):
            print("Error: Batch-all command returned unexpected payload")
            exit_code = max(exit_code, 1)
            continue

        # Cast to proper type since we know it's a
        # dict[str, BatchGenerationResult | GenerationResult]
        result_dict = cast(dict[str, BatchGenerationResult | GenerationResult], result)

        plan_code = 0
        for result_format, plan_result in result_dict.items():
            if isinstance(plan_result, BatchGenerationResult):
                batch_code = _summarize_batch_result(plan_result, result_format)
                plan_code = max(plan_code, batch_code)
            elif isinstance(plan_result, GenerationResult) and _did_generation_succeed(
                plan_result
            ):
                output = getattr(plan_result, "output_path", "generated")
                print(f"{result_format.upper()} generated: {output}")
            else:
                print(f"Failed to generate {result_format.upper()}")
                plan_code = 1
        exit_code = max(exit_code, plan_code)

    return exit_code


def _bool_flag(value: Any) -> bool:
    """Coerce a value to a boolean flag.

    Args:
        value: The value to coerce.

    Returns:
        True if the value is truthy, False otherwise.

    """
    return value if isinstance(value, bool) else False


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
