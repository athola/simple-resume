"""Provide PDF rendering helpers for the core resume pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import simple_resume.core.latex.types as latex_types
from simple_resume.core.constants import RenderMode
from simple_resume.core.effects import Effect, MakeDirectory, RenderPdf, WriteFile
from simple_resume.core.exceptions import ConfigurationError
from simple_resume.core.generate.exceptions import TemplateError
from simple_resume.core.latex.types import LatexGenerationContext
from simple_resume.core.models import RenderPlan
from simple_resume.core.protocols import EffectExecutor, LaTeXRenderer, TemplateLocator
from simple_resume.core.render import get_template_environment
from simple_resume.core.result import GenerationMetadata, GenerationResult


@dataclass(frozen=True)
class _PdfGenerationParams:
    """Parameters for PDF generation to reduce function argument count."""

    render_plan: RenderPlan
    output_path: Path
    resume_name: str
    filename: str | None = None
    template_locator: TemplateLocator | None = None
    latex_renderer: LaTeXRenderer | None = None
    effect_executor: EffectExecutor | None = None
    existing_context: LatexGenerationContext | None = None


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


class PdfGeneratorFactory:
    """Factory for creating PDF generation functions with configured dependencies."""

    def __init__(
        self,
        effect_executor: EffectExecutor | None = None,
        template_locator: TemplateLocator | None = None,
        latex_renderer: LaTeXRenderer | None = None,
    ):
        """Initialize factory with optional default dependencies.

        Args:
            effect_executor: Default effect executor to use when none is injected
            template_locator: Default template locator to use when none is injected
            latex_renderer: Default LaTeX renderer to use when none is injected

        """
        self._effect_executor = effect_executor
        self._template_locator = template_locator
        self._latex_renderer = latex_renderer

    def _get_effect_executor(self, injected: EffectExecutor | None) -> EffectExecutor:
        """Get effect executor, preferring injected over default."""
        if injected is not None:
            return injected
        if self._effect_executor is not None:
            return self._effect_executor
        raise ConfigurationError(
            "No effect executor available. "
            "Either inject one or ensure factory is configured with a default."
        )

    def _get_template_locator(
        self, injected: TemplateLocator | None
    ) -> TemplateLocator:
        """Get template locator, preferring injected over default."""
        if injected is not None:
            return injected
        if self._template_locator is not None:
            return self._template_locator
        raise ConfigurationError(
            "No template locator available. "
            "Inject one or configure the factory with a default."
        )

    def _get_latex_renderer(self, injected: LaTeXRenderer | None) -> LaTeXRenderer:
        """Get LaTeX renderer, preferring injected over default."""
        if injected is not None:
            return injected
        if self._latex_renderer is not None:
            return self._latex_renderer
        raise ConfigurationError(
            "No LaTeX renderer available. "
            "Inject one or configure the factory with a default."
        )

    def create_prepare_pdf_with_weasyprint_function(
        self,
    ) -> Callable[..., tuple[str, list[Effect], GenerationMetadata]]:
        """Create a prepare_pdf_with_weasyprint function with factory's dependencies.

        Returns:
            A function that takes (render_plan, output_path, **kwargs) and returns
            (html_content, effects, metadata)

        """
        factory = self

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
            params = _PdfGenerationParams(
                render_plan=render_plan,
                output_path=output_path,
                resume_name=resume_name,
                filename=filename,
                template_locator=template_locator,
            )
            return _prepare_pdf_with_weasyprint_impl(
                params,
                factory,
            )

        return prepare_pdf_with_weasyprint

    def create_generate_pdf_with_weasyprint_function(
        self,
    ) -> Callable[..., tuple[GenerationResult, int | None]]:
        """Create a generate_pdf_with_weasyprint function with factory's dependencies.

        Returns:
            A function that takes (render_plan, output_path, **kwargs) and returns
            (result, page_count)

        """
        factory = self

        def generate_pdf_with_weasyprint(
            render_plan: RenderPlan,
            output_path: Path,
            *,
            resume_name: str,
            filename: str | None = None,
            effect_executor: EffectExecutor | None = None,
        ) -> tuple[GenerationResult, int | None]:
            """Generate PDF using WeasyPrint (shell execution).

            This function executes effects produced by prepare_pdf_with_weasyprint
            and returns result and page count.
            """
            # Prepare PDF generation in core (pure)
            html_content, effects, metadata = (
                factory.create_prepare_pdf_with_weasyprint_function()(
                    render_plan=render_plan,
                    output_path=output_path,
                    resume_name=resume_name,
                    filename=filename,
                )
            )

            # Execute effects using injected or default executor
            executor = factory._get_effect_executor(effect_executor)
            page_count: int | None = None
            for effect in effects:
                result = executor.execute(effect)
                if isinstance(effect, RenderPdf) and isinstance(result, int):
                    page_count = result

            # Create and return result
            result = GenerationResult(
                output_path=output_path,
                format_type="pdf",
                metadata=metadata,
            )

            return result, page_count

        return generate_pdf_with_weasyprint

    def create_prepare_pdf_with_latex_function(
        self,
    ) -> Callable[..., tuple[str, list[Effect], GenerationMetadata]]:
        """Create a prepare_pdf_with_latex function with factory's dependencies.

        Returns:
            A function that takes (render_plan, output_path, **kwargs) and returns
            (tex_content, effects, metadata)

        """
        factory = self

        def prepare_pdf_with_latex(
            render_plan: RenderPlan,
            output_path: Path,
            config: PdfGenerationConfig,
        ) -> tuple[str, list[Effect], GenerationMetadata]:
            """Prepare PDF generation using LaTeX (pure function).

            This function performs NO I/O operations. It prepares LaTeX content and
            returns a list of effects that the shell layer should execute.

            Args:
                render_plan: Rendering configuration and context
                output_path: Target PDF file path
                config: Configuration for PDF generation including resume details
                    and dependencies
                resume_name: Name of the resume
                filename: Source filename for error messages
                template_locator: Optional template locator for dependency injection
                latex_renderer: Optional LaTeX renderer for dependency injection

            Returns:
                Tuple of (tex_content, effects, metadata)
                - tex_content: Rendered LaTeX as string
                - effects: List of effects to execute (MakeDirectory, WriteFile)
                - metadata: Generation metadata

            Raises:
                TemplateError: If render plan is invalid or uses HTML mode
                LaTeXCompilationError: If LaTeX compilation fails
                FileNotFoundError: If required files are missing

            """
            params = _PdfGenerationParams(
                render_plan=render_plan,
                output_path=output_path,
                resume_name=config.resume_name,
                filename=config.filename,
                template_locator=config.template_locator,
                latex_renderer=config.latex_renderer,
            )
            return _prepare_pdf_with_latex_impl(
                params,
                factory,
            )

        return prepare_pdf_with_latex

    def create_generate_pdf_with_latex_function(
        self,
    ) -> Callable[..., tuple[GenerationResult, int | None]]:
        """Create a generate_pdf_with_latex function with factory's dependencies.

        Returns:
            A function that takes (render_plan, output_path, **kwargs) and returns
            (result, page_count)

        """
        factory = self

        def generate_pdf_with_latex(  # noqa: PLR0913
            render_plan: RenderPlan,
            output_path: Path,
            *,
            resume_name: str,
            filename: str | None = None,
            template_locator: TemplateLocator | None = None,
            latex_renderer: LaTeXRenderer | None = None,
            effect_executor: EffectExecutor | None = None,
        ) -> tuple[GenerationResult, int | None]:
            """Generate PDF using LaTeX (shell execution).

            This function executes effects produced by prepare_pdf_with_latex
            and returns result and page count.
            """
            # Prepare PDF generation in core (pure)
            tex_content, effects, metadata = (
                factory.create_prepare_pdf_with_latex_function()(
                    render_plan=render_plan,
                    output_path=output_path,
                    resume_name=resume_name,
                    filename=filename,
                    template_locator=template_locator,
                )
            )

            # Execute effects using injected or default executor
            executor = factory._get_effect_executor(effect_executor)
            executor.execute_many(effects)

            # Extract page count from prepared metadata
            page_count = (
                metadata.page_count if hasattr(metadata, "page_count") else None
            )

            # Create and return result
            result = GenerationResult(
                output_path=output_path,
                format_type="pdf",
                metadata=metadata,
            )

            return result, page_count

        return generate_pdf_with_latex


def _prepare_pdf_with_weasyprint_impl(
    params: _PdfGenerationParams,
    factory: PdfGeneratorFactory,
) -> tuple[str, list[Effect], GenerationMetadata]:
    """Implement WeasyPrint PDF generation using factory for dependencies.

    Args:
        params: Parameters containing render_plan, output_path, resume_name,
                 filename, and template_locator
        factory: PDF generator factory for dependency resolution

    Returns:
        Tuple of (html_content, effects, metadata)

    Raises:
        TemplateError: If render plan is invalid or uses LaTeX mode

    """
    if params.render_plan.mode is RenderMode.LATEX:
        raise TemplateError(
            "LaTeX mode not supported in WeasyPrint generation method",
            template_name="latex",
            filename=params.filename,
        )

    if not params.render_plan.context or not params.render_plan.template_name:
        raise TemplateError(
            "HTML plan missing context or template_name",
            filename=params.filename,
        )

    # Resolve template location using factory
    locator = factory._get_template_locator(params.template_locator)
    template_loc = locator.get_template_location()
    env = get_template_environment(str(template_loc))
    html = (
        env.get_template(params.render_plan.template_name)
        .render(**params.render_plan.context)
        .lstrip()
    )

    # Pure operations: Prepare CSS for page size
    page_width = params.render_plan.config.page_width or 210
    page_height = params.render_plan.config.page_height or 297
    css_string = f"@page {{size: {page_width}mm {page_height}mm; margin: 0mm;}}"

    # Create effects for shell execution (no PDF rendering here)
    # Use static/css as base_url so font paths like "../fonts/AvenirLTStd-Light.otf"
    # resolve correctly to assets/static/fonts/AvenirLTStd-Light.otf
    css_base_url = template_loc.parent / "static" / "css"
    effects: list[Effect] = [
        MakeDirectory(path=params.output_path.parent, parents=True),
        RenderPdf(
            html=html,
            css=css_string,
            output_path=params.output_path,
            base_url=str(css_base_url),
        ),
    ]

    # Create metadata
    metadata = GenerationMetadata(
        format_type="pdf",
        template_name=params.render_plan.template_name or "unknown",
        generation_time=0.0,
        file_size=0,
        resume_name=params.resume_name,
        palette_info=params.render_plan.palette_metadata,
        page_count=None,
    )

    return html, effects, metadata


def _prepare_pdf_with_latex_impl(
    params: _PdfGenerationParams,
    factory: PdfGeneratorFactory,
) -> tuple[str, list[Effect], GenerationMetadata]:
    """Implement LaTeX PDF generation using factory for dependencies.

    Args:
        params: Parameters containing render_plan, output_path, resume_name,
                 filename, template_locator, and latex_renderer
        factory: PDF generator factory for dependency resolution

    Returns:
        Tuple of (tex_content, effects, metadata)

    Raises:
        ConfigurationError: If LaTeX renderer unavailable

    """
    # Check latex renderer availability
    renderer = factory._get_latex_renderer(params.latex_renderer)
    LatexCompilationError, compile_tex_to_pdf, render_resume_latex_from_data = (
        get_latex_functions(renderer)
    )
    if any(
        func is None
        for func in (
            LatexCompilationError,
            compile_tex_to_pdf,
            render_resume_latex_from_data,
        )
    ):
        raise ConfigurationError(
            "LaTeX renderer unavailable. "
            "Inject a renderer that provides compilation functions."
        )

    # Prepare LaTeX generation context and resolve paths.
    if params.existing_context is not None:
        context = params.existing_context
    elif latex_types.LatexGenerationContext.last_context is not None:
        context = latex_types.LatexGenerationContext.last_context
    else:
        context = LatexGenerationContext(
            resume_data=params.render_plan.context,
            processed_data=params.render_plan.context or {},
            output_path=params.output_path,
            base_path=params.render_plan.base_path,
            filename=params.filename,
        )
    resolved_paths = context.paths
    if resolved_paths is None:
        # Strictly require resolved paths to avoid implicit template resolution.
        # Tests expect a configuration error when paths are missing so we fail
        # fast instead of attempting to fall back to packaged assets.
        raise ConfigurationError(
            "LaTeX generation requires resolved paths (templates/static). "
            "Provide Paths or configure the shell layer before rendering."
        )

    # Generate LaTeX content
    try:
        resume_data = (
            context.processed_data
            if isinstance(context.processed_data, dict)
            else context.resume_data
            if isinstance(context.resume_data, dict)
            else params.render_plan.context or {}
        )
        tex_result = render_resume_latex_from_data(
            resume_data,
            paths=resolved_paths,
            template_name=params.render_plan.template_name or "latex/basic.tex",
        )
        tex_content = getattr(tex_result, "tex", tex_result)
    except Exception as exc:
        if "No such file or directory" in str(exc):
            raise FileNotFoundError(
                f"Template not found: {resolved_paths.templates}"
            ) from exc
        raise

    # Resolve paths for effects
    # resolved_paths is guaranteed by earlier guard

    # Prepare effects for shell execution
    effects: list[Effect] = [
        MakeDirectory(path=params.output_path.parent, parents=True),
        WriteFile(
            path=params.output_path.with_suffix(".tex"),
            content=tex_content,
            encoding="utf-8",
        ),
    ]

    # Create metadata
    metadata = GenerationMetadata(
        format_type="pdf",
        template_name=params.render_plan.template_name or "latex",
        generation_time=0.0,
        file_size=len(tex_content.encode("utf-8")),
        resume_name=params.resume_name,
        palette_info=params.render_plan.palette_metadata,
        page_count=context.metadata.page_count
        if hasattr(context.metadata, "page_count")
        else None,
    )

    return tex_content, effects, metadata


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
    factory = PdfGeneratorFactory()
    params = _PdfGenerationParams(
        render_plan=render_plan,
        output_path=output_path,
        resume_name=resume_name,
        filename=filename,
        template_locator=template_locator,
    )
    return _prepare_pdf_with_weasyprint_impl(params, factory)


class PdfGenerationConfig:
    """Configuration for PDF generation functions."""

    def __init__(
        self,
        *,
        resume_name: str,
        filename: str | None = None,
        template_locator: TemplateLocator | None = None,
        latex_renderer: LaTeXRenderer | None = None,
        effect_executor: EffectExecutor | None = None,
    ):
        self.resume_name = resume_name
        self.filename = filename
        self.template_locator = template_locator
        self.latex_renderer = latex_renderer
        self.effect_executor = effect_executor


def prepare_pdf_with_latex(
    render_plan: RenderPlan,
    output_path: Path,
    config: PdfGenerationConfig | LatexGenerationContext,
) -> tuple[str, list[Effect], GenerationMetadata]:
    """Prepare PDF generation using LaTeX (pure function).

    This function performs NO I/O operations. It prepares TeX content and
    returns a list of effects that the shell layer should execute.

    Args:
        render_plan: Rendering configuration and context
        output_path: Target PDF file path
        config: PDF generation configuration

    Returns:
        Tuple of (tex_content, effects, metadata)
        - tex_content: Rendered TeX source code
        - effects: List of effects to execute
        - metadata: Generation metadata

    Raises:
        ConfigurationError: If paths is None or LaTeX renderer unavailable

    """
    factory = PdfGeneratorFactory()
    if isinstance(config, LatexGenerationContext):
        params = _PdfGenerationParams(
            render_plan=render_plan,
            output_path=output_path,
            resume_name=render_plan.name,
            filename=config.filename,
            existing_context=config,
        )
    else:
        params = _PdfGenerationParams(
            render_plan=render_plan,
            output_path=output_path,
            resume_name=config.resume_name,
            filename=config.filename,
            template_locator=config.template_locator,
            latex_renderer=config.latex_renderer,
            effect_executor=config.effect_executor,
        )
    return _prepare_pdf_with_latex_impl(
        params,
        factory,
    )


def generate_pdf_with_weasyprint(
    render_plan: RenderPlan,
    output_path: Path,
    config: PdfGenerationConfig,
) -> tuple[GenerationResult, int | None]:
    """Generate PDF using WeasyPrint (shell execution).

    This function executes the effects produced by prepare_pdf_with_weasyprint
    and returns the result and page count.
    """
    factory = PdfGeneratorFactory(
        effect_executor=config.effect_executor,
        template_locator=config.template_locator,
        latex_renderer=config.latex_renderer,
    )
    generator = factory.create_generate_pdf_with_weasyprint_function()
    return generator(
        render_plan=render_plan,
        output_path=output_path,
        resume_name=config.resume_name,
        filename=config.filename,
        effect_executor=config.effect_executor,
    )


__all__ = [
    "PdfGeneratorFactory",
    "prepare_pdf_with_weasyprint",
    "prepare_pdf_with_latex",
    "generate_pdf_with_weasyprint",
    "get_latex_functions",
]
