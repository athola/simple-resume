"""Command line interface for simple-resume backed by the generation API."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable, Iterable
from os import PathLike
from pathlib import Path
from typing import Any, Protocol

from . import __version__
from .config import resolve_paths
from .core.resume import Resume
from .exceptions import GenerationError, SimpleResumeError, ValidationError
from .generation import (
    GenerationConfig,
)
from .generation import (
    generate_all as _generate_all,
)
from .generation import (
    generate_html as _generate_html,
)
from .generation import (
    generate_pdf as _generate_pdf,
)
from .generation import (
    generate_resume as _generate_resume,
)
from .result import BatchGenerationResult, GenerationResult
from .session import ResumeSession, SessionConfig


class GenerationResultProtocol(Protocol):
    """Protocol for objects that represent generation results."""

    @property
    def exists(self) -> bool:
        """Check if the generated output exists and is valid."""
        ...


def _handle_unexpected_error(exc: Exception, context: str) -> int:
    """Handle unexpected exceptions with proper logging and classification.

    Args:
        exc: The unexpected exception
        context: Context where the error occurred (e.g., "generation", "validation")

    Returns:
        Appropriate exit code

    """
    logger = logging.getLogger(__name__)

    # Classify the error type for better user experience
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

    # Log the full error for debugging
    logger.error(
        f"{error_type} in {context}: {exc}",
        exc_info=True,
        extra={
            "error_type": error_type,
            "context": context,
            "exception_type": type(exc).__name__,
        },
    )

    # Show user-friendly message
    print(f"{error_type}: {exc}")
    if suggestion:
        print(f"Suggestion: {suggestion}")

    return exit_code


# Expose generation helpers so downstream code and tests can patch them.
generate_all = _generate_all
generate_html = _generate_html
generate_pdf = _generate_pdf
generate_resume = _generate_resume


def main() -> int:
    """Run the CLI entry point."""
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
    """Handle the generate subcommand using the generation helpers."""
    overrides = _build_config_overrides(args)
    try:
        if args.name:
            return _generate_single_resume(args, overrides)
        return _generate_batch_resumes(args, overrides)
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


# ---------------------------------------------------------------------------
# Generation helpers
# ---------------------------------------------------------------------------


def _generate_single_resume(args: argparse.Namespace, overrides: dict[str, Any]) -> int:
    formats = args.formats or [args.format]
    successes: list[bool] = []

    output_value = getattr(args, "output", None)
    output_path = _select_output_path(_to_path_or_none(output_value))

    for format_type in formats:
        config = GenerationConfig(
            name=args.name,
            data_dir=_to_path_or_none(args.data_dir),
            template=args.template,
            format=format_type,
            output_path=output_path,
            open_after=_bool_flag(getattr(args, "open", False)),
            preview=_bool_flag(getattr(args, "preview", False)),
            browser=getattr(args, "browser", None),
        )

        result = generate_resume(config, **overrides)
        success = _did_generation_succeed(result)
        successes.append(success)

        if success:
            output = getattr(result, "output_path", "generated")
            print(f"✓ {format_type.upper()} generated: {output}")
        else:
            print(f"✗ Failed to generate {format_type.upper()}")

    return 0 if all(successes) else 1


def _generate_batch_resumes(args: argparse.Namespace, overrides: dict[str, Any]) -> int:
    formats = args.formats or [args.format]
    data_dir = _to_path_or_none(args.data_dir)
    output_value = getattr(args, "output", None)
    output_dir = _select_output_dir(_to_path_or_none(output_value))

    if len(formats) == 1:
        format_type = formats[0]
        config = GenerationConfig(
            data_dir=data_dir,
            template=args.template,
            output_dir=output_dir,
            open_after=_bool_flag(getattr(args, "open", False)),
            preview=_bool_flag(getattr(args, "preview", False)),
            browser=getattr(args, "browser", None),
        )

        if format_type == "pdf":
            batch_result = generate_pdf(config, **overrides)
        elif format_type == "html":
            batch_result = generate_html(config, **overrides)
        else:
            print(f"Error: Unsupported format: {format_type}")
            return 1

        return _summarize_batch_result(batch_result, format_type)

    config = GenerationConfig(
        data_dir=data_dir,
        template=args.template,
        output_dir=output_dir,
        open_after=_bool_flag(getattr(args, "open", False)),
        preview=_bool_flag(getattr(args, "preview", False)),
        browser=getattr(args, "browser", None),
        formats=formats,
    )

    results = generate_all(config, **overrides)
    exit_code = 0
    for format_type, result in results.items():
        code = _summarize_batch_result(result, format_type)
        exit_code = max(exit_code, code)
    return exit_code


def _summarize_batch_result(
    result: GenerationResult | BatchGenerationResult,
    format_type: str,
) -> int:
    if isinstance(result, BatchGenerationResult):
        latex_skips: list[str] = []
        other_failures: list[tuple[str, Exception]] = []

        for name, error in (result.errors or {}).items():
            if isinstance(error, GenerationError) and "LaTeX" in str(error):
                latex_skips.append(name)
            else:
                other_failures.append((name, error))

        print(f"{format_type.upper()} generation summary")
        print(f"Successful: {result.successful}")
        print(f"Failed: {len(other_failures)}")
        if latex_skips:
            print(f"Skipped (LaTeX): {len(latex_skips)}")
            print(f"ℹ️ Skipped LaTeX template(s): {', '.join(sorted(latex_skips))}")

        for name, error in other_failures:
            print(f"✗ {name}: {error}")

        return 0 if not other_failures else 1

    return 0 if _did_generation_succeed(result) else 1


def _did_generation_succeed(result: GenerationResultProtocol) -> bool:
    """Check if generation succeeded.

    Args:
        result: Generation result with exists property

    Returns:
        True if generation succeeded (output file exists), False otherwise

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
    try:
        resume = session.resume(resume_name)
    except (KeyError, FileNotFoundError, ValueError) as exc:
        # Expected errors when resume doesn't exist or has invalid data
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

    result = resume.to_pdf()
    if _did_generation_succeed(result):
        print(f"Generated: {getattr(result, 'output_path', 'output.pdf')}")
    else:
        print(f"Generation failed for {resume_name}")


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


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _log_validation_result(name: str, validation: Any) -> bool:
    if validation.is_valid:
        warnings = _normalize_warnings(getattr(validation, "warnings", []))
        if warnings:
            for warning in warnings:
                print(f"⚠️ {name}: {warning}")
        else:
            print(f"✓ {name} is valid")
        return True

    print(f"✗ {name}: {'; '.join(validation.errors)}")
    return False


def _normalize_warnings(warnings: Any) -> list[str]:
    if not warnings:
        return []
    if isinstance(warnings, (list, tuple, set)):
        return [str(warning) for warning in warnings if warning]
    return [str(warnings)]


def _normalize_errors(errors: Any, fallback: list[str]) -> list[str]:
    if isinstance(errors, (list, tuple, set)):
        return [str(error) for error in errors if error]
    if errors:
        return [str(errors)]
    return fallback


def _validate_single_resume_cli(name: str, data_dir: Path | None) -> int:
    paths = resolve_paths(data_dir=data_dir) if data_dir else None
    resume = Resume.read_yaml(name, paths=paths)
    validation = resume.validate()
    try:
        resume.validate_or_raise()
    except ValidationError as exc:
        errors = _normalize_errors(getattr(validation, "errors", None), exc.errors)
        if not errors:
            errors = [str(exc)]
        print(f"✗ {name}: {'; '.join(errors)}")
        return 1

    warnings = _normalize_warnings(getattr(validation, "warnings", []))
    if warnings:
        for warning in warnings:
            print(f"⚠️ {name}: {warning}")
    else:
        print(f"✓ {name} is valid")
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
            validation = resume.validate()
            try:
                resume.validate_or_raise()
            except ValidationError as exc:
                errors = _normalize_errors(
                    getattr(validation, "errors", None), exc.errors
                )
                if not errors:
                    errors = [str(exc)]
                print(f"✗ {resume_name}: {'; '.join(errors)}")
                continue

            warnings = _normalize_warnings(getattr(validation, "warnings", []))
            if warnings:
                for warning in warnings:
                    print(f"⚠️ {resume_name}: {warning}")
            else:
                print(f"✓ {resume_name} is valid")
            valid += 1

    print(f"\nValidation complete: {valid}/{len(yaml_files)} resumes are valid")
    return 0 if valid == len(yaml_files) else 1


def _to_path_or_none(value: Any) -> Path | None:
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
    """Check if palette argument points to an existing YAML file."""
    path = Path(palette)
    return path.suffix.lower() in {".yaml", ".yml"} and path.is_file()


def _build_config_overrides(args: argparse.Namespace) -> dict[str, Any]:
    overrides: dict[str, Any] = {}
    theme_color = getattr(args, "theme_color", None)
    palette = getattr(args, "palette", None)
    page_width = getattr(args, "page_width", None)
    page_height = getattr(args, "page_height", None)

    if isinstance(theme_color, str) and theme_color:
        overrides["theme_color"] = theme_color

    if isinstance(palette, (str, Path)) and palette:
        if _looks_like_palette_file(palette):
            # Keep as Path object - load_palette_from_file accepts str | Path
            overrides["palette_file"] = palette
        else:
            overrides["color_scheme"] = palette

    if isinstance(page_width, (int, float)):
        overrides["page_width"] = page_width
    if isinstance(page_height, (int, float)):
        overrides["page_height"] = page_height

    return overrides


def _bool_flag(value: Any) -> bool:
    return value if isinstance(value, bool) else False


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
