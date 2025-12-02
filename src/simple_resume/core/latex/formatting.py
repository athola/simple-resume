"""LaTeX formatting functions for dates and links (pure, no side effects)."""

from __future__ import annotations

from simple_resume.core.latex.conversion import convert_inline
from simple_resume.core.latex.escaping import escape_url


def format_date(start: str | None, end: str | None) -> str | None:
    """Format start and end dates for LaTeX rendering.

    This is a pure function that formats date ranges according to resume
    conventions.

    Args:
        start: Start date string (may be None or empty).
        end: End date string (may be None or empty).

    Returns:
        Formatted date range string, or None if both inputs are empty.

    Examples:
        >>> format_date("2020", "2023")
        '2020 -- 2023'
        >>> format_date("2023", "2023")
        '2023'
        >>> format_date("2020", "Present")
        '2020 -- Present'
        >>> format_date(None, None)
        None

    """
    start_clean = start.strip() if isinstance(start, str) else ""
    end_clean = end.strip() if isinstance(end, str) else ""

    if start_clean and end_clean:
        if start_clean == end_clean:
            return convert_inline(start_clean)
        return convert_inline(f"{start_clean} -- {end_clean}")
    if end_clean:
        return convert_inline(end_clean)
    if start_clean:
        return convert_inline(start_clean)
    return None


def linkify(text: str | None, link: str | None) -> str | None:
    r"""Convert text to a hyperlink if a URL is provided.

    This is a pure function that creates LaTeX \\href commands when
    a link is provided, or returns the text as-is if no link.

    Args:
        text: The text to display (may be None).
        link: The URL to link to (may be None or empty).

    Returns:
        LaTeX hyperlink command if link is provided, plain text otherwise,
        or None if text is empty.

    Examples:
        >>> linkify("Company", "https://example.com")
        '\\href{https://example.com}{Company}'
        >>> linkify("Company", None)
        'Company'
        >>> linkify(None, "https://example.com")
        None

    """
    if not text:
        return None
    rendered = convert_inline(text)
    if link:
        return rf"\href{{{escape_url(link)}}}{{{rendered}}}"
    return rendered


__all__ = [
    "format_date",
    "linkify",
]
