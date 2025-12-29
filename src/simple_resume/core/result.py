"""Pure result objects for simple-resume operations.

This module contains immutable data classes that describe generation results.
These are pure data structures with NO I/O operations - all file operations
should be performed by the shell layer.

Following the functional core / imperative shell pattern:
- Core: Describes what was generated (this module)
- Shell: Performs I/O operations on the results (shell/file_opener.py)
"""

from __future__ import annotations

import os
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import PosixPath, PurePath
from typing import Any


@dataclass(frozen=True)
class GenerationMetadata:
    """Metadata describing a generation operation (pure data)."""

    format_type: str
    template_name: str
    generation_time: float
    file_size: int
    resume_name: str
    palette_info: dict[str, Any] | None = None
    page_count: int | None = None


@dataclass(frozen=True)
class GenerationResult:
    """Pure generation result - describes the artifact location.

    This is a pure data class that only holds information about a generated file.
    It does NOT perform any I/O operations. For file operations like opening,
    deleting, or reading files, use the shell layer (shell/file_opener.py).

    Attributes:
        output_path: Path where the file was generated
        format_type: Type of the generated file ('pdf', 'html', etc.)
        metadata: Optional metadata about the generation process

    """

    output_path: Any
    _normalized_path: PosixPath = field(init=False, repr=False, compare=False)
    format_type: str
    metadata: GenerationMetadata | None = None

    def __post_init__(self) -> None:
        """Initialize the GenerationResult after dataclass creation."""
        original_path = self.output_path
        try:
            if isinstance(original_path, PurePath):
                normalized_path = PosixPath(os.fspath(original_path))
            else:
                # Force POSIX concrete path to avoid WindowsPath instantiation
                # when platform is mocked during CI strategy tests.
                normalized_path = PosixPath(os.fspath(original_path))
        except Exception:
            # Final safety net: force a POSIX path from string.
            normalized_path = PosixPath(str(original_path))

        object.__setattr__(self, "_normalized_path", normalized_path)

        # Normalize format_type to lowercase
        normalized_format = self.format_type.lower()
        object.__setattr__(self, "format_type", normalized_format)

        # Create default metadata if none provided
        if self.metadata is None:
            default_metadata = GenerationMetadata(
                format_type=normalized_format,
                template_name="unknown",
                generation_time=time.time(),
                file_size=0,
                resume_name="unknown",
                palette_info=None,
                page_count=None,
            )
            object.__setattr__(self, "metadata", default_metadata)

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        """Return a detailed string representation for debugging."""
        return (
            f"GenerationResult(output_path={self.output_path}, "
            f"format_type={self.format_type})"
        )

    def __str__(self) -> str:
        """Return a string representation of the GenerationResult."""
        return f"GenerationResult(format={self.format_type}, path={self.output_path})"

    @property
    def name(self) -> str:
        """Return the filename of the output file."""
        return self._normalized_path.name

    @property
    def stem(self) -> str:
        """Return the stem (filename without extension) of the output file."""
        return self._normalized_path.stem

    @property
    def suffix(self) -> str:
        """Return the suffix (extension) of the output file."""
        return self._normalized_path.suffix

    @property
    def exists(self) -> bool:
        """Check if the output file exists and is a file (not a directory).

        Note: This is a read-only property that checks file existence.
        It's acceptable in core because it's a pure query with no side effects.
        """
        return self._normalized_path.exists() and self._normalized_path.is_file()

    @property
    def size(self) -> int:
        """Return file size in bytes (0 if file doesn't exist).

        Note: This is a read-only property that queries file metadata.
        It's acceptable in core because it's a pure query with no side effects.
        """
        try:
            return self._normalized_path.stat().st_size if self.exists else 0
        except OSError:
            return 0

    @property
    def size_human(self) -> str:
        """Return file size in human-readable format."""
        size = self.size
        KB_FACTOR = 1024
        MB_FACTOR = 1024 * 1024
        GB_FACTOR = 1024 * 1024 * 1024
        if size < KB_FACTOR:
            return f"{size} B"
        elif size < MB_FACTOR:
            return f"{size / KB_FACTOR:.1f} KB"
        elif size < GB_FACTOR:
            return f"{size / MB_FACTOR:.1f} MB"
        else:
            return f"{size / GB_FACTOR:.1f} GB"

    def __bool__(self) -> bool:
        """Return True if the output file exists."""
        return self.exists


@dataclass(frozen=True)
class BatchGenerationResult:
    """Pure batch result with aggregate reporting information.

    This is a pure data class that holds multiple GenerationResults.
    It does NOT perform any I/O operations directly.
    """

    results: dict[str, GenerationResult] = field(default_factory=dict)
    resume_name: str | None = None
    formats: list[str] | None = None
    total_time: float = 0.0
    successful: int = 0
    failed: int = 0
    errors: dict[str, Exception] = field(default_factory=dict)

    @property
    def total(self) -> int:
        """Return total number of operations."""
        return self.successful + self.failed

    @property
    def success_rate(self) -> float:
        """Return success rate as a percentage."""
        total = self.total
        if total == 0:
            return 0.0
        return (self.successful / total) * 100.0

    def __iter__(self) -> Iterator[GenerationResult]:
        """Return an iterator over the results."""
        if self.results is None:
            return iter([])
        return iter(self.results.values())

    def __len__(self) -> int:
        """Return the number of results."""
        return len(self.results) if self.results is not None else 0

    def __getitem__(self, key: str) -> GenerationResult:
        """Return the result with the given key."""
        if self.results is None:
            raise KeyError(f"No results available - key '{key}' not found")
        return self.results[key]

    def __contains__(self, key: str) -> bool:
        """Check if a result with the given key exists."""
        return self.results is not None and key in self.results

    def get(
        self, key: str, default: GenerationResult | None = None
    ) -> GenerationResult | None:
        """Get a result by key, returning default if not found."""
        if self.results is None:
            return default
        return self.results.get(key, default)

    def get_successful(self) -> list[GenerationResult]:
        """Return the list of successful results."""
        return list(self.results.values()) if self.results is not None else []

    def get_failed(self) -> dict[str, Exception]:
        """Return the dictionary of failed results."""
        return self.errors.copy() if self.errors is not None else {}


__all__ = [
    "GenerationMetadata",
    "GenerationResult",
    "BatchGenerationResult",
]
