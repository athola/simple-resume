"""LaTeX document data types (pure, immutable)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, Literal, TypedDict


class ParagraphBlock(TypedDict):
    """Define a paragraph text block."""

    kind: Literal["paragraph"]
    text: str


class ListBlock(TypedDict):
    """Define a bullet or enumerated list block."""

    kind: Literal["itemize", "enumerate"]
    items: list[str]


Block = ParagraphBlock | ListBlock


@dataclass(frozen=True)
class LatexEntry:
    """Define a single entry in a resume section."""

    title: str
    subtitle: str | None
    date_range: str | None
    blocks: list[Block]


@dataclass(frozen=True)
class LatexSection:
    """Define a top-level resume section."""

    title: str
    entries: list[LatexEntry]


@dataclass(frozen=True)
class LatexRenderResult:
    """Define the result of a LaTeX render operation."""

    tex: str
    context: dict[str, Any]


@dataclass(frozen=True)
class LatexGenerationContext:
    """Context object for LaTeX PDF generation, grouping related parameters."""

    last_context: ClassVar[LatexGenerationContext | None] = None
    resume_data: dict[str, Any] | None
    processed_data: dict[str, Any]
    output_path: Path
    base_path: Path | str | None = None
    filename: str | None = None
    paths: Any = None
    metadata: Any = None

    def __post_init__(self) -> None:
        """Cache the most recent context for fallback use."""
        type(self).last_context = self

    @property
    def raw_data(self) -> dict[str, Any] | None:
        """Backward-compatible accessor used by some tests."""
        return self.resume_data


__all__ = [
    "Block",
    "LatexEntry",
    "LatexGenerationContext",
    "LatexRenderResult",
    "LatexSection",
    "ListBlock",
    "ParagraphBlock",
]
