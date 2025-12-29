"""Tests for core/render/manage.py - render management functions."""

from __future__ import annotations

from pathlib import Path

from simple_resume.core.constants import RenderMode
from simple_resume.core.models import RenderPlan, ResumeConfig
from simple_resume.core.render.manage import (
    dynamic_font_size,
    get_template_environment,
    prepare_html_generation_request,
    prepare_pdf_generation_request,
    validate_render_plan,
)


class TestDynamicFontSize:
    """Tests for dynamic_font_size function - safety margin for long text."""

    def test_long_text_returns_smaller_than_max(self) -> None:
        """Test that very long text returns font size smaller than max.

        Long text like job titles with company names should scale down
        to fit within the available width, verifying the safety margin works.
        """
        # Test with a realistic long job title
        company = "International Business Machines Corporation"
        long_text = f"Senior Software Engineer at {company}"
        available_width_mm = 100.0  # Typical resume body width
        max_font_pt = 11.5
        min_font_pt = 8.0

        result = dynamic_font_size(
            long_text,
            available_width_mm,
            max_font_pt=max_font_pt,
            min_font_pt=min_font_pt,
        )

        # Extract numeric value from "X.Xpt" format
        font_size = float(result.replace("pt", ""))

        # Long text should require scaling down
        assert font_size < max_font_pt

    def test_font_size_respects_minimum_bound(self) -> None:
        """Test that returned font size never goes below min_font_pt.

        Even with extremely long text and small available width,
        the function should enforce the minimum font size constraint.
        """
        # Extremely long text with tight width constraint
        company = "International Business Machines Corporation"
        very_long_text = f"Senior Principal Staff Software Engineer at {company}"
        available_width_mm = 50.0  # Very small width
        max_font_pt = 11.5
        min_font_pt = 8.0

        result = dynamic_font_size(
            very_long_text,
            available_width_mm,
            max_font_pt=max_font_pt,
            min_font_pt=min_font_pt,
        )

        # Extract numeric value from "X.Xpt" format
        font_size = float(result.replace("pt", ""))

        # Should never go below minimum
        assert font_size >= min_font_pt

    def test_typical_resume_width_with_long_text(self) -> None:
        """Test with 100mm available width (typical resume body) and long text.

        This tests the common real-world scenario where typical job titles
        need to fit within standard resume column widths.
        """
        # Moderately long job title
        text = "Lead Software Engineer at Microsoft"
        available_width_mm = 100.0  # Standard resume body width
        max_font_pt = 11.5
        min_font_pt = 8.0

        result = dynamic_font_size(
            text,
            available_width_mm,
            max_font_pt=max_font_pt,
            min_font_pt=min_font_pt,
        )

        # Extract numeric value from "X.Xpt" format
        font_size = float(result.replace("pt", ""))

        # Font size should be within valid range
        assert min_font_pt <= font_size <= max_font_pt
        # Result should include "pt" suffix
        assert result.endswith("pt")


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
