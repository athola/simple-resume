"""LaTeX context building functions (pure version without I/O)."""

from __future__ import annotations

from typing import Any

from simple_resume.core.latex.conversion import collect_blocks, convert_inline
from simple_resume.core.latex.sections import (
    build_contact_lines,
    prepare_sections,
    prepare_skill_sections,
)


def build_latex_context_pure(data: dict[str, Any]) -> dict[str, Any]:
    """Prepare the LaTeX template context from raw resume data (pure version).

    This is the pure, core version of context building that does NOT perform
    any file system operations. The fontawesome_block is set to None and must
    be added by the shell layer which has access to the file system.

    Args:
        data: Raw resume data dictionary.

    Returns:
        Dictionary of context variables for LaTeX template rendering.
        Note: fontawesome_block will be None and must be set by shell layer.

    Examples:
        >>> data = {"full_name": "John Doe", "job_title": "Engineer"}
        >>> context = build_latex_context_pure(data)
        >>> context["full_name"]
        'John Doe'
        >>> context["headline"]
        'Engineer'

    """
    full_name = convert_inline(str(data.get("full_name", "")))
    headline = data.get("job_title")
    rendered_headline = convert_inline(str(headline)) if headline else None
    summary_blocks = collect_blocks(data.get("description"))

    return {
        "full_name": full_name,
        "headline": rendered_headline,
        "contact_lines": build_contact_lines(data),
        "summary_blocks": summary_blocks,
        "skill_sections": prepare_skill_sections(data),
        "sections": prepare_sections(data),
        "fontawesome_block": None,  # Must be set by shell layer
    }


__all__ = [
    "build_latex_context_pure",
]
