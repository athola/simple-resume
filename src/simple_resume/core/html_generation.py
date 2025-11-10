"""HTML rendering helpers for the core resume pipeline."""

from __future__ import annotations

from pathlib import Path

from ..config import TEMPLATE_LOC
from ..constants import RenderMode
from ..exceptions import TemplateError
from ..rendering import get_template_environment
from ..result import GenerationResult
from .models import RenderPlan


def generate_html_with_jinja(
    render_plan: RenderPlan,
    output_path: Path,
    *,
    filename: str | None = None,
) -> GenerationResult:
    """Generate HTML using Jinja2 templates."""
    if render_plan.mode is RenderMode.LATEX:
        raise TemplateError(
            "LaTeX mode not supported in HTML generation method",
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

    base_path = (
        render_plan.base_path
        if isinstance(render_plan.base_path, Path)
        else Path(render_plan.base_path)
    )
    base_uri = base_path.resolve().as_uri().rstrip("/") + "/"
    base_tag = f'<base href="{base_uri}">'
    if "<head>" in html:
        html_with_base = html.replace("<head>", f"<head>\n  {base_tag}", 1)
    else:
        html_with_base = f"{base_tag}\n{html}"

    output_path.write_text(html_with_base, encoding="utf-8")

    return GenerationResult(output_path, "html")


__all__ = ["generate_html_with_jinja"]
