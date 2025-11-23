"""HTML rendering helpers for the core resume pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from simple_resume.core.constants import RenderMode
from simple_resume.core.effects import Effect, MakeDirectory, WriteFile
from simple_resume.core.exceptions import ConfigurationError
from simple_resume.core.generate.exceptions import TemplateError
from simple_resume.core.models import RenderPlan
from simple_resume.core.protocols import TemplateLocator
from simple_resume.core.render import get_template_environment
from simple_resume.core.result import GenerationMetadata


# Module-level dependency injection container
class _DependencyContainer:
    """Container for module-level dependencies (avoids global statement)."""

    template_locator: TemplateLocator | None = None


_deps = _DependencyContainer()


def set_default_template_locator(locator: TemplateLocator) -> None:
    """Set the default template locator (called by shell layer)."""
    _deps.template_locator = locator


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


@dataclass(frozen=True)
class HtmlGenerationConfig:
    """Configuration for HTML generation."""

    resume_name: str = "resume"
    filename: str | None = None
    template_loc: Path | None = None
    template_locator: TemplateLocator | None = None


def prepare_html_with_jinja(
    render_plan: RenderPlan,
    output_path: Path,
    config: HtmlGenerationConfig | None = None,
) -> tuple[str, list[Effect], GenerationMetadata]:
    """Prepare HTML generation (pure function).

    This function performs NO I/O operations. It prepares HTML content and
    returns a list of effects that the shell layer should execute.

    Args:
        render_plan: Rendering configuration and context
        output_path: Target HTML file path
        config: Optional configuration object

    Returns:
        Tuple of (html_content, effects, metadata)
        - html_content: Rendered HTML as string
        - effects: List of effects to execute (MakeDirectory, WriteFile)
        - metadata: Generation metadata

    Raises:
        TemplateError: If render plan is invalid or uses LaTeX mode

    """
    # Use default config if none provided
    if config is None:
        config = HtmlGenerationConfig()

    if render_plan.mode is RenderMode.LATEX:
        raise TemplateError(
            "LaTeX mode not supported in HTML generation method",
            template_name="latex",
            filename=config.filename,
        )

    if not render_plan.context or not render_plan.template_name:
        raise TemplateError(
            "HTML plan missing context or template_name",
            filename=config.filename,
        )

    # Resolve template location using dependency injection
    if config.template_loc is None:
        locator = _get_template_locator(config.template_locator)
        resolved_template_loc = locator.get_template_location()
    else:
        resolved_template_loc = config.template_loc

    # Pure operation: Render HTML template
    env = get_template_environment(str(resolved_template_loc))
    html = (
        env.get_template(render_plan.template_name)
        .render(**render_plan.context)
        .lstrip()
    )

    # Pure operation: Add base tag for asset resolution
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

    # Create effects for shell execution
    effects: list[Effect] = [
        MakeDirectory(path=output_path.parent, parents=True),
        WriteFile(path=output_path, content=html_with_base, encoding="utf-8"),
    ]

    # Create metadata
    metadata = GenerationMetadata(
        format_type="html",
        template_name=render_plan.template_name or "unknown",
        generation_time=0.0,
        file_size=len(html_with_base.encode("utf-8")),
        resume_name=config.resume_name,
        palette_info=render_plan.palette_metadata,
    )

    return html_with_base, effects, metadata


__all__ = [
    "HtmlGenerationConfig",
    "prepare_html_with_jinja",
    "set_default_template_locator",
]
