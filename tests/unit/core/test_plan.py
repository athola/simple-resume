from __future__ import annotations

import tempfile
from typing import Any

import pytest

from simple_resume.core import plan
from simple_resume.core.models import RenderMode, ResumeConfig
from simple_resume.exceptions import ValidationError
from simple_resume.palettes.exceptions import PaletteGenerationError
from tests.bdd import Scenario


class TestPlanValidation:
    def test_validate_config_valid_config(self) -> None:
        raw_config = {
            "page_width": 210,
            "page_height": 297,
            "sidebar_width": 60,
            "theme_color": "#0395DE",
            "sidebar_color": "#F6F6F6",
        }

        result = plan.validate_resume_config(raw_config)

        assert result.is_valid
        assert result.errors == []
        assert result.warnings == []
        assert result.normalized_config is not None
        assert result.normalized_config.template == "resume_no_bars"

    def test_validate_config_invalid_page_dimensions(self) -> None:
        raw_config = {"page_width": -10, "page_height": 0}

        result = plan.validate_resume_config(raw_config)

        assert not result.is_valid
        assert any("positive" in error.lower() for error in result.errors)
        assert result.normalized_config is None

    def test_validate_config_sidebar_wider_than_page(self) -> None:
        raw_config = {"page_width": 100, "sidebar_width": 150}

        result = plan.validate_resume_config(raw_config)

        assert not result.is_valid
        assert any("sidebar width" in error.lower() for error in result.errors)

    def test_validate_config_invalid_colors(self) -> None:
        raw_config = {"theme_color": "invalid_color", "sidebar_color": "#ZZZZZZ"}

        result = plan.validate_resume_config(raw_config)

        assert not result.is_valid
        assert any("theme_color" in error for error in result.errors)
        assert any("sidebar_color" in error for error in result.errors)

    def test_validate_config_defaults_filling(self) -> None:
        result = plan.validate_resume_config({})

        assert result.is_valid
        assert result.normalized_config is not None
        assert result.normalized_config.theme_color == "#0395DE"
        assert result.normalized_config.template == "resume_no_bars"

    def test_validate_config_string_numeric_conversion(self) -> None:
        raw_config = {
            "page_width": "210",
            "page_height": "297.5",
            "sidebar_width": "60",
        }

        result = plan.validate_resume_config(raw_config)

        assert result.is_valid
        assert result.normalized_config is not None
        assert isinstance(result.normalized_config.page_width, int)
        assert isinstance(result.normalized_config.page_height, float)

    def test_validate_config_with_filename_context(self) -> None:
        filename = "test_resume.yaml"
        raw_config = {"page_width": -10}

        result = plan.validate_resume_config(raw_config, filename=filename)

        assert not result.is_valid
        assert any(filename in error for error in result.errors)

    def test_validate_config_or_raise_success(self) -> None:
        raw_config = {
            "page_width": 210,
            "page_height": 297,
            "sidebar_width": 60,
            "theme_color": "#0395DE",
            "sidebar_color": "#F6F6F6",
        }

        config = plan.validate_resume_config_or_raise(
            raw_config, filename="test_config.yaml"
        )

        assert isinstance(config, ResumeConfig)
        assert config.page_width == 210
        assert config.page_height == 297

    def test_validate_config_or_raise_failure(self) -> None:
        raw_config = {
            "page_width": -100,
            "page_height": 297,
            "sidebar_width": 60,
            "theme_color": "#0395DE",
            "sidebar_color": "#F6F6F6",
        }

        with pytest.raises(ValidationError) as exc_info:
            plan.validate_resume_config_or_raise(
                raw_config, filename="test_config.yaml"
            )

        exc_value = exc_info.value
        assert isinstance(exc_value, ValidationError)
        assert "page_width" in str(exc_value)
        assert exc_value.filename == "test_config.yaml"


class TestPlanHelpers:
    def test_normalize_with_palette_fallback_success(self, story: Scenario) -> None:
        story.case(
            given="a raw config without palette data",
            when="normalize_with_palette_fallback runs",
            then="the normalized config matches the input and metadata stays empty",
        )
        raw_config = {"template": "resume_no_bars"}

        normalized, palette_meta, config_for_validation = (
            plan.normalize_with_palette_fallback(raw_config)
        )

        assert normalized["template"] == "resume_no_bars"
        assert palette_meta is None
        assert config_for_validation is raw_config

    def test_normalize_with_palette_fallback_uses_meta(
        self, story: Scenario, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        story.case(
            given="palette normalization fails and fallback metadata exists",
            when="normalize_with_palette_fallback runs",
            then="the palette field is stripped and fallback metadata returned",
        )

        raw_config = {"template": "resume_no_bars", "palette": {"source": "custom"}}
        fallback_meta = {"source": "registry", "name": "ocean"}
        captured_calls: list[dict[str, Any]] = []

        def fake_normalize(
            config: dict[str, Any],
        ) -> tuple[dict[str, Any], dict[str, Any]]:
            captured_calls.append(config.copy())
            if "palette" in config:
                raise PaletteGenerationError("palette failure")
            return {"template": config.get("template", "default")}, {"verified": True}

        monkeypatch.setattr(plan, "normalize_config", fake_normalize)

        normalized, palette_meta, config_for_validation = (
            plan.normalize_with_palette_fallback(
                raw_config,
                palette_meta_source={"palette": fallback_meta},
            )
        )

        assert captured_calls[0]["palette"] == {"source": "custom"}
        assert "palette" not in captured_calls[1]
        assert normalized == {"template": "resume_no_bars"}
        assert palette_meta == fallback_meta
        assert "palette" not in config_for_validation

    def test_transform_for_mode_latex_returns_copy(self) -> None:
        original = {"nested": {"value": 1}}

        transformed = plan.transform_for_mode(original, RenderMode.LATEX)

        assert transformed == original
        assert transformed is not original
        assert transformed["nested"] is not original["nested"]

    def test_transform_for_mode_html_renders_markdown(self) -> None:
        original = {"description": "**Bold**"}

        transformed = plan.transform_for_mode(original, RenderMode.HTML)

        description = transformed["description"]
        assert "font-weight: 700 !important;" in description
        assert "Bold</strong>" in description

    def test_transform_for_mode_html_prefers_bold_color(self) -> None:
        original = {
            "description": "**Dark Accent**",
            "config": {"bold_color": "#123456", "frame_color": "#111827"},
        }

        transformed = plan.transform_for_mode(original, RenderMode.HTML)

        description = transformed["description"]
        assert "color: #123456" in description

    def test_transform_for_mode_html_falls_back_to_frame_color(self) -> None:
        original = {
            "description": "**Dark Accent**",
            "config": {"frame_color": "#111827"},
        }

        transformed = plan.transform_for_mode(original, RenderMode.HTML)

        description = transformed["description"]
        assert "color: #111827" in description

    def test_build_render_plan_latex_mode(self) -> None:
        config = plan.validate_resume_config_or_raise({"output_mode": "latex"})

        render_plan = plan.build_render_plan(
            "Test",
            RenderMode.LATEX,
            config,
            context=None,
            base_path=tempfile.gettempdir(),
            palette_meta={"palette": "meta"},
        )

        assert render_plan.mode is RenderMode.LATEX
        assert render_plan.template_name is None
        assert render_plan.context is None
        assert render_plan.palette_metadata == {"palette": "meta"}

    def test_build_render_plan_html_requires_context(self) -> None:
        config = plan.validate_resume_config_or_raise({})

        with pytest.raises(ValueError, match="context"):
            plan.build_render_plan(
                "Test",
                RenderMode.HTML,
                config,
                context=None,
                base_path=tempfile.gettempdir(),
                template_name="resume.html",
            )

    def test_build_render_plan_html_requires_template(self) -> None:
        config = plan.validate_resume_config_or_raise({})

        with pytest.raises(ValueError, match="template"):
            plan.build_render_plan(
                "Test",
                RenderMode.HTML,
                config,
                context={"key": "value"},
                base_path=tempfile.gettempdir(),
                template_name=None,
            )

    def test_build_render_plan_html_success(self) -> None:
        config = plan.validate_resume_config_or_raise({})
        context = {"key": "value"}

        render_plan = plan.build_render_plan(
            "Test",
            RenderMode.HTML,
            config,
            context,
            base_path=tempfile.gettempdir(),
            template_name="resume.html",
            palette_meta={"palette": "meta"},
        )

        assert render_plan.mode is RenderMode.HTML
        assert render_plan.context == context
        assert render_plan.template_name == "resume.html"
        assert render_plan.palette_metadata == {"palette": "meta"}

    @pytest.mark.parametrize(
        "width,expected_type",
        [
            (210, int),
            ("210", int),
            (210.5, float),
            ("210.5", float),
            (None, type(None)),
        ],
    )
    def test_config_numeric_conversion(self, width: Any, expected_type: type) -> None:
        raw_config = {"page_width": width}
        result = plan.validate_resume_config(raw_config)

        if width is not None and result.is_valid:
            assert result.normalized_config is not None
            actual_type = type(result.normalized_config.page_width)
            assert actual_type == expected_type

    @pytest.mark.parametrize(
        "page_width,sidebar_width",
        [
            (210, 50),
            (100, 99),
            (100, 100),
            (100, 101),
        ],
    )
    def test_sidebar_width_validation(
        self, page_width: int, sidebar_width: int
    ) -> None:
        raw_config = {"page_width": page_width, "sidebar_width": sidebar_width}
        result = plan.validate_resume_config(raw_config)

        if sidebar_width >= page_width:
            assert not result.is_valid
