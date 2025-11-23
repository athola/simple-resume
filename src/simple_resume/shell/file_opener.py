"""File opener for the shell layer.

This module handles platform-specific file opening operations.
All I/O operations for opening files in external applications
are consolidated here, following the functional core / imperative shell pattern.

The core layer should never import this module directly.
"""

from __future__ import annotations

import logging
import shutil
import subprocess  # nosec B404
import sys
import webbrowser
from pathlib import Path

from simple_resume.core.exceptions import FileSystemError


class FileOpener:
    """Platform-aware file opener for generated artifacts.

    This class consolidates all file-opening logic in one place,
    handling PDF, HTML, and generic file types across platforms.
    """

    @staticmethod
    def open_file(path: Path, format_type: str | None = None) -> bool:
        """Open a file using the appropriate system application.

        Args:
            path: Path to the file to open
            format_type: Optional format hint ('pdf', 'html', or None for generic)

        Returns:
            True if file was opened successfully

        Raises:
            FileSystemError: If file doesn't exist or cannot be opened

        """
        if not path.exists():
            raise FileSystemError(
                f"File doesn't exist: {path}",
                path=str(path),
                operation="open",
            )

        if not path.is_file():
            raise FileSystemError(
                f"Path is not a file: {path}",
                path=str(path),
                operation="open",
            )

        # Determine format from extension if not provided
        if format_type is None:
            suffix = path.suffix.lower()
            if suffix == ".pdf":
                format_type = "pdf"
            elif suffix in (".html", ".htm"):
                format_type = "html"

        try:
            if format_type == "pdf":
                return FileOpener._open_pdf(path)
            elif format_type == "html":
                return FileOpener._open_html(path)
            else:
                return FileOpener._open_generic(path)
        except Exception as exc:
            raise FileSystemError(
                f"Failed to open file: {exc}",
                path=str(path),
                operation="open",
            ) from exc

    @staticmethod
    def _validate_path(path: Path) -> str:
        """Validate path for security and return string representation.

        Args:
            path: Path to validate

        Returns:
            String representation of the path

        Raises:
            ValueError: If path contains unsafe characters

        """
        path_str = str(path.resolve() if not path.is_absolute() else path)

        # Check for command injection characters
        unsafe_patterns = ["..", ";", "|", "&", "`", "$", "(", ")"]
        if any(pattern in path_str for pattern in unsafe_patterns):
            raise ValueError(f"Unsafe path detected: {path_str}")

        return path_str

    # PDF opening methods

    @staticmethod
    def _open_pdf(path: Path) -> bool:
        """Open PDF file using system's PDF viewer."""
        if sys.platform == "darwin":
            return FileOpener._open_pdf_macos(path)
        elif sys.platform.startswith("linux"):
            return FileOpener._open_pdf_linux(path)
        else:
            return FileOpener._open_pdf_windows(path)

    @staticmethod
    def _open_pdf_macos(path: Path) -> bool:
        """Open PDF file on macOS."""
        path_str = FileOpener._validate_path(path)
        subprocess.run(  # noqa: S603  # nosec B603
            ["/usr/bin/open", path_str],
            check=True,
            capture_output=True,
        )
        return True

    @staticmethod
    def _open_pdf_linux(path: Path) -> bool:
        """Open PDF file on Linux."""
        path_str = FileOpener._validate_path(path)

        # Try xdg-open first
        xdg_open = shutil.which("xdg-open")
        if xdg_open:
            result = subprocess.run(  # noqa: S603  # nosec B603
                [xdg_open, path_str],
                check=False,
                capture_output=True,
            )
            if result.returncode == 0:
                return True

        # Fallback to common PDF viewers
        for viewer in ["evince", "okular", "acroread"]:
            viewer_path = shutil.which(viewer)
            if viewer_path:
                try:
                    subprocess.run(  # noqa: S603  # nosec B603
                        [viewer_path, path_str],
                        check=True,
                        capture_output=True,
                    )
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue

        return False

    @staticmethod
    def _open_pdf_windows(path: Path) -> bool:
        """Open PDF file on Windows."""
        path_str = FileOpener._validate_path(path)
        cmd_path = shutil.which("cmd") or "cmd"

        subprocess.run(  # noqa: S603  # nosec B603
            [cmd_path, "/c", "start", "", path_str],
            check=True,
            shell=False,
            capture_output=True,
        )
        return True

    # HTML opening methods

    @staticmethod
    def _open_html(path: Path) -> bool:
        """Open HTML file using system's web browser."""
        path_str = FileOpener._validate_path(path)

        # Try webbrowser module first (cross-platform)
        try:
            if webbrowser.open(f"file://{path_str}"):
                return True
        except Exception:  # noqa: BLE001
            logging.debug("Failed to open browser with webbrowser module")
            pass

        # Platform-specific fallbacks
        if sys.platform == "darwin":
            return FileOpener._open_html_macos(path)
        elif sys.platform.startswith("linux"):
            return FileOpener._open_html_linux(path)
        else:
            return FileOpener._open_html_windows(path)

    @staticmethod
    def _open_html_macos(path: Path) -> bool:
        """Open HTML file on macOS."""
        path_str = FileOpener._validate_path(path)
        result = subprocess.run(  # noqa: S603  # nosec B603
            ["/usr/bin/open", path_str],
            check=False,
            capture_output=True,
        )
        return result.returncode == 0

    @staticmethod
    def _open_html_linux(path: Path) -> bool:
        """Open HTML file on Linux."""
        path_str = FileOpener._validate_path(path)

        xdg_open = shutil.which("xdg-open")
        if xdg_open:
            result = subprocess.run(  # noqa: S603  # nosec B603
                [xdg_open, path_str],
                check=False,
                capture_output=True,
            )
            return result.returncode == 0

        return False

    @staticmethod
    def _open_html_windows(path: Path) -> bool:
        """Open HTML file on Windows."""
        path_str = FileOpener._validate_path(path)
        cmd_path = shutil.which("cmd") or "cmd"

        result = subprocess.run(  # noqa: S603  # nosec B603
            [cmd_path, "/c", "start", "", path_str],
            check=False,
            shell=False,
            capture_output=True,
        )
        return result.returncode == 0

    # Generic file opening

    @staticmethod
    def _open_generic(path: Path) -> bool:
        """Open file using system's default application."""
        if sys.platform == "darwin":
            return FileOpener._open_generic_macos(path)
        elif sys.platform.startswith("linux"):
            return FileOpener._open_generic_linux(path)
        else:
            return FileOpener._open_generic_windows(path)

    @staticmethod
    def _open_generic_macos(path: Path) -> bool:
        """Open file on macOS."""
        path_str = FileOpener._validate_path(path)
        result = subprocess.run(  # noqa: S603  # nosec B603
            ["/usr/bin/open", path_str],
            check=False,
            capture_output=True,
        )
        return result.returncode == 0

    @staticmethod
    def _open_generic_linux(path: Path) -> bool:
        """Open file on Linux."""
        path_str = FileOpener._validate_path(path)

        xdg_open = shutil.which("xdg-open")
        if xdg_open is None:
            return False

        try:
            result = subprocess.run(  # noqa: S603  # nosec B603
                [xdg_open, path_str],
                check=False,
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False

    @staticmethod
    def _open_generic_windows(path: Path) -> bool:
        """Open file on Windows."""
        path_str = FileOpener._validate_path(path)
        cmd_path = shutil.which("cmd") or "cmd"

        result = subprocess.run(  # noqa: S603  # nosec B603
            [cmd_path, "/c", "start", "", path_str],
            check=False,
            shell=False,
            capture_output=True,
        )
        return result.returncode == 0


def open_file(path: Path, format_type: str | None = None) -> bool:
    """Open a file using the system default application.

    Args:
        path: Path to the file to open
        format_type: Optional format hint ('pdf', 'html', or None for generic)

    Returns:
        True if file was opened successfully

    """
    return FileOpener.open_file(path, format_type)


__all__ = ["FileOpener", "open_file"]
