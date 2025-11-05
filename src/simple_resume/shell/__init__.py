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

__all__ = [
    "ResumeGenerator",
    "GenerationDeps",
    "LocalFileSystem",
    "WeasyPrintWriter",
    "HtmlWriter",
    "PrintLogger",
    "PageSpec",
]
