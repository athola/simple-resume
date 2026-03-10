"""Provide a command-line interface for simple-resume, backed by the generation API."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, Protocol

from simple_resume import __version__
from simple_resume.core.constants import OutputFormat
from simple_resume.core.exceptions import SimpleResumeError, ValidationError
from simple_resume.core.generate.plan import (
    CommandType,
    GeneratePlanOptions,
    GenerationCommand,
    build_generation_plan,
)
from simple_resume.core.resume import Resume
from simple_resume.shell.cli._errors import (  # noqa: F401
    _handle_unexpected_error,
)
from simple_resume.shell.cli._generation import (  # noqa: F401
    _bool_flag,
    _build_config_overrides,
    _build_plan_options,
    _coerce_output_format,
    _did_generation_succeed,
    _execute_generation_plan,
    _looks_like_palette_file,
    _resolve_cli_formats,
    _select_output_dir,
    _select_output_path,
    _summarize_batch_result,
    _to_path_or_none,
)
from simple_resume.shell.cli._import import (  # noqa: F401
    handle_import_command,
)
from simple_resume.shell.cli._screen import (  # noqa: F401
    _collect_ats_warnings,
    _format_text_report,
    _get_status_label,
    _read_file_text,
    handle_screen_command,
)
from simple_resume.shell.cli._tailor import (  # noqa: F401
    handle_tailor_command,
)
from simple_resume.shell.config import resolve_paths
from simple_resume.shell.resume_extensions import (
    render_markdown_file,
    render_tex_file,
    to_html,
    to_markdown,
    to_pdf,
    to_tex,
)
from simple_resume.shell.services import register_default_services
from simple_resume.shell.session import ResumeSession, SessionConfig


class GenerationResultProtocol(Protocol):
    """A protocol for objects representing generation results."""

    @property
    def exists(self) -> bool:
        """Check if the generated output exists and is valid."""
        ...


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
        "screen": handle_screen_command,
        "import": handle_import_command,
        "tailor": handle_tailor_command,
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
        choices=["pdf", "html", "markdown", "tex"],
        default="markdown",
        help="Output format (default: markdown). Use markdown/tex for intermediate "
        "files that can be edited before final render.",
    )
    generate_parser.add_argument(
        "--formats",
        nargs="+",
        choices=["pdf", "html", "markdown", "tex"],
        help="Generate in multiple formats (only valid when name is supplied)",
    )
    generate_parser.add_argument(
        "--output-mode",
        "-m",
        choices=["markdown", "tex"],
        help="Intermediate format: markdown (for HTML) or tex (for PDF). "
        "Overrides the output_mode in config file.",
    )
    generate_parser.add_argument(
        "--no-render",
        action="store_true",
        help="Only generate intermediate files (markdown/tex) without "
        "rendering to final PDF/HTML output.",
    )
    generate_parser.add_argument(
        "--render-file",
        type=Path,
        metavar="FILE",
        help="Render an existing .md or .tex file to PDF/HTML instead of "
        "processing YAML input.",
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

    # screen subcommand
    screen_parser = subparsers.add_parser(
        "screen",
        help="Screen resume against job description using ATS scoring",
    )
    screen_parser.add_argument(
        "resume",
        type=Path,
        help="Path to resume file (PDF, HTML, YAML, or text)",
    )
    screen_parser.add_argument(
        "job",
        type=Path,
        help="Path to job description file (YAML, text, or URL)",
    )
    screen_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output path for scoring report (default: stdout)",
    )
    screen_parser.add_argument(
        "--format",
        "-f",
        choices=["yaml", "json", "text"],
        default="text",
        help="Report format (default: text for human-readable output)",
    )
    screen_parser.add_argument(
        "--scorers",
        choices=["all", "tfidf", "jaccard", "keyword"],
        default="all",
        help="Which scorers to use (default: all)",
    )
    screen_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed breakdown of scores",
    )

    # import subcommand
    import_parser = subparsers.add_parser(
        "import",
        help="Import a LinkedIn profile and convert to simple-resume YAML",
    )
    import_parser.add_argument(
        "linkedin",
        help="Path to LinkedIn profile file (HTML or text)",
    )
    import_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output YAML file path (default: same name with .yaml extension)",
    )

    # tailor subcommand
    tailor_parser = subparsers.add_parser(
        "tailor",
        help="Tailor resume to a job posting using gap analysis and LLM",
    )
    tailor_parser.add_argument(
        "resume",
        type=Path,
        help="Path to resume YAML file",
    )
    tailor_parser.add_argument(
        "job",
        type=Path,
        help="Path to job posting file (text)",
    )
    tailor_parser.add_argument(
        "--api-key",
        help="API key for LLM provider (or set OPENAI_API_KEY env var)",
    )
    tailor_parser.add_argument(
        "--model",
        help="LLM model identifier (default: claude-sonnet-4-20250514)",
    )
    tailor_parser.add_argument(
        "--report",
        action="store_true",
        help="Show gap analysis report only, without LLM tailoring",
    )

    return parser


def handle_generate_command(args: argparse.Namespace) -> int:
    """Handle the generate subcommand using generation helpers."""
    # Handle --render-file separately (renders existing .md/.tex file)
    render_file = getattr(args, "render_file", None)
    if render_file is not None:
        return _handle_render_file(args, render_file)

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


def _handle_render_file(args: argparse.Namespace, render_file: Path) -> int:  # noqa: PLR0911
    """Render an existing .md or .tex file to PDF/HTML.

    Args:
        args: The parsed command-line arguments.
        render_file: Path to the .md or .tex file to render.

    Returns:
        Exit code (0 for success, non-zero for failure).

    """
    if not render_file.exists():
        print(f"Error: File not found: {render_file}")
        return 1

    suffix = render_file.suffix.lower()
    output_value = _to_path_or_none(getattr(args, "output", None))
    open_after = _bool_flag(getattr(args, "open", False))

    try:
        if suffix == ".md":
            # Render markdown to HTML
            output_path = output_value or render_file.with_suffix(".html")
            result = render_markdown_file(
                render_file,
                output_path=output_path,
                open_after=open_after,
            )
            if result.exists:
                print(f"HTML generated: {result.output_path}")
                return 0
            print("Failed to generate HTML")
            return 1

        if suffix == ".tex":
            # Render LaTeX to PDF
            output_path = output_value or render_file.with_suffix(".pdf")
            result = render_tex_file(
                render_file,
                output_path=output_path,
                open_after=open_after,
            )
            if result.exists:
                print(f"PDF generated: {result.output_path}")
                return 0
            print("Failed to generate PDF")
            return 1

        print(f"Error: Unsupported file type: {suffix}")
        print("Use .md for markdown or .tex for LaTeX files")
        return 1

    except SimpleResumeError as exc:
        print(f"Error: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - safety net
        return _handle_unexpected_error(exc, "file rendering")


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
    yield from session.paths.input.glob("*.json")


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
            suffix_map = {
                OutputFormat.PDF: ".pdf",
                OutputFormat.HTML: ".html",
                OutputFormat.MARKDOWN: ".md",
                OutputFormat.TEX: ".tex",
            }
            suffix = suffix_map.get(format_type, ".pdf")
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
            elif format_type is OutputFormat.MARKDOWN:
                result = to_markdown(
                    resume,
                    output_path=output_path,
                )
            elif format_type is OutputFormat.TEX:
                result = to_tex(
                    resume,
                    output_path=output_path,
                )
            else:
                print(f"Unsupported format: {format_type}")
                continue
        except SimpleResumeError as exc:
            print(f"Generation error for {resume_label}: {exc}")
            continue

        # Friendly labels for output messages
        label_map = {
            OutputFormat.PDF: "PDF",
            OutputFormat.HTML: "HTML",
            OutputFormat.MARKDOWN: "Markdown",
            OutputFormat.TEX: "LaTeX",
        }
        label = label_map.get(format_type, format_type.value.upper())
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

if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
