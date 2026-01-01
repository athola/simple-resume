"""Shell layer functions for Resume I/O operations.

This module provides the I/O operations for Resume that live in the shell layer,
keeping the core Resume class pure and functional.

Functions:
    to_pdf: Generate PDF from a Resume
    to_html: Generate HTML from a Resume
    to_markdown: Generate intermediate Markdown from a Resume
    to_tex: Generate intermediate LaTeX from a Resume
    generate: Generate output in specified format from a Resume
    render_markdown_file: Render an existing .md file to HTML
    render_tex_file: Render an existing .tex file to PDF
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from simple_resume.core.constants import MARKDOWN_EXTENSION, TEX_EXTENSION, OutputFormat
from simple_resume.core.exceptions import ConfigurationError, GenerationError
from simple_resume.core.protocols import PdfGenerationStrategy
from simple_resume.core.result import GenerationResult
from simple_resume.shell.file_opener import open_file as shell_open_file
from simple_resume.shell.render.latex import LatexCompilationError
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


def to_markdown(
    resume: Resume,
    output_path: Path | str | None = None,
    *,
    open_after: bool = False,
) -> GenerationResult:
    """Generate intermediate Markdown from a Resume.

    This creates an editable .md file that can be modified before
    rendering to HTML. Use render_markdown_file() to convert to HTML.

    Args:
        resume: The Resume instance to generate Markdown from.
        output_path: Optional output path (defaults to output directory).
        open_after: Whether to open the file after generation.

    Returns:
        GenerationResult with metadata and output path.

    Raises:
        ConfigurationError: If paths are not available.
        GenerationError: If generation fails.

    """
    try:
        # Validate data first
        resume.validate_or_raise()

        # Prepare render plan for HTML mode (markdown is the HTML intermediate)
        render_plan = resume.prepare_render_plan(preview=True)

        # Determine output path
        if output_path is None:
            if resume.paths is None:
                raise ConfigurationError(
                    "No paths available - provide output_path or create with paths",
                    filename=resume.filename,
                )
            resolved_path = resume.paths.output / f"{resume.name}{MARKDOWN_EXTENSION}"
        else:
            resolved_path = Path(output_path)

        # Get context from render plan and generate markdown
        context = render_plan.context or {}

        # Generate structured markdown from context
        md_content = _generate_markdown_from_context(context, resume.name)

        # Ensure output directory exists
        resolved_path.parent.mkdir(parents=True, exist_ok=True)

        # Write markdown file
        resolved_path.write_text(md_content, encoding="utf-8")

        # Create metadata
        from simple_resume.core.result import GenerationMetadata  # noqa: PLC0415

        metadata = GenerationMetadata(
            format_type="markdown",
            template_name=render_plan.template_name or "markdown",
            generation_time=0.0,
            file_size=len(md_content.encode("utf-8")),
            resume_name=resume.name,
            palette_info=render_plan.palette_metadata,
        )

        result = GenerationResult(
            output_path=resolved_path,
            format_type="markdown",
            metadata=metadata,
        )

        # Open file if requested
        if open_after and result.output_path.exists():
            shell_open_file(result.output_path, format_type="markdown")

        return result

    except (ConfigurationError, GenerationError):
        raise
    except Exception as exc:
        raise GenerationError(
            f"Failed to generate Markdown: {exc}",
            format_type="markdown",
            output_path=output_path,
            filename=resume.filename,
        ) from exc


def _generate_markdown_from_context(  # noqa: PLR0912, PLR0915
    context: dict[str, object], resume_name: str
) -> str:
    """Generate structured markdown content from render context.

    Args:
        context: Render context dictionary containing resume data.
        resume_name: Name of the resume for the title.

    Returns:
        Formatted markdown string.

    """
    lines: list[str] = []

    # Header with name
    full_name = context.get("full_name", resume_name)
    lines.append(f"# {full_name}")
    lines.append("")

    # Contact info
    if "email" in context or "phone" in context or "location" in context:
        contact_parts: list[str] = []
        if context.get("email"):
            contact_parts.append(str(context["email"]))
        if context.get("phone"):
            contact_parts.append(str(context["phone"]))
        if context.get("location"):
            contact_parts.append(str(context["location"]))
        if contact_parts:
            lines.append(" | ".join(contact_parts))
            lines.append("")

    # Links
    links = context.get("links") or []
    if links and isinstance(links, list):
        link_parts: list[str] = []
        for link in links:
            if isinstance(link, dict):
                link_dict = cast(dict[str, Any], link)
                url = link_dict.get("url", "")
                label = link_dict.get("label", url)
                link_parts.append(f"[{label}]({url})")
        if link_parts:
            lines.append(" | ".join(link_parts))
            lines.append("")

    # Summary/Objective
    if context.get("summary"):
        lines.append("## Summary")
        lines.append("")
        lines.append(str(context["summary"]))
        lines.append("")

    # Experience
    experience = context.get("experience") or []
    if experience and isinstance(experience, list):
        lines.append("## Experience")
        lines.append("")
        for job in experience:
            if isinstance(job, dict):
                job_dict = cast(dict[str, Any], job)
                title = job_dict.get("title", "")
                company = job_dict.get("company", "")
                dates = job_dict.get("dates", "")
                lines.append(f"### {title} at {company}")
                if dates:
                    lines.append(f"*{dates}*")
                lines.append("")
                highlights = job_dict.get("highlights", [])
                for highlight in highlights:
                    lines.append(f"- {highlight}")
                lines.append("")

    # Education
    education = context.get("education") or []
    if education and isinstance(education, list):
        lines.append("## Education")
        lines.append("")
        for edu in education:
            if isinstance(edu, dict):
                edu_dict = cast(dict[str, Any], edu)
                degree = edu_dict.get("degree", "")
                school = edu_dict.get("school", "")
                dates = edu_dict.get("dates", "")
                lines.append(f"### {degree}")
                lines.append(f"*{school}*")
                if dates:
                    lines.append(f"*{dates}*")
                lines.append("")

    # Skills
    skills = context.get("skills") or []
    if skills and isinstance(skills, list):
        lines.append("## Skills")
        lines.append("")
        for skill_group in skills:
            if isinstance(skill_group, dict):
                skill_dict = cast(dict[str, Any], skill_group)
                category = skill_dict.get("category", "")
                items = skill_dict.get("items", [])
                if category:
                    lines.append(f"**{category}:** {', '.join(items)}")
                else:
                    lines.append(", ".join(items))
        lines.append("")

    return "\n".join(lines)


def to_tex(
    resume: Resume,
    output_path: Path | str | None = None,
    *,
    open_after: bool = False,
) -> GenerationResult:
    """Generate intermediate LaTeX (.tex) from a Resume.

    This creates an editable .tex file that can be modified before
    rendering to PDF. Use render_tex_file() to convert to PDF.

    Args:
        resume: The Resume instance to generate LaTeX from.
        output_path: Optional output path (defaults to output directory).
        open_after: Whether to open the file after generation.

    Returns:
        GenerationResult with metadata and output path.

    Raises:
        ConfigurationError: If paths are not available.
        ValidationError: If resume data fails validation.
        GenerationError: If LaTeX generation fails.

    """
    try:
        # Validate data first (consistent with to_markdown)
        resume.validate_or_raise()

        # Prepare render plan for LaTeX mode
        render_plan = resume.prepare_render_plan(preview=False)

        # Determine output path
        if output_path is None:
            if resume.paths is None:
                raise ConfigurationError(
                    "No paths available - provide output_path or create with paths",
                    filename=resume.filename,
                )
            resolved_path = resume.paths.output / f"{resume.name}{TEX_EXTENSION}"
        else:
            resolved_path = Path(output_path)

        # Use the shell-layer render functions which have all dependencies
        from simple_resume.core.result import GenerationMetadata  # noqa: PLC0415
        from simple_resume.shell.render.latex import (  # noqa: PLC0415
            render_resume_latex_from_data,
        )

        # Get resume data for LaTeX rendering
        resume_data = resume.data if isinstance(resume.data, dict) else resume.raw_data

        # Generate LaTeX content using the shell render function
        tex_result = render_resume_latex_from_data(
            resume_data,
            paths=resume.paths,
            template_name=render_plan.template_name or "latex/basic.tex",
        )
        tex_content_raw = getattr(tex_result, "tex", tex_result)
        tex_content: str = (
            str(tex_content_raw)
            if not isinstance(tex_content_raw, str)
            else tex_content_raw
        )

        # Write .tex file (don't compile to PDF)
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_path.write_text(tex_content, encoding="utf-8")

        # Create metadata with actual file size (after write)
        metadata = GenerationMetadata(
            format_type="tex",
            template_name=render_plan.template_name or "latex/basic.tex",
            generation_time=0.0,
            file_size=len(tex_content.encode("utf-8")),
            resume_name=resume.name,
            palette_info=render_plan.palette_metadata,
        )

        result = GenerationResult(
            output_path=resolved_path,
            format_type="tex",
            metadata=metadata,
        )

        # Open file if requested
        if open_after and result.output_path.exists():
            shell_open_file(result.output_path, format_type="tex")

        return result

    except (ConfigurationError, GenerationError):
        raise
    except Exception as exc:
        raise GenerationError(
            f"Failed to generate LaTeX: {exc}",
            format_type="tex",
            output_path=output_path,
            filename=resume.filename,
        ) from exc


def render_markdown_file(
    input_path: Path | str,
    output_path: Path | str | None = None,
    *,
    open_after: bool = False,
) -> GenerationResult:
    """Render an existing Markdown file to HTML.

    Args:
        input_path: Path to the .md file to render.
        output_path: Optional output path (defaults to same name with .html).
        open_after: Whether to open the file after generation.

    Returns:
        GenerationResult with metadata and output path.

    Raises:
        GenerationError: If rendering fails.

    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise GenerationError(
            f"Markdown file not found: {input_path}",
            format_type="html",
            output_path=output_path,
        )

    if output_path is None:
        resolved_output = input_path.with_suffix(".html")
    else:
        resolved_output = Path(output_path)

    try:
        # Read markdown content
        md_content = input_path.read_text(encoding="utf-8")

        # Convert markdown to HTML using a simple wrapper
        import markdown  # noqa: PLC0415

        html_body = markdown.markdown(md_content, extensions=["tables", "fenced_code"])

        # Create full HTML document
        body_style = (
            "font-family: system-ui, -apple-system, sans-serif; "
            "max-width: 800px; margin: 2em auto; padding: 0 1em; line-height: 1.6;"
        )
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{input_path.stem}</title>
    <style>
        body {{ {body_style} }}
        h1, h2, h3 {{ margin-top: 1.5em; }}
        ul, ol {{ padding-left: 2em; }}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""

        # Write HTML file
        resolved_output.parent.mkdir(parents=True, exist_ok=True)
        resolved_output.write_text(html_content, encoding="utf-8")

        # Create metadata
        from simple_resume.core.result import GenerationMetadata  # noqa: PLC0415

        metadata = GenerationMetadata(
            format_type="html",
            template_name="markdown-to-html",
            generation_time=0.0,
            file_size=len(html_content.encode("utf-8")),
            resume_name=input_path.stem,
        )

        result = GenerationResult(
            output_path=resolved_output,
            format_type="html",
            metadata=metadata,
        )

        # Open file if requested
        if open_after and result.output_path.exists():
            shell_open_file(result.output_path, format_type="html")

        return result

    except Exception as exc:
        raise GenerationError(
            f"Failed to render Markdown to HTML: {exc}",
            format_type="html",
            output_path=output_path,
        ) from exc


def render_tex_file(
    input_path: Path | str,
    output_path: Path | str | None = None,
    *,
    open_after: bool = False,
) -> GenerationResult:
    """Render an existing LaTeX (.tex) file to PDF.

    Args:
        input_path: Path to the .tex file to render.
        output_path: Optional output path (defaults to same name with .pdf).
        open_after: Whether to open the file after generation.

    Returns:
        GenerationResult with metadata and output path.

    Raises:
        GenerationError: If rendering fails.

    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise GenerationError(
            f"LaTeX file not found: {input_path}",
            format_type="pdf",
            output_path=output_path,
        )

    if output_path is None:
        resolved_output = input_path.with_suffix(".pdf")
    else:
        resolved_output = Path(output_path)

    try:
        # Use the LaTeX compilation from the shell layer
        import shutil  # noqa: PLC0415

        from simple_resume.shell.render.latex import (  # noqa: PLC0415
            compile_tex_to_pdf,
        )

        # Compile to PDF (outputs next to the .tex file)
        resolved_output.parent.mkdir(parents=True, exist_ok=True)
        compiled_pdf = compile_tex_to_pdf(input_path)

        # Move to desired output path if different
        if compiled_pdf != resolved_output:
            shutil.move(str(compiled_pdf), str(resolved_output))

        # Create metadata
        from simple_resume.core.result import GenerationMetadata  # noqa: PLC0415

        file_size = resolved_output.stat().st_size if resolved_output.exists() else 0
        metadata = GenerationMetadata(
            format_type="pdf",
            template_name="tex-to-pdf",
            generation_time=0.0,
            file_size=file_size,
            resume_name=input_path.stem,
        )

        result = GenerationResult(
            output_path=resolved_output,
            format_type="pdf",
            metadata=metadata,
        )

        # Open file if requested
        if open_after and result.output_path.exists():
            shell_open_file(result.output_path, format_type="pdf")

        return result

    except LatexCompilationError as exc:
        raise GenerationError(
            f"LaTeX compilation failed: {exc}",
            format_type="pdf",
            output_path=output_path,
        ) from exc
    except Exception as exc:
        raise GenerationError(
            f"Failed to render LaTeX to PDF: {exc}",
            format_type="pdf",
            output_path=output_path,
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
        format_type: Output format ('pdf', 'html', 'markdown', 'tex').
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
            f"Unsupported format: {format_type}. "
            "Use 'pdf', 'html', 'markdown', or 'tex'."
        ) from None

    if format_enum is OutputFormat.PDF:
        return to_pdf(resume, output_path, open_after=open_after)

    if format_enum is OutputFormat.HTML:
        return to_html(resume, output_path, open_after=open_after)

    if format_enum is OutputFormat.MARKDOWN:
        return to_markdown(resume, output_path, open_after=open_after)

    if format_enum in (OutputFormat.TEX, OutputFormat.LATEX):
        return to_tex(resume, output_path, open_after=open_after)

    raise ValueError(
        f"Unsupported format: {format_enum.value}. "
        "Use 'pdf', 'html', 'markdown', or 'tex'."
    )


__all__ = [
    "generate",
    "render_markdown_file",
    "render_tex_file",
    "to_html",
    "to_markdown",
    "to_pdf",
    "to_tex",
]
