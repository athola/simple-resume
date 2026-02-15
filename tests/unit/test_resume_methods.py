"""Unit tests for Resume instance methods."""

from __future__ import annotations

import pytest

from simple_resume.core.exceptions import ValidationError
from simple_resume.core.models import RenderMode
from simple_resume.core.resume import Resume
from tests.bdd import Scenario


class TestResumeInstanceMethods:
    """Test Resume instance methods and configuration management."""

    def test_name_property(self) -> None:
        """Test Resume.name property returns the resume name."""
        resume = Resume.from_data({"full_name": "John Doe"})
        assert resume.name is not None
        assert isinstance(resume.name, str)

    def test_with_template_method(self) -> None:
        """Test the with_template method creates new Resume with updated template."""
        raw_data = {
            "full_name": "Test User",
            "template": "resume_with_bars",
            "config": {
                "theme_color": "#0395DE",
            },
        }

        resume = Resume.from_data(raw_data)
        new_resume = resume.with_template("resume_no_bars")

        assert new_resume._data["template"] == "resume_no_bars"
        assert (
            new_resume._data["config"]["theme_color"] == "#0395DE"
        )  # Other config preserved
        assert resume._data["template"] == "resume_with_bars"  # Original unchanged

    def test_with_palette_string(self) -> None:
        """Test the with_palette method with string palette name."""
        raw_data = {
            "full_name": "Test User",
            "config": {"theme_color": "#0395DE"},
        }

        resume = Resume.from_data(raw_data)
        new_resume = resume.with_palette("ocean")

        assert new_resume._data["config"]["color_scheme"] == "ocean"
        assert new_resume._data["config"]["theme_color"] == "#0395DE"

    def test_with_palette_dict(self) -> None:
        """Test the with_palette method with palette dictionary."""
        raw_data = {
            "full_name": "Test User",
            "config": {"theme_color": "#0395DE"},
        }

        palette_dict = {
            "primary": "#1a5490",
            "secondary": "#8ecae6",
            "accent": "#219ebc",
        }

        resume = Resume.from_data(raw_data)
        new_resume = resume.with_palette(palette_dict)

        assert new_resume._data["config"]["palette"] == palette_dict

    def test_with_palette_dict_no_config(self) -> None:
        """Test with_palette creates config when not present."""
        raw_data = {
            "full_name": "Test User",
        }

        palette_dict = {
            "primary": "#1a5490",
            "secondary": "#8ecae6",
        }

        resume = Resume.from_data(raw_data)
        new_resume = resume.with_palette(palette_dict)

        assert "config" in new_resume._data
        assert new_resume._data["config"]["palette"] == palette_dict

    def test_with_config_palette_dict_override(self) -> None:
        """Test with_config when passing palette as dict override."""
        raw_data = {
            "full_name": "Test User",
            "config": {},
        }

        palette = {"primary": "#FF0000", "secondary": "#00FF00"}

        resume = Resume.from_data(raw_data)
        new_resume = resume.with_config(palette=palette)

        assert new_resume._data["config"]["palette"] == palette
        assert new_resume._data["config"]["palette"] is not palette

    def test_with_config_overrides(self) -> None:
        """Test the with_config method applies configuration overrides."""
        raw_data = {
            "full_name": "Test User",
            "config": {
                "theme_color": "#0395DE",
                "page_width": 210,
            },
        }

        resume = Resume.from_data(raw_data)
        new_resume = resume.with_config(
            theme_color="#FF0000", page_height=300, font_size="12pt"
        )

        config = new_resume._data["config"]
        assert config["theme_color"] == "#FF0000"  # Overridden
        assert config["page_height"] == 300  # Added
        assert config["page_width"] == 210  # Preserved
        assert config["font_size"] == "12pt"  # Added

    def test_preview_method(self) -> None:
        """Test the preview method sets preview mode."""
        raw_data = {
            "full_name": "Test User",
            "template": "resume_with_bars",
            "config": {},
        }

        resume = Resume.from_data(raw_data)
        preview_resume = resume.preview()

        assert preview_resume._is_preview is True
        assert resume._is_preview is False

    def test_validate_method_success(self) -> None:
        """Test the validate method with valid resume data."""
        raw_data = {
            "full_name": "Test User",
            "config": {
                "template": "resume_with_bars",
                "page_width": 210,
                "theme_color": "#0395DE",
            },
        }

        resume = Resume.from_data(raw_data)
        result = resume.validate()

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.normalized_config is not None

    def test_validate_method_failure(self) -> None:
        """Test the validate method with invalid resume data."""
        raw_data = {
            "full_name": "Test User",
            "config": {
                "template": "resume_with_bars",
                "page_width": -10,
                "theme_color": "invalid_color",
            },
        }

        resume = Resume.from_data(raw_data)
        result = resume.validate()

        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_or_raise_raises_on_invalid(self) -> None:
        """Test validate_or_raise raises ValidationError on invalid data."""
        raw_data = {
            "full_name": "Test User",
            "config": {
                "template": "resume_with_bars",
                "page_width": -10,
            },
        }

        resume = Resume.from_data(raw_data)
        with pytest.raises(ValidationError, match="Resume validation failed"):
            resume.validate_or_raise()

    def test_prepare_plan_html_mode(self) -> None:
        """Test render plan preparation for HTML mode."""
        raw_data = {
            "full_name": "Test User",
            "config": {
                "template": "resume_with_bars",
                "output_mode": "html",
                "theme_color": "#0395DE",
            },
        }

        resume = Resume.from_data(raw_data)
        plan = resume.prepare_render_plan(preview=False)

        assert plan.mode is RenderMode.HTML
        assert plan.name == "Test User"
        assert plan.config.output_mode == "html"
        assert plan.base_path is not None

    def test_prepare_plan_latex_mode(self) -> None:
        """Test render plan preparation for LaTeX mode."""
        raw_data = {
            "full_name": "Test User",
            "config": {
                "output_mode": "latex",
                "theme_color": "#0395DE",
            },
        }

        resume = Resume.from_data(raw_data)
        plan = resume.prepare_render_plan(preview=False)

        assert plan.mode is RenderMode.LATEX
        assert plan.name == "Test User"
        assert plan.config.output_mode == "latex"
        assert plan.tex is None
        assert plan.base_path is not None

    def test_prepare_plan_palette_fallback(self, story: Scenario) -> None:
        """Test render plan preparation with palette generation fallback."""
        story.given("the config includes an invalid palette generator block")
        raw_data = {
            "full_name": "Test User",
            "config": {
                "template": "resume_with_bars",
                "palette": {
                    "source": "generator",
                    "size": 3,
                    "hue_range": [0],
                    "luminance_range": [0.3, 0.8],
                },
                "theme_color": "#0395DE",
                "sidebar_color": "#F6F6F6",
            },
            "meta": {"palette": {"source": "user", "name": "custom"}},
        }

        resume = Resume.from_data(raw_data)
        story.when("prepare_plan executes for HTML mode")
        plan = resume.prepare_render_plan(preview=False)

        story.then("palette metadata falls back to user-supplied meta")
        assert plan.palette_metadata == {"source": "user", "name": "custom"}
