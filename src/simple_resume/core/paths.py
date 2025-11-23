"""Core filesystem path dataclasses used across the project."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Paths:
    """Resolved filesystem locations for resume data and assets."""

    data: Path
    input: Path
    output: Path
    content: Path
    templates: Path
    static: Path


__all__ = ["Paths"]
