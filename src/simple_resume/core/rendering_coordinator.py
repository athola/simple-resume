"""Core rendering coordinator without external dependencies.

This module provides pure coordination logic for rendering operations.
Actual I/O and external dependencies are handled by the shell layer.
"""

from __future__ import annotations

from typing import Any

from .models import RenderPlan, ValidationResult


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

    if render_plan.mode.value == "html" and render_plan.template_name is None:
        errors.append("HTML rendering requires a template name")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=[],
        normalized_config=None,
        palette_metadata=None,
    )


__all__ = [
    "prepare_html_generation_request",
    "prepare_pdf_generation_request",
    "validate_render_plan",
]
