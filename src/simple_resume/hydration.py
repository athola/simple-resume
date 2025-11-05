"""Utilities for loading and hydrating resume content."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .config import (
    FILE_DEFAULT,
    PATH_DATA,
    PATH_INPUT,
    PATH_OUTPUT,
    Paths,
    resolve_paths,
)
from .utilities import (
    _read_yaml,
    _transform_from_markdown,
    normalize_config,
)


def _resolve_active_paths(paths: Paths | None) -> Paths:
    """Return the configured paths, reproducing legacy defaults."""
    if paths is not None:
        return paths

    base_paths = resolve_paths()
    return Paths(
        data=Path(PATH_DATA),
        input=Path(PATH_INPUT),
        output=Path(PATH_OUTPUT),
        content=base_paths.content,
        templates=base_paths.templates,
        static=base_paths.static,
    )


def _select_resume_name(name: str) -> str:
    """Normalize resume identifiers by stripping extensions and defaults."""
    if not name:
        return FILE_DEFAULT
    parts = name.split(".")
    return parts[0] if parts else name


def load_resume_yaml(
    name: str = "",
    *,
    paths: Paths | None = None,
) -> tuple[dict[str, Any], str, Paths]:
    """Read a resume YAML file and return the raw payload, filename, and paths."""
    resume_name = _select_resume_name(name)
    resolved_paths = _resolve_active_paths(paths)
    input_path = resolved_paths.input

    candidates: list[Path] = []
    for ext in ("yaml", "yml"):
        candidates.extend(input_path.glob(f"{resume_name}.{ext}"))
        candidates.extend(input_path.glob(f"{resume_name}.{ext.upper()}"))

    if candidates:
        source_path = candidates[0]
    else:
        source_path = input_path / f"{resume_name}.yaml"

    data = _read_yaml(source_path)
    return data, source_path.name, resolved_paths


def hydrate_resume_data(
    raw_data: dict[str, Any],
    *,
    filename: str = "",
    transform_markdown: bool = True,
) -> dict[str, Any]:
    """Return a normalized copy of resume data with optional Markdown expansion."""
    from .utilities import format_skill_groups  # noqa: PLC0415

    hydrated = copy.deepcopy(raw_data)

    config = hydrated.get("config")
    if isinstance(config, dict):
        normalized_config, palette_meta = normalize_config(config, filename=filename)
        hydrated["config"] = normalized_config
        if palette_meta:
            meta = dict(hydrated.get("meta", {}))
            meta["palette"] = palette_meta
            hydrated["meta"] = meta

    if transform_markdown:
        _transform_from_markdown(hydrated)

    # Create skill groups for sidebar sections
    hydrated["expertise_groups"] = format_skill_groups(hydrated.get("expertise"))
    hydrated["programming_groups"] = format_skill_groups(hydrated.get("programming"))
    hydrated["keyskills_groups"] = format_skill_groups(hydrated.get("keyskills"))
    hydrated["certification_groups"] = format_skill_groups(
        hydrated.get("certification")
    )

    return hydrated


__all__ = ["hydrate_resume_data", "load_resume_yaml"]
