"""LaTeX document data types (pure, immutable)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, TypedDict


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


__all__ = [
    "Block",
    "LatexEntry",
    "LatexRenderResult",
    "LatexSection",
    "ListBlock",
    "ParagraphBlock",
]
