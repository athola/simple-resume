"""Create all resumes from the input folder."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess  # nosec B404
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, TextIO, cast

# TODO (long-term): Evaluate PDF rendering alternatives.
# WeasyPrint has rendering quirks (z-index, positioning) that require workarounds.
#
# Alternatives:
# 1. Playwright: Best rendering quality, but adds a heavy browser dependency.
# 2. ReportLab: Fast and precise, but requires a full template rewrite.
# 3. wkhtmltopdf: Good compatibility, but deprecated and unmaintained.
# 4. Prince: Excellent quality, but commercial licensing is expensive.
#
# See PDF-Renderer-Evaluation.md in the wiki for a detailed comparison.
from weasyprint import CSS, HTML

from . import config
from .rendering import render_resume_html

MIN_FILENAME_PARTS = 2  # filename must have at least name and extension
_ALLOWED_PATH_OVERRIDES = {"content_dir", "templates_dir", "static_dir"}


class FileSystem(Protocol):
    """Minimal filesystem abstraction used by PDF generation."""

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
        css = CSS(
            string=f"@page {{size: {page.width_mm}mm {page.height_mm}mm; margin: 0mm;}}"
        )
        HTML(string=html, base_url=base_url).write_pdf(
            str(output_path),
            stylesheets=[css],
        )


class PdfLogger(Protocol):
    """Reporting hooks for PDF generation progress."""

    def starting(self, name: str, output_path: Path) -> None:  # pragma: no cover
        """Log the beginning of a resume PDF generation."""
        ...

    def succeeded(self, name: str, output_path: Path) -> None:  # pragma: no cover
        """Log a successful resume PDF generation."""
        ...

    def failed(
        self, name: str, output_path: Path, error: Exception
    ) -> None:  # pragma: no cover
        """Log a failure to generate a resume PDF."""
        ...


class PrintLogger:
    """Default PdfLogger that prints to stdout/stderr."""

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


class ResumeRenderer(Protocol):
    """Callable responsible for converting resume data into HTML."""

    def __call__(
        self,
        name: str,
        *,
        preview: bool,
        paths: config.Paths | None,
    ) -> tuple[str, str, dict[str, object]]:  # pragma: no cover - protocol
        """Return rendered HTML, base URL, and resume context."""
        ...


Viewer = Callable[[str], None]


@dataclass(frozen=True)
class PageSpec:
    """Page dimension information in millimetres."""

    width_mm: int
    height_mm: int


def _resolve_paths(
    data_dir: str | os.PathLike[str] | None,
    paths: config.Paths | None,
    overrides: dict[str, str | os.PathLike[str] | None],
    *,
    fs: FileSystem,
) -> config.Paths:
    if paths is not None and any(value is not None for value in overrides.values()):
        raise ValueError("Provide `paths` or individual overrides, not both.")

    if data_dir is not None and not fs.is_dir(Path(data_dir)):
        raise ValueError(f"Data directory does not exist: {data_dir}")

    if paths is not None:
        return paths

    clean_overrides = {
        key: value for key, value in overrides.items() if value is not None
    }
    return config.resolve_paths(data_dir, **clean_overrides)


def _collect_yaml_inputs(input_path: Path, *, fs: FileSystem) -> list[Path]:
    yaml_files: list[Path] = []
    for entry in fs.iterdir(input_path):
        if not entry.is_file():
            continue
        parts = entry.name.split(".")
        if len(parts) >= MIN_FILENAME_PARTS and parts[-1].lower() in {"yaml", "yml"}:
            yaml_files.append(entry)
    return yaml_files


def _determine_page_spec(resume_config: dict[str, object]) -> PageSpec:
    width = int(float(resume_config.get("page_width", 190)))  # type: ignore[arg-type]
    height = int(float(resume_config.get("page_height", 270)))  # type: ignore[arg-type]
    return PageSpec(width_mm=width, height_mm=height)


def _render_resume(
    name: str,
    *,
    renderer: ResumeRenderer,
    resolved_paths: config.Paths,
) -> tuple[str, str, dict[str, object]]:
    html, base_url, context = renderer(name, preview=False, paths=resolved_paths)
    resume_config = context.get("resume_config")
    if not isinstance(resume_config, dict):
        raise ValueError(
            f"Missing 'config' section in resume data for {name}. "
            "Add a config block with page dimensions and colors."
        )
    typed_resume_config = cast(dict[str, object], resume_config)
    return html, base_url, typed_resume_config


@dataclass(frozen=True)
class PdfGenerationDeps:
    """Container for dependencies used when emitting resume PDFs."""

    renderer: ResumeRenderer
    writer: PdfWriter
    logger: PdfLogger
    viewer: Viewer


def _generate_single_pdf(
    name: str,
    resolved_paths: config.Paths,
    output_dir: Path,
    *,
    open_after: bool,
    deps: PdfGenerationDeps,
) -> None:
    output_file = output_dir / f"{name}.pdf"
    deps.logger.starting(name, output_file)
    try:
        html, base_url, resume_config = _render_resume(
            name, renderer=deps.renderer, resolved_paths=resolved_paths
        )
        page = _determine_page_spec(resume_config)
        deps.writer.write(
            output_path=output_file,
            html=html,
            base_url=base_url,
            page=page,
        )
        deps.logger.succeeded(name, output_file)
        if open_after:
            deps.viewer(str(output_file))
    except Exception as exc:  # noqa: BLE001
        deps.logger.failed(name, output_file, exc)


def _open_file(path: str) -> None:
    """Open a file with the OS default PDF viewer."""
    try:
        if sys.platform.startswith("darwin"):
            opener = shutil.which("open") or "open"
            subprocess.Popen(  # noqa: S603  # nosec B603
                [opener, path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]  # noqa: S606  # nosec B606
        else:
            opener = shutil.which("xdg-open")
            if opener is None:
                print(
                    "Tip: install xdg-utils to open PDFs automatically.",
                    file=sys.stderr,
                )
                return
            subprocess.Popen(  # noqa: S603  # nosec B603
                [opener, path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: Could not open {path}: {exc}", file=sys.stderr)


def generate_pdf(
    data_dir: str | os.PathLike[str] | None = None,
    *,
    open_after: bool = False,
    paths: config.Paths | None = None,
    deps: PdfGenerationDeps | None = None,
    filesystem: FileSystem | None = None,
    **path_overrides: str | os.PathLike[str],
) -> None:
    """Generate PDFs from YAML files.

    Args:
        data_dir: Optional path to the directory containing resume inputs.
        open_after: When True, open each generated PDF with the system viewer.
        paths: Pre-resolved config paths. Overrides are ignored when provided.
        deps: Optional dependency bundle controlling rendering, writing, logging,
            and viewing.
        filesystem: Optional filesystem abstraction (defaults to
            :class:`LocalFileSystem`).

    Keyword Args:
        path_overrides: Additional directory overrides; supports the keys
            ``content_dir``, ``templates_dir``, and ``static_dir``.
        content_dir: Optional override for the content directory.
        templates_dir: Optional override for the templates directory.
        static_dir: Optional override for the static assets directory.


    Raises:
        ValueError: If data_dir does not exist or both paths and overrides are set.
        FileNotFoundError: If no YAML files are in the input directory.

    """
    fs = filesystem or LocalFileSystem()
    resolved_deps = deps or PdfGenerationDeps(
        renderer=render_resume_html,
        writer=WeasyPrintWriter(),
        logger=PrintLogger(),
        viewer=_open_file,
    )

    unexpected_keys = set(path_overrides) - _ALLOWED_PATH_OVERRIDES
    if unexpected_keys:
        joined = ", ".join(sorted(unexpected_keys))
        raise TypeError(f"Unsupported path override(s): {joined}")

    overrides = {key: path_overrides.get(key) for key in _ALLOWED_PATH_OVERRIDES}
    resolved_paths = _resolve_paths(
        data_dir,
        paths,
        overrides,
        fs=fs,
    )

    input_path = resolved_paths.input
    output_path = resolved_paths.output

    # Ensure input and output directories exist.
    fs.ensure_dir(input_path)
    fs.ensure_dir(output_path)

    # Find all YAML files in the input directory.
    yaml_files = _collect_yaml_inputs(input_path, fs=fs)
    if not yaml_files:
        raise FileNotFoundError(
            f"No YAML files found in {input_path}. "
            f"Add at least one .yaml or .yml file to generate PDFs."
        )

    for source in yaml_files:
        _generate_single_pdf(
            source.stem,
            resolved_paths,
            output_path,
            open_after=open_after,
            deps=resolved_deps,
        )


def main() -> None:
    """Generate PDF files from resume data via command line interface."""
    parser = argparse.ArgumentParser(description="Generate PDF files from resume data")
    parser.add_argument(
        "--data-dir",
        type=str,
        help=(
            "Path to data directory containing input/output folders "
            "(default: use config)"
        ),
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help=(
            "⚠️ TRIGGERS SUBPROCESS - Open each generated PDF with the system viewer. "
            "Executes: xdg-open (Linux), open (macOS), or start (Windows)."
        ),
    )
    args = parser.parse_args()

    generate_pdf(data_dir=args.data_dir, open_after=args.open)


if __name__ == "__main__":
    main()
