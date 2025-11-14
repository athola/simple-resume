"""Shell layer for rendering operations with external dependencies.

This module contains all the external dependencies and rendering logic
that should be isolated from the pure core functionality.
"""

from __future__ import annotations

import subprocess  # nosec B404
from pathlib import Path
from types import ModuleType
from typing import Any

from weasyprint import CSS, HTML

# Import internal modules that will receive injected dependencies
from simple_resume.core import html_generation as _html_generation
from simple_resume.core import pdf_generation as _pdf_generation
from simple_resume.core.models import RenderPlan
from simple_resume.rendering import get_template_environment
from simple_resume.result import GenerationMetadata, GenerationResult


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
) -> tuple[GenerationResult, int | None]:
    """Delegate to the HTML-to-PDF backend with patchable dependencies."""
    backend_injector = create_backend_injector(
        _pdf_generation,
        get_template_environment=get_template_environment,
        WEASYPRINT_HTML=HTML,
        WEASYPRINT_CSS=CSS,
    )

    with backend_injector:
        return _pdf_generation.generate_pdf_with_weasyprint(
            render_plan,
            output_path,
            resume_name=resume_name,
            filename=filename,
        )


def generate_html_with_jinja(
    render_plan: RenderPlan,
    output_path: Path,
    filename: str | None = None,
) -> GenerationResult:
    """Render HTML via Jinja with injectable template environment."""
    backend_injector = create_backend_injector(
        _html_generation,
        get_template_environment=get_template_environment,
    )

    with backend_injector:
        return _html_generation.generate_html_with_jinja(
            render_plan,
            output_path,
            filename=filename,
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
            [browser, file_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        # Use default system opener
        subprocess.run(  # noqa: S603  # nosec B603
            ["xdg-open", file_path]
            if Path("/usr/bin/xdg-open").exists()
            else ["open", file_path]
            if Path("/usr/bin/open").exists()
            else ["start", file_path],
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
