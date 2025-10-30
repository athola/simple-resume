"""Create all CVs from the input folder."""

import argparse
import os
import shutil
import subprocess  # nosec B404
import sys
from pathlib import Path

# TODO (long-term): Consider alternatives to WeasyPrint for PDF generation.
# WeasyPrint has rendering quirks (z-index issues, positioned elements) that require
# workarounds like the gradient hack in cv_base.html. Potential alternatives:
# 1. Playwright/Puppeteer: Better CSS support, more predictable rendering
# 2. ReportLab: More control but requires rewriting templates
# 3. wkhtmltopdf: Better compatibility but deprecated
# 4. prince: Commercial but excellent CSS support
# Evaluate based on: rendering quality, CSS support, maintenance burden, cost.
from weasyprint import CSS, HTML

from . import config
from .rendering import render_resume_html

MIN_FILENAME_PARTS = 2  # filename must have at least name and extension
_ALLOWED_PATH_OVERRIDES = {"content_dir", "templates_dir", "static_dir"}


def _resolve_paths(
    data_dir: str | os.PathLike[str] | None,
    paths: config.Paths | None,
    overrides: dict[str, str | os.PathLike[str] | None],
) -> config.Paths:
    if paths is not None and any(value is not None for value in overrides.values()):
        raise ValueError("Provide `paths` or individual overrides, not both.")

    if data_dir is not None:
        candidate = Path(data_dir)
        if not candidate.is_dir():
            raise ValueError(f"Data directory does not exist: {data_dir}")

    if paths is not None:
        return paths

    clean_overrides = {
        key: value for key, value in overrides.items() if value is not None
    }
    return config.resolve_paths(data_dir, **clean_overrides)


def _collect_yaml_inputs(input_path: Path) -> list[Path]:
    yaml_files: list[Path] = []
    for entry in input_path.iterdir():
        if not entry.is_file():
            continue
        parts = entry.name.split(".")
        if len(parts) >= MIN_FILENAME_PARTS and parts[-1].lower() in {"yaml", "yml"}:
            yaml_files.append(entry)
    return yaml_files


def _generate_single_pdf(
    name: str,
    resolved_paths: config.Paths,
    output_dir: Path,
    *,
    open_after: bool,
) -> None:
    output_file = output_dir / f"{name}.pdf"
    try:
        print(f"\n-- Creating {name}.pdf --")

        html, base_url, context = render_resume_html(
            name, preview=False, paths=resolved_paths
        )
        cv_config = context.get("cv_config", {})

        page_width = cv_config.get("page_width", 190)
        page_height = cv_config.get("page_height", 270)

        css = CSS(
            string=f"@page {{size: {page_width}mm {page_height}mm; margin: 0mm;}}"
        )
        HTML(string=html, base_url=base_url).write_pdf(
            str(output_file), stylesheets=[css]
        )
        print(f"✓ Generated: {output_file}")
        if open_after:
            _open_file(str(output_file))
    except Exception as exc:  # noqa: BLE001
        print(f"✗ Failed to generate {name}.pdf: {exc}", file=sys.stderr)


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
    **path_overrides: str | os.PathLike[str],
) -> None:
    """Generate PDFs from YAML files.

    Args:
        data_dir: Optional path to the directory containing resume inputs.
        open_after: When True, open each generated PDF with the system viewer.
        paths: Pre-resolved config paths. Overrides are ignored when provided.

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
    unexpected_keys = set(path_overrides) - _ALLOWED_PATH_OVERRIDES
    if unexpected_keys:
        joined = ", ".join(sorted(unexpected_keys))
        raise TypeError(f"Unsupported path override(s): {joined}")

    overrides = {key: path_overrides.get(key) for key in _ALLOWED_PATH_OVERRIDES}
    resolved_paths = _resolve_paths(data_dir, paths, overrides)

    input_path = resolved_paths.input
    output_path = resolved_paths.output

    # Ensure input and output directories exist.
    input_path.mkdir(parents=True, exist_ok=True)
    output_path.mkdir(parents=True, exist_ok=True)

    # Find all YAML files in the input directory.
    yaml_files = _collect_yaml_inputs(input_path)
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
        )


def main() -> None:
    """Generate PDF files from CV data via command line interface."""
    parser = argparse.ArgumentParser(description="Generate PDF files from CV data")
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
            "Open each generated PDF with the system viewer (uses xdg-open/open/start)."
        ),
    )
    args = parser.parse_args()

    generate_pdf(data_dir=args.data_dir, open_after=args.open)


if __name__ == "__main__":
    main()
