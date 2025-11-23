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

import subprocess  # nosec B404
import webbrowser
from pathlib import Path
from typing import Any

from simple_resume.core.effects import (
    DeleteFile,
    Effect,
    MakeDirectory,
    OpenBrowser,
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
        if isinstance(effect, WriteFile):
            return self._write_file(effect.path, effect.content, effect.encoding)
        elif isinstance(effect, MakeDirectory):
            return self._make_directory(effect.path, effect.parents)
        elif isinstance(effect, DeleteFile):
            return self._delete_file(effect.path)
        elif isinstance(effect, OpenBrowser):
            return self._open_browser(effect.url)
        elif isinstance(effect, RunCommand):
            return self._run_command(effect.command, effect.cwd)
        else:
            raise ValueError(f"Unknown effect type: {type(effect)}")

    def execute_many(self, effects: list[Effect]) -> list[Any]:
        """Execute multiple effects in sequence.

        Effects are executed in order. If any effect fails, execution stops
        and the exception is propagated.

        Args:
            effects: List of effects to execute

        Returns:
            List of results from each effect execution

        """
        return [self.execute(effect) for effect in effects]

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
