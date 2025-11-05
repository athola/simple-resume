"""Shell layer for resume generation - orchestrates I/O and external dependencies.

This module contains the imperative shell that handles file I/O, subprocess calls,
and orchestration of the resume generation process. All business logic is delegated
to the pure core functions.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, TextIO

from .. import config
from ..core.resume import RenderPlan, Resume
from ..latex_renderer import (
    LatexCompilationError,
    compile_tex_to_html,
    compile_tex_to_pdf,
)
from ..rendering import get_template_environment
from ..utilities import get_content

try:
    from weasyprint import CSS, HTML
except ImportError:
    CSS = HTML = None  # typer: ignore


class FileSystem(Protocol):
    """Minimal filesystem abstraction used by resume generation."""

    def ensure_dir(self, path: Path) -> None:  # pragma: no cover - protocol
        """Create the provided directory (idempotent)."""
        ...

    def iterdir(self, path: Path) -> Iterable[Path]:  # pragma: no cover - protocol
        """Yield the direct children for the given directory."""
        ...

    def is_dir(self, path: Path) -> bool:  # pragma: no cover - protocol
        """Return True when the provided path points to an existing directory."""
        ...


class LocalFileSystem:
    """FileSystem implementation backed by pathlib."""

    def ensure_dir(self, path: Path) -> None:
        """Create the directory if it does not already exist."""
        path.mkdir(parents=True, exist_ok=True)

    def iterdir(self, path: Path) -> Iterable[Path]:
        """Yield entries inside the provided directory."""
        return path.iterdir()

    def is_dir(self, path: Path) -> bool:
        """Return True when the path exists and is a directory."""
        return path.is_dir()


class PdfWriter(Protocol):
    """Write HTML + CSS content to a PDF file on disk."""

    def write(
        self,
        *,
        output_path: Path,
        html: str,
        base_url: str,
        page: PageSpec,
    ) -> None:  # pragma: no cover - protocol
        """Persist the rendered resume to the provided path."""
        ...


class WeasyPrintWriter:
    """PdfWriter implementation backed by WeasyPrint."""

    def write(
        self,
        *,
        output_path: Path,
        html: str,
        base_url: str,
        page: PageSpec,
    ) -> None:
        """Render the resume HTML with WeasyPrint and write to disk."""
        if CSS is None or HTML is None:
            raise ImportError("WeasyPrint is required for PDF generation")

        css = CSS(
            string=f"@page {{size: {page.width_mm}mm {page.height_mm}mm; margin: 0mm;}}"
        )
        HTML(string=html, base_url=base_url).write_pdf(
            str(output_path),
            stylesheets=[css],
        )


class HtmlWriter:
    """Write HTML content to a file on disk."""

    def write(
        self,
        *,
        output_path: Path,
        html: str,
    ) -> None:
        """Write the HTML content to the provided path."""
        output_path.write_text(html, encoding="utf-8")


class Logger(Protocol):
    """Reporting hooks for generation progress."""

    def starting(self, name: str, output_path: Path) -> None:  # pragma: no cover
        """Log the beginning of a resume generation."""
        ...

    def succeeded(self, name: str, output_path: Path) -> None:  # pragma: no cover
        """Log a successful resume generation."""
        ...

    def failed(
        self, name: str, output_path: Path, error: Exception
    ) -> None:  # pragma: no cover
        """Log a failure to generate a resume."""
        ...


class PrintLogger:
    """Default Logger that prints to stdout/stderr."""

    def __init__(
        self, stdout: TextIO | None = None, stderr: TextIO | None = None
    ) -> None:
        """Create a printer-based logger with optional stream overrides."""
        self._stdout: TextIO = stdout if stdout is not None else sys.stdout
        self._stderr: TextIO = stderr if stderr is not None else sys.stderr

    def starting(self, name: str, output_path: Path) -> None:
        """Emit a friendly heading before generation."""
        print(f"\n-- Creating {output_path.name} --", file=self._stdout)

    def succeeded(self, name: str, output_path: Path) -> None:
        """Emit a success message after generation."""
        print(f"✓ Generated: {output_path}", file=self._stdout)

    def failed(self, name: str, output_path: Path, error: Exception) -> None:
        """Emit a failure message when generation raises."""
        print(f"✗ Failed to generate {output_path.name}: {error}", file=self._stderr)


@dataclass(frozen=True)
class PageSpec:
    """Page dimension information in millimetres."""

    width_mm: int
    height_mm: int


@dataclass(frozen=True)
class GenerationDeps:
    """Container for dependencies used when emitting resumes."""

    pdf_writer: PdfWriter
    html_writer: HtmlWriter
    logger: Logger
    viewer: Callable[[str], None]
    filesystem: FileSystem = LocalFileSystem()


class ResumeGenerator:
    """Shell orchestration for resume generation with I/O dependencies."""

    def __init__(self, deps: GenerationDeps | None = None) -> None:
        """Create generator with dependency injection for testing."""
        self.deps = deps or GenerationDeps(
            pdf_writer=WeasyPrintWriter(),
            html_writer=HtmlWriter(),
            logger=PrintLogger(),
            viewer=self._open_file,
            filesystem=LocalFileSystem(),
        )

    def generate_pdf(
        self,
        data_dir: str | os.PathLike[str] | None = None,
        *,
        open_after: bool = False,
        paths: config.Paths | None = None,
        **path_overrides: str | os.PathLike[str],
    ) -> None:
        """Generate PDFs from YAML files.

        Args:
            data_dir: Optional path to the directory containing resume inputs.
            open_after: When True, open each generated PDF with the system viewer.
            paths: Pre-resolved config paths. Overrides are ignored when provided.
            **path_overrides: Override specific paths (data=, input=, output=).

        Raises:
            ValueError: If data_dir does not exist or both paths and overrides are set.
            FileNotFoundError: If no YAML files are in the input directory.

        """
        resolved_paths = self._resolve_paths(data_dir, paths, path_overrides)
        self._ensure_directories(resolved_paths)

        yaml_files = self._collect_yaml_inputs(resolved_paths.input)
        if not yaml_files:
            raise FileNotFoundError(
                f"No YAML files found in {resolved_paths.input}. "
                f"Add at least one .yaml or .yml file to generate PDFs."
            )

        for source in yaml_files:
            try:
                self._generate_single_pdf(source, resolved_paths, open_after)
            except Exception as exc:
                output_path = resolved_paths.output / f"{source.stem}.pdf"
                self.deps.logger.failed(source.stem, output_path, exc)

    def generate_html(
        self,
        data_dir: str | os.PathLike[str] | None = None,
        *,
        open_after: bool = False,
        browser: str | None = None,
        paths: config.Paths | None = None,
        **path_overrides: str | os.PathLike[str],
    ) -> None:
        """Generate HTML resumes from YAML files.

        Args:
            data_dir: Optional path to the directory containing resume inputs.
            open_after: When True, open each generated HTML file in a browser.
            browser: Optional explicit browser command, e.g., "firefox".
            paths: Pre-resolved config paths.
            **path_overrides: Override specific paths (data=, input=, output=).

        Raises:
            ValueError: If data_dir does not exist or both paths and overrides are set.
            FileNotFoundError: If no YAML files are in the input directory.

        """
        resolved_paths = self._resolve_paths(data_dir, paths, path_overrides)
        self._ensure_directories(resolved_paths)

        yaml_files = self._collect_yaml_inputs(resolved_paths.input)
        if not yaml_files:
            raise FileNotFoundError(
                f"No YAML files found in {resolved_paths.input}. "
                f"Add at least one .yaml or .yml file to render HTML resumes."
            )

        for source in yaml_files:
            try:
                self._generate_single_html(source, resolved_paths, open_after, browser)
            except Exception as exc:
                output_path = resolved_paths.output / f"{source.stem}.html"
                self.deps.logger.failed(source.stem, output_path, exc)

    def _generate_single_pdf(
        self,
        source: Path,
        paths: config.Paths,
        open_after: bool,
    ) -> None:
        """Generate a single PDF from a YAML file."""
        name = source.stem
        output_file = paths.output / f"{name}.pdf"

        self.deps.logger.starting(name, output_file)

        # Load raw data (I/O)
        raw_data = get_content(name, paths=paths, transform_markdown=False)

        # Create render plan using core logic (pure)
        plan = Resume.prepare_render_data(
            raw_data=raw_data, preview=False, base_path=str(paths.content)
        )

        # Execute the plan (I/O)
        if plan.mode == "latex":
            self._execute_latex_plan(plan, output_file, open_after)
        else:
            self._execute_html_pdf_plan(plan, output_file, open_after)

        self.deps.logger.succeeded(name, output_file)

    def _generate_single_html(
        self,
        source: Path,
        paths: config.Paths,
        open_after: bool,
        browser: str | None,
    ) -> None:
        """Generate a single HTML from a YAML file."""
        name = source.stem
        output_file = paths.output / f"{name}.html"

        self.deps.logger.starting(name, output_file)

        # Load raw data (I/O)
        raw_data = get_content(name, paths=paths, transform_markdown=False)

        # Create render plan using core logic (pure)
        plan = Resume.prepare_render_data(
            raw_data=raw_data, preview=True, base_path=str(paths.content)
        )

        # Execute the plan (I/O)
        if plan.mode == "latex":
            self._execute_latex_html_plan(plan, output_file, open_after, browser)
        else:
            self._execute_html_plan(plan, output_file, open_after, browser)

        self.deps.logger.succeeded(name, output_file)

    def _execute_html_pdf_plan(
        self,
        plan: RenderPlan,
        output_file: Path,
        open_after: bool,
    ) -> None:
        """Execute an HTML-to-PDF render plan."""
        if not plan.context or not plan.template_name:
            raise ValueError("HTML plan missing context or template")

        # Render template (I/O)
        env = get_template_environment(str(plan.base_path))
        html = env.get_template(plan.template_name).render(**plan.context)

        # Generate PDF (I/O)
        page = self._determine_page_spec(plan.config)
        self.deps.pdf_writer.write(
            output_path=output_file,
            html=html,
            base_url=plan.base_path,
            page=page,
        )

        if open_after:
            self.deps.viewer(str(output_file))

    def _execute_html_plan(
        self,
        plan: RenderPlan,
        output_file: Path,
        open_after: bool,
        browser: str | None,
    ) -> None:
        """Execute an HTML render plan."""
        if not plan.context or not plan.template_name:
            raise ValueError("HTML plan missing context or template")

        # Render template (I/O)
        env = get_template_environment(str(plan.base_path))
        html = env.get_template(plan.template_name).render(**plan.context)

        # Add base href for asset resolution
        html_with_base = self._inject_base_href(html, Path(plan.base_path))

        # Write HTML file (I/O)
        self.deps.html_writer.write(output_path=output_file, html=html_with_base)

        if open_after:
            self._open_in_browser(output_file, browser)

    def _execute_latex_plan(
        self,
        plan: RenderPlan,
        output_file: Path,
        open_after: bool,
    ) -> None:
        """Execute a LaTeX-to-PDF render plan."""
        if not plan.tex:
            raise ValueError("LaTeX plan missing tex content")

        tex_path = output_file.parent / f"{output_file.stem}.tex"
        tex_path.write_text(plan.tex, encoding="utf-8")

        try:
            pdf_path = compile_tex_to_pdf(tex_path)
        except LatexCompilationError as exc:
            # Persist log for easier debugging when available.
            if exc.log:
                tex_path.with_suffix(".log").write_text(exc.log, encoding="utf-8")
            raise
        finally:
            self._cleanup_latex_artifacts(tex_path)

        if open_after:
            self.deps.viewer(str(pdf_path))

    def _execute_latex_html_plan(
        self,
        plan: RenderPlan,
        output_file: Path,
        open_after: bool,
        browser: str | None,
    ) -> None:
        """Execute a LaTeX-to-HTML render plan."""
        if not plan.tex:
            raise ValueError("LaTeX plan missing tex content")

        tex_path = output_file.parent / f"{output_file.stem}.tex"
        tex_path.write_text(plan.tex, encoding="utf-8")

        try:
            html_path = compile_tex_to_html(tex_path)
        finally:
            self._cleanup_latex_artifacts(tex_path)

        if open_after:
            self._open_in_browser(html_path, browser)

    def _resolve_paths(
        self,
        data_dir: str | os.PathLike[str] | None,
        paths: config.Paths | None,
        overrides: dict[str, str | os.PathLike[str]],
    ) -> config.Paths:
        """Resolve configuration paths with validation."""
        _ALLOWED_PATH_OVERRIDES = {"content_dir", "templates_dir", "static_dir"}

        if paths is not None and any(value is not None for value in overrides.values()):
            raise ValueError("Provide `paths` or individual overrides, not both.")

        if data_dir is not None and not self.deps.filesystem.is_dir(Path(data_dir)):
            raise ValueError(f"Data directory does not exist: {data_dir}")

        if paths is not None:
            return paths

        clean_overrides = {
            key: value for key, value in overrides.items() if value is not None
        }
        return config.resolve_paths(data_dir, **clean_overrides)

    def _ensure_directories(self, paths: config.Paths) -> None:
        """Ensure required directories exist."""
        self.deps.filesystem.ensure_dir(paths.input)
        self.deps.filesystem.ensure_dir(paths.output)

    def _collect_yaml_inputs(self, input_path: Path) -> list[Path]:
        """Collect YAML input files from directory."""
        MIN_FILENAME_PARTS = 2
        yaml_files: list[Path] = []

        for entry in self.deps.filesystem.iterdir(input_path):
            if not entry.is_file():
                continue
            parts = entry.name.split(".")
            if len(parts) >= MIN_FILENAME_PARTS and parts[-1].lower() in {
                "yaml",
                "yml",
            }:
                yaml_files.append(entry)

        return yaml_files

    def _determine_page_spec(self, config: Any) -> PageSpec:
        """Extract page dimensions from config."""
        if hasattr(config, "page_width") and hasattr(config, "page_height"):
            width = int(float(config.page_width or 190))
            height = int(float(config.page_height or 270))
        else:
            width = 190
            height = 270
        return PageSpec(width_mm=width, height_mm=height)

    def _inject_base_href(self, html: str, base_path: Path) -> str:
        """Inject base href tag into HTML for asset resolution."""
        base_uri = base_path.resolve().as_uri().rstrip("/") + "/"
        base_tag = f'<base href="{base_uri}">'
        if "<head>" in html:
            return html.replace("<head>", f"<head>\n  {base_tag}", 1)
        return f"{base_tag}\n{html}"

    def _cleanup_latex_artifacts(self, tex_path: Path) -> None:
        """Remove auxiliary files generated during LaTeX compilation."""
        for suffix in (".aux", ".log", ".out"):
            candidate = tex_path.with_suffix(suffix)
            try:
                if candidate.exists():
                    candidate.unlink()
            except OSError:
                continue

    def _open_file(self, path: str) -> None:
        """Open a file with the OS default PDF viewer."""
        try:
            if sys.platform.startswith("darwin"):
                opener = shutil.which("open") or "open"
                subprocess.Popen(  # noqa: S603
                    [opener, path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]  # noqa: S606
            else:
                opener = shutil.which("xdg-open")
                if opener is None:
                    print(
                        "Tip: install xdg-utils to open PDFs automatically.",
                        file=sys.stderr,
                    )
                    return
                subprocess.Popen(  # noqa: S603
                    [opener, path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except Exception as exc:  # noqa: BLE001
            print(f"Warning: Could not open {path}: {exc}", file=sys.stderr)

    def _open_in_browser(self, path: Path, browser: str | None) -> None:
        """Open HTML file in browser."""
        DEFAULT_BROWSERS = ("firefox", "chromium")

        def _browser_command(browser_name: str | None) -> list[str] | None:
            if browser_name is None:
                for candidate in DEFAULT_BROWSERS:
                    if shutil.which(candidate):
                        return [candidate]
                return None
            if shutil.which(browser_name):
                return [browser_name]
            return None

        command = _browser_command(browser)
        if command is None:
            print(
                "Tip: install Firefox or Chromium to preview HTML resumes "
                "automatically.",
                file=sys.stderr,
            )
            return

        try:
            subprocess.Popen(  # noqa: S603
                [*command, str(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"Warning: could not launch {command[0]}: {exc}", file=sys.stderr)


__all__ = [
    "ResumeGenerator",
    "GenerationDeps",
    "LocalFileSystem",
    "WeasyPrintWriter",
    "HtmlWriter",
    "PrintLogger",
    "PageSpec",
]
