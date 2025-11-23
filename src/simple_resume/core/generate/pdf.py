"""Provide PDF rendering helpers for the core resume pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from simple_resume.core.constants import RenderMode
from simple_resume.core.effects import (
    DeleteFile,
    Effect,
    MakeDirectory,
    RunCommand,
    WriteFile,
)
from simple_resume.core.exceptions import ConfigurationError
from simple_resume.core.generate.exceptions import TemplateError
from simple_resume.core.models import RenderPlan
from simple_resume.core.protocols import (
    EffectExecutor,
    LaTeXRenderer,
    TemplateLocator,
)
from simple_resume.core.render import get_template_environment
from simple_resume.core.result import GenerationMetadata, GenerationResult


# Module-level dependency injection container
class _PdfDependencyContainer:
    """Container for PDF module dependencies (avoids global statement)."""

    effect_executor: EffectExecutor | None = None
    template_locator: TemplateLocator | None = None
    latex_renderer: LaTeXRenderer | None = None


_deps = _PdfDependencyContainer()


def set_default_pdf_dependencies(
    effect_executor: EffectExecutor | None = None,
    template_locator: TemplateLocator | None = None,
    latex_renderer: LaTeXRenderer | None = None,
) -> None:
    """Set default PDF generation dependencies (called by shell layer)."""
    if effect_executor is not None:
        _deps.effect_executor = effect_executor
    if template_locator is not None:
        _deps.template_locator = template_locator
    if latex_renderer is not None:
        _deps.latex_renderer = latex_renderer


def _get_effect_executor(injected: EffectExecutor | None) -> EffectExecutor:
    """Get effect executor, preferring injected over default."""
    if injected is not None:
        return injected
    if _deps.effect_executor is not None:
        return _deps.effect_executor
    raise ConfigurationError(
        "No effect executor available. "
        "Either inject one or ensure shell layer is initialized."
    )


def _get_template_locator(injected: TemplateLocator | None) -> TemplateLocator:
    """Get template locator, preferring injected over default."""
    if injected is not None:
        return injected
    if _deps.template_locator is not None:
        return _deps.template_locator
    raise ConfigurationError(
        "No template locator available. "
        "Either inject one or ensure shell layer is initialized."
    )


def _get_latex_renderer(injected: LaTeXRenderer | None) -> LaTeXRenderer:
    """Get LaTeX renderer, preferring injected over default."""
    if injected is not None:
        return injected
    if _deps.latex_renderer is not None:
        return _deps.latex_renderer
    raise ConfigurationError(
        "No LaTeX renderer available. "
        "Either inject one or ensure shell layer is initialized."
    )


def get_latex_functions(latex_renderer: LaTeXRenderer) -> tuple[Any, Any, Any]:
    """Get LaTeX functions from provided renderer.

    Args:
        latex_renderer: LaTeX renderer implementation

    Returns:
        Tuple of (LatexCompilationError, compile_tex_to_pdf,
        render_resume_latex_from_data)
        Returns (None, None, None) if LaTeX module is not available.

    """
    return latex_renderer.get_latex_functions()


@dataclass(frozen=True)
class LatexGenerationContext:
    """Context object for LaTeX PDF generation, grouping related parameters."""

    raw_data: dict[str, Any] | None
    processed_data: dict[str, Any]
    paths: Any
    filename: str | None = None


def generate_pdf_with_weasyprint(
    render_plan: RenderPlan,
    output_path: Path,
    resume_name: str,
    filename: str | None = None,
    effect_executor: EffectExecutor | None = None,
) -> tuple[GenerationResult, int | None]:
    """Generate PDF using WeasyPrint (shell execution).

    This function executes the effects produced by prepare_pdf_with_weasyprint
    and returns the result and page count.
    """
    # Prepare PDF generation in core (pure)
    html_content, effects, metadata = prepare_pdf_with_weasyprint(
        render_plan=render_plan,
        output_path=output_path,
        resume_name=resume_name,
        filename=filename,
    )

    # Execute effects using injected or default executor
    executor = _get_effect_executor(effect_executor)
    executor.execute_many(effects)

    # Extract page count from the prepared metadata
    page_count = metadata.page_count if hasattr(metadata, "page_count") else None

    # Create and return result
    result = GenerationResult(
        output_path=output_path,
        format_type="pdf",
        metadata=metadata,
    )

    return result, page_count


def prepare_pdf_with_weasyprint(
    render_plan: RenderPlan,
    output_path: Path,
    *,
    resume_name: str,
    filename: str | None = None,
    template_locator: TemplateLocator | None = None,
) -> tuple[str, list[Effect], GenerationMetadata]:
    """Prepare PDF generation using WeasyPrint (pure function).

    This function performs NO I/O operations. It prepares HTML content and
    returns a list of effects that the shell layer should execute.

    Args:
        render_plan: Rendering configuration and context
        output_path: Target PDF file path
        resume_name: Name of the resume
        filename: Source filename for error messages
        template_locator: Optional template locator for dependency injection

    Returns:
        Tuple of (html_content, effects, metadata)
        - html_content: Rendered HTML as string
        - effects: List of effects to execute (MakeDirectory, WriteFile)
        - metadata: Generation metadata

    Raises:
        TemplateError: If render plan is invalid or uses LaTeX mode

    """
    if render_plan.mode is RenderMode.LATEX:
        raise TemplateError(
            "LaTeX mode not supported in PDF generation method",
            template_name="latex",
            filename=filename,
        )

    if not render_plan.context or not render_plan.template_name:
        raise TemplateError(
            "HTML plan missing context or template_name",
            filename=filename,
        )

    # Resolve template location using dependency injection
    locator = _get_template_locator(template_locator)
    template_loc = locator.get_template_location()
    env = get_template_environment(str(template_loc))
    html = (
        env.get_template(render_plan.template_name)
        .render(**render_plan.context)
        .lstrip()
    )

    # Pure operations: Prepare CSS for page size
    page_width = render_plan.config.page_width or 210
    page_height = render_plan.config.page_height or 297
    css_string = f"@page {{size: {page_width}mm {page_height}mm; margin: 0mm;}}"

    # Optional dependency import - acceptable for optional dependencies
    try:
        import weasyprint  # noqa: PLC0415

        html_doc = weasyprint.HTML(string=html, base_url=render_plan.base_path)
        css = weasyprint.CSS(string=css_string)
        document = html_doc.render(stylesheets=[css])

        # Extract page count
        page_count: int | None = None
        if hasattr(document, "pages"):
            try:
                page_count = len(document.pages)
            except (TypeError, AttributeError):
                page_count = None

        # Generate PDF bytes in memory
        pdf_bytes = document.write_pdf()
    except ImportError as e:
        raise ConfigurationError(
            "WeasyPrint is required for PDF generation. "
            "Install with: pip install simple-resume[pdf]",
            filename=filename,
        ) from e

    # Create effects for shell execution
    effects: list[Effect] = [
        MakeDirectory(path=output_path.parent, parents=True),
        WriteFile(path=output_path, content=pdf_bytes),
    ]

    # Create metadata
    metadata = GenerationMetadata(
        format_type="pdf",
        template_name=render_plan.template_name or "unknown",
        generation_time=0.0,
        file_size=len(pdf_bytes),
        resume_name=resume_name,
        palette_info=render_plan.palette_metadata,
        page_count=page_count,
    )

    return html, effects, metadata


def prepare_pdf_with_latex(
    render_plan: RenderPlan,
    output_path: Path,
    context: LatexGenerationContext,
    latex_renderer: LaTeXRenderer | None = None,
) -> tuple[str, list[Effect], GenerationMetadata]:
    """Prepare PDF generation using LaTeX (pure function).

    This function performs NO I/O operations. It prepares TeX content and
    returns a list of effects that the shell layer should execute.

    Args:
        render_plan: Rendering configuration
        output_path: Target PDF file path
        context: LaTeX generation context with data and paths
        latex_renderer: Optional LaTeX renderer for dependency injection

    Returns:
        Tuple of (tex_content, effects, metadata)
        - tex_content: Rendered TeX source code
        - effects: List of effects to execute
        - metadata: Generation metadata

    Raises:
        ConfigurationError: If paths is None or LaTeX renderer unavailable

    """
    if context.paths is None:
        raise ConfigurationError(
            "LaTeX generation requires resolved paths", filename=context.filename
        )

    # Get LaTeX functions via dependency injection
    renderer = _get_latex_renderer(latex_renderer)
    LatexCompilationError, compile_tex_to_pdf, render_resume_latex_from_data = (
        get_latex_functions(renderer)
    )

    if (
        LatexCompilationError is None
        or compile_tex_to_pdf is None
        or render_resume_latex_from_data is None
    ):
        raise ConfigurationError(
            "LaTeX renderer is required for LaTeX generation. "
            "Install with: pip install simple-resume[latex]",
            filename=context.filename,
        )

    # Pure operation: Render LaTeX source
    latex_source = context.raw_data or context.processed_data
    latex_result = render_resume_latex_from_data(
        latex_source,
        paths=context.paths,
    )

    tex_content = latex_result.tex
    tex_path = output_path.with_suffix(".tex")

    # Get resume name from context
    resume_name = "latex_resume"
    if context.raw_data and isinstance(context.raw_data, dict):
        resume_name = context.raw_data.get("full_name", "latex_resume")
    elif context.processed_data and isinstance(context.processed_data, dict):
        resume_name = context.processed_data.get("full_name", "latex_resume")

    # Create effects for shell execution
    effects: list[Effect] = [
        # 1. Create output directory
        MakeDirectory(path=output_path.parent, parents=True),
        # 2. Write .tex file
        WriteFile(path=tex_path, content=tex_content, encoding="utf-8"),
        # 3. Run pdflatex (single pass sufficient for resumes)
        RunCommand(
            command=["pdflatex", "-interaction=nonstopmode", str(tex_path.name)],
            cwd=tex_path.parent,
        ),
        # 4. Cleanup auxiliary files (.aux, .out)
        # Note: .log is preserved for debugging
        DeleteFile(path=tex_path.with_suffix(".aux")),
        DeleteFile(path=tex_path.with_suffix(".out")),
    ]

    # Create metadata
    metadata = GenerationMetadata(
        format_type="pdf",
        template_name="latex",
        generation_time=0.0,
        file_size=0,  # Unknown until compiled
        resume_name=resume_name,
        palette_info=render_plan.palette_metadata,
    )

    return tex_content, effects, metadata


__all__ = [
    "LatexGenerationContext",
    "generate_pdf_with_weasyprint",
    "prepare_pdf_with_latex",
    "prepare_pdf_with_weasyprint",
    "set_default_pdf_dependencies",
]
