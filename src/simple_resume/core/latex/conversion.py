"""Markdown to LaTeX conversion functions (pure, deterministic)."""

from __future__ import annotations

import itertools
import re
from typing import Any, Literal

from simple_resume.core.latex.escaping import escape_latex, escape_url
from simple_resume.core.latex.types import Block


class _InlineConverter:
    """Convert limited Markdown inline formatting to LaTeX.

    This class is pure and deterministic - it uses internal state only for
    placeholder generation during conversion, which is deterministic based
    on the order of replacements.
    """

    def __init__(self) -> None:
        self._placeholders: dict[str, str] = {}
        self._counter = itertools.count()

    def convert(self, text: str) -> str:
        """Return a string that is safe for LaTeX.

        Args:
            text: Markdown-formatted text.

        Returns:
            LaTeX-formatted text with escaping applied.

        """
        working = text
        working = re.sub(r"`([^`]+)`", self._code_replacement, working)
        working = re.sub(
            r"\[([^\]]+)\]\(([^)]+)\)",
            self._link_replacement,
            working,
        )
        working = re.sub(r"\*\*(.+?)\*\*", self._bold_replacement, working)
        working = re.sub(r"__(.+?)__", self._bold_replacement, working)
        working = re.sub(
            r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)",
            self._italic_replacement,
            working,
        )
        working = re.sub(r"_(.+?)_", self._italic_replacement, working)

        escaped = escape_latex(working)
        for key, value in self._placeholders.items():
            escaped = escaped.replace(key, value)
        return escaped

    def _placeholder(self, value: str) -> str:
        token = f"LATEXPH{next(self._counter)}"
        self._placeholders[token] = value
        return token

    def _code_replacement(self, match: re.Match[str]) -> str:
        content = escape_latex(match.group(1))
        return self._placeholder(rf"\texttt{{{content}}}")

    def _link_replacement(self, match: re.Match[str]) -> str:
        label = convert_inline(match.group(1))
        url = escape_url(match.group(2))
        return self._placeholder(rf"\href{{{url}}}{{{label}}}")

    def _bold_replacement(self, match: re.Match[str]) -> str:
        content = convert_inline(match.group(1))
        return self._placeholder(rf"\textbf{{{content}}}")

    def _italic_replacement(self, match: re.Match[str]) -> str:
        content = convert_inline(match.group(1))
        return self._placeholder(rf"\textit{{{content}}}")


def convert_inline(text: str) -> str:
    r"""Convert simple Markdown inline formatting to LaTeX.

    This is a pure function that transforms Markdown syntax to LaTeX.

    Supported Markdown:
    - **bold** or __bold__ → \textbf{bold}
    - *italic* or _italic_ → \textit{italic}
    - `code` → \texttt{code}
    - [text](url) → \href{url}{text}

    Args:
        text: Markdown-formatted text.

    Returns:
        LaTeX-formatted text.

    Examples:
        >>> convert_inline("This is **bold** text")
        'This is \\textbf{bold} text'
        >>> convert_inline("[GitHub](https://github.com)")
        '\\href{https://github.com}{GitHub}'

    """
    converter = _InlineConverter()
    return converter.convert(text)


def normalize_iterable(value: Any) -> list[str]:
    """Return a list of strings, regardless of the input type.

    This is a pure function that coerces various types to a list of strings
    with Markdown-to-LaTeX conversion applied.

    Args:
        value: Input value (None, str, list, tuple, set, or dict).

    Returns:
        List of LaTeX-formatted strings.

    Examples:
        >>> normalize_iterable(["Python", "JavaScript"])
        ['Python', 'JavaScript']
        >>> normalize_iterable({"Python": "Expert", "Go": "Intermediate"})
        ['Python (Expert)', 'Go (Intermediate)']
        >>> normalize_iterable(None)
        []

    """
    if value is None:
        return []
    if isinstance(value, dict):
        items = []
        for key, val in value.items():
            item = f"{key} ({val})"
            items.append(convert_inline(str(item)))
        return items
    if isinstance(value, (list, tuple, set)):
        return [convert_inline(str(item)) for item in value]
    return [convert_inline(str(value))]


def collect_blocks(description: str | None) -> list[Block]:
    r"""Parse Markdown text into structured blocks for LaTeX rendering.

    This is a pure function that transforms Markdown text into a list of
    block structures (paragraphs and lists) suitable for LaTeX rendering.

    Supported Markdown:
    - Paragraphs separated by blank lines
    - Bullet lists (-, *, +)
    - Numbered lists (1., 2., etc.)
    - Multi-line list items (indented continuation)

    Args:
        description: Markdown-formatted text (may be None).

    Returns:
        List of Block structures (ParagraphBlock or ListBlock).

    Examples:
        >>> blocks = collect_blocks("Paragraph.\\n\\n- Item 1\\n- Item 2")
        >>> len(blocks)
        2
        >>> blocks[0]['kind']
        'paragraph'
        >>> blocks[1]['kind']
        'itemize'

    """
    if not description:
        return []

    lines = description.strip("\n").splitlines()
    blocks: list[Block] = []
    current_items: list[str] = []
    ordered = False

    def flush_items() -> None:
        nonlocal current_items, ordered
        if current_items:
            converted = [convert_inline(item) for item in current_items]
            kind: Literal["itemize", "enumerate"] = (
                "enumerate" if ordered else "itemize"
            )
            blocks.append({"kind": kind, "items": converted})
            current_items = []
            ordered = False

    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            flush_items()
            continue

        bullet_match = re.match(r"^[-*+]\s+(.*)", stripped)
        ordered_match = re.match(r"^\d+\.\s+(.*)", stripped)

        if bullet_match:
            if current_items and ordered:
                flush_items()
            ordered = False
            current_items.append(bullet_match.group(1).strip())
            continue

        if ordered_match:
            if current_items and not ordered:
                flush_items()
            ordered = True
            current_items.append(ordered_match.group(1).strip())
            continue

        if stripped.startswith(" ") and current_items:
            current_items[-1] = f"{current_items[-1]} {stripped.strip()}"
            continue

        flush_items()
        paragraph_text = convert_inline(stripped)
        blocks.append({"kind": "paragraph", "text": paragraph_text})

    flush_items()
    return blocks


__all__ = [
    "collect_blocks",
    "convert_inline",
    "normalize_iterable",
]
