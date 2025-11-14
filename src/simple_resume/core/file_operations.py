"""Core file operations for resume management.

Pure functions for file discovery and path operations without external dependencies.
"""

from collections.abc import Generator
from pathlib import Path


def find_yaml_files(input_dir: Path, pattern: str = "*") -> list[Path]:
    """Find YAML files matching the given pattern.

    Args:
        input_dir: Directory to search for YAML files.
        pattern: Glob pattern for matching files.

    Returns:
        List of matching YAML file paths.

    """
    if not input_dir.exists():
        return []

    yaml_files = []

    # Find files matching pattern with .yaml/.yml extension
    for file_path in input_dir.glob(f"{pattern}.yaml"):
        if file_path.is_file():
            yaml_files.append(file_path)
    for file_path in input_dir.glob(f"{pattern}.yml"):
        if file_path.is_file():
            yaml_files.append(file_path)

    return sorted(yaml_files)


def iterate_yaml_files(
    input_dir: Path, pattern: str = "*"
) -> Generator[Path, None, None]:
    """Iterate over YAML files matching the given pattern.

    Args:
        input_dir: Directory to search for YAML files.
        pattern: Glob pattern for matching files.

    Yields:
        YAML file paths.

    """
    yield from find_yaml_files(input_dir, pattern)


def get_resume_name_from_path(file_path: Path) -> str:
    """Extract resume name from file path.

    Args:
        file_path: Path to YAML file.

    Returns:
        Resume name (filename without extension).

    """
    return file_path.stem


__all__ = [
    "find_yaml_files",
    "iterate_yaml_files",
    "get_resume_name_from_path",
]
