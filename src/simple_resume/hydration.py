"""Utilities for loading and hydrating resume content."""

from __future__ import annotations

import copy
import os
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
from .exceptions import FileSystemError
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
        maybe_path = Path(name)
        if maybe_path.suffix.lower() in {".yaml", ".yml"}:
            candidate_path = maybe_path

    if candidate_path is not None:
        if not candidate_path.exists():
            raise FileSystemError(
                f"Resume file not found: {candidate_path}",
                path=str(candidate_path),
                operation="read",
            )

        if paths is not None:
            resolved_paths = paths
        else:
            if candidate_path.parent.name == "input":
                base_dir = candidate_path.parent.parent
            else:
                base_dir = candidate_path.parent

            resolved = resolve_paths(data_dir=str(base_dir))
            resolved_paths = Paths(
                data=resolved.data,
                input=candidate_path.parent,
                output=resolved.output,
                content=resolved.content,
                templates=resolved.templates,
                static=resolved.static,
            )

        yaml_content = _read_yaml(candidate_path)
        return yaml_content, candidate_path.name, resolved_paths

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

    yaml_content = _read_yaml(source_path)
    return yaml_content, source_path.name, resolved_paths


def hydrate_resume_data(
    source_yaml: dict[str, Any],
    *,
    filename: str = "",
    transform_markdown: bool = True,
) -> dict[str, Any]:
    """Return a normalized copy of resume data with optional Markdown expansion."""
    from .utilities import format_skill_groups  # noqa: PLC0415

    processed_resume = copy.deepcopy(source_yaml)

    config = processed_resume.get("config")
    if isinstance(config, dict):
        normalized_config, palette_meta = normalize_config(config, filename=filename)
        processed_resume["config"] = normalized_config
        if palette_meta:
            meta = dict(processed_resume.get("meta", {}))
            meta["palette"] = palette_meta
            processed_resume["meta"] = meta

    if transform_markdown:
        _transform_from_markdown(processed_resume)

    # Create skill groups for sidebar sections
    processed_resume["expertise_groups"] = format_skill_groups(
        processed_resume.get("expertise")
    )
    processed_resume["programming_groups"] = format_skill_groups(
        processed_resume.get("programming")
    )
    processed_resume["keyskills_groups"] = format_skill_groups(
        processed_resume.get("keyskills")
    )
    processed_resume["certification_groups"] = format_skill_groups(
        processed_resume.get("certification")
    )

    return processed_resume


__all__ = ["hydrate_resume_data", "load_resume_yaml"]
