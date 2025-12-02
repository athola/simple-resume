"""LaTeX escaping functions (pure, no side effects)."""

from __future__ import annotations

LATEX_SPECIAL_CHARS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def escape_latex(text: str) -> str:
    r"""Escape LaTeX special characters.

    This is a pure function that transforms a string by escaping characters
    that have special meaning in LaTeX.

    Args:
        text: The input string to escape.

    Returns:
        The escaped string safe for use in LaTeX documents.

    Examples:
        >>> escape_latex("Price: $50 & up")
        'Price: \\$50 \\& up'
        >>> escape_latex("file_name")
        'file\\_name'

    """
    return "".join(LATEX_SPECIAL_CHARS.get(char, char) for char in text)


def escape_url(url: str) -> str:
    r"""Escape characters in URLs that break LaTeX hyperlinks.

    This is a pure function that escapes only the subset of characters
    that cause issues in LaTeX URLs (fewer than general LaTeX escaping).

    Args:
        url: The URL to escape.

    Returns:
        The escaped URL safe for use in LaTeX \\href commands.

    Examples:
        >>> escape_url("https://example.com?q=test&foo=bar")
        'https://example.com?q=test\\&foo=bar'
        >>> escape_url("https://example.com/page#section")
        'https://example.com/page\\#section'

    """
    replacements = {"%": r"\%", "#": r"\#", "&": r"\&", "_": r"\_"}
    return "".join(replacements.get(char, char) for char in url)


__all__ = [
    "LATEX_SPECIAL_CHARS",
    "escape_latex",
    "escape_url",
]
