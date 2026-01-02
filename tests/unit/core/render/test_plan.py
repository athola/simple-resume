"""Tests for core/render/plan.py - render plan building and validation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

from simple_resume.core.constants import RenderMode
from simple_resume.core.exceptions import ValidationError
from simple_resume.core.models import ResumeConfig
from simple_resume.core.palettes.exceptions import (
    PaletteError,
    PaletteGenerationError,
    PaletteLookupError,
    PaletteRemoteError,
)
from simple_resume.core.palettes.registry import PaletteRegistry
from simple_resume.core.render.plan import (
    RenderPlanConfig,
    _build_resume_config,
    _validate_color_fields,
    build_render_plan,
    normalize_with_palette_fallback,
    prepare_render_data,
    transform_for_mode,
    validate_resume_config,
    validate_resume_config_or_raise,
)


class TestValidateColorFields:
    """Tests for _validate_color_fields function."""

    def test_valid_colors(self) -> None:
        """Test validation with all valid colors."""
        config = {
            "theme_color": "#0395DE",
            "sidebar_color": "#F6F6F6",
            "bold_color": "#585858",
        }
        cleaned, errors = _validate_color_fields(config)
        assert len(errors) == 0
        assert cleaned == config

    def test_invalid_color_format(self) -> None:
        """Test validation with invalid color format."""
        config = {"theme_color": "invalid_color", "sidebar_color": "#F6F6F6"}
        cleaned, errors = _validate_color_fields(config)
        assert len(errors) == 1
        assert "Invalid color format for 'theme_color'" in errors[0]
        assert "theme_color" not in cleaned
        assert cleaned["sidebar_color"] == "#F6F6F6"

    def test_missing_color_fields(self) -> None:
        """Test validation with missing color fields."""
        config = {"some_other_field": "value"}
        cleaned, errors = _validate_color_fields(config)
        assert len(errors) == 0
        assert cleaned == config

    def test_none_color_value(self) -> None:
        """Test validation with None color value."""
        config = {"theme_color": None}
        cleaned, errors = _validate_color_fields(config)
        assert len(errors) == 1
        assert "Invalid color format for 'theme_color'" in errors[0]

    def test_multiple_invalid_colors(self) -> None:
        """Test validation with multiple invalid colors."""
        config = {
            "theme_color": "bad",
            "sidebar_color": "also_bad",
            "bold_color": "#585858",
        }
        cleaned, errors = _validate_color_fields(config)
        assert len(errors) == 2
        assert cleaned["bold_color"] == "#585858"
        assert "theme_color" not in cleaned
        assert "sidebar_color" not in cleaned


class TestBuildResumeConfig:
    """Tests for _build_resume_config function."""

    def test_build_with_all_fields(self) -> None:
        """Test building ResumeConfig with all fields provided."""
        normalized = {
            "page_width": 190,
            "page_height": 270,
            "sidebar_width": 60,
            "output_mode": "latex",
            "template": "basic",
            "color_scheme": "blue",
            "theme_color": "#0395DE",
            "sidebar_color": "#F6F6F6",
            "sidebar_text_color": "#000000",
            "sidebar_bold_color": "#000000",
            "bar_background_color": "#DFDFDF",
            "date2_color": "#616161",
            "frame_color": "#757575",
            "heading_icon_color": "#0395DE",
            "bold_color": "#585858",
        }
        config = _build_resume_config(normalized)
        assert isinstance(config, ResumeConfig)
        assert config.page_width == 190
        assert config.output_mode == "latex"
        assert config.theme_color == "#0395DE"

    def test_build_with_defaults(self) -> None:
        """Test building ResumeConfig with default values."""
        normalized: dict[str, Any] = {}
        config = _build_resume_config(normalized)
        assert config.output_mode == "markdown"
        assert config.template == "resume_no_bars"
        assert config.theme_color == "#0395DE"

    def test_build_with_section_icon_fields(self) -> None:
        """Test section icon float values are correctly assigned from config."""
        normalized = {
            "section_icon_circle_size": 8.6,
            "section_icon_circle_x_offset": -0.75,
            "section_icon_design_size": 4.0,
            "section_icon_design_x_offset": -1.5,
            "section_icon_design_y_offset": -0.5,
            "section_heading_text_margin": -6,
        }
        config = _build_resume_config(normalized)

        assert config.section_icon_circle_size == 8.6
        assert config.section_icon_circle_x_offset == -0.75
        assert config.section_icon_design_size == 4.0
        assert config.section_icon_design_x_offset == -1.5
        assert config.section_icon_design_y_offset == -0.5
        assert config.section_heading_text_margin == -6

    def test_build_with_contact_icon_fields(self) -> None:
        """Test contact icon float values are correctly assigned from config."""
        normalized = {
            "contact_icon_size": 6.0,
            "contact_icon_margin_top": 1.0,
            "contact_icon_margin_right": 3.0,
            "contact_icon_gap": 5.0,
        }
        config = _build_resume_config(normalized)

        assert config.contact_icon_size == 6.0
        assert config.contact_icon_margin_top == 1.0
        assert config.contact_icon_margin_right == 3.0
        assert config.contact_icon_gap == 5.0

    def test_build_icon_fields_defaults(self) -> None:
        """Test icon fields have correct float defaults (no mm suffix)."""
        normalized: dict[str, Any] = {}
        config = _build_resume_config(normalized)

        # Section icon defaults
        assert config.section_icon_circle_size == 7.8
        assert config.section_icon_circle_x_offset == 0
        assert config.section_icon_design_size == 3.5
        assert config.section_icon_design_x_offset == 0
        assert config.section_icon_design_y_offset == 0
        assert config.section_heading_text_margin == -6

        # Contact icon defaults
        assert config.contact_icon_size == 5
        assert config.contact_icon_margin_top == 0.5
        assert config.contact_icon_margin_right == 2
        assert config.contact_icon_gap == 4


class TestValidateResumeConfig:
    """Tests for validate_resume_config function."""

    def test_valid_config(self) -> None:
        """Test validation with valid configuration."""
        raw_config = {"theme_color": "#0395DE"}
        registry = PaletteRegistry()
        result = validate_resume_config(raw_config, registry=registry)
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.normalized_config is not None

    def test_invalid_color_in_config(self) -> None:
        """Test validation with invalid color."""
        raw_config = {"theme_color": "not_a_color"}
        registry = PaletteRegistry()
        result = validate_resume_config(raw_config, registry=registry)
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("Invalid color format" in err for err in result.errors)

    @mock.patch("simple_resume.core.render.plan.normalize_config")
    def test_value_error_handling(self, mock_normalize) -> None:
        """Test handling of ValueError during validation."""
        mock_normalize.side_effect = ValueError("Test error")
        raw_config: dict[str, Any] = {}
        registry = PaletteRegistry()
        result = validate_resume_config(raw_config, registry=registry)
        assert result.is_valid is False
        assert "Test error" in result.errors

    @mock.patch("simple_resume.core.render.plan.normalize_config")
    def test_key_error_handling(self, mock_normalize) -> None:
        """Test handling of KeyError during validation."""
        mock_normalize.side_effect = KeyError("missing_key")
        raw_config: dict[str, Any] = {}
        registry = PaletteRegistry()
        result = validate_resume_config(raw_config, registry=registry)
        assert result.is_valid is False
        assert any("Configuration error" in err for err in result.errors)
        assert any("missing_key" in err for err in result.errors)

    @mock.patch("simple_resume.core.render.plan.normalize_config")
    def test_type_error_handling(self, mock_normalize) -> None:
        """Test handling of TypeError during validation."""
        mock_normalize.side_effect = TypeError("expected str, got int")
        raw_config: dict[str, Any] = {}
        registry = PaletteRegistry()
        result = validate_resume_config(raw_config, registry=registry)
        assert result.is_valid is False
        assert any("Configuration error" in err for err in result.errors)
        assert any("expected str, got int" in err for err in result.errors)

    @mock.patch("simple_resume.core.render.plan.normalize_config")
    def test_attribute_error_handling(self, mock_normalize) -> None:
        """Test handling of AttributeError during validation."""
        mock_normalize.side_effect = AttributeError("'NoneType' has no attribute 'get'")
        raw_config: dict[str, Any] = {}
        registry = PaletteRegistry()
        result = validate_resume_config(raw_config, registry=registry)
        assert result.is_valid is False
        assert any("Configuration error" in err for err in result.errors)
        assert any("NoneType" in err for err in result.errors)

    @mock.patch("simple_resume.core.render.plan.normalize_config")
    def test_palette_error_handling(self, mock_normalize) -> None:
        """Test handling of PaletteError during validation."""
        mock_normalize.side_effect = PaletteError("Palette lookup failed")
        raw_config: dict[str, Any] = {}
        registry = PaletteRegistry()
        result = validate_resume_config(raw_config, registry=registry)
        assert result.is_valid is False
        assert any("Palette error" in err for err in result.errors)
        assert any("Palette lookup failed" in err for err in result.errors)

    @mock.patch("simple_resume.core.render.plan.normalize_config")
    def test_palette_lookup_error_handling(self, mock_normalize) -> None:
        """Test handling of PaletteLookupError during validation."""
        mock_normalize.side_effect = PaletteLookupError("Unknown palette: 'foo'")
        raw_config: dict[str, Any] = {}
        registry = PaletteRegistry()
        result = validate_resume_config(raw_config, registry=registry)
        assert result.is_valid is False
        assert any("Palette error" in err for err in result.errors)
        assert any("Unknown palette" in err for err in result.errors)

    @mock.patch("simple_resume.core.render.plan.normalize_config")
    def test_palette_remote_error_handling(self, mock_normalize) -> None:
        """Test handling of PaletteRemoteError during validation."""
        mock_normalize.side_effect = PaletteRemoteError("Remote service unavailable")
        raw_config: dict[str, Any] = {}
        registry = PaletteRegistry()
        result = validate_resume_config(raw_config, registry=registry)
        assert result.is_valid is False
        assert any("Palette error" in err for err in result.errors)
        assert any("Remote service unavailable" in err for err in result.errors)


class TestValidateResumeConfigOrRaise:
    """Tests for validate_resume_config_or_raise function."""

    def test_valid_config_returns_resume_config(self) -> None:
        """Test successful validation returns ResumeConfig."""
        raw_config = {"theme_color": "#0395DE"}
        registry = PaletteRegistry()
        config = validate_resume_config_or_raise(raw_config, registry=registry)
        assert isinstance(config, ResumeConfig)

    def test_invalid_config_raises_validation_error(self) -> None:
        """Test invalid config raises ValidationError."""
        raw_config = {"theme_color": "invalid"}
        registry = PaletteRegistry()
        with pytest.raises(ValidationError, match="Configuration validation failed"):
            validate_resume_config_or_raise(raw_config, registry=registry)

    def test_none_registry_creates_default(self) -> None:
        """Test that None registry creates a default PaletteRegistry."""
        raw_config = {"theme_color": "#0395DE"}
        config = validate_resume_config_or_raise(raw_config, registry=None)
        assert isinstance(config, ResumeConfig)


class TestNormalizeWithPaletteFallback:
    """Tests for normalize_with_palette_fallback function."""

    def test_successful_normalization(self) -> None:
        """Test successful normalization without fallback."""
        raw_config = {"theme_color": "#0395DE"}
        registry = PaletteRegistry()
        normalized, palette_meta, validation_config = normalize_with_palette_fallback(
            raw_config, registry=registry
        )
        assert isinstance(normalized, dict)
        assert validation_config == raw_config

    @mock.patch("simple_resume.core.render.plan.normalize_config")
    def test_palette_generation_error_fallback(self, mock_normalize) -> None:
        """Test fallback when PaletteGenerationError occurs."""
        mock_normalize.side_effect = [
            PaletteGenerationError("Palette failed"),
            ({}, None),
        ]
        raw_config = {"palette": "invalid", "theme_color": "#0395DE"}
        registry = PaletteRegistry()
        palette_meta_source = {"palette": {"name": "fallback"}}

        normalized, palette_meta, validation_config = normalize_with_palette_fallback(
            raw_config, registry=registry, palette_meta_source=palette_meta_source
        )

        assert "palette" not in validation_config
        assert palette_meta == {"name": "fallback"}

    @mock.patch("simple_resume.core.render.plan.normalize_config")
    def test_palette_error_no_fallback_source(self, mock_normalize) -> None:
        """Test fallback without palette_meta_source."""
        mock_normalize.side_effect = [
            PaletteGenerationError("Palette failed"),
            ({}, None),
        ]
        raw_config = {"palette": "invalid"}
        registry = PaletteRegistry()

        normalized, palette_meta, validation_config = normalize_with_palette_fallback(
            raw_config, registry=registry
        )

        assert palette_meta is None

    @mock.patch("simple_resume.core.render.plan.normalize_config")
    def test_palette_fallback_logs_warning(
        self, mock_normalize, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that a warning is logged when palette generation fails."""
        mock_normalize.side_effect = [
            PaletteGenerationError("Palette failed"),
            ({}, None),
        ]
        raw_config = {"palette": "my-custom-palette", "theme_color": "#0395DE"}
        registry = PaletteRegistry()

        with caplog.at_level(logging.WARNING):
            normalize_with_palette_fallback(raw_config, registry=registry)

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "WARNING"
        assert "Palette error" in caplog.records[0].message
        assert "my-custom-palette" in caplog.records[0].message

    @mock.patch("simple_resume.core.render.plan.normalize_config")
    def test_palette_lookup_error_fallback(
        self, mock_normalize, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test fallback when PaletteLookupError occurs."""
        mock_normalize.side_effect = [
            PaletteLookupError("Unknown palette: 'foo'"),
            ({}, None),
        ]
        raw_config = {"palette": "foo", "theme_color": "#0395DE"}
        registry = PaletteRegistry()

        with caplog.at_level(logging.WARNING):
            _, _, validation_config = normalize_with_palette_fallback(
                raw_config, registry=registry
            )

        assert "palette" not in validation_config
        assert len(caplog.records) == 1
        assert "PaletteLookupError" in caplog.records[0].message

    @mock.patch("simple_resume.core.render.plan.normalize_config")
    def test_palette_remote_error_fallback(
        self, mock_normalize, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test fallback when PaletteRemoteError occurs."""
        mock_normalize.side_effect = [
            PaletteRemoteError("Remote service unavailable"),
            ({}, None),
        ]
        raw_config = {"palette": "remote-palette", "theme_color": "#0395DE"}
        registry = PaletteRegistry()

        with caplog.at_level(logging.WARNING):
            _, _, validation_config = normalize_with_palette_fallback(
                raw_config, registry=registry
            )

        assert "palette" not in validation_config
        assert len(caplog.records) == 1
        assert "PaletteRemoteError" in caplog.records[0].message

    @mock.patch("simple_resume.core.render.plan.normalize_config")
    def test_fallback_normalization_failure_logs_error(
        self, mock_normalize, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that error is logged when fallback normalization also fails."""
        mock_normalize.side_effect = [
            PaletteGenerationError("Initial palette failed"),
            ValueError("Fallback also failed"),
        ]
        raw_config = {"palette": "bad-palette"}
        registry = PaletteRegistry()

        with caplog.at_level(logging.WARNING):
            with pytest.raises(ValueError, match="Fallback also failed"):
                normalize_with_palette_fallback(raw_config, registry=registry)

        # Should have warning for initial failure and error for fallback failure
        warning_records = [r for r in caplog.records if r.levelname == "WARNING"]
        error_records = [r for r in caplog.records if r.levelname == "ERROR"]
        assert len(warning_records) == 1
        assert len(error_records) == 1
        assert "Fallback normalization also failed" in error_records[0].message


class TestTransformForMode:
    """Tests for transform_for_mode function."""

    def test_latex_mode_returns_copy(self) -> None:
        """Test LATEX mode returns deep copy."""
        content = {"name": "John", "skills": ["Python"]}
        result = transform_for_mode(content, RenderMode.LATEX)
        assert result == content
        assert result is not content  # Should be a copy

    @mock.patch("simple_resume.core.render.plan.render_markdown_content")
    def test_html_mode_calls_markdown_renderer(self, mock_render) -> None:
        """Test HTML mode calls markdown renderer."""
        content = {"name": "John"}
        mock_render.return_value = {"name": "John", "rendered": True}
        result = transform_for_mode(content, RenderMode.HTML)
        mock_render.assert_called_once_with(content)
        assert result == {"name": "John", "rendered": True}


class TestRenderPlanConfig:
    """Tests for RenderPlanConfig dataclass validation."""

    def test_latex_mode_no_validation_required(self) -> None:
        """Test LATEX mode allows None context and template_name."""
        config = ResumeConfig(output_mode="latex")
        plan_config = RenderPlanConfig(
            name="Test",
            mode=RenderMode.LATEX,
            config=config,
            context=None,
            template_name=None,
        )
        assert plan_config.mode == RenderMode.LATEX
        assert plan_config.context is None
        assert plan_config.template_name is None

    def test_html_mode_requires_context(self) -> None:
        """Test HTML mode raises ValueError when context is None."""
        config = ResumeConfig(output_mode="html")
        with pytest.raises(ValueError, match="HTML mode requires context"):
            RenderPlanConfig(
                name="Test",
                mode=RenderMode.HTML,
                config=config,
                context=None,
                template_name="template.html",
            )

    def test_html_mode_requires_template_name(self) -> None:
        """Test HTML mode raises ValueError when template_name is None."""
        config = ResumeConfig(output_mode="html")
        with pytest.raises(ValueError, match="HTML mode requires template_name"):
            RenderPlanConfig(
                name="Test",
                mode=RenderMode.HTML,
                config=config,
                context={"key": "value"},
                template_name=None,
            )

    def test_html_mode_valid_configuration(self) -> None:
        """Test HTML mode accepts valid context and template_name."""
        config = ResumeConfig(output_mode="html")
        plan_config = RenderPlanConfig(
            name="Test",
            mode=RenderMode.HTML,
            config=config,
            context={"key": "value"},
            template_name="html/resume.html",
        )
        assert plan_config.mode == RenderMode.HTML
        assert plan_config.context == {"key": "value"}
        assert plan_config.template_name == "html/resume.html"

    def test_html_mode_empty_context_is_valid(self) -> None:
        """Test HTML mode accepts empty dict {} as context (not None)."""
        config = ResumeConfig(output_mode="html")
        plan_config = RenderPlanConfig(
            name="Test",
            mode=RenderMode.HTML,
            config=config,
            context={},  # Empty dict is valid, None is not
            template_name="html/resume.html",
        )
        assert plan_config.mode == RenderMode.HTML
        assert plan_config.context == {}
        assert plan_config.template_name == "html/resume.html"

    def test_palette_meta_accepts_dict(self) -> None:
        """Test palette_meta accepts dict type."""
        config = ResumeConfig(output_mode="latex")
        plan_config = RenderPlanConfig(
            name="Test",
            mode=RenderMode.LATEX,
            config=config,
            palette_meta={"scheme": "blue", "primary": "#0395DE"},
        )
        assert plan_config.palette_meta == {"scheme": "blue", "primary": "#0395DE"}

    def test_palette_meta_accepts_none(self) -> None:
        """Test palette_meta accepts None."""
        config = ResumeConfig(output_mode="latex")
        plan_config = RenderPlanConfig(
            name="Test",
            mode=RenderMode.LATEX,
            config=config,
            palette_meta=None,
        )
        assert plan_config.palette_meta is None

    def test_base_path_accepts_path_object(self) -> None:
        """Test base_path accepts Path object."""
        config = ResumeConfig(output_mode="latex")
        plan_config = RenderPlanConfig(
            name="Test",
            mode=RenderMode.LATEX,
            config=config,
            base_path=Path("/tmp"),  # noqa: S108
        )
        assert plan_config.base_path == Path("/tmp")  # noqa: S108

    def test_base_path_accepts_string(self) -> None:
        """Test base_path accepts string."""
        config = ResumeConfig(output_mode="latex")
        plan_config = RenderPlanConfig(
            name="Test",
            mode=RenderMode.LATEX,
            config=config,
            base_path="/home/user",
        )
        assert plan_config.base_path == "/home/user"


class TestBuildRenderPlan:
    """Tests for build_render_plan function."""

    def test_latex_render_plan(self) -> None:
        """Test building LATEX render plan."""
        config = ResumeConfig(output_mode="latex")
        plan_config = RenderPlanConfig(
            name="John Doe",
            mode=RenderMode.LATEX,
            config=config,
            base_path=Path("/tmp"),  # noqa: S108
            palette_meta={"scheme": "blue"},
        )

        plan = build_render_plan(plan_config)
        assert plan.mode == RenderMode.LATEX
        assert plan.name == "John Doe"
        assert plan.tex is None
        assert plan.palette_metadata == {"scheme": "blue"}

    def test_html_render_plan(self) -> None:
        """Test building HTML render plan."""
        config = ResumeConfig(output_mode="html")
        context = {"full_name": "John Doe"}
        plan_config = RenderPlanConfig(
            name="John Doe",
            mode=RenderMode.HTML,
            config=config,
            context=context,
            template_name="html/resume.html",
            base_path=Path("/tmp"),  # noqa: S108
        )

        plan = build_render_plan(plan_config)
        assert plan.mode == RenderMode.HTML
        assert plan.template_name == "html/resume.html"
        assert plan.context == context

    def test_html_plan_requires_context(self) -> None:
        """Test HTML plan raises error without context at construction time."""
        config = ResumeConfig(output_mode="html")
        # Validation now happens in RenderPlanConfig.__post_init__
        with pytest.raises(ValueError, match="HTML mode requires context"):
            RenderPlanConfig(
                name="John Doe",
                mode=RenderMode.HTML,
                config=config,
                template_name="template.html",
            )

    def test_html_plan_requires_template_name(self) -> None:
        """Test HTML plan raises error without template_name at construction time."""
        config = ResumeConfig(output_mode="html")
        # Validation now happens in RenderPlanConfig.__post_init__
        with pytest.raises(ValueError, match="HTML mode requires template_name"):
            RenderPlanConfig(
                name="John Doe",
                mode=RenderMode.HTML,
                config=config,
                context={"name": "John"},
            )


class TestPrepareRenderData:
    """Tests for prepare_render_data function."""

    def test_missing_config_raises_error(self) -> None:
        """Test missing config section raises ValueError."""
        source: dict[str, Any] = {}
        with pytest.raises(ValueError, match="missing or malformed config section"):
            prepare_render_data(source)

    def test_invalid_config_raises_error(self) -> None:
        """Test invalid config type raises ValueError."""
        source = {"config": "not a dict"}
        with pytest.raises(ValueError, match="missing or malformed config section"):
            prepare_render_data(source)

    @mock.patch("simple_resume.core.render.plan.normalize_with_palette_fallback")
    @mock.patch("simple_resume.core.render.plan.validate_resume_config_or_raise")
    def test_latex_render_plan_creation(self, mock_validate, mock_normalize) -> None:
        """Test creation of LATEX render plan."""
        source = {
            "config": {"output_mode": "latex", "theme_color": "#0395DE"},
            "full_name": "John Doe",
        }

        mock_normalize.return_value = ({"output_mode": "latex"}, None, {})
        mock_validate.return_value = ResumeConfig(output_mode="latex")

        registry = PaletteRegistry()
        plan = prepare_render_data(source, registry=registry)

        assert plan.mode == RenderMode.LATEX
        assert plan.name == "John Doe"

    @mock.patch("simple_resume.core.render.plan.normalize_with_palette_fallback")
    @mock.patch("simple_resume.core.render.plan.validate_resume_config_or_raise")
    @mock.patch("simple_resume.core.render.plan.render_markdown_content")
    def test_html_render_plan_creation(
        self, mock_render, mock_validate, mock_normalize
    ) -> None:
        """Test creation of HTML render plan."""
        source = {
            "config": {"output_mode": "html", "theme_color": "#0395DE"},
            "full_name": "Jane Doe",
            "template": "basic",
        }

        mock_normalize.return_value = ({"output_mode": "html"}, None, {})
        mock_validate.return_value = ResumeConfig(output_mode="html")
        mock_render.return_value = {
            "full_name": "Jane Doe",
            "template": "basic",
        }

        registry = PaletteRegistry()
        plan = prepare_render_data(source, registry=registry, preview=True)

        assert plan.mode == RenderMode.HTML
        assert plan.name == "Jane Doe"
        assert plan.context is not None
        assert plan.context["preview"] is True

    def test_default_registry_creation(self) -> None:
        """Test that None registry creates default."""
        source = {
            "config": {"theme_color": "#0395DE"},
            "full_name": "Test User",
        }

        # Should not raise even with None registry
        plan = prepare_render_data(source, registry=None)
        assert plan is not None
