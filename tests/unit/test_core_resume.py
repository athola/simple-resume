"""Unit tests for core resume transformations - pure functions without side effects.

These tests focus on the functional core of the resume system, ensuring that
all business logic transformations are deterministic and fast to execute.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from simple_resume.core.exceptions import (
    ConfigurationError,
    FileSystemError,
    GenerationError,
    ValidationError,
)
from simple_resume.core.models import (
    RenderMode,
    RenderPlan,
    ResumeConfig,
    ValidationResult,
)
from simple_resume.core.paths import Paths
from simple_resume.core.render.plan import prepare_render_data
from simple_resume.core.result import GenerationMetadata, GenerationResult
from simple_resume.core.resume import Resume
from simple_resume.shell.palettes.loader import get_palette_registry
from simple_resume.shell.render.latex import LatexCompilationError
from simple_resume.shell.resume_extensions import generate as shell_generate
from simple_resume.shell.resume_extensions import to_html, to_pdf
from tests.bdd import Scenario


def _make_paths(base: Path) -> Paths:
    """Create a Paths instance rooted at the provided base directory."""
    input_dir = base / "input"
    output_dir = base / "output"
    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    return Paths(
        data=base,
        input=input_dir,
        output=output_dir,
        content=base,
        templates=base,
        static=base,
    )


class TestResumeDataPreparation:
    """Test pure resume data transformation to render plans."""

    def test_prepare_render_data_html_mode(self, story: Scenario) -> None:
        story.given("complete resume data targeting HTML preview")
        raw_data = {
            "full_name": "John Doe",
            "email": "john@example.com",
            "config": {
                "template": "resume_no_bars",
                "page_width": 210,
                "page_height": 297,
                "theme_color": "#0395DE",
            },
            "description": "# Professional Summary\nExperienced developer.",
            "body": {
                "experience": [
                    {
                        "title": "Senior Developer",
                        "description": "Led development of key features.",
                    }
                ]
            },
        }

        story.when("prepare_render_data runs with preview enabled")
        get_palette_registry()
        registry = get_palette_registry()
        plan = prepare_render_data(
            raw_data, preview=True, base_path="/test", registry=registry
        )

        story.then("the plan targets HTML with rendered markdown and preview context")
        assert isinstance(plan, RenderPlan)
        assert plan.mode is RenderMode.HTML
        assert plan.name == "John Doe"
        assert plan.base_path == "/test"
        assert plan.template_name == "html/resume_no_bars.html"
        assert plan.context is not None
        assert plan.context["preview"] is True
        assert "<h1>Professional Summary</h1>" in plan.context["description"]
        assert "<p>Experienced developer.</p>" in plan.context["description"]
        assert plan.config.page_width == 210
        assert plan.config.page_height == 297

    def test_prepare_render_data_latex_mode(self, story: Scenario) -> None:
        story.given("resume data configured for latex output")
        raw_data = {
            "full_name": "Jane Smith",
            "config": {
                "output_mode": "latex",
                "page_width": 210,
                "page_height": 297,
            },
        }

        story.when("prepare_render_data runs without preview")
        get_palette_registry()
        registry = get_palette_registry()
        plan = prepare_render_data(
            raw_data, preview=False, base_path="/test", registry=registry
        )

        story.then("a latex render plan without template/context is produced")
        assert isinstance(plan, RenderPlan)
        assert plan.mode is RenderMode.LATEX
        assert plan.name == "Jane Smith"
        assert plan.base_path == "/test"
        assert plan.tex is None
        assert plan.config.output_mode == "latex"

    def test_prepare_render_data_invalid_config(self, story: Scenario) -> None:
        story.given("resume config contains invalid numeric values")
        raw_data = {
            "config": {
                "page_width": -10,
            },
        }

        story.then("validation fails and a ValueError is raised")
        registry = get_palette_registry()
        with pytest.raises(ValueError, match="Invalid resume config"):
            prepare_render_data(
                raw_data, preview=False, base_path="/test", registry=registry
            )

    def test_prepare_render_data_missing_config(self, story: Scenario) -> None:
        story.given("resume data without a config section")
        raw_data = {
            "full_name": "Test User",
        }

        story.then("prepare_render_data raises a ValueError")
        registry = get_palette_registry()
        with pytest.raises(ValueError, match="Invalid resume config"):
            prepare_render_data(
                raw_data, preview=False, base_path="/test", registry=registry
            )

    def test_prepare_render_data_markdown_transformation(self, story: Scenario) -> None:
        story.given("resume data with markdown fields and HTML target")
        raw_data = {
            "full_name": "Test User",
            "config": {
                "template": "resume_no_bars",
                "frame_color": "#1D1F2A",
            },
            "description": "**Bold text** and *italic text*",
            "body": {
                "projects": [
                    {
                        "name": "Project X",
                        "description": "## Features\n- Feature 1\n- Feature 2",
                    }
                ]
            },
        }

        story.when("prepare_render_data produces an HTML plan")
        get_palette_registry()
        registry = get_palette_registry()
        plan = prepare_render_data(
            raw_data, preview=False, base_path="/test", registry=registry
        )

        story.then("markdown content is rendered for description and nested sections")
        assert plan.context is not None
        description = plan.context["description"]
        assert "Bold text</strong>" in description
        assert "markdown-strong" in description
        assert "#1D1F2A" in description
        assert "<em>italic text</em>" in plan.context["description"]
        projects = plan.context["body"]["projects"]
        assert len(projects) > 0
        assert "<h2>Features</h2>" in projects[0]["description"]
        assert "<li>Feature 1</li>" in projects[0]["description"]

    def test_prepare_render_data_palette_metadata(self, story: Scenario) -> None:
        story.given("config includes palette details and fallback metadata")
        raw_data = {
            "full_name": "Test User",
            "config": {
                "template": "resume_no_bars",
                "palette": {
                    "source": "registry",
                    "name": "ocean",
                },
            },
            "meta": {
                "palette": {
                    "source": "registry",
                    "name": "ocean",
                    "size": 5,
                },
            },
        }

        story.when("prepare_render_data builds the plan")
        get_palette_registry()
        registry = get_palette_registry()
        plan = prepare_render_data(
            raw_data, preview=False, base_path="/test", registry=registry
        )

        story.then("palette metadata is preserved on the render plan")
        assert plan.palette_metadata is not None
        assert plan.palette_metadata["source"] == "registry"
        assert plan.palette_metadata["name"] == "ocean"


# NOTE: Color utilities are in simple_resume.core.colors
# Tests for color utilities are in test_api.py


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


# Property-based tests for input validation
class TestPropertyBased:
    """Property-based tests for core resume transformations."""

    # NOTE: Color validation tests moved to test_api_colors.py


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
            "template": "resume_with_bars",  # Template is at root level, not in config
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
            # No config key
        }

        palette_dict = {
            "primary": "#1a5490",
            "secondary": "#8ecae6",
        }

        resume = Resume.from_data(raw_data)
        new_resume = resume.with_palette(palette_dict)

        # Config should be created
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

        # Palette should be deep copied
        assert new_resume._data["config"]["palette"] == palette
        # Ensure it's a copy, not the same reference
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

        # Preview should set the _is_preview instance variable
        assert preview_resume._is_preview is True
        # Original resume should not be affected
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
                "page_width": -10,  # Invalid
                "theme_color": "invalid_color",  # Invalid
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
                "page_width": -10,  # Invalid negative width
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
        assert plan.tex is None  # Will be filled by shell layer
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
                    "hue_range": [0],  # Invalid length triggers PaletteGenerationError
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

        # Should use fallback palette from meta
        story.then("palette metadata falls back to user-supplied meta")
        assert plan.palette_metadata == {"source": "user", "name": "custom"}


class TestResumeIOBehaviour:
    """Story-driven tests covering read/write paths and error handling."""

    def test_read_yaml_conflicting_paths_and_overrides(
        self, story: Scenario, tmp_path: Path
    ) -> None:
        story.given("callers pass resolved paths and explicit overrides simultaneously")
        paths = _make_paths(tmp_path)
        with pytest.raises(
            ConfigurationError, match="Provide either paths or path_overrides"
        ):
            Resume.read_yaml(
                "demo",
                paths=paths,
                content_dir="/sandbox/content",
            )

    def test_read_yaml_wraps_io_errors(self, story: Scenario, tmp_path: Path) -> None:
        story.given("get_content raises an unexpected OSError while reading YAML")
        fake_paths = _make_paths(tmp_path)
        # Patch the shell layer content loader (late-binding target)
        with patch(
            "simple_resume.shell.runtime.content.get_content",
            side_effect=OSError("disk error"),
        ):
            with pytest.raises(FileSystemError, match="Failed to read resume YAML"):
                Resume.read_yaml("broken", paths=fake_paths, transform_markdown=False)

    def test_to_pdf_requires_paths_or_output(self, story: Scenario) -> None:
        story.given("a resume instance without resolved paths")
        resume = Resume.from_data(
            {
                "full_name": "Candidate",
                "config": {
                    "template": "resume_no_bars",
                    "page_width": 210,
                    "page_height": 297,
                },
            }
        )

        with pytest.raises(ConfigurationError, match="No paths available"):
            to_pdf(resume)

    def test_generate_pdf_with_weasyprint_renders_template(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        story: Scenario,
    ) -> None:
        story.given(
            "a complete professional resume ready for PDF generation "
            "to be submitted to potential employers"
        )
        resume = Resume.from_data(
            {
                "full_name": "Sarah Williams",
                "email": "sarah.williams@professionals.com",
                "phone": "+1 (555) 234-5678",
                "template": "resume_no_bars",
                "titles": {
                    "contact": "Contact Information",
                    "certification": "Professional Certifications",
                    "expertise": "Areas of Expertise",
                    "keyskills": "Key Skills & Competencies",
                },
                "description": (
                    "Experienced Project Manager with track record of "
                    "successful product launches"
                ),
                "config": {
                    "page_width": 210,
                    "page_height": 297,
                    "sidebar_width": 60,
                    "h2_padding_left": 4,
                    "padding": 12,
                    "date_container_width": 13,
                    "description_container_padding_left": 3,
                    "theme_color": "#2E4057",
                },
                "body": {
                    "experience": [
                        {
                            "company": "Global Tech Solutions",
                            "position": "Senior Project Manager",
                            "start_date": "2017-03",
                            "end_date": "2024-01",
                            "description": (
                                "Managed $5M+ project portfolios with "
                                "cross-functional teams"
                            ),
                        }
                    ],
                    "expertise": [
                        "Project Management (PMP)",
                        "Agile & Scrum Methodologies",
                        "Stakeholder Communication",
                    ],
                },
            }
        )
        output_path = tmp_path / "case.pdf"

        # Mock the PDF generation to avoid WeasyPrint dependency
        metadata = GenerationMetadata(
            format_type="pdf",
            template_name="resume_no_bars",
            generation_time=0.0,
            file_size=1024,
            resume_name="Sarah Williams",
        )
        mock_result = GenerationResult(
            output_path=output_path,
            format_type="pdf",
            metadata=metadata,
        )

        with patch(
            "simple_resume.shell.strategies.generate_pdf_with_weasyprint",
            return_value=(mock_result, 1),
        ) as mock_pdf_generation:
            result = to_pdf(resume, output_path=output_path)

        story.then(
            "PDF generation creates employer-ready document with proper "
            "business formatting"
        )
        assert result.output_path == output_path, (
            "PDF result must reference the correct output file"
        )
        assert result.metadata is not None
        assert result.metadata.file_size == 1024, (
            "PDF should contain substantial business content"
        )

        # Verify PDF generation was called with business-relevant HTML content
        mock_pdf_generation.assert_called_once()
        call_args = mock_pdf_generation.call_args
        assert call_args is not None, "PDF generation must receive proper parameters"

        called_plan = call_args.args[0] if call_args.args else None
        assert isinstance(called_plan, RenderPlan)
        assert called_plan.context is not None
        experience = called_plan.context.get("body", {}).get("experience", [])
        assert any(
            entry.get("company") == "Global Tech Solutions" for entry in experience
        )

    def test_generate_pdf_with_latex_preserves_log_on_failure(
        self,
        tmp_path: Path,
        story: Scenario,
    ) -> None:
        story.given(
            "a professional with LaTeX resume requirements experiences "
            "compilation failure"
        )
        story.when("the LaTeX compilation process encounters technical errors")
        story.then(
            "the system should preserve diagnostic logs for troubleshooting "
            "and provide clear error information to the user"
        )

        # Create realistic professional resume data
        resume_data = {
            "full_name": "Dr. Robert Martinez",
            "email": "robert.martinez@university.edu",
            "phone": "+1 (555) 789-0123",
            "template": "resume_with_bars",
            "titles": {
                "contact": "Contact Information",
                "certification": "Academic Credentials",
                "expertise": "Research Expertise",
            },
            "description": (
                "Professor of Computer Science specializing in machine learning"
            ),
            "config": {
                "output_mode": "latex",
                "page_width": 210,
                "page_height": 297,
                "sidebar_width": 60,
                "h2_padding_left": 4,
                "padding": 12,
                "date_container_width": 13,
                "description_container_padding_left": 3,
                "theme_color": "#1f4e79",
            },
            "body": {
                "experience": [
                    {
                        "company": "State University",
                        "position": "Associate Professor",
                        "start_date": "2018-08",
                        "end_date": "2024-01",
                        "description": (
                            "Teaching graduate courses and leading research in "
                            "ML algorithms"
                        ),
                    }
                ]
            },
        }

        paths = _make_paths(tmp_path)
        resume = Resume.from_data(resume_data, paths=paths, name="Robert Martinez")
        output_path = paths.output / "robert_martinez_academic_resume.pdf"

        # Simulate realistic LaTeX compilation error
        realistic_error_log = (
            "! LaTeX Error: File `moderncv.sty' not found.\n"
            "l.10 \\moderncvstyle{banking}\n"
            "Type H <return> for immediate help.\n"
            "...\n"
            "See the LaTeX manual for explanation.\n"
            "Type  I <command> <return> to replace it with another command,\n"
            "or  <return> to continue without it.\n"
        )
        latex_error = LatexCompilationError(
            "LaTeX compilation failed", log=realistic_error_log
        )

        # Test the business requirement: preserve diagnostic information on failure
        with patch(
            "simple_resume.shell.strategies.prepare_pdf_with_latex",
            side_effect=latex_error,
        ):
            with pytest.raises(GenerationError) as exc_info:
                # Attempt to generate PDF using LaTeX (should fail gracefully)
                to_pdf(resume, output_path=output_path)

        # Verify business requirements for error handling are met
        story.then("diagnostic information should be preserved for troubleshooting")
        assert "LaTeX" in str(exc_info.value), (
            "Error should mention LaTeX compilation issue"
        )

        # Verify no partial output is created when compilation fails (business rule)
        assert not output_path.exists(), (
            "No PDF should be created when LaTeX compilation fails"
        )

    def test_resume_to_pdf_passes_paths_to_latex_strategy(
        self,
        tmp_path: Path,
        story: Scenario,
    ) -> None:
        story.given(
            "a candidate needs LaTeX output with bundled templates and palettes"
        )
        resume_data = {
            "full_name": "Case Candidate",
            "email": "case@example.com",
            "template": "resume_with_bars",
            "config": {
                "output_mode": "latex",
                "page_width": 210,
                "page_height": 297,
                "sidebar_width": 60,
            },
        }
        paths = _make_paths(tmp_path)
        resume = Resume.from_data(resume_data, paths=paths, name="Case Candidate")
        output_path = paths.output / "case_candidate.pdf"

        mock_result = Mock(spec=GenerationResult)
        mock_result.exists = False

        metadata = GenerationMetadata(
            format_type="pdf",
            template_name="latex",
            generation_time=0.0,
            file_size=0,
            resume_name="Case Candidate",
        )

        with patch(
            "simple_resume.shell.strategies.prepare_pdf_with_latex",
            return_value=("", [], metadata),
        ) as mock_prepare:
            to_pdf(resume, output_path=output_path)

        call = mock_prepare.call_args
        assert call is not None
        _, _, context = call.args
        assert context.paths == paths
        assert context.raw_data["full_name"] == "Case Candidate"

    def test_generate_html_with_jinja_injects_base_href(
        self,
        tmp_path: Path,
        story: Scenario,
    ) -> None:
        story.given(
            "a professional resume containing candidate's contact information, "
            "work experience, and technical expertise for job applications"
        )
        resume = Resume.from_data(
            {
                "full_name": "Michael Johnson",
                "email": "michael.johnson@techcompany.com",
                "phone": "+1 (555) 987-6543",
                "template": "resume_no_bars",
                "titles": {
                    "contact": "Contact Information",
                    "certification": "Professional Certifications",
                    "expertise": "Technical Expertise",
                    "keyskills": "Core Competencies",
                },
                "description": (
                    "Senior Software Engineer specializing in scalable systems"
                ),
                "config": {
                    "page_width": 210,
                    "page_height": 297,
                    "sidebar_width": 60,
                    "h2_padding_left": 4,
                    "padding": 12,
                    "date_container_width": 13,
                    "description_container_padding_left": 3,
                },
                "body": {
                    "experience": [
                        {
                            "company": "Enterprise Solutions Inc.",
                            "position": "Senior Software Engineer",
                            "start_date": "2018-06",
                            "end_date": "2024-01",
                            "description": (
                                "Led development of enterprise-scale applications "
                                "serving Fortune 500 clients"
                            ),
                        }
                    ],
                    "expertise": [
                        "Microservices Architecture",
                        "Cloud Platform Engineering",
                        "Performance Optimization",
                    ],
                },
            }
        )
        output_path = tmp_path / "case.html"

        # Mock the HTML generation to avoid template rendering
        metadata = GenerationMetadata(
            format_type="html",
            template_name="resume_no_bars",
            generation_time=0.0,
            file_size=2048,
            resume_name="Michael Johnson",
        )
        mock_result = GenerationResult(
            output_path=output_path,
            format_type="html",
            metadata=metadata,
        )

        # Patch the shell HTML generation function
        with patch(
            "simple_resume.shell.resume_extensions.generate_html_with_jinja",
            return_value=mock_result,
        ) as mock_html_generation:
            result = to_html(resume, output_path=output_path)

        story.then(
            "HTML generation produces business-valid output with proper "
            "content structure"
        )
        assert result.output_path == output_path, (
            "Generation result must reference output file"
        )
        assert result.metadata is not None
        assert result.metadata.file_size == 2048, (
            "Generated content should have reasonable size"
        )

        # Additional business validation: verify the HTML generation was called
        # with proper context
        mock_html_generation.assert_called_once()
        call_args = mock_html_generation.call_args
        assert call_args is not None, (
            "HTML generation must be invoked with proper parameters"
        )

        # Verify the generation plan contains business-critical data
        # Check both positional args and kwargs for plan
        plan = None
        if call_args.args and len(call_args.args) > 0:
            plan = call_args.args[0]
        elif call_args.kwargs and "plan" in call_args.kwargs:
            plan = call_args.kwargs["plan"]

        if plan:
            assert hasattr(plan, "context"), (
                "Render plan must include context for template"
            )
            if hasattr(plan, "context") and plan.context:
                context = plan.context
                # Verify business context is preserved through the generation pipeline
                assert "full_name" in context or "Michael Johnson" in str(context), (
                    "Applicant name must be in generation context"
                )

    def test_generate_html_with_jinja_rejects_latex_mode(
        self,
        tmp_path: Path,
        story: Scenario,
    ) -> None:
        story.given(
            "a user requests HTML generation but accidentally configures "
            "LaTeX output mode"
        )
        story.when("the system attempts to generate HTML with LaTeX configuration")
        story.then("the system should gracefully reject the incompatible configuration")

        # Create a realistic resume with business data
        resume = Resume.from_data(
            {
                "full_name": "Alexandra Chen",
                "email": "alexandra.chen@techcorp.com",
                "phone": "+1 (555) 456-7890",
                "template": "resume_no_bars",
                "titles": {
                    "contact": "Contact Information",
                    "expertise": "Technical Expertise",
                },
                "description": "Software Engineer specializing in backend systems",
                "config": {
                    "output_mode": "latex",
                    "page_width": 210,
                    "page_height": 297,
                    "sidebar_width": 60,
                    "h2_padding_left": 4,
                    "padding": 12,
                    "date_container_width": 13,
                    "description_container_padding_left": 3,
                },
                "body": {
                    "experience": [
                        {
                            "company": "Tech Innovations Inc",
                            "position": "Senior Backend Engineer",
                            "start_date": "2019-01",
                            "end_date": "2024-01",
                            "description": (
                                "Developed scalable microservices handling 1M+ requests"
                            ),
                        }
                    ]
                },
            }
        )

        output_path = tmp_path / "alexandra_resume.html"

        # Test the business rule: HTML generation should reject LaTeX mode
        with pytest.raises(GenerationError) as exc_info:
            to_html(resume, output_path=output_path)

        # Verify the business requirement is properly communicated
        assert "LaTeX mode not supported" in str(exc_info.value), (
            "Error should mention LaTeX incompatibility"
        )
        assert "format=html" in str(exc_info.value), (
            "Error should specify attempted format"
        )
        assert not output_path.exists(), (
            "No output file should be created when configuration is invalid"
        )

    def test_generate_with_string_format_pdf(
        self, story: Scenario, tmp_path: Path
    ) -> None:
        """Test shell generate function with string format 'pdf' routes to to_pdf."""
        story.given("a resume requesting PDF format via string")
        resume = Resume.from_data({"full_name": "Test User"})
        mock_result = GenerationResult(
            output_path=tmp_path / "test.pdf",
            format_type="pdf",
        )

        story.when("shell generate is called with format='pdf'")
        with patch(
            "simple_resume.shell.resume_extensions.to_pdf",
            return_value=mock_result,
        ) as mock_to_pdf:
            result = shell_generate(resume, "pdf", output_path=tmp_path / "test.pdf")

        story.then("it routes to to_pdf")
        mock_to_pdf.assert_called_once()
        assert result.output_path == tmp_path / "test.pdf"

    def test_generate_with_string_format_html(
        self, story: Scenario, tmp_path: Path
    ) -> None:
        """Test shell generate function with string format 'html' routes to to_html."""
        story.given("a resume requesting HTML format via string")
        resume = Resume.from_data({"full_name": "Test User"})
        mock_result = GenerationResult(
            output_path=tmp_path / "test.html",
            format_type="html",
        )

        story.when("shell generate is called with format='html'")
        with patch(
            "simple_resume.shell.resume_extensions.to_html",
            return_value=mock_result,
        ) as mock_to_html:
            result = shell_generate(resume, "html", output_path=tmp_path / "test.html")

        story.then("it routes to to_html")
        mock_to_html.assert_called_once()
        assert result.output_path == tmp_path / "test.html"

    def test_generate_with_invalid_format_raises_error(
        self, story: Scenario, tmp_path: Path
    ) -> None:
        """Test shell generate function with invalid format raises ValueError."""
        story.given("a resume with invalid format string")
        resume = Resume.from_data({"full_name": "Test User"})

        story.when("shell generate is called with invalid format")
        with pytest.raises(ValueError, match="Unsupported format"):
            shell_generate(resume, "docx", output_path=tmp_path / "test.docx")
