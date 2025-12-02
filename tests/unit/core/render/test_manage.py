"""Tests for core/render/manage.py - render management functions."""

from __future__ import annotations

from pathlib import Path

from simple_resume.core.constants import RenderMode
from simple_resume.core.models import RenderPlan, ResumeConfig
from simple_resume.core.render.manage import (
    get_template_environment,
    prepare_html_generation_request,
    prepare_pdf_generation_request,
    validate_render_plan,
)


class TestGetTemplateEnvironment:
    """Tests for get_template_environment function."""

    def test_creates_jinja_environment(self, tmp_path: Path) -> None:
        """Test creating a Jinja2 environment."""
        env = get_template_environment(str(tmp_path))
        assert env is not None


class TestPrepareHtmlGenerationRequest:
    """Tests for prepare_html_generation_request function."""

    def test_returns_request_dict(self) -> None:
        """Test that function returns correct request dictionary."""
        render_plan = RenderPlan(
            name="test",
            mode=RenderMode.HTML,
            config=ResumeConfig(),
        )
        output_path = Path("/output/test.html")

        result = prepare_html_generation_request(render_plan, output_path)

        assert result["render_plan"] == render_plan
        assert result["output_path"] == output_path
        assert "filename" in result

    def test_includes_additional_kwargs(self) -> None:
        """Test that additional kwargs are included."""
        render_plan = RenderPlan(
            name="test",
            mode=RenderMode.HTML,
            config=ResumeConfig(),
        )
        output_path = Path("/output/test.html")

        result = prepare_html_generation_request(
            render_plan, output_path, extra_key="extra_value"
        )

        assert result["extra_key"] == "extra_value"


class TestPreparePdfGenerationRequest:
    """Tests for prepare_pdf_generation_request function."""

    def test_returns_request_dict(self) -> None:
        """Test that function returns correct request dictionary."""
        render_plan = RenderPlan(
            name="test",
            mode=RenderMode.HTML,
            config=ResumeConfig(),
        )
        output_path = Path("/output/test.pdf")

        result = prepare_pdf_generation_request(render_plan, output_path)

        assert result["render_plan"] == render_plan
        assert result["output_path"] == output_path
        assert result["open_after"] is False
        assert result["resume_name"] == "test"

    def test_includes_open_after_flag(self) -> None:
        """Test open_after flag is included."""
        render_plan = RenderPlan(
            name="test",
            mode=RenderMode.HTML,
            config=ResumeConfig(),
        )
        output_path = Path("/output/test.pdf")

        result = prepare_pdf_generation_request(
            render_plan, output_path, open_after=True
        )

        assert result["open_after"] is True


class TestValidateRenderPlan:
    """Tests for validate_render_plan function."""

    def test_valid_plan_passes_validation(self) -> None:
        """Test that a valid render plan passes validation."""
        render_plan = RenderPlan(
            name="test",
            mode=RenderMode.HTML,
            config=ResumeConfig(),
            template_name="demo.html",
        )

        result = validate_render_plan(render_plan)

        assert result.is_valid is True
        assert result.errors == []

    def test_none_mode_fails_validation(self) -> None:
        """Test that None mode fails validation."""
        render_plan = RenderPlan(
            name="test",
            mode=None,  # type: ignore[arg-type]  # Intentionally test validation
            config=ResumeConfig(),
        )

        result = validate_render_plan(render_plan)

        assert result.is_valid is False
        assert "Render mode is required" in result.errors

    def test_none_config_fails_validation(self) -> None:
        """Test that None config fails validation."""
        render_plan = RenderPlan(
            name="test",
            mode=RenderMode.HTML,
            config=None,  # type: ignore[arg-type]  # Intentionally test validation
        )

        result = validate_render_plan(render_plan)

        assert result.is_valid is False
        assert "Render config is required" in result.errors

    def test_html_mode_without_template_fails(self) -> None:
        """Test that HTML mode without template name fails validation."""
        render_plan = RenderPlan(
            name="test",
            mode=RenderMode.HTML,
            config=ResumeConfig(),
            template_name=None,
        )

        result = validate_render_plan(render_plan)

        assert result.is_valid is False
        assert "HTML rendering requires a template name" in result.errors
