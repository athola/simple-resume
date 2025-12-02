"""Shell layer implementations of core protocols.

This module provides concrete implementations of the protocols defined
in the core layer, enabling dependency injection without late-bound imports.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

from simple_resume.core.generate.html import create_html_generator_factory
from simple_resume.core.generate.pdf import PdfGeneratorFactory
from simple_resume.core.markdown import render_markdown_content
from simple_resume.core.protocols import (
    ContentLoader,
    EffectExecutor,
    FileOpenerService,
    HtmlGenerator,
    LaTeXRenderer,
    PaletteLoader,
    PathResolver,
    PdfGenerationStrategy,
    TemplateLocator,
)
from simple_resume.core.resume import set_default_loaders
from simple_resume.shell.config import TEMPLATE_LOC
from simple_resume.shell.effect_executor import EffectExecutor as ShellEffectExecutor
from simple_resume.shell.file_opener import open_file as shell_open_file
from simple_resume.shell.io_utils import candidate_yaml_path, resolve_paths_for_read
from simple_resume.shell.palettes.loader import get_palette_registry
from simple_resume.shell.render.latex import (
    LatexCompilationError,
    compile_tex_to_pdf,
    render_resume_latex_from_data,
)
from simple_resume.shell.render.operations import (
    generate_html_with_jinja as shell_generate,
)
from simple_resume.shell.runtime.content import get_content, load_palette_from_file
from simple_resume.shell.service_locator import register_service
from simple_resume.shell.strategies import (
    LatexStrategy,
    PdfGenerationRequest,
    WeasyPrintStrategy,
)


class DefaultTemplateLocator(TemplateLocator):
    """Default template locator implementation."""

    def get_template_location(self) -> Path:
        """Get the template directory path."""
        return TEMPLATE_LOC


class DefaultEffectExecutor(EffectExecutor):
    """Default effect executor implementation."""

    def __init__(self) -> None:
        """Initialize the default effect executor."""
        self._executor = ShellEffectExecutor()

    def execute(self, effect: Any) -> None:
        """Execute a single effect."""
        self._executor.execute(effect)

    def execute_many(self, effects: list[Any]) -> None:
        """Execute multiple effects."""
        self._executor.execute_many(effects)


class DefaultPathResolver(PathResolver):
    """Default path resolver implementation."""

    def candidate_yaml_path(self, name: str) -> Path:
        """Get candidate YAML path for a name."""
        result = candidate_yaml_path(name)
        if result is None:
            # Fallback to creating a Path from name
            return Path(name)
        return result

    def resolve_paths_for_read(
        self,
        paths: Any,
        overrides: dict[str, Any],
        candidate_path: Path,
    ) -> Any:
        """Resolve paths for reading operations."""
        return resolve_paths_for_read(paths, overrides, candidate_path)


class DefaultContentLoader(ContentLoader):
    """Default content loader implementation."""

    def __init__(self) -> None:
        """Initialize the default content loader."""
        self._path_resolver = DefaultPathResolver()

    def load(
        self,
        name: str,
        paths: Any,
        transform_markdown: bool,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Load content from a YAML file."""
        candidate_path = self._path_resolver.candidate_yaml_path(name)
        resolved_paths = self._path_resolver.resolve_paths_for_read(
            paths, {}, candidate_path
        )
        raw_data = get_content(name, paths=resolved_paths, transform_markdown=False)

        if transform_markdown:
            processed_data = render_markdown_content(raw_data)
        else:
            processed_data = copy.deepcopy(raw_data)
        return processed_data, raw_data


class DefaultPdfGenerationStrategy(PdfGenerationStrategy):
    """Default PDF generation strategy implementation."""

    def __init__(self, mode: str = "weasyprint") -> None:
        """Initialize the PDF generation strategy.

        Args:
            mode: PDF generation mode ('latex' or 'weasyprint')

        """
        if mode == "latex":
            self._strategy: LatexStrategy | WeasyPrintStrategy = LatexStrategy()
        else:
            self._strategy = WeasyPrintStrategy()

    def generate(
        self,
        render_plan: Any,
        output_path: Path,
        resume_name: str,
        filename: str | None = None,
    ) -> tuple[Any, int | None]:
        """Generate a PDF file."""
        if not isinstance(render_plan, PdfGenerationRequest):
            raise TypeError(
                "render_plan must be a PdfGenerationRequest; "
                "legacy inputs are not supported"
            )
        request = render_plan
        result = self._strategy.generate_pdf(request)
        return result, None if hasattr(result, "page_count") else None


class DefaultHtmlGenerator(HtmlGenerator):
    """Default HTML generator implementation."""

    def generate(
        self,
        render_plan: Any,
        output_path: Path,
        filename: str | None = None,
    ) -> Any:
        """Generate HTML content."""
        # Use shell's render operations directly since this service is in shell layer
        return shell_generate(render_plan, output_path, filename)


class DefaultFileOpenerService(FileOpenerService):
    """Default file opener service implementation."""

    def open_file(self, path: Path, format_type: str | None = None) -> bool:
        """Open a file with the system default application."""
        return shell_open_file(path, format_type)


class DefaultPaletteLoader(PaletteLoader):
    """Default palette loader implementation."""

    def load_palette_from_file(self, path: str | Path) -> dict[str, Any]:
        """Load a palette from a file."""
        return load_palette_from_file(path)


class DefaultLaTeXRenderer(LaTeXRenderer):
    """Default LaTeX renderer implementation."""

    def get_latex_functions(self) -> tuple[Any, Any, Any]:
        """Get LaTeX compilation functions."""
        try:
            return (
                LatexCompilationError,
                compile_tex_to_pdf,
                render_resume_latex_from_data,
            )
        except ImportError:
            return None, None, None


def register_default_services() -> None:
    """Register all default services with the service locator."""
    # Create default implementations
    content_loader = DefaultContentLoader()
    path_resolver = DefaultPathResolver()
    palette_loader = DefaultPaletteLoader()
    template_locator = DefaultTemplateLocator()
    effect_executor = DefaultEffectExecutor()
    latex_renderer = DefaultLaTeXRenderer()

    # Set default dependencies for core HTML generation
    html_factory = create_html_generator_factory(template_locator)

    # Set default dependencies for core PDF generation
    pdf_factory = PdfGeneratorFactory(
        effect_executor=effect_executor,
        template_locator=template_locator,
        latex_renderer=latex_renderer,
    )

    # Register with service locator (for legacy compatibility)
    register_service("html_generator_factory", html_factory)
    register_service("pdf_generator_factory", pdf_factory)
    register_service("file_opener", DefaultFileOpenerService())
    register_service("palette_loader", palette_loader)
    register_service("latex_renderer", latex_renderer)
    register_service("html_generator", DefaultHtmlGenerator())
    register_service("pdf_generation_strategy", DefaultPdfGenerationStrategy())

    # Set default loaders for core Resume class
    set_default_loaders(
        content_loader=content_loader,
        palette_loader=palette_loader,
        path_resolver=path_resolver,
        palette_registry_provider=get_palette_registry,
    )

    # Warm the palette registry once at startup to avoid expensive discovery
    # during latency-sensitive operations (e.g., concurrent renders in tests).
    get_palette_registry()


__all__ = [
    "DefaultTemplateLocator",
    "DefaultEffectExecutor",
    "DefaultPathResolver",
    "DefaultContentLoader",
    "DefaultPdfGenerationStrategy",
    "DefaultHtmlGenerator",
    "DefaultFileOpenerService",
    "DefaultPaletteLoader",
    "DefaultLaTeXRenderer",
    "register_default_services",
]
