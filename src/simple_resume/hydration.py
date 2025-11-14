"""Provide utilities for loading and hydrating resume content."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .config import Paths
from .core.hydration_core import hydrate_resume_structure
from .exceptions import FileSystemError
from .utilities import normalize_config, render_markdown_content
from .utils.io import (
    candidate_yaml_path,
    find_resume_file,
    normalize_resume_name,
    read_yaml_file,
    resolve_paths_for_read,
)


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
    """Return a normalized copy of resume data with optional Markdown expansion."""
    return hydrate_resume_structure(
        source_yaml,
        filename=filename,
        transform_markdown=transform_markdown,
        normalize_config_fn=normalize_config,
        render_markdown_fn=render_markdown_content,
    )


__all__ = ["hydrate_resume_data", "load_resume_yaml"]
