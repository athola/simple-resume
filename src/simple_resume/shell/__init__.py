"""Shell layer for resume generation - orchestrates I/O and external dependencies."""

from .generation import (
    GenerationDeps,
    HtmlWriter,
    LocalFileSystem,
    PageSpec,
    PrintLogger,
    ResumeGenerator,
    WeasyPrintWriter,
)
from .rendering_operations import (
    create_backend_injector,
    create_generation_result,
    generate_html_with_jinja,
    generate_pdf_with_weasyprint,
    open_file_in_browser,
)
from .strategies import (
    LatexStrategy,
    PdfGenerationRequest,
    PdfGenerationStrategy,
    WeasyPrintStrategy,
)

__all__ = [
    "ResumeGenerator",
    "GenerationDeps",
    "LocalFileSystem",
    "WeasyPrintWriter",
    "HtmlWriter",
    "PrintLogger",
    "PageSpec",
    "create_backend_injector",
    "create_generation_result",
    "generate_html_with_jinja",
    "generate_pdf_with_weasyprint",
    "open_file_in_browser",
    "PdfGenerationStrategy",
    "WeasyPrintStrategy",
    "LatexStrategy",
    "PdfGenerationRequest",
]
