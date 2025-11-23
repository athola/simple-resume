"""Consolidated path and file handling utilities.

This module provides centralized path handling following the Path-first principle:
- Accept str | Path at API boundaries for flexibility
- Normalize to Path immediately after receiving input
- Use Path objects internally throughout the codebase
- Convert to str only when required by external APIs
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from oyaml import safe_load

from simple_resume.core.paths import Paths
from simple_resume.shell.config import FILE_DEFAULT, resolve_paths


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


def normalize_resume_name(name: str | os.PathLike[str]) -> str:
    """Normalize resume identifiers by stripping extensions and defaults.

    Args:
        name: Resume identifier (filename, stem, or path)

    Returns:
        Normalized resume name without extension

    """
    if not name:
        return FILE_DEFAULT
    if isinstance(name, (str, os.PathLike)):
        candidate = Path(name)
        suffix = candidate.suffix.lower()
        if suffix in {".yaml", ".yml"}:
            return candidate.stem
        return candidate.name or str(name)
    return str(name)


def find_resume_file(
    resume_name: str, input_path: Path, *, include_uppercase: bool = True
) -> Path:
    """Find a resume file in the input directory by name.

    Args:
        resume_name: Name of the resume (without extension)
        input_path: Directory to search for resume files
        include_uppercase: Whether to search for uppercase extensions

    Returns:
        Path to the found resume file

    """
    candidates: list[Path] = []
    extensions = ["yaml", "yml"]

    # Search for files with both lowercase and uppercase extensions
    for ext in extensions:
        candidates.extend(input_path.glob(f"{resume_name}.{ext}"))
        if include_uppercase:
            candidates.extend(input_path.glob(f"{resume_name}.{ext.upper()}"))

    if candidates:
        return candidates[0]

    # Fallback to default yaml file
    return input_path / f"{resume_name}.yaml"


def read_yaml_file(path: str | Path) -> dict[str, Any]:
    """Read and parse a YAML file.

    Args:
        path: Path to the YAML file

    Returns:
        Parsed YAML content as dictionary

    Raises:
        ValueError: If YAML content is not a dictionary
        FileNotFoundError: If file doesn't exist

    """
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")

    with open(path_obj, encoding="utf-8") as file:
        content = safe_load(file)

    if content is None:
        return {}

    if not isinstance(content, dict):
        raise ValueError(
            f"YAML file must contain a dictionary at the root level, "
            f"but found {type(content).__name__}: {path_obj}"
        )

    return content


def ensure_directory_exists(path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists

    Returns:
        The same path for convenience

    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_output_path(base_dir: Path, filename: str, extension: str = ".pdf") -> Path:
    """Resolve an output file path with proper extension.

    Args:
        base_dir: Base output directory
        filename: Base filename (without extension)
        extension: Desired file extension

    Returns:
        Resolved output file path

    """
    if not filename.endswith(extension):
        filename = f"{filename}{extension}"

    ensure_directory_exists(base_dir)
    return base_dir / filename


__all__ = [
    "candidate_yaml_path",
    "resolve_paths_for_read",
    "normalize_resume_name",
    "find_resume_file",
    "read_yaml_file",
    "ensure_directory_exists",
    "resolve_output_path",
]
