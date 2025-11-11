"""Provide rich result objects for simple-resume operations.

This module provides rich result objects that contain both data and useful methods,
similar to how `requests.Response` objects work.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess  # nosec B404
import sys
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Bandit: subprocess usage is limited to launching trusted viewer commands.
from .exceptions import FileSystemError

# File size formatting constants
BYTES_PER_UNIT = 1024


@dataclass(frozen=True)
class GenerationMetadata:
    """Define metadata about a generation operation."""

    format_type: str
    template_name: str
    generation_time: float
    file_size: int
    resume_name: str
    palette_info: dict[str, Any] | None = None
    page_count: int | None = None


class GenerationResult:
    """Define a rich result object with both data and methods.

    Similar to `requests.Response`, this object provides both access to data
    and useful methods for working with the generated result.
    """

    def __init__(
        self,
        output_path: Path,
        format_type: str,
        metadata: GenerationMetadata | None = None,
    ) -> None:
        """Initialize the generation result."""
        self.output_path = output_path
        self.format_type = format_type.lower()
        self.metadata = metadata or GenerationMetadata(
            format_type=format_type,
            template_name="unknown",
            generation_time=0.0,
            file_size=0,
            resume_name="unknown",
        )

    @property
    def size(self) -> int:
        """Return the file size in bytes."""
        try:
            return self.output_path.stat().st_size
        except OSError:
            return 0

    @property
    def size_human(self) -> str:
        """Return the file size in human-readable format."""
        size = float(self.size)
        for unit in ["B", "KB", "MB", "GB"]:
            if size < BYTES_PER_UNIT:
                return f"{size:.1f} {unit}"
            size /= BYTES_PER_UNIT
        return f"{size:.1f} TB"

    @property
    def exists(self) -> bool:
        """Check if the generated file exists."""
        return self.output_path.exists() and self.output_path.is_file()

    @property
    def name(self) -> str:
        """Get the filename without path."""
        return self.output_path.name

    @property
    def stem(self) -> str:
        """Get the filename without extension."""
        return self.output_path.stem

    @property
    def suffix(self) -> str:
        """Get the file extension."""
        return self.output_path.suffix

    def open(self) -> bool:
        """Open the generated file with the system default application."""
        if not self.exists:
            raise FileSystemError(
                f"Cannot open file that doesn't exist: {self.output_path}",
                path=str(self.output_path),
                operation="open",
            )

        try:
            if self.format_type == "pdf":
                return self._open_pdf()
            elif self.format_type == "html":
                return self._open_html()
            else:
                return self._open_generic()
        except Exception as exc:
            raise FileSystemError(
                f"Failed to open {self.output_path}: {exc}",
                path=str(self.output_path),
                operation="open",
            ) from exc

    def _open_pdf(self) -> bool:
        """Open a PDF file with the system PDF viewer."""
        try:
            if sys.platform.startswith("darwin"):
                opener = shutil.which("open") or "open"
                # Bandit: command is limited to macOS open with the generated file path.
                subprocess.Popen(  # noqa: S603  # nosec B603
                    [opener, str(self.output_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif os.name == "nt":
                # Bandit: Windows open uses os.startfile on a file created by this tool.
                os.startfile(str(self.output_path))  # type: ignore[attr-defined]  # noqa: S606  # nosec B606
            else:
                opener = shutil.which("xdg-open")
                if opener is None:
                    print(
                        "Tip: install xdg-utils to open PDFs automatically.",
                        file=sys.stderr,
                    )
                    return False
                # Bandit: linux desktop opener is resolved via shutil.which and
                # invoked with the generated resume path.
                subprocess.Popen(  # noqa: S603  # nosec B603
                    [opener, str(self.output_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            return True
        except Exception:
            return False

    def _open_html(self) -> bool:
        """Open an HTML file with a browser."""
        browsers = ("firefox", "chromium", "google-chrome", "safari")
        for browser in browsers:
            if shutil.which(browser):
                try:
                    # Bandit: browsers are selected from an allowlist and
                    # invoked with the generated file.
                    subprocess.Popen(  # noqa: S603  # nosec B603
                        [browser, str(self.output_path)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return True
                except Exception as e:
                    logging.debug("Failed to open file with browser %s: %s", browser, e)
                    continue
        return False

    def _open_generic(self) -> bool:
        """Open any file with the system default application."""
        try:
            if sys.platform.startswith("darwin"):
                # Bandit: generic opener on macOS uses the system open command
                # with the resume path.
                subprocess.run(  # noqa: S603  # nosec B603
                    ["/usr/bin/open", str(self.output_path)],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif os.name == "nt":
                # Bandit: os.startfile opens the generated artifact via the OS
                # shell.
                os.startfile(str(self.output_path))  # type: ignore[attr-defined]  # noqa: S606  # nosec B606
            else:
                opener = shutil.which("xdg-open")
                if opener is None:
                    return False
                # Bandit: linux opener is selected via which and called with the
                # single output path.
                subprocess.run(  # noqa: S603  # nosec B603
                    [opener, str(self.output_path)],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            return True
        except Exception:
            return False

    def delete(self) -> bool:
        """Delete the generated file."""
        try:
            if self.exists:
                self.output_path.unlink()
                return True
            return False
        except OSError:
            return False

    def copy_to(self, destination: Path | str) -> Path:
        """Copy the file to a new location."""
        dest_path = Path(destination)
        if dest_path.is_dir():
            dest_path = dest_path / self.name

        try:
            shutil.copy2(self.output_path, dest_path)
            return dest_path
        except OSError as exc:
            raise FileSystemError(
                f"Failed to copy {self.output_path} to {dest_path}: {exc}",
                path=str(self.output_path),
                operation="copy",
            ) from exc

    def move_to(self, destination: Path | str) -> Path:
        """Move the file to a new location."""
        dest_path = Path(destination)
        if dest_path.is_dir():
            dest_path = dest_path / self.name

        try:
            shutil.move(str(self.output_path), str(dest_path))
            return dest_path
        except OSError as exc:
            raise FileSystemError(
                f"Failed to move {self.output_path} to {dest_path}: {exc}",
                path=str(self.output_path),
                operation="move",
            ) from exc

    def read_text(self, encoding: str = "utf-8") -> str:
        """Read the file content as text."""
        try:
            return self.output_path.read_text(encoding=encoding)
        except OSError as exc:
            raise FileSystemError(
                f"Failed to read {self.output_path}: {exc}",
                path=str(self.output_path),
                operation="read",
            ) from exc

    def read_bytes(self) -> bytes:
        """Read the file content as bytes."""
        try:
            return self.output_path.read_bytes()
        except OSError as exc:
            raise FileSystemError(
                f"Failed to read {self.output_path}: {exc}",
                path=str(self.output_path),
                operation="read",
            ) from exc

    def __str__(self) -> str:
        """Return a string representation of the generation result."""
        return f"GenerationResult({self.output_path}, format={self.format_type})"

    def __repr__(self) -> str:
        """Return a detailed string representation."""
        return (
            f"GenerationResult(output_path={self.output_path!r}, "
            f"format_type={self.format_type!r}, size={self.size})"
        )

    def __bool__(self) -> bool:
        """Return `True` if the generated file exists."""
        return self.exists


@dataclass(frozen=True)
class BatchGenerationResult:
    """Define the result for batch generation operations."""

    results: dict[str, GenerationResult] = field(default_factory=dict)
    total_time: float = 0.0
    successful: int = 0
    failed: int = 0
    errors: dict[str, Exception] = field(default_factory=dict)

    @property
    def total(self) -> int:
        """Return the total number of attempted generations."""
        return self.successful + self.failed

    @property
    def success_rate(self) -> float:
        """Return the success rate as a percentage."""
        if self.total == 0:
            return 0.0
        return (self.successful / self.total) * 100

    def get_successful(self) -> dict[str, GenerationResult]:
        """Get only successful results."""
        return {name: result for name, result in self.results.items() if result.exists}

    def get_failed(self) -> dict[str, Exception]:
        """Get only failed results."""
        return self.errors.copy()

    def open_all(self) -> None:
        """Open all successful results."""
        for result in self.get_successful().values():
            try:
                result.open()
            except Exception as e:
                # Continue opening other files even if one fails
                logging.warning("Failed to open result %s: %s", result.output_path, e)
                continue

    def delete_all(self) -> int:
        """Delete all successful results. Return the number of deleted files."""
        deleted = 0
        for result in self.get_successful().values():
            if result.delete():
                deleted += 1
        return deleted

    def __str__(self) -> str:
        """Return a string representation of the batch result."""
        return (
            f"BatchGenerationResult(successful={self.successful}, "
            f"failed={self.failed}, success_rate={self.success_rate:.1f}%)"
        )

    def __len__(self) -> int:
        """Return the total number of results."""
        return self.total

    def __iter__(self) -> Iterator[tuple[str, GenerationResult]]:
        """Iterate over successful results."""
        return iter(self.get_successful().items())


__all__ = [
    "GenerationResult",
    "GenerationMetadata",
    "BatchGenerationResult",
]
