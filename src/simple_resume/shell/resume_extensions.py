"""Shell layer functions for Resume I/O operations.

This module provides the I/O operations for Resume that live in the shell layer,
keeping the core Resume class pure and functional.

Functions:
    to_pdf: Generate PDF from a Resume
    to_html: Generate HTML from a Resume
    generate: Generate output in specified format from a Resume
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import TYPE_CHECKING, cast

from simple_resume.core.constants import OutputFormat
from simple_resume.core.exceptions import ConfigurationError, GenerationError
from simple_resume.core.protocols import PdfGenerationStrategy
from simple_resume.core.result import GenerationResult
from simple_resume.shell.file_opener import open_file as shell_open_file
from simple_resume.shell.render.operations import generate_html_with_jinja
from simple_resume.shell.services import DefaultPdfGenerationStrategy
from simple_resume.shell.strategies import PdfGenerationRequest

if TYPE_CHECKING:
    from simple_resume.core.resume import Resume


def _get_pdf_strategy(mode: str) -> PdfGenerationStrategy:
    """Get the appropriate PDF generation strategy from service locator."""
    return DefaultPdfGenerationStrategy(mode)


def to_pdf(
    resume: Resume,
    output_path: Path | str | None = None,
    *,
    open_after: bool = False,
    strategy: PdfGenerationStrategy | None = None,
) -> GenerationResult:
    """Generate PDF from a Resume.

    This is the shell-layer implementation that handles PDF generation
    with proper strategy injection and shell service dependencies.

    Args:
        resume: The Resume instance to generate PDF from.
        output_path: Optional output path (defaults to output directory).
        open_after: Whether to open the PDF after generation.
        strategy: Optional custom PDF generation strategy (for testing).

    Returns:
        GenerationResult with metadata and output path.

    Raises:
        ConfigurationError: If paths are not available.
        GenerationError: If PDF generation fails.

    """
    try:
        # Prepare render plan
        render_plan = resume.prepare_render_plan(preview=False)

        # Determine output path
        if output_path is None:
            if resume.paths is None:
                raise ConfigurationError(
                    "No paths available - provide output_path or create with paths",
                    filename=resume.filename,
                )
            resolved_path = resume.paths.output / f"{resume.name}.pdf"
        else:
            resolved_path = Path(output_path)

        # Create PDF generation request
        request = PdfGenerationRequest(
            render_plan=render_plan,
            output_path=resolved_path,
            open_after=open_after,
            filename=resume.filename,
            resume_name=resume.name,
            raw_data=copy.deepcopy(resume.raw_data),
            processed_data=copy.deepcopy(resume.data),
            paths=resume.paths,
        )

        # Select appropriate strategy (injected or default)
        if strategy is None:
            strategy = _get_pdf_strategy(render_plan.mode.value)

        # Generate PDF using strategy
        result, page_count = strategy.generate(
            render_plan=request,
            output_path=request.output_path,
            resume_name=request.resume_name,
            filename=request.filename,
        )

        return cast(GenerationResult, result)

    except (ConfigurationError, GenerationError):
        raise
    except Exception as exc:
        raise GenerationError(
            f"Failed to generate PDF: {exc}",
            format_type="pdf",
            output_path=output_path,
            filename=resume.filename,
        ) from exc


def to_html(
    resume: Resume,
    output_path: Path | str | None = None,
    *,
    open_after: bool = False,
    browser: str | None = None,
) -> GenerationResult:
    """Generate HTML from a Resume.

    This is the shell-layer implementation that handles HTML generation
    with proper service injection and dependencies.

    Args:
        resume: The Resume instance to generate HTML from.
        output_path: Optional output path (defaults to output directory).
        open_after: Whether to open HTML after generation.
        browser: Optional browser command for opening (unused, for API compat).

    Returns:
        GenerationResult with metadata and output path.

    Raises:
        ConfigurationError: If paths are not available.
        GenerationError: If HTML generation fails.

    """
    try:
        # Validate data first
        resume.validate_or_raise()

        # Prepare render plan
        render_plan = resume.prepare_render_plan(preview=True)

        # Determine output path
        if output_path is None:
            if resume.paths is None:
                raise ConfigurationError(
                    "No paths available - provide output_path or create with paths",
                    filename=resume.filename,
                )
            resolved_path = resume.paths.output / f"{resume.name}.html"
        else:
            resolved_path = Path(output_path)

        # Generate HTML using shell renderer
        result = generate_html_with_jinja(
            render_plan, resolved_path, filename=resume.filename
        )

        # Open file if requested
        if open_after and result.output_path.exists():
            shell_open_file(result.output_path, format_type="html")

        return result

    except (ConfigurationError, GenerationError):
        raise
    except Exception as exc:
        raise GenerationError(
            f"Failed to generate HTML: {exc}",
            format_type="html",
            output_path=output_path,
            filename=resume.filename,
        ) from exc


def generate(
    resume: Resume,
    format_type: OutputFormat | str = OutputFormat.PDF,
    output_path: Path | str | None = None,
    *,
    open_after: bool = False,
) -> GenerationResult:
    """Generate a resume in the specified format.

    This is the shell-layer dispatcher that routes to the appropriate
    generation function based on format type.

    Args:
        resume: The Resume instance to generate from.
        format_type: Output format ('pdf' or 'html').
        output_path: Optional output path.
        open_after: Whether to open after generation.

    Returns:
        GenerationResult with metadata and operations.

    Raises:
        ValueError: If format is not supported.
        ConfigurationError: If paths are not available.
        GenerationError: If generation fails.

    """
    try:
        format_enum = (
            format_type
            if isinstance(format_type, OutputFormat)
            else OutputFormat.normalize(format_type)
        )
    except (ValueError, TypeError):
        raise ValueError(
            f"Unsupported format: {format_type}. Use 'pdf' or 'html'."
        ) from None

    if format_enum is OutputFormat.PDF:
        return to_pdf(resume, output_path, open_after=open_after)

    if format_enum is OutputFormat.HTML:
        return to_html(resume, output_path, open_after=open_after)

    raise ValueError(f"Unsupported format: {format_enum.value}. Use 'pdf' or 'html'.")


__all__ = [
    "to_pdf",
    "to_html",
    "generate",
]
