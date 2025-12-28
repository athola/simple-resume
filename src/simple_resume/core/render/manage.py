"""Core rendering management without external dependencies.

This module provides pure functions for template rendering setup and coordination
between different rendering backends without any I/O side effects.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from simple_resume.core.models import RenderPlan, ValidationResult


def dynamic_font_size(
    text: str,
    available_width_mm: float,
    max_font_pt: float = 11.5,
    min_font_pt: float = 8.0,
) -> str:
    """Calculate dynamic font size based on text length and available width.

    This filter estimates font size needed to fit text within a given width,
    scaling down proportionally from max to min size when text is too long.

    Args:
        text: The text to measure (combined title + company)
        available_width_mm: Available width in millimeters
        max_font_pt: Maximum font size in points (default 11.5pt)
        min_font_pt: Minimum font size in points (default 8.0pt)

    Returns:
        Font size string with "pt" suffix (e.g., "10.5pt")

    Note:
        Uses approximate character width estimation for Avenir font.
        Mixed-case text averages ~1.9mm per character at 11.5pt.
        This errs on the side of reduction to prevent text wrapping.

    """
    # Handle edge cases: empty text or invalid dimensions
    if not text or available_width_mm <= 0:
        return f"{max_font_pt}pt"

    text_length = len(text)

    # Approximate character width at 11.5pt for Avenir font
    # Mixed-case text: ~2.1mm average per character
    # Errs on the side of reduction to prevent text wrapping
    base_char_width_mm = 2.1

    # Scale character width based on font size
    char_width_at_max = base_char_width_mm * (max_font_pt / 11.5)

    # Estimate text width at max font size
    estimated_width_at_max = text_length * char_width_at_max

    if estimated_width_at_max <= available_width_mm:
        # Text fits at max size
        return f"{max_font_pt}pt"

    # Calculate the scaling factor needed
    scale_factor = available_width_mm / estimated_width_at_max

    # Apply scaling but clamp to min size
    scaled_font = max_font_pt * scale_factor
    final_font = max(min_font_pt, min(max_font_pt, scaled_font))

    # Round to one decimal place for cleaner CSS
    return f"{round(final_font, 1)}pt"


def get_template_environment(template_path: str) -> Environment:
    """Create and return a Jinja2 environment for template rendering.

    Args:
        template_path: Path to the templates directory

    Returns:
        Jinja2 Environment configured for rendering

    """
    # Include both templates and static/css directories for CSS inlining
    template_dir = Path(template_path)
    css_dir = template_dir.parent / "static" / "css"
    search_paths = [str(template_dir)]
    if css_dir.exists():
        search_paths.append(str(css_dir))

    env = Environment(
        loader=FileSystemLoader(search_paths),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Register custom filters for template use
    env.filters["dynamic_font_size"] = dynamic_font_size
    # Also expose as a global function for use in set statements
    env.globals["dynamic_font_size"] = dynamic_font_size

    return env


def prepare_html_generation_request(
    render_plan: RenderPlan,
    output_path: Any,
    **kwargs: Any,
) -> dict[str, Any]:
    """Prepare request data for HTML generation.

    Args:
        render_plan: The render plan to use.
        output_path: Output file path.
        **kwargs: Additional generation options.

    Returns:
        Dictionary with request data for shell layer.

    """
    return {
        "render_plan": render_plan,
        "output_path": output_path,
        "filename": getattr(render_plan, "filename", None),
        **kwargs,
    }


def prepare_pdf_generation_request(
    render_plan: RenderPlan,
    output_path: Any,
    open_after: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    """Prepare request data for PDF generation.

    Args:
        render_plan: The render plan to use.
        output_path: Output file path.
        open_after: Whether to open the PDF after generation.
        **kwargs: Additional generation options.

    Returns:
        Dictionary with request data for shell layer.

    """
    return {
        "render_plan": render_plan,
        "output_path": output_path,
        "open_after": open_after,
        "filename": getattr(render_plan, "filename", None),
        "resume_name": getattr(render_plan, "name", "resume"),
        **kwargs,
    }


def validate_render_plan(render_plan: RenderPlan) -> ValidationResult:
    """Validate a render plan before generation.

    Args:
        render_plan: The render plan to validate.

    Returns:
        ValidationResult indicating if the plan is valid.

    """
    errors = []

    if render_plan.mode is None:
        errors.append("Render mode is required")

    if render_plan.config is None:
        errors.append("Render config is required")

    if (
        render_plan.mode is not None
        and render_plan.mode.value == "html"
        and render_plan.template_name is None
    ):
        errors.append("HTML rendering requires a template name")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=[],
        normalized_config=None,
        palette_metadata=None,
    )


__all__ = [
    "dynamic_font_size",
    "get_template_environment",
    "prepare_html_generation_request",
    "prepare_pdf_generation_request",
    "validate_render_plan",
]
