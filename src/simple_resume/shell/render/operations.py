"""Shell layer for rendering operations with external dependencies.

This module contains all the external dependencies and rendering logic
that should be isolated from the pure core functionality.
"""

from __future__ import annotations

import subprocess  # nosec B404
from pathlib import Path
from types import ModuleType
from typing import Any

# Import internal modules that will receive injected dependencies
from simple_resume.core.effects import CopyFile, MakeDirectory
from simple_resume.core.generate import html as _html_generation
from simple_resume.core.generate import pdf as _pdf_generation
from simple_resume.core.generate.html import create_html_generator_factory
from simple_resume.core.generate.pdf import PdfGenerationConfig
from simple_resume.core.models import RenderPlan
from simple_resume.core.protocols import EffectExecutor as EffectExecutorProtocol
from simple_resume.core.protocols import TemplateLocator
from simple_resume.core.render import get_template_environment
from simple_resume.core.result import GenerationMetadata, GenerationResult
from simple_resume.shell.config import ASSETS_ROOT, TEMPLATE_LOC
from simple_resume.shell.effect_executor import EffectExecutor


def create_backend_injector(module: ModuleType, **overrides: Any) -> Any:
    """Create a context manager for temporarily overriding module attributes.

    This is a factory function that returns a context manager, keeping the
    core module pure while allowing dependency injection in the shell layer.
    """

    class _BackendInjector:
        def __init__(self, module: ModuleType, **overrides: Any) -> None:
            self.module = module
            self.overrides = overrides
            self.originals: dict[str, Any] = {}

        def __enter__(self) -> None:
            for name, value in self.overrides.items():
                self.originals[name] = getattr(self.module, name, None)
                setattr(self.module, name, value)

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: object,
        ) -> None:
            for name, original in self.originals.items():
                setattr(self.module, name, original)

    return _BackendInjector(module, **overrides)


def generate_pdf_with_weasyprint(
    render_plan: RenderPlan,
    output_path: Path,
    resume_name: str,
    filename: str | None = None,
    effect_executor: EffectExecutorProtocol | None = None,
) -> tuple[GenerationResult, int | None]:
    """Delegate to the HTML-to-PDF backend with patchable dependencies."""

    class _TemplateLocator(TemplateLocator):
        def get_template_location(self) -> Path:
            return TEMPLATE_LOC

    locator = _TemplateLocator()
    executor = effect_executor or EffectExecutor()

    backend_injector = create_backend_injector(
        _pdf_generation,
        get_template_environment=get_template_environment,
    )

    with backend_injector:
        config = PdfGenerationConfig(
            resume_name=resume_name,
            filename=filename,
            template_locator=locator,
            effect_executor=executor,
        )
        return _pdf_generation.generate_pdf_with_weasyprint(
            render_plan,
            output_path,
            config,
        )


def _get_asset_copy_effects(output_dir: Path) -> list[CopyFile | MakeDirectory]:
    """Generate effects to copy CSS and font files to output directory.

    This ensures HTML files work standalone without needing a base tag
    or server. Assets are copied to output_dir/static/css/ and output_dir/static/fonts/.

    Args:
        output_dir: The directory where HTML output is being written

    Returns:
        List of effects to create directories and copy files

    """
    effects: list[CopyFile | MakeDirectory] = []
    static_src = ASSETS_ROOT / "static"

    # CSS files
    css_src = static_src / "css"
    css_dest = output_dir / "static" / "css"
    effects.append(MakeDirectory(path=css_dest, parents=True))

    for css_file in css_src.glob("*.css"):
        effects.append(CopyFile(source=css_file, destination=css_dest / css_file.name))

    # Font files
    fonts_src = static_src / "fonts"
    fonts_dest = output_dir / "static" / "fonts"
    if fonts_src.exists():
        effects.append(MakeDirectory(path=fonts_dest, parents=True))
        for font_file in fonts_src.glob("*"):
            if font_file.is_file():
                effects.append(
                    CopyFile(source=font_file, destination=fonts_dest / font_file.name)
                )

    return effects


def generate_html_with_jinja(
    render_plan: RenderPlan,
    output_path: Path,
    filename: str | None = None,
    effect_executor: EffectExecutorProtocol | None = None,
) -> GenerationResult:
    """Render HTML via Jinja with injectable template environment."""

    class _TemplateLocator(TemplateLocator):
        def get_template_location(self) -> Path:
            return TEMPLATE_LOC

    locator = _TemplateLocator()

    # Create HTML generator factory with explicit locator
    html_factory = create_html_generator_factory(default_template_locator=locator)
    prepare_html_func = html_factory.create_prepare_html_function()

    backend_injector = create_backend_injector(
        _html_generation,
        get_template_environment=get_template_environment,
    )

    with backend_injector:
        html_content, effects, metadata = prepare_html_func(
            render_plan=render_plan,
            output_path=output_path,
            resume_name=filename or "resume",
            filename=filename,
            template_locator=locator,
        )

        # Add effects to copy static assets (CSS, fonts) to output directory
        output_dir = output_path.parent
        asset_effects = _get_asset_copy_effects(output_dir)
        all_effects = list(effects) + asset_effects

        # Execute the effects to actually create the files
        executor = effect_executor or EffectExecutor()
        executor.execute_many(all_effects)

        # Create and return GenerationResult
        return GenerationResult(
            output_path=output_path,
            format_type="html",
            metadata=metadata,
        )


def open_file_in_browser(
    file_path: Path,
    browser: str | None = None,
) -> None:
    """Open a file in the default or specified browser.

    Args:
        file_path: Path to the file to open.
        browser: Optional browser command.

    Returns:
        None

    """
    if browser:
        # Use specified browser command for opening the file
        subprocess.Popen(  # noqa: S603  # nosec B603
            [browser, str(file_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        # Use default system opener
        subprocess.run(  # noqa: S603  # nosec B603
            ["xdg-open", str(file_path)]
            if Path("/usr/bin/xdg-open").exists()
            else ["open", str(file_path)]
            if Path("/usr/bin/open").exists()
            else ["start", str(file_path)],
            check=False,
        )


def create_generation_result(
    output_path: Path,
    format_type: str,
    generation_time: float,
    **metadata_kwargs: Any,
) -> GenerationResult:
    """Create a GenerationResult with metadata."""
    # Explicitly construct metadata with proper types to satisfy type checkers
    metadata = GenerationMetadata(
        format_type=format_type,
        template_name=str(metadata_kwargs.get("template_name", "unknown")),
        generation_time=generation_time,
        file_size=int(metadata_kwargs.get("file_size", 0)),
        resume_name=str(metadata_kwargs.get("resume_name", "resume")),
        palette_info=metadata_kwargs.get("palette_info"),
        page_count=metadata_kwargs.get("page_count"),
    )
    return GenerationResult(output_path, format_type, metadata)


__all__ = [
    "create_backend_injector",
    "generate_pdf_with_weasyprint",
    "generate_html_with_jinja",
    "open_file_in_browser",
    "create_generation_result",
]
