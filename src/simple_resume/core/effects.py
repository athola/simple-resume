"""Effect types for the functional core.

Effects represent side effects (I/O operations) that should be
executed by the shell layer. Core functions return effects instead
of performing I/O directly, enabling pure testing.

This implements the "Effect System" pattern where:
- Core functions are pure and return descriptions of side effects (Effects)
- Shell layer executes these effects, performing actual I/O

All effects are immutable (frozen dataclasses) and hashable.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


class Effect(ABC):
    """Base class for all side effects.

    Effects describe I/O operations without performing them.
    They are created by core logic and executed by the shell layer.
    """

    @abstractmethod
    def describe(self) -> str:
        """Return human-readable description of this effect."""
        pass


@dataclass(frozen=True)
class WriteFile(Effect):
    """Effect: Write content to a file.

    Attributes:
        path: Target file path
        content: Content to write (string or bytes)
        encoding: Text encoding (used only for string content)

    """

    path: Path
    content: str | bytes
    encoding: str = "utf-8"

    def describe(self) -> str:
        """Return human-readable description."""
        return f"Write file: {self.path}"


@dataclass(frozen=True)
class MakeDirectory(Effect):
    """Effect: Create a directory.

    Attributes:
        path: Directory path to create
        parents: If True, create parent directories as needed

    """

    path: Path
    parents: bool = True

    def describe(self) -> str:
        """Return human-readable description."""
        return f"Create directory: {self.path}"


@dataclass(frozen=True)
class DeleteFile(Effect):
    """Effect: Delete a file.

    Attributes:
        path: File path to delete

    """

    path: Path

    def describe(self) -> str:
        """Return human-readable description."""
        return f"Delete file: {self.path}"


@dataclass(frozen=True)
class OpenBrowser(Effect):
    """Effect: Open a URL in the default web browser.

    Attributes:
        url: URL to open (can be http://, https://, or file://)

    """

    url: str

    def describe(self) -> str:
        """Return human-readable description."""
        return f"Open browser: {self.url}"


@dataclass(frozen=True)
class RunCommand(Effect):
    """Effect: Execute a shell command.

    Attributes:
        command: Command to run as a list of arguments
        cwd: Working directory for command execution (None for current dir)

    """

    command: list[str]
    cwd: Path | None = None

    def describe(self) -> str:
        """Return human-readable description."""
        command_str = " ".join(self.command)
        return f"Run command: {command_str}"


@dataclass(frozen=True)
class CopyFile(Effect):
    """Effect: Copy a file from source to destination.

    Attributes:
        source: Source file path
        destination: Destination file path

    """

    source: Path
    destination: Path

    def describe(self) -> str:
        """Return human-readable description."""
        return f"Copy file: {self.source} -> {self.destination}"


@dataclass(frozen=True)
class RenderPdf(Effect):
    """Effect: Render HTML+CSS to PDF at the target path.

    The shell layer is responsible for providing the rendering engine
    (e.g., WeasyPrint).
    """

    html: str
    css: str
    output_path: Path
    base_url: str | None = None

    def describe(self) -> str:
        """Return human-readable description."""
        return f"Render PDF to: {self.output_path}"
