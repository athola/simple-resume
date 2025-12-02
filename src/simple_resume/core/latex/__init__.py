"""Core LaTeX functionality (pure, deterministic, no side effects).

This package contains pure business logic for LaTeX document generation.
All functions are deterministic and have no side effects (no file I/O,
no network access, no randomness).

The shell layer (simple_resume.shell.render.latex) handles all I/O operations
including template loading, file system access, and LaTeX compilation.
"""

from simple_resume.core.latex.context import build_latex_context_pure
from simple_resume.core.latex.conversion import (
    collect_blocks,
    convert_inline,
    normalize_iterable,
)
from simple_resume.core.latex.escaping import escape_latex, escape_url
from simple_resume.core.latex.fonts import fontawesome_support_block
from simple_resume.core.latex.formatting import format_date, linkify
from simple_resume.core.latex.sections import (
    build_contact_lines,
    prepare_sections,
    prepare_skill_sections,
)
from simple_resume.core.latex.types import (
    Block,
    LatexEntry,
    LatexRenderResult,
    LatexSection,
    ListBlock,
    ParagraphBlock,
)

__all__ = [
    # Types
    "Block",
    "LatexEntry",
    "LatexRenderResult",
    "LatexSection",
    "ListBlock",
    "ParagraphBlock",
    # Escaping
    "escape_latex",
    "escape_url",
    # Conversion
    "collect_blocks",
    "convert_inline",
    "normalize_iterable",
    # Formatting
    "format_date",
    "linkify",
    # Sections
    "build_contact_lines",
    "prepare_sections",
    "prepare_skill_sections",
    # Context
    "build_latex_context_pure",
    # Fonts
    "fontawesome_support_block",
]
