"""Protocol definitions for shell layer dependencies.

These protocols define the interfaces that shell layer implementations
must provide to the core layer, enabling dependency injection without
late-bound imports.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class TemplateLocator(Protocol):
    """Protocol for locating template directories."""

    def get_template_location(self) -> Path:
        """Get the template directory path."""
        ...


@runtime_checkable
class EffectExecutor(Protocol):
    """Protocol for executing effects."""

    def execute(self, effect: Any) -> Any:
        """Execute a single effect and return its result (type varies)."""
        ...

    def execute_many(self, effects: list[Any]) -> None:
        """Execute multiple effects."""
        ...


@runtime_checkable
class ContentLoader(Protocol):
    """Protocol for loading resume content."""

    def load(
        self,
        name: str,
        paths: Any,
        transform_markdown: bool,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Load content from a YAML file."""
        ...


@runtime_checkable
class PdfGenerationStrategy(Protocol):
    """Protocol for PDF generation strategies."""

    def generate(
        self,
        render_plan: Any,
        output_path: Path,
        resume_name: str,
        filename: str | None = None,
    ) -> tuple[Any, int | None]:
        """Generate a PDF file."""
        ...


@runtime_checkable
class HtmlGenerator(Protocol):
    """Protocol for HTML generation."""

    def generate(
        self,
        render_plan: Any,
        output_path: Path,
        filename: str | None = None,
    ) -> Any:
        """Generate HTML content."""
        ...


@runtime_checkable
class FileOpenerService(Protocol):
    """Protocol for opening files."""

    def open_file(self, path: Path, format_type: str | None = None) -> bool:
        """Open a file with the system default application."""
        ...


@runtime_checkable
class PaletteLoader(Protocol):
    """Protocol for loading color palettes."""

    def load_palette_from_file(self, path: str | Path) -> dict[str, Any]:
        """Load a palette from a file."""
        ...


@runtime_checkable
class PathResolver(Protocol):
    """Protocol for resolving file paths."""

    def candidate_yaml_path(self, name: str) -> Path:
        """Get candidate YAML path for a name."""
        ...

    def resolve_paths_for_read(
        self,
        paths: Any,
        overrides: dict[str, Any],
        candidate_path: Path,
    ) -> Any:
        """Resolve paths for reading operations."""
        ...


@runtime_checkable
class LaTeXRenderer(Protocol):
    """Protocol for LaTeX rendering."""

    def get_latex_functions(self) -> tuple[Any, Any, Any]:
        """Get LaTeX compilation functions."""
        ...


__all__ = [
    "TemplateLocator",
    "EffectExecutor",
    "ContentLoader",
    "PdfGenerationStrategy",
    "HtmlGenerator",
    "FileOpenerService",
    "PaletteLoader",
    "PathResolver",
    "LaTeXRenderer",
]
