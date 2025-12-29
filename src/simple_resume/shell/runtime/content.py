"""Imperative helpers for loading and hydrating resume content."""

from __future__ import annotations

import copy
import logging
from pathlib import Path
from typing import Any

from simple_resume.core.config import normalize_config
from simple_resume.core.exceptions import FileSystemError
from simple_resume.core.hydration import hydrate_resume_structure
from simple_resume.core.markdown import render_markdown_content
from simple_resume.core.paths import Paths
from simple_resume.shell.io_utils import (
    candidate_yaml_path,
    find_resume_file,
    normalize_resume_name,
    read_yaml_file,
    resolve_paths_for_read,
)
from simple_resume.shell.palettes.fetch import execute_palette_fetch
from simple_resume.shell.palettes.loader import get_palette_registry
from simple_resume.shell.themes import resolve_theme_in_data

logger = logging.getLogger(__name__)


def _normalize_with_palette(
    config: dict[str, Any],
    filename: str = "",
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Normalize configuration with palette fetching enabled (shell I/O)."""
    # Get registry from shell layer (singleton with I/O)
    registry = get_palette_registry()

    return normalize_config(
        config,
        filename=filename,
        registry=registry,
        palette_fetcher=execute_palette_fetch,
    )


def load_resume_yaml(
    name: str | Path = "",
    *,
    paths: Paths | None = None,
) -> tuple[dict[str, Any], str, Paths]:
    """Read resume YAML content and return payload, filename, and paths."""
    candidate_path: Path | None = None
    if isinstance(name, (str, Path)):
        candidate_path = candidate_yaml_path(name)

    overrides: dict[str, Any] = {}
    if candidate_path is not None:
        if not candidate_path.exists():
            raise FileSystemError(
                f"Resume file not found: {candidate_path}",
                path=str(candidate_path),
                operation="read",
            )
        resolved_paths = resolve_paths_for_read(paths, overrides, candidate_path)
        yaml_content = read_yaml_file(candidate_path)
        return yaml_content, candidate_path.name, resolved_paths

    resume_name = normalize_resume_name(name)
    resolved_paths = resolve_paths_for_read(paths, overrides, None)
    input_path = resolved_paths.input

    source_path = find_resume_file(resume_name, input_path)
    yaml_content = read_yaml_file(source_path)
    return yaml_content, source_path.name, resolved_paths


def hydrate_resume_data(
    source_yaml: dict[str, Any],
    *,
    filename: str = "",
    transform_markdown: bool = True,
) -> dict[str, Any]:
    """Return normalized resume data using pure core helpers.

    If the source YAML contains a 'theme' key, the theme is loaded
    and merged with the config before processing.
    """
    # Resolve theme references before hydration
    resolved_data = resolve_theme_in_data(source_yaml)

    return hydrate_resume_structure(
        resolved_data,
        filename=filename,
        transform_markdown=transform_markdown,
        normalize_config_fn=_normalize_with_palette,
        render_markdown_fn=render_markdown_content,
    )


def get_content(
    name: str = "",
    *,
    paths: Paths | None = None,
    transform_markdown: bool = True,
) -> dict[str, Any]:
    """Load, hydrate, and optionally transform a resume payload.

    Theme references are automatically resolved before processing.
    """
    raw_data, filename, _ = load_resume_yaml(name, paths=paths)

    # Resolve theme references before hydration
    resolved_data = resolve_theme_in_data(raw_data)

    return hydrate_resume_structure(
        resolved_data,
        filename=filename,
        transform_markdown=transform_markdown,
        normalize_config_fn=_normalize_with_palette,
        render_markdown_fn=render_markdown_content,
    )


def load_palette_from_file(palette_file: str | Path) -> dict[str, Any]:
    """Load palette configuration from a YAML file."""
    path = Path(palette_file)
    if not path.exists():
        raise FileNotFoundError(f"Palette file not found: {path}")
    if path.suffix.lower() not in {".yaml", ".yml"}:
        raise ValueError("Palette file must be a YAML file")

    # Check for missing trailing newline (common YAML parsing issue)
    with path.open("rb") as f:
        f.seek(0, 2)  # Seek to end
        if f.tell() > 0:  # File is not empty
            f.seek(-1, 2)  # Seek to last byte
            last_byte = f.read(1)
            if last_byte != b"\n":
                logger.warning(
                    "Palette file '%s' is missing a trailing newline. "
                    "This may cause YAML parsing issues. "
                    "Consider adding a newline at the end of the file.",
                    path.name,
                )

    content = read_yaml_file(path)
    palette_data: Any = content.get("palette", content)

    if isinstance(palette_data, dict) and "config" in palette_data:
        config_block = palette_data["config"]
        if isinstance(config_block, dict):
            nested_palette = config_block.get("palette")
            if isinstance(nested_palette, dict):
                palette_data = nested_palette
            else:
                palette_data = config_block

    if not isinstance(palette_data, dict):
        raise ValueError("Palette configuration must be a dictionary")

    return {"palette": copy.deepcopy(palette_data)}


def apply_external_palette(
    config: dict[str, Any],
    palette_file: str | Path,
) -> dict[str, Any]:
    """Return a new configuration with palette data applied."""
    palette_payload = load_palette_from_file(palette_file)
    updated = copy.deepcopy(config)
    updated["palette"] = palette_payload["palette"]
    return updated


__all__ = [
    "apply_external_palette",
    "get_content",
    "hydrate_resume_data",
    "load_palette_from_file",
    "load_resume_yaml",
]
