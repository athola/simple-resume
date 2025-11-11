"""Helpers for resolving resume file paths."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ..config import Paths, resolve_paths


def candidate_yaml_path(name: str | os.PathLike[str]) -> Path | None:
    """Return a Path if ``name`` resembles a YAML file, otherwise ``None``."""
    if isinstance(name, (str, os.PathLike)):
        maybe_path = Path(name)
        if maybe_path.suffix.lower() in {".yaml", ".yml"}:
            return maybe_path
    return None


def resolve_paths_for_read(
    supplied_paths: Paths | None,
    overrides: dict[str, Any],
    candidate: Path | None,
) -> Paths:
    """Resolve path configuration for read operations."""
    if supplied_paths is not None:
        return supplied_paths

    if overrides:
        return resolve_paths(**overrides)

    if candidate is not None:
        if candidate.parent.name == "input":
            base_dir = candidate.parent.parent
        else:
            base_dir = candidate.parent

        base_paths = resolve_paths(data_dir=base_dir)
        return Paths(
            data=base_paths.data,
            input=candidate.parent,
            output=base_paths.output,
            content=base_paths.content,
            templates=base_paths.templates,
            static=base_paths.static,
        )

    return resolve_paths(**overrides)


__all__ = ["candidate_yaml_path", "resolve_paths_for_read"]
