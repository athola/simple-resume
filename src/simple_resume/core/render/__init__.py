"""Core rendering functionality for resumes.

This module provides pure functions for template rendering and coordination
between different rendering backends without any I/O side effects.
"""

from __future__ import annotations

from simple_resume.core.render.manage import (
    get_template_environment,
    prepare_html_generation_request,
    prepare_pdf_generation_request,
    validate_render_plan,
)
from simple_resume.core.render.plan import (
    RenderPlanConfig,
    build_render_plan,
    normalize_with_palette_fallback,
    prepare_render_data,
    transform_for_mode,
    validate_resume_config,
    validate_resume_config_or_raise,
)

__all__ = [
    "get_template_environment",
    "prepare_html_generation_request",
    "prepare_pdf_generation_request",
    "validate_render_plan",
    "build_render_plan",
    "normalize_with_palette_fallback",
    "prepare_render_data",
    "RenderPlanConfig",
    "transform_for_mode",
    "validate_resume_config",
    "validate_resume_config_or_raise",
]
