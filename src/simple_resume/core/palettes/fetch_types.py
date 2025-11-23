"""Palette request and response types for pure core operations.

These types allow core functions to describe what network operations
are needed without actually performing them, keeping the core pure.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PaletteFetchRequest:
    """Request to fetch palette from remote source.

    This describes a network operation that should be executed by the shell layer.
    The core layer creates these requests but never executes them directly.
    """

    source: str  # e.g., "colourlovers"
    keywords: list[str] | None = None
    num_results: int = 1
    order_by: str = "score"


@dataclass(frozen=True)
class PaletteResolution:
    """Result of palette resolution - either colors or fetch request.

    This represents the result of pure palette resolution logic.
    It either contains resolved colors (for local sources) or a
    fetch request (for remote sources) that the shell should execute.
    """

    colors: list[str] | None = None
    metadata: dict[str, Any] | None = None
    fetch_request: PaletteFetchRequest | None = None

    @property
    def needs_fetch(self) -> bool:
        """Check if this resolution requires network fetching."""
        return self.fetch_request is not None

    @property
    def has_colors(self) -> bool:
        """Check if this resolution already contains colors."""
        return self.colors is not None and len(self.colors) > 0


__all__ = [
    "PaletteFetchRequest",
    "PaletteResolution",
]
