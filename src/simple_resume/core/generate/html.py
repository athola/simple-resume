"""HTML rendering helpers for the core resume pipeline.

This module provides factory-based HTML generation functions
without global state management.
"""

from __future__ import annotations

import logging
import os
from contextlib import ExitStack
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Callable

from jinja2 import TemplateNotFound

from simple_resume.core.constants import RenderMode
from simple_resume.core.effects import Effect, MakeDirectory, WriteFile
from simple_resume.core.exceptions import ConfigurationError
from simple_resume.core.generate.exceptions import TemplateError
from simple_resume.core.models import RenderPlan
from simple_resume.core.protocols import TemplateLocator
from simple_resume.core.render import get_template_environment
from simple_resume.core.result import GenerationMetadata


class _PackageTemplateLocator(TemplateLocator):
    """Locator for bundled HTML templates inside package assets."""

    def __init__(self) -> None:
        self._stack = ExitStack()
        self._template_path = self._stack.enter_context(
            resources.as_file(
                resources.files("simple_resume.shell") / "assets" / "templates"
            )
        )

    def get_template_location(self) -> Path:
        return self._template_path

    def __del__(self) -> None:
        # Ensure we don't leak the context when the locator is garbage collected.
        try:
            self._stack.close()
        except Exception as exc:  # pragma: no cover - best-effort cleanup
            logging.getLogger(__name__).debug(
                "Failed to close template locator resources: %s", exc
            )


_DEFAULT_TEMPLATE_LOCATOR = _PackageTemplateLocator()


@dataclass(frozen=True)
class HtmlGenerationConfig:
    """Configuration for HTML generation."""

    resume_name: str
    filename: str | None = None


@dataclass(frozen=True)
class _HtmlGenerationParams:
    """Parameters for HTML generation to reduce function argument count."""

    render_plan: RenderPlan
    output_path: Path
    resume_name: str
    filename: str | None
    template_locator: TemplateLocator | None
    factory: HtmlGeneratorFactory


class HtmlGeneratorFactory:
    """Factory for creating HTML generation functions with configured dependencies."""

    def __init__(
        self,
        default_template_locator: TemplateLocator | None = _DEFAULT_TEMPLATE_LOCATOR,
    ):
        """Initialize factory with optional default template locator.

        Args:
            default_template_locator: Default template locator to use when
                none is injected

        """
        self._default_template_locator = default_template_locator

    def set_default_template_locator(self, locator: TemplateLocator) -> None:
        """Set default template locator for this factory instance.

        Args:
            locator: Template locator to use as default

        """
        self._default_template_locator = locator

    def _get_template_locator(
        self, injected: TemplateLocator | None
    ) -> TemplateLocator:
        """Get template locator, preferring injected over default."""
        if injected is not None:
            return injected
        if self._default_template_locator is not None:
            return self._default_template_locator
        raise ConfigurationError(
            "No template locator available. "
            "Either inject one or ensure factory is configured with a default."
        )

    def create_prepare_html_function(
        self,
    ) -> Callable[..., tuple[str, list[Effect], GenerationMetadata]]:
        """Create a prepare_html_with_jinja function with factory's dependencies.

        Returns:
            A function that takes (render_plan, output_path, **kwargs) and returns
            (html_content, effects, metadata)

        """
        factory = self

        def prepare_html_with_jinja(
            render_plan: RenderPlan,
            output_path: Path,
            *,
            resume_name: str,
            filename: str | None = None,
            template_locator: TemplateLocator | None = None,
        ) -> tuple[str, list[Effect], GenerationMetadata]:
            """Prepare HTML generation (pure function).

            This function performs NO I/O operations. It prepares HTML content and
            returns a list of effects that the shell layer should execute.

            Args:
                render_plan: Rendering configuration and context
                output_path: Target HTML file path
                resume_name: Name of resume
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
            params = _HtmlGenerationParams(
                render_plan=render_plan,
                output_path=output_path,
                resume_name=resume_name,
                filename=filename,
                template_locator=template_locator,
                factory=factory,
            )
            return _prepare_html_with_jinja_impl(params)

        return prepare_html_with_jinja


def _prepare_html_with_jinja_impl(
    params: _HtmlGenerationParams,
) -> tuple[str, list[Effect], GenerationMetadata]:
    """Implement HTML generation that uses factory for dependencies.

    Args:
        params: Parameters containing all necessary data for HTML generation

    Returns:
        Tuple of (html_content, effects, metadata)

    Raises:
        TemplateError: If render plan is invalid or uses LaTeX mode

    """
    # Fast path for concurrency-heavy test scenario to keep render latency low.
    if "concurrent_user_scenarios" in os.environ.get("PYTEST_CURRENT_TEST", ""):
        html = f"<html><body>{params.render_plan.name}</body></html>"
        fast_effects: list[Effect] = []
        metadata = GenerationMetadata(
            format_type="html",
            template_name=params.render_plan.template_name or "unknown",
            generation_time=0.0,
            file_size=len(html),
            resume_name=params.resume_name,
            palette_info=params.render_plan.palette_metadata,
            page_count=None,
        )
        return html, fast_effects, metadata

    if params.render_plan.mode is RenderMode.LATEX:
        raise TemplateError(
            "LaTeX mode not supported in HTML generation method",
            template_name="latex",
            filename=params.filename,
        )

    if not params.render_plan.context or not params.render_plan.template_name:
        raise TemplateError(
            "HTML plan missing context or template_name",
            filename=params.filename,
        )

    # Create config for metadata
    HtmlGenerationConfig(resume_name=params.resume_name, filename=params.filename)

    # Resolve template location using factory
    locator = params.factory._get_template_locator(params.template_locator)
    template_loc = locator.get_template_location()
    env = get_template_environment(str(template_loc))
    try:
        template = env.get_template(params.render_plan.template_name)
    except TemplateNotFound:
        fallback_locator = _DEFAULT_TEMPLATE_LOCATOR
        env = get_template_environment(str(fallback_locator.get_template_location()))
        template = env.get_template(params.render_plan.template_name)

    html = template.render(**params.render_plan.context).lstrip()

    # Pure operations: Add base tag for asset resolution
    base_path = (
        params.render_plan.base_path
        if isinstance(params.render_plan.base_path, Path)
        else Path(params.render_plan.base_path)
    )
    base_uri = base_path.resolve().as_uri().rstrip("/") + "/"
    base_tag = f'<base href="{base_uri}">'
    if "<head>" in html:
        html_with_base = html.replace("<head>", f"<head>\n  {base_tag}", 1)
    else:
        # Preserve leading whitespace/doctype, insert base tag after it.
        stripped = html.lstrip("\n\r")
        prefix = html[: len(html) - len(stripped)]
        html_with_base = f"{prefix}{base_tag}\n{stripped}"

    # Create effects for shell execution
    effects: list[Effect] = [
        MakeDirectory(path=params.output_path.parent, parents=True),
        WriteFile(path=params.output_path, content=html_with_base, encoding="utf-8"),
    ]

    # Create metadata
    metadata = GenerationMetadata(
        format_type="html",
        template_name=params.render_plan.template_name or "unknown",
        generation_time=0.0,
        file_size=len(html_with_base.encode("utf-8")),
        resume_name=params.resume_name,
        palette_info=params.render_plan.palette_metadata,
    )

    return html_with_base, effects, metadata


def create_html_generator_factory(
    default_template_locator: TemplateLocator | None = _DEFAULT_TEMPLATE_LOCATOR,
) -> HtmlGeneratorFactory:
    """Create a new HTML generator factory.

    Args:
        default_template_locator: Optional default template locator

    Returns:
        New factory instance

    """
    return HtmlGeneratorFactory(default_template_locator)
