"""Provide utilities for loading and hydrating resume content."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .config import FILE_DEFAULT, Paths
from .core.hydration_core import hydrate_resume_structure
from .core.io_utils import candidate_yaml_path, resolve_paths_for_read
from .exceptions import FileSystemError
from .utilities import _read_yaml, normalize_config, render_markdown_content


def _select_resume_name(name: str | os.PathLike[str]) -> str:
    """Normalize resume identifiers by stripping extensions and defaults."""
    if not name:
        return FILE_DEFAULT
    if isinstance(name, (str, os.PathLike)):
        candidate = Path(name)
        suffix = candidate.suffix.lower()
        if suffix in {".yaml", ".yml"}:
            return candidate.stem
        return candidate.name or str(name)
    return str(name)


def load_resume_yaml(
    name: str | os.PathLike[str] = "",
    *,
    paths: Paths | None = None,
) -> tuple[dict[str, Any], str, Paths]:
    """Read a resume YAML file and return the raw payload, filename, and paths."""
    candidate_path: Path | None = None
    if isinstance(name, (str, os.PathLike)):
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
        yaml_content = _read_yaml(candidate_path)
        return yaml_content, candidate_path.name, resolved_paths

    resume_name = _select_resume_name(name)
    resolved_paths = resolve_paths_for_read(paths, overrides, None)
    input_path = resolved_paths.input

    candidates: list[Path] = []
    for ext in ("yaml", "yml"):
        candidates.extend(input_path.glob(f"{resume_name}.{ext}"))
        candidates.extend(input_path.glob(f"{resume_name}.{ext.upper()}"))

    if candidates:
        source_path = candidates[0]
    else:
        source_path = input_path / f"{resume_name}.yaml"

    yaml_content = _read_yaml(source_path)
    return yaml_content, source_path.name, resolved_paths


def hydrate_resume_data(
    source_yaml: dict[str, Any],
    *,
    filename: str = "",
    transform_markdown: bool = True,
) -> dict[str, Any]:
    """Return a normalized copy of resume data with optional Markdown expansion."""
    return hydrate_resume_structure(
        source_yaml,
        filename=filename,
        transform_markdown=transform_markdown,
        normalize_config_fn=normalize_config,
        render_markdown_fn=render_markdown_content,
    )


__all__ = ["hydrate_resume_data", "load_resume_yaml"]
