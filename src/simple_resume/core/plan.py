"""Provide helpers for building render plans and validating configuration."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from ..constants import RenderMode
from ..exceptions import ValidationError
from ..palettes.exceptions import PaletteGenerationError
from ..utilities import normalize_config, render_markdown_content
from .colors import is_valid_color
from .models import RenderPlan, ResumeConfig, ValidationResult


def _validate_color_fields(config: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Validate color fields in configuration.

    Args:
        config: Configuration dictionary to validate.

    Returns:
        Tuple of (cleaned_config, color_errors).

    """
    working_config = copy.deepcopy(config)
    errors: list[str] = []

    color_fields = [
        "theme_color",
        "sidebar_color",
        "sidebar_text_color",
        "sidebar_bold_color",
        "bar_background_color",
        "date2_color",
        "frame_color",
        "heading_icon_color",
        "bold_color",
    ]

    for field in color_fields:
        if field not in working_config:
            continue
        candidate = working_config.get(field)
        candidate_str = str(candidate) if candidate is not None else ""
        if not is_valid_color(candidate_str):
            errors.append(
                f"Invalid color format for '{field}': {candidate}. "
                "Expected hex color like '#0395DE' or '#FFF'"
            )
            working_config.pop(field, None)

    return working_config, errors


def _build_resume_config(normalized_config: dict[str, Any]) -> ResumeConfig:
    """Build ResumeConfig from normalized configuration.

    Args:
        normalized_config: Normalized configuration dictionary.

    Returns:
        ResumeConfig instance.

    """
    return ResumeConfig(
        page_width=normalized_config.get("page_width"),
        page_height=normalized_config.get("page_height"),
        sidebar_width=normalized_config.get("sidebar_width"),
        output_mode=str(normalized_config.get("output_mode", "markdown"))
        .strip()
        .lower(),
        template=normalized_config.get("template", "resume_no_bars"),
        color_scheme=normalized_config.get("color_scheme", "default"),
        theme_color=normalized_config.get("theme_color", "#0395DE"),
        sidebar_color=normalized_config.get("sidebar_color", "#F6F6F6"),
        sidebar_text_color=normalized_config.get("sidebar_text_color", "#000000"),
        sidebar_bold_color=normalized_config.get("sidebar_bold_color", "#000000"),
        bar_background_color=normalized_config.get("bar_background_color", "#DFDFDF"),
        date2_color=normalized_config.get("date2_color", "#616161"),
        frame_color=normalized_config.get("frame_color", "#757575"),
        heading_icon_color=normalized_config.get("heading_icon_color", "#0395DE"),
        bold_color=normalized_config.get("bold_color", "#585858"),
        section_icon_circle_size=normalized_config.get(
            "section_icon_circle_size", "7.8mm"
        ),
        section_icon_circle_x_offset=normalized_config.get(
            "section_icon_circle_x_offset", "-0.5mm"
        ),
        section_icon_design_size=normalized_config.get(
            "section_icon_design_size", "4mm"
        ),
        section_icon_design_x_offset=normalized_config.get(
            "section_icon_design_x_offset", "-0.1mm"
        ),
        section_icon_design_y_offset=normalized_config.get(
            "section_icon_design_y_offset", "-0.4mm"
        ),
        section_heading_text_margin=normalized_config.get(
            "section_heading_text_margin", "-6mm"
        ),
    )


def validate_resume_config(
    raw_config: dict[str, Any], filename: str = ""
) -> ValidationResult:
    """Validate and normalize resume configuration."""
    errors: list[str] = []
    warnings: list[str] = []

    try:
        # Validate color fields
        working_config, color_errors = _validate_color_fields(raw_config)
        errors.extend(color_errors)

        # Normalize configuration
        normalized_config, palette_meta = normalize_config(
            working_config, filename=filename
        )

        # Build configuration object
        config = _build_resume_config(normalized_config)

        if errors:
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                normalized_config=None,
                palette_metadata=None,
            )

        return ValidationResult(
            is_valid=True,
            errors=[],
            warnings=warnings,
            normalized_config=config,
            palette_metadata=palette_meta,
        )

    except ValueError as exc:
        errors.append(str(exc))
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
    except Exception as exc:  # pragma: no cover - defensive
        errors.append(f"Unexpected validation error: {exc}")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)


def validate_resume_config_or_raise(
    raw_config: dict[str, Any], filename: str = ""
) -> ResumeConfig:
    """Validate configuration and raise `ValidationError` on failure."""
    result = validate_resume_config(raw_config, filename)
    if not result.is_valid:
        raise ValidationError(
            f"Configuration validation failed: {result.errors}",
            errors=result.errors,
            filename=filename,
        )

    if result.normalized_config is None:  # pragma: no cover - defensive branch
        raise ValidationError(
            "Configuration validation failed: No normalized config produced",
            errors=["Internal validation error"],
            filename=filename,
        )

    return result.normalized_config


def normalize_with_palette_fallback(
    raw_config: dict[str, Any],
    *,
    palette_meta_source: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], Any, dict[str, Any]]:
    """Normalize a raw config while handling palette generation failures."""
    config_for_validation = raw_config

    try:
        normalized_config_dict, palette_meta = normalize_config(raw_config)
        return normalized_config_dict, palette_meta, config_for_validation
    except PaletteGenerationError:
        fallback_meta = None
        if isinstance(palette_meta_source, dict):
            fallback_meta = palette_meta_source.get("palette")

        cleaned_config = copy.deepcopy(raw_config)
        cleaned_config.pop("palette", None)
        normalized_config_dict, _ = normalize_config(cleaned_config)

        return normalized_config_dict, fallback_meta, cleaned_config


def transform_for_mode(
    source_yaml_content: dict[str, Any], mode: RenderMode
) -> dict[str, Any]:
    """Transform YAML content based on render mode."""
    if mode is RenderMode.LATEX:
        return copy.deepcopy(source_yaml_content)

    return render_markdown_content(source_yaml_content)


def build_render_plan(  # noqa: PLR0913
    name: str,
    mode: RenderMode,
    config: ResumeConfig,
    context: dict[str, Any] | None,
    *,
    base_path: Path | str,
    template_name: str | None = None,
    palette_meta: Any = None,
) -> RenderPlan:
    """Build the final `RenderPlan` based on resolved mode and context."""
    if mode is RenderMode.LATEX:
        return RenderPlan(
            name=name,
            mode=RenderMode.LATEX,
            config=config,
            base_path=base_path,
            tex=None,
            palette_metadata=palette_meta,
        )

    if context is None:
        raise ValueError("HTML render plans require a context dictionary")

    if template_name is None:
        raise ValueError("HTML render plans require a template name")

    return RenderPlan(
        name=name,
        mode=RenderMode.HTML,
        config=config,
        template_name=template_name,
        context=context,
        base_path=base_path,
        palette_metadata=palette_meta,
    )


def prepare_render_data(
    source_yaml_content: dict[str, Any],
    *,
    preview: bool = False,
    base_path: Path | str = "",
) -> RenderPlan:
    """Transform raw resume data into a render plan."""
    raw_config = source_yaml_content.get("config")
    if not isinstance(raw_config, dict) or not raw_config:
        raise ValueError("Invalid resume config: missing or malformed config section")

    normalized_config_dict, palette_meta, config_for_validation = (
        normalize_with_palette_fallback(
            raw_config,
            palette_meta_source=source_yaml_content.get("meta"),
        )
    )

    config = validate_resume_config_or_raise(config_for_validation)

    mode: RenderMode = (
        RenderMode.LATEX if config.output_mode == "latex" else RenderMode.HTML
    )

    transformed_data = transform_for_mode(source_yaml_content, mode)

    name = transformed_data.get("full_name", "resume")

    if mode is RenderMode.LATEX:
        return build_render_plan(
            name,
            mode,
            config,
            context=None,
            base_path=base_path,
            palette_meta=palette_meta,
        )

    template = transformed_data.get("template", "resume_no_bars")
    template_name = f"html/{template}.html"

    context = dict(transformed_data)
    context["resume_config"] = normalized_config_dict or {}
    context["preview"] = preview

    return build_render_plan(
        name,
        mode,
        config,
        context,
        base_path=base_path,
        template_name=template_name,
        palette_meta=palette_meta,
    )


__all__ = [
    "build_render_plan",
    "normalize_with_palette_fallback",
    "prepare_render_data",
    "transform_for_mode",
    "validate_resume_config",
    "validate_resume_config_or_raise",
]
