"""Core resume data transformations - pure functions without side effects."""

from simple_resume.core.file_operations import (
    find_yaml_files,
    get_resume_name_from_path,
    iterate_yaml_files,
)
from simple_resume.core.models import (
    RenderMode,
    RenderPlan,
    ResumeConfig,
    ValidationResult,
)
from simple_resume.core.render import (
    prepare_html_generation_request,
    prepare_pdf_generation_request,
    validate_render_plan,
)
from simple_resume.core.render.plan import (
    build_render_plan,
    normalize_with_palette_fallback,
    prepare_render_data,
    transform_for_mode,
    validate_resume_config,
    validate_resume_config_or_raise,
)
from simple_resume.core.resume import Resume

__all__ = [
    "Resume",
    "ResumeConfig",
    "RenderPlan",
    "ValidationResult",
    "RenderMode",
    "find_yaml_files",
    "get_resume_name_from_path",
    "iterate_yaml_files",
    "build_render_plan",
    "normalize_with_palette_fallback",
    "prepare_render_data",
    "transform_for_mode",
    "validate_resume_config",
    "validate_resume_config_or_raise",
    "prepare_html_generation_request",
    "prepare_pdf_generation_request",
    "validate_render_plan",
]
