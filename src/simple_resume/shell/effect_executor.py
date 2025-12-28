"""Effect executor for the shell layer.

The EffectExecutor performs actual I/O operations
described by Effect objects.
This is the "imperative shell" that executes
side effects created by the "functional core".

Usage:
    executor = EffectExecutor()
    effects = [
        MakeDirectory(path=Path("/tmp/output")),
        WriteFile(path=Path("/tmp/output/file.txt"), content="data"),
    ]
    executor.execute_many(effects)
"""

import shutil
import subprocess  # nosec B404
import webbrowser
from pathlib import Path
from typing import Any, Callable

import weasyprint

from simple_resume.core.effects import (
    CopyFile,
    DeleteFile,
    Effect,
    MakeDirectory,
    OpenBrowser,
    RenderPdf,
    RunCommand,
    WriteFile,
)


class EffectExecutor:
    """Executes effects in the shell layer.

    This class performs actual I/O operations based on Effect descriptions.
    It implements the "imperative shell" pattern, isolating all side effects
    from the functional core.
    """

    def execute(self, effect: Effect) -> Any:
        """Execute a single effect.

        Args:
            effect: The effect to execute

        Returns:
            Result of the operation (type depends on effect)

        Raises:
            ValueError: If effect type is unknown
            Various I/O exceptions: Depending on the operation

        """
        # Dispatch table for effect types
        handlers: dict[type[Effect], Callable[[Any], Any]] = {
            WriteFile: lambda e: self._write_file(e.path, e.content, e.encoding),
            MakeDirectory: lambda e: self._make_directory(e.path, e.parents),
            DeleteFile: lambda e: self._delete_file(e.path),
            CopyFile: lambda e: self._copy_file(e.source, e.destination),
            OpenBrowser: lambda e: self._open_browser(e.url),
            RunCommand: lambda e: self._run_command(e.command, e.cwd),
            RenderPdf: lambda e: self._render_pdf(
                e.html, e.css, e.output_path, e.base_url
            ),
        }

        handler = handlers.get(type(effect))
        if handler is None:
            raise ValueError(f"Unknown effect type: {type(effect)}")
        return handler(effect)

    def execute_many(self, effects: list[Effect]) -> None:
        """Execute multiple effects in sequence.

        Effects are executed in order. If any effect fails, execution stops
        and the exception is propagated.

        Args:
            effects: List of effects to execute

        """
        for effect in effects:
            self.execute(effect)

    def _write_file(self, path: Path, content: str | bytes, encoding: str) -> None:
        """Write content to a file.

        Creates parent directories if they don't exist.
        Overwrites existing file content.

        Args:
            path: Target file path
            content: Content to write (string or bytes)
            encoding: Text encoding (used only for string content)

        """
        # Ensure parent directories exist
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write content based on type
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding=encoding)

    def _make_directory(self, path: Path, parents: bool) -> None:
        """Create a directory.

        Args:
            path: Directory path to create
            parents: If True, create parent directories as needed

        Raises:
            FileNotFoundError: If parents=False and parent directory doesn't exist

        """
        path.mkdir(parents=parents, exist_ok=True)

    def _delete_file(self, path: Path) -> None:
        """Delete a file.

        Does not raise an error if the file doesn't exist.

        Args:
            path: File path to delete

        """
        path.unlink(missing_ok=True)

    def _copy_file(self, source: Path, destination: Path) -> None:
        """Copy a file from source to destination.

        Creates parent directories if they don't exist.

        Args:
            source: Source file path
            destination: Destination file path

        """
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    def _open_browser(self, url: str) -> None:
        """Open a URL in the default web browser.

        Args:
            url: URL to open (http://, https://, or file://)

        """
        webbrowser.open(url)

    def _run_command(
        self, command: list[str], cwd: Path | None
    ) -> subprocess.CompletedProcess[bytes]:
        """Execute a shell command.

        Args:
            command: Command to run as a list of arguments
            cwd: Working directory for command execution

        Returns:
            CompletedProcess object with execution results

        Raises:
            CalledProcessError: If command exits with non-zero status

        """
        # Validate command for security
        if isinstance(command, (list, tuple)):
            unsafe_chars = [";", "|", "&"]
            if any(any(char in str(arg) for char in unsafe_chars) for arg in command):
                raise ValueError("Unsafe command detected")
        elif isinstance(command, str):
            if ";" in command or "|" in command or "&" in command:
                raise ValueError("Unsafe command detected")

        return subprocess.run(command, cwd=cwd, check=True)  # noqa: S603  # nosec B603

    def _render_pdf(
        self, html: str, css: str, output_path: Path, base_url: str | None
    ) -> int | None:
        """Render HTML+CSS to PDF using WeasyPrint."""
        html_doc = weasyprint.HTML(string=html, base_url=base_url)
        css_obj = weasyprint.CSS(string=css)
        document = html_doc.render(stylesheets=[css_obj])
        pdf_bytes = document.write_pdf()
        if not isinstance(pdf_bytes, (bytes, bytearray)):
            # Guard against test doubles returning non-bytes payloads.
            try:
                pdf_bytes = bytes(pdf_bytes)
            except Exception as exc:
                raise RuntimeError(
                    "WeasyPrint returned invalid output (not bytes)"
                ) from exc

        if not pdf_bytes:
            raise RuntimeError("WeasyPrint returned empty PDF output")

        # Ensure parent directories and write file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(pdf_bytes)

        try:
            return len(document.pages)
        except Exception:  # pragma: no cover - defensive
            return None
