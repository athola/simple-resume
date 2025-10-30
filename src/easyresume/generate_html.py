"""Generate standalone HTML resumes."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess  # nosec B404
import sys
from pathlib import Path

from . import config
from .rendering import render_resume_html

MIN_FILENAME_PARTS = 2
DEFAULT_BROWSERS = ("firefox", "chromium")
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


def _discover_yaml_inputs(input_path: Path) -> list[Path]:
    try:
        entries = list(input_path.iterdir())
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Input directory not found: {input_path}. "
            "Create the directory and add .yaml files."
        ) from exc

    yaml_files: list[Path] = []
    for entry in entries:
        if not entry.is_file():
            continue
        parts = entry.name.split(".")
        if len(parts) >= MIN_FILENAME_PARTS and parts[-1].lower() in {"yaml", "yml"}:
            yaml_files.append(entry)
    return yaml_files


def _browser_command(browser: str | None) -> list[str] | None:
    if browser is None:
        for candidate in DEFAULT_BROWSERS:
            if shutil.which(candidate):
                return [candidate]
        return None
    if shutil.which(browser):
        return [browser]
    return None


def _open_in_browser(path: Path, browser: str | None) -> None:
    command = _browser_command(browser)
    if command is None:
        print(
            "Tip: install Firefox or Chromium to preview HTML resumes automatically.",
            file=sys.stderr,
        )
        return

    try:
        subprocess.Popen(  # noqa: S603  # nosec B603
            [*command, str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )  # noqa: S603
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: could not launch {command[0]}: {exc}", file=sys.stderr)


def _inject_base_href(html: str, base_path: Path) -> str:
    base_uri = base_path.resolve().as_uri().rstrip("/") + "/"
    base_tag = f'<base href="{base_uri}">'
    if "<head>" in html:
        return html.replace("<head>", f"<head>\n  {base_tag}", 1)
    return f"{base_tag}\n{html}"


def generate_html(
    data_dir: str | os.PathLike[str] | None = None,
    *,
    open_after: bool = False,
    browser: str | None = None,
    paths: config.Paths | None = None,
    **path_overrides: str | os.PathLike[str],
) -> None:
    """Render resumes to HTML files.

    Args:
        data_dir: Optional path to the directory containing resume inputs.
        open_after: When True, open each generated HTML file in a browser.
        browser: Optional explicit browser command, e.g., "firefox".
        paths: Pre-resolved config paths. Overrides are ignored when provided.

    Keyword Args:
        path_overrides: Additional directory overrides; supports the keys
            ``content_dir``, ``templates_dir``, and ``static_dir``.
        content_dir: Optional override for the content directory.
        templates_dir: Optional override for the templates directory.
        static_dir: Optional override for the static assets directory.

    """
    unexpected_keys = set(path_overrides) - _ALLOWED_PATH_OVERRIDES
    if unexpected_keys:
        joined = ", ".join(sorted(unexpected_keys))
        raise TypeError(f"Unsupported path override(s): {joined}")

    overrides = {key: path_overrides.get(key) for key in _ALLOWED_PATH_OVERRIDES}
    resolved_paths = _resolve_paths(data_dir, paths, overrides)
    input_path = resolved_paths.input
    output_path = resolved_paths.output
    output_path.mkdir(parents=True, exist_ok=True)

    yaml_files = _discover_yaml_inputs(input_path)
    if not yaml_files:
        raise FileNotFoundError(
            f"No YAML files found in {input_path}. "
            "Add at least one .yaml or .yml file to render HTML resumes."
        )

    for source in yaml_files:
        name = source.stem
        output_file = output_path / f"{name}.html"

        try:
            html, base_url, _ = render_resume_html(
                name, preview=True, paths=resolved_paths
            )
            html_with_base = _inject_base_href(html, Path(base_url))
            output_file.write_text(html_with_base, encoding="utf-8")
            print(f"✓ Rendered HTML: {output_file}")
            if open_after:
                _open_in_browser(output_file, browser)
        except Exception as exc:  # noqa: BLE001
            print(f"✗ Failed to render {name}.html: {exc}", file=sys.stderr)


def main() -> None:
    """CLI entry point for HTML generation."""
    parser = argparse.ArgumentParser(description="Generate HTML resumes.")
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
            "Open each generated HTML file in a browser "
            "(prefers Firefox, fallback to Chromium)."
        ),
    )
    parser.add_argument(
        "--browser",
        type=str,
        help=(
            "Explicit browser command to launch when using --open "
            "(e.g., firefox, chromium)."
        ),
    )
    args = parser.parse_args()

    generate_html(data_dir=args.data_dir, open_after=args.open, browser=args.browser)


if __name__ == "__main__":
    main()
