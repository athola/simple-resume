"""Unit tests for core resume data models."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from simple_resume.core.models import (
    RenderMode,
    RenderPlan,
    ResumeConfig,
    ValidationResult,
)


class TestResumeConfigDataClass:
    """Test ResumeConfig dataclass functionality."""

    def test_resume_config_immutability(self) -> None:
        """Test that ResumeConfig is immutable (frozen)."""
        config = ResumeConfig(page_width=210, page_height=297)

        with pytest.raises(FrozenInstanceError):
            config.page_width = 300  # type: ignore[misc]

    def test_resume_config_equality(self) -> None:
        """Test ResumeConfig equality comparison."""
        config1 = ResumeConfig(page_width=210, page_height=297, theme_color="#0395DE")
        config2 = ResumeConfig(page_width=210, page_height=297, theme_color="#0395DE")
        config3 = ResumeConfig(page_width=210, page_height=297, theme_color="#FF0000")

        assert config1 == config2
        assert config1 != config3

    def test_resume_config_default_values(self) -> None:
        """Test ResumeConfig default values."""
        config = ResumeConfig()

        assert config.page_width is None
        assert config.page_height is None
        assert config.sidebar_width is None
        assert config.output_mode == "markdown"
        assert config.template == "resume_no_bars"
        assert config.theme_color == "#0395DE"
        assert config.sidebar_color == "#F6F6F6"

    def test_resume_config_section_icon_defaults(self) -> None:
        """Test section icon layout fields have correct float defaults."""
        config = ResumeConfig()

        # Section heading icon layout fields (all floats, no mm suffix)
        assert config.section_icon_circle_size == 7.8
        assert isinstance(config.section_icon_circle_size, float)

        assert config.section_icon_circle_x_offset == 0
        assert isinstance(config.section_icon_circle_x_offset, (int, float))

        assert config.section_icon_design_size == 3.5
        assert isinstance(config.section_icon_design_size, float)

        assert config.section_icon_design_x_offset == 0
        assert isinstance(config.section_icon_design_x_offset, (int, float))

        assert config.section_icon_design_y_offset == 0
        assert isinstance(config.section_icon_design_y_offset, (int, float))

        assert config.section_heading_text_margin == -6
        assert isinstance(config.section_heading_text_margin, (int, float))

    def test_resume_config_contact_icon_defaults(self) -> None:
        """Test contact icon layout fields have correct float defaults."""
        config = ResumeConfig()

        # Contact icon customization fields (all floats, no mm suffix)
        assert config.contact_icon_size == 5
        assert isinstance(config.contact_icon_size, (int, float))

        assert config.contact_icon_margin_top == 0.5
        assert isinstance(config.contact_icon_margin_top, float)

        assert config.contact_icon_margin_right == 2
        assert isinstance(config.contact_icon_margin_right, (int, float))

        assert config.contact_icon_gap == 4
        assert isinstance(config.contact_icon_gap, (int, float))

    def test_resume_config_with_custom_icon_values(self) -> None:
        """Test custom icon layout values are preserved in ResumeConfig."""
        config = ResumeConfig(
            section_icon_circle_size=10.5,
            section_icon_design_size=5.0,
            contact_icon_size=6.5,
            contact_icon_margin_top=1.0,
        )

        assert config.section_icon_circle_size == 10.5
        assert config.section_icon_design_size == 5.0
        assert config.contact_icon_size == 6.5
        assert config.contact_icon_margin_top == 1.0


class TestRenderPlanDataClass:
    """Test RenderPlan dataclass functionality."""

    def test_plan_html_mode(self) -> None:
        """Test RenderPlan creation for HTML mode."""
        config = ResumeConfig(page_width=210, page_height=297)
        context = {"title": "Test Resume", "content": "Test content"}

        plan = RenderPlan(
            name="test_resume",
            mode=RenderMode.HTML,
            config=config,
            template_name="html/resume_no_bars.html",
            context=context,
            base_path="/test",
        )

        assert plan.name == "test_resume"
        assert plan.mode is RenderMode.HTML
        assert plan.config == config
        assert plan.template_name == "html/resume_no_bars.html"
        assert plan.context == context
        assert plan.base_path == "/test"
        assert plan.tex is None
        assert plan.palette_metadata is None

    def test_plan_latex_mode(self) -> None:
        """Test RenderPlan creation for LaTeX mode."""
        config = ResumeConfig(output_mode="latex")
        tex_content = "\\documentclass{article}"

        plan = RenderPlan(
            name="test_resume",
            mode=RenderMode.LATEX,
            config=config,
            tex=tex_content,
            base_path="/test",
        )

        assert plan.mode is RenderMode.LATEX
        assert plan.tex == tex_content
        assert plan.template_name is None
        assert plan.context is None

    def test_plan_immutability(self) -> None:
        """Test that RenderPlan is immutable (frozen)."""
        config = ResumeConfig()
        plan = RenderPlan(
            name="test", mode=RenderMode.HTML, config=config, base_path="/test"
        )

        with pytest.raises(FrozenInstanceError):
            plan.name = "new_name"  # type: ignore[misc]


class TestValidationResult:
    """Test ValidationResult functionality."""

    def test_validation_result_success(self) -> None:
        """Test successful validation result."""
        config = ResumeConfig(page_width=210)
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            normalized_config=config,
        )

        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
        assert result.normalized_config == config

    def test_validation_result_failure(self) -> None:
        """Test failed validation result."""
        result = ValidationResult(
            is_valid=False,
            errors=["Invalid page width"],
            warnings=["Deprecated field used"],
        )

        assert result.is_valid is False
        assert result.errors == ["Invalid page width"]
        assert result.warnings == ["Deprecated field used"]
        assert result.normalized_config is None


class TestRenderMode:
    """Test RenderMode enum behavior."""

    def test_render_mode_values(self) -> None:
        """Test valid RenderMode values."""
        valid_modes: list[RenderMode] = [RenderMode.HTML, RenderMode.LATEX]
        assert RenderMode.HTML in valid_modes
        assert RenderMode.LATEX in valid_modes

    def test_plan_mode_type_safety(self) -> None:
        """Test that RenderPlan mode accepts only valid RenderMode values."""
        config = ResumeConfig()

        # These should work
        plan1 = RenderPlan(
            name="test1", mode=RenderMode.HTML, config=config, base_path="/test"
        )
        plan2 = RenderPlan(
            name="test2", mode=RenderMode.LATEX, config=config, base_path="/test"
        )

        assert plan1.mode is RenderMode.HTML
        assert plan2.mode is RenderMode.LATEX
