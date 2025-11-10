"""Provide PDF rendering helpers for the core resume pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any, SupportsInt, cast

from weasyprint import CSS, HTML

from ..config import TEMPLATE_LOC
from ..constants import RenderMode
from ..exceptions import ConfigurationError, GenerationError, TemplateError
from ..latex_renderer import (
    LatexCompilationError,
    compile_tex_to_pdf,
    render_resume_latex_from_data,
)
from ..rendering import get_template_environment
from ..result import GenerationMetadata, GenerationResult
from .models import RenderPlan


def generate_pdf_with_weasyprint(
    render_plan: RenderPlan,
    output_path: Path,
    *,
    resume_name: str,
    filename: str | None = None,
) -> tuple[GenerationResult, int | None]:
    """Generate a PDF using the WeasyPrint backend."""
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

    output_path.parent.mkdir(parents=True, exist_ok=True)

    env = get_template_environment(str(TEMPLATE_LOC))
    html = (
        env.get_template(render_plan.template_name)
        .render(**render_plan.context)
        .lstrip()
    )

    page_width = render_plan.config.page_width or 210
    page_height = render_plan.config.page_height or 297

    css = CSS(string=f"@page {{size: {page_width}mm {page_height}mm; margin: 0mm;}}")
    html_doc = HTML(string=html, base_url=render_plan.base_path)

    document = html_doc.render(stylesheets=[css])
    raw_page_count: int | None = None
    pages = getattr(document, "pages", None)
    if pages is not None:
        try:
            raw_page_count = len(pages)
        except TypeError:  # pragma: no cover - defensive
            length_func = getattr(pages, "__len__", None)
            if callable(length_func):
                try:
                    candidate_value = cast(SupportsInt | str, length_func())
                    raw_page_count = int(candidate_value)
                except Exception:
                    raw_page_count = None

    page_count = (
        raw_page_count
        if isinstance(raw_page_count, int) and raw_page_count >= 0
        else None
    )

    html_doc.write_pdf(
        str(output_path),
        stylesheets=[css],
    )

    metadata = GenerationMetadata(
        format_type="pdf",
        template_name=render_plan.template_name or "unknown",
        generation_time=0.0,
        file_size=0,
        resume_name=resume_name,
        palette_info=render_plan.palette_metadata,
        page_count=page_count,
    )

    return GenerationResult(output_path, "pdf", metadata), page_count


def generate_pdf_with_latex(  # noqa: PLR0913 - backend needs explicit context
    render_plan: RenderPlan,
    output_path: Path,
    *,
    raw_data: dict[str, Any] | None,
    processed_data: dict[str, Any],
    paths: Any,
    filename: str | None = None,
) -> tuple[GenerationResult, int | None]:
    """Generate a PDF using the LaTeX backend."""
    if paths is None:
        raise ConfigurationError(
            "LaTeX generation requires resolved paths", filename=filename
        )

    if (
        LatexCompilationError is None
        or compile_tex_to_pdf is None
        or render_resume_latex_from_data is None
    ):
        raise ConfigurationError(
            "LaTeX renderer is required for LaTeX generation. "
            "Install with: pip install simple-resume[latex]",
            filename=filename,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    tex_path = output_path.with_suffix(".tex")
    preserve_log = False
    try:
        latex_source = raw_data if raw_data is not None else processed_data
        latex_result = render_resume_latex_from_data(
            latex_source,
            paths=paths,
        )
        tex_path.write_text(latex_result.tex, encoding="utf-8")
        pdf_path = compile_tex_to_pdf(tex_path)
        if pdf_path != output_path:
            pdf_path.replace(output_path)
    except Exception as exc:  # pragma: no cover - exercised in tests via mocks
        if LatexCompilationError is not None and isinstance(exc, LatexCompilationError):
            log_value = getattr(exc, "log", "")
            if log_value:
                tex_path.with_suffix(".log").write_text(
                    str(log_value), encoding="utf-8"
                )
                preserve_log = True
            raise GenerationError(
                f"LaTeX compilation failed: {exc}",
                format_type="pdf",
                output_path=str(output_path),
                filename=filename,
            ) from exc
        raise
    finally:
        cleanup_latex_artifacts(tex_path, preserve_log=preserve_log)

    return GenerationResult(output_path, "pdf"), None


def cleanup_latex_artifacts(tex_path: Path, *, preserve_log: bool = False) -> None:
    """Remove auxiliary files emitted by LaTeX engines."""
    for suffix in (".aux", ".log", ".out"):
        if preserve_log and suffix == ".log":
            continue
        candidate = tex_path.with_suffix(suffix)
        try:
            if candidate.exists():
                candidate.unlink()
        except OSError:  # pragma: no cover - best effort cleanup
            continue


__all__ = [
    "cleanup_latex_artifacts",
    "generate_pdf_with_latex",
    "generate_pdf_with_weasyprint",
]
