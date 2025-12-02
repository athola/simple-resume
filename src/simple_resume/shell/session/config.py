"""Session configuration for simple-resume operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from simple_resume.core.constants import OutputFormat
from simple_resume.core.exceptions import ConfigurationError
from simple_resume.core.paths import Paths


@dataclass
class SessionConfig:
    """Configuration for a `ResumeSession`."""

    paths: Paths | None = None
    default_template: str | None = None
    default_palette: str | None = None
    default_format: OutputFormat | str = OutputFormat.PDF
    auto_open: bool = False
    preview_mode: bool = False
    output_dir: Path | None = None
    # Additional session-wide settings
    session_metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Normalize enum-backed fields."""
        try:
            self.default_format = OutputFormat.normalize(self.default_format)
        except (ValueError, TypeError) as exc:
            raise ConfigurationError(
                f"Invalid default format: {self.default_format}"
            ) from exc
