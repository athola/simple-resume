"""Enhanced CLI with new API patterns.

This module provides an improved command-line interface that uses the new
unified API with better error handling and user experience.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from . import __version__
from .core.resume import Resume, ValidationResult
from .exceptions import GenerationError, SimpleResumeError, TemplateError
from .generation import (
    GenerationConfig,
    generate_all,
    generate_html,
    generate_pdf,
    generate_resume,
)
from .result import BatchGenerationResult, GenerationResult
from .session import ResumeSession, SessionConfig


def _is_latex_only_html_error(error: Exception) -> bool:
    """Return True when exception is LaTeX-only resume rendered via HTML CLI."""
    if isinstance(error, GenerationError):
        context = error.__context__
        if isinstance(context, TemplateError):
            return "LaTeX mode not supported" in str(context)
        return "LaTeX mode not supported" in str(error)
    if isinstance(error, TemplateError):
        return "LaTeX mode not supported" in str(error)
    return False


def _partition_html_failures(
    result: BatchGenerationResult,
) -> tuple[dict[str, Exception], dict[str, Exception]]:
    """Split batch failures into LaTeX skips and real errors."""
    skipped: dict[str, Exception] = {}
    failures: dict[str, Exception] = {}
    for name, error in result.get_failed().items():
        if _is_latex_only_html_error(error):
            skipped[name] = error
        else:
            failures[name] = error
    return skipped, failures


def _print_success_rate(
    success_count: int,
    failure_count: int,
    skipped: Mapping[str, Exception],
) -> None:
    """Print success rate with appropriate formatting."""
    effective_total = success_count + failure_count
    if effective_total:
        success_rate = (success_count / effective_total) * 100
        print(f"Success rate: {success_rate:.1f}%")
    elif skipped:
        print("Success rate: n/a (only LaTeX templates skipped)")
    else:
        print("Success rate: 0.0%")


def _collect_page_overflow_resumes(
    successful_results: Mapping[str, GenerationResult],
    format_type: str,
) -> list[tuple[str, int]]:
    """Collect resumes with page overflow for PDF format."""
    if format_type != "pdf":
        return []

    page_overflow_resumes = []
    for name, gen_result in successful_results.items():
        metadata = getattr(gen_result, "metadata", None)
        page_count = getattr(metadata, "page_count", None) if metadata else None
        if page_count and page_count > 1:
            page_overflow_resumes.append((name, page_count))
    return page_overflow_resumes


def _display_batch_result(format_type: str, result: BatchGenerationResult) -> None:
    """Render a summary of batch generation results."""
    format_upper = format_type.upper()
    print(f"\n=== {format_upper} Results ===")

    # Get failures and skipped items
    if format_type == "html":
        skipped, failures = _partition_html_failures(result)
    else:
        skipped = {}
        failures = result.get_failed()

    successful_results = result.get_successful()
    success_count = len(successful_results)
    failure_count = len(failures)

    # Print summary statistics
    print(f"Successful: {success_count}")
    if skipped:
        print(f"Skipped (LaTeX): {len(skipped)}")
    print(f"Failed: {failure_count}")

    _print_success_rate(success_count, failure_count, skipped)

    if hasattr(result, "total_time"):
        print(f"Total time: {result.total_time:.2f}s")

    # Display successful results and collect overflow warnings
    page_overflow_resumes = _collect_page_overflow_resumes(
        successful_results, format_type
    )
    for gen_result in successful_results.values():
        print(f"✓ Generated {format_upper}: {gen_result.output_path}")

    # Display failures
    for name, error in failures.items():
        print(f"✗ Failed {name}: {error}")

    # Display skipped LaTeX templates
    if skipped:
        skipped_list = ", ".join(sorted(skipped))
        print(
            "ℹ️ Skipped LaTeX template(s): "
            f"{skipped_list}. Use the PDF format to render these resumes."
        )

    # Display page overflow warnings
    if page_overflow_resumes:
        print("\n⚠️  Page Overflow Warnings:")
        for name, page_count in page_overflow_resumes:
            print(
                f"  • {name}: {page_count} pages - "
                "Consider consolidating content to fit on 1 page"
            )


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="simple-resume",
        description="Generate professional resumes from YAML data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all resumes as PDFs
  simple-resume generate --format pdf

  # Generate specific resume with template
  simple-resume generate my_resume --template professional --open

  # Generate multiple formats
  simple-resume generate my_resume --formats pdf html

  # Use session with custom data directory
  simple-resume generate --data-dir ./my_resumes --template modern

  # Generate in preview mode
  simple-resume generate my_resume --preview --open
        """,
    )

    parser.add_argument(
        "--version", action="version", version=f"simple-resume {__version__}"
    )

    subparsers = parser.add_subparsers(
        dest="command", help="Available commands", required=True
    )

    # Generate command
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate resume(s)",
        description="Generate one or more resumes in specified formats",
    )

    generate_parser.add_argument(
        "name", nargs="?", help="Resume name to generate (omit for all resumes)"
    )

    generate_parser.add_argument(
        "--format",
        "-f",
        choices=["pdf", "html"],
        default="pdf",
        help="Output format (default: pdf)",
    )

    generate_parser.add_argument(
        "--formats",
        nargs="+",
        choices=["pdf", "html"],
        help="Multiple formats to generate",
    )

    generate_parser.add_argument("--template", "-t", help="Template name to use")

    generate_parser.add_argument(
        "--output", "-o", type=Path, help="Output directory or file path"
    )

    generate_parser.add_argument(
        "--data-dir", "-d", type=Path, help="Data directory containing resume files"
    )

    generate_parser.add_argument(
        "--open", action="store_true", help="Open generated file(s) after creation"
    )

    generate_parser.add_argument(
        "--preview", action="store_true", help="Generate in preview mode"
    )

    generate_parser.add_argument(
        "--browser", help="Browser to use for opening HTML files"
    )

    # Add configuration overrides
    generate_parser.add_argument(
        "--theme-color", help="Theme color (hex format, e.g., #0395DE)"
    )

    generate_parser.add_argument(
        "--palette", help="Color palette name or configuration"
    )

    generate_parser.add_argument(
        "--page-width", type=int, help="Page width in millimeters"
    )

    generate_parser.add_argument(
        "--page-height", type=int, help="Page height in millimeters"
    )

    # Session command
    session_parser = subparsers.add_parser(
        "session",
        help="Interactive session for multiple operations",
        description="Start an interactive session for batch operations",
    )

    session_parser.add_argument(
        "--data-dir", "-d", type=Path, help="Data directory for the session"
    )

    session_parser.add_argument(
        "--template", "-t", help="Default template for the session"
    )

    session_parser.add_argument(
        "--preview", action="store_true", help="Default to preview mode"
    )

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate resume data",
        description="Validate one or more resume files without generating",
    )

    validate_parser.add_argument(
        "name", nargs="?", help="Resume name to validate (omit for all resumes)"
    )

    validate_parser.add_argument(
        "--data-dir", "-d", type=Path, help="Data directory containing resume files"
    )

    return parser


def _page_count(result: GenerationResult) -> int | None:
    """Safely extract page_count metadata for warnings."""
    metadata = getattr(result, "metadata", None)
    value = getattr(metadata, "page_count", None) if metadata else None
    return value if isinstance(value, int) and value >= 0 else None


def _result_exists(result: GenerationResult) -> bool:
    """Support both property-style and callable exists checks."""
    exists_attr = getattr(result, "exists", None)
    if callable(exists_attr):
        try:
            return bool(exists_attr())
        except Exception:
            return False
    return bool(exists_attr)


def _build_config_overrides(args: argparse.Namespace) -> dict[str, Any]:
    """Build configuration overrides from command-line arguments."""
    config_overrides: dict[str, Any] = {}
    if args.theme_color:
        config_overrides["theme_color"] = args.theme_color
    if args.palette:
        config_overrides["color_scheme"] = args.palette
    if args.page_width:
        config_overrides["page_width"] = args.page_width
    if args.page_height:
        config_overrides["page_height"] = args.page_height
    return config_overrides


def _get_output_path(args: argparse.Namespace) -> Path | None:
    """Determine output path from arguments."""
    if not args.output:
        return None
    if not isinstance(args.output, Path):
        return None
    if args.output.is_dir() or not args.output.suffix:
        return args.output
    return args.output


def _display_single_result_with_warnings(
    result: GenerationResult,
    format_type: str,
    should_open: bool,
) -> None:
    """Display generation result and check for warnings."""
    print(f"✓ Generated {format_type.upper()}: {result.output_path}")

    # Check for page overflow (PDF only)
    if format_type == "pdf":
        page_count = _page_count(result)
        if page_count and page_count > 1:
            print(f"\n⚠️  Page Overflow Warning: {result.metadata.page_count} pages")
            print("  Consider consolidating content to fit on 1 page")

    if should_open and _result_exists(result):
        result.open()


def _handle_single_resume_multiple_formats(
    args: argparse.Namespace,
    config_overrides: Mapping[str, Any],
    output_path: Path | None,
) -> int:
    """Generate single resume in multiple formats."""
    for format_type in args.formats:
        config = GenerationConfig(
            name=args.name,
            data_dir=args.data_dir,
            format=format_type,
            template=args.template,
            output_path=output_path,
            open_after=args.open,
            preview=args.preview,
        )
        result = generate_resume(config, **config_overrides)
        _display_single_result_with_warnings(result, format_type, args.open)
    return 0


def _handle_multiple_resumes_multiple_formats(
    args: argparse.Namespace,
    config_overrides: Mapping[str, Any],
    output_path: Path | None,
) -> int:
    """Generate multiple resumes in multiple formats."""
    config = GenerationConfig(
        data_dir=args.data_dir,
        formats=args.formats,
        template=args.template,
        output_dir=output_path,
        open_after=args.open,
        preview=args.preview,
    )
    all_results = generate_all(config, **config_overrides)

    for format_type, result in all_results.items():
        if isinstance(result, BatchGenerationResult):
            _display_batch_result(format_type, result)
        else:
            print(f"✓ Generated {format_type.upper()}: {result.output_path}")
    return 0


def _handle_single_resume_single_format(
    args: argparse.Namespace,
    config_overrides: Mapping[str, Any],
    output_path: Path | None,
    format_type: str,
) -> int:
    """Generate single resume in single format."""
    config = GenerationConfig(
        name=args.name,
        data_dir=args.data_dir,
        format=format_type,
        template=args.template,
        output_path=output_path,
        open_after=args.open,
        preview=args.preview,
    )
    result = generate_resume(config, **config_overrides)
    _display_single_result_with_warnings(result, format_type, args.open)
    return 0


def _handle_multiple_resumes_single_format(
    args: argparse.Namespace,
    config_overrides: Mapping[str, Any],
    output_path: Path | None,
    format_type: str,
) -> int:
    """Generate multiple resumes in single format."""
    if format_type == "pdf":
        config = GenerationConfig(
            data_dir=args.data_dir,
            template=args.template,
            output_dir=output_path,
            open_after=args.open,
            preview=args.preview,
        )
        result = generate_pdf(config, **config_overrides)
    else:  # html
        config = GenerationConfig(
            data_dir=args.data_dir,
            template=args.template,
            output_dir=output_path,
            open_after=args.open,
            browser=args.browser,
            preview=args.preview,
        )
        result = generate_html(config, **config_overrides)

    if isinstance(result, BatchGenerationResult):
        _display_batch_result(format_type, result)
    else:
        _display_single_result_with_warnings(result, format_type, False)
    return 0


def handle_generate_command(args: argparse.Namespace) -> int:
    """Handle the generate command."""
    try:
        config_overrides = _build_config_overrides(args)
        output_path = _get_output_path(args)

        # Route to appropriate handler based on scenario
        if args.formats:
            if args.name:
                return _handle_single_resume_multiple_formats(
                    args, config_overrides, output_path
                )
            return _handle_multiple_resumes_multiple_formats(
                args, config_overrides, output_path
            )

        format_type = args.format
        if args.name:
            return _handle_single_resume_single_format(
                args, config_overrides, output_path, format_type
            )
        return _handle_multiple_resumes_single_format(
            args, config_overrides, output_path, format_type
        )

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        return 130
    except Exception as exc:
        is_known_error = isinstance(exc, SimpleResumeError)
        error_prefix = "Error" if is_known_error else "Unexpected error"
        print(f"{error_prefix}: {exc}", file=sys.stderr)
        return 1


def _session_cmd_help() -> None:
    """Display session help."""
    print("Available commands:")
    print("  generate [name] - Generate resume(s)")
    print("  list - List available resumes")
    print("  validate [name] - Validate resume(s)")
    print("  status - Show session status")
    print("  exit/quit - Exit session")


def _session_cmd_generate(session: ResumeSession, parts: Sequence[str]) -> None:
    """Handle generate command in session."""
    if len(parts) > 1:
        name = parts[1]
        result = session.resume(name).to_pdf(open_after=True)
        print(f"✓ Generated PDF: {result.output_path}")
    else:
        batch_result = session.generate_all(format="pdf", open_after=True)
        print(f"Generated {len(batch_result.get_successful())} PDFs successfully")


def _session_cmd_list(session: ResumeSession) -> None:
    """Handle list command in session."""
    yaml_files = session._find_yaml_files()
    if yaml_files:
        print("Available resumes:")
        for yaml_file in yaml_files:
            print(f"  • {yaml_file.stem}")
    else:
        print("No resume files found.")


def _session_cmd_validate(session: ResumeSession, parts: Sequence[str]) -> None:
    """Handle validate command in session."""
    if len(parts) > 1:
        name = parts[1]
        resume = session.resume(name)
        validation = resume.validate()
        if validation.is_valid:
            print(f"✓ {name} is valid")
        else:
            print(f"✗ {name} validation failed:")
            for error in validation.errors:
                print(f"  - {error}")
    else:
        print("Usage: validate <name>")


def _session_cmd_status(session: ResumeSession) -> None:
    """Handle status command in session."""
    cache_info = session.get_cache_info()
    print(f"Session ID: {session.session_id}")
    print(f"Operations: {session.operation_count}")
    print(f"Cached resumes: {cache_info['cache_size']}")
    print(f"Average generation time: {session.average_generation_time:.2f}s")


def _process_session_command(session: ResumeSession, command: str) -> bool:
    """Process a single session command. Returns True to exit, False to continue."""
    if not command:
        return False

    parts = command.split()
    cmd = parts[0].lower()

    if cmd in ["exit", "quit"]:
        return True

    command_handlers: dict[str, Callable[[], None]] = {
        "help": _session_cmd_help,
        "generate": lambda: _session_cmd_generate(session, parts),
        "list": lambda: _session_cmd_list(session),
        "validate": lambda: _session_cmd_validate(session, parts),
        "status": lambda: _session_cmd_status(session),
    }

    handler = command_handlers.get(cmd)
    if handler:
        handler()
    else:
        print(f"Unknown command: {cmd}. Type 'help' for available commands.")

    return False


def handle_session_command(args: argparse.Namespace) -> int:
    """Handle the session command."""
    try:
        print("🚀 Starting Simple-Resume Session")
        print("=" * 40)

        session_config = SessionConfig(
            default_template=args.template,
            preview_mode=args.preview,
        )

        with ResumeSession(data_dir=args.data_dir, config=session_config) as session:
            print(f"Session ID: {session.session_id}")
            print(f"Data directory: {session.paths.input}")
            print(f"Output directory: {session.paths.output}")
            print()

            # Interactive prompt loop
            while True:
                try:
                    command = input("simple-resume> ").strip()
                    should_exit = _process_session_command(session, command)
                    if should_exit:
                        break

                except EOFError:
                    break
                except KeyboardInterrupt:
                    print()
                    continue
                except Exception as exc:
                    print(f"Error: {exc}")

        print("\nSession ended.")
        return 0

    except SimpleResumeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def _display_validation_result(
    name: str,
    validation: ValidationResult,
    verbose: bool = True,
) -> None:
    """Display validation result for a single resume."""
    if validation.is_valid:
        print(f"✓ {name}" if not verbose else f"✓ {name} is valid")
        if validation.warnings:
            if verbose:
                print("Warnings:")
            for warning in validation.warnings:
                prefix = "  ⚠ " if verbose else "  ⚠ "
                print(f"{prefix}{warning}")
    else:
        print(f"✗ {name}" if not verbose else f"✗ {name} validation failed:")
        for error in validation.errors:
            prefix = "    • " if not verbose else "  • "
            print(f"{prefix}{error}")


def _validate_single_resume(args: argparse.Namespace) -> int:
    """Validate a single resume."""
    resume = Resume.read_yaml(args.name, data_dir=args.data_dir)
    validation = resume.validate()
    _display_validation_result(args.name, validation, verbose=True)
    return 0 if validation.is_valid else 1


def _validate_all_resumes(args: argparse.Namespace) -> int:
    """Validate all resumes in the data directory."""
    with ResumeSession(data_dir=args.data_dir) as session:
        yaml_files = session._find_yaml_files()
        if not yaml_files:
            print("No resume files found.")
            return 0

        valid_count = 0
        total_count = len(yaml_files)

        for yaml_file in yaml_files:
            name = yaml_file.stem
            try:
                resume = session.resume(name)
                validation = resume.validate()
                _display_validation_result(name, validation, verbose=False)
                if validation.is_valid:
                    valid_count += 1
            except Exception as exc:
                print(f"✗ {name}: {exc}")

        print(f"\nValidation complete: {valid_count}/{total_count} resumes are valid")
        return 0 if valid_count == total_count else 1


def handle_validate_command(args: argparse.Namespace) -> int:
    """Handle the validate command."""
    try:
        if args.name:
            return _validate_single_resume(args)
        return _validate_all_resumes(args)

    except SimpleResumeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def main() -> int:
    """Run main CLI entry point."""
    try:
        parser = create_parser()
        args = parser.parse_args()

        if args.command == "generate":
            return handle_generate_command(args)
        elif args.command == "session":
            return handle_session_command(args)
        elif args.command == "validate":
            return handle_validate_command(args)
        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
