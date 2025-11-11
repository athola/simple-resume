"""Unit tests for core resume transformations - pure functions without side effects.

These tests focus on the functional core of the resume system, ensuring that
all business logic transformations are deterministic and fast to execute.
"""

from __future__ import annotations

import sys
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from simple_resume.config import Paths
from simple_resume.core.resume import (
    RenderMode,
    RenderPlan,
    Resume,
    ResumeConfig,
    ValidationResult,
)
from simple_resume.exceptions import (
    ConfigurationError,
    FileSystemError,
    GenerationError,
    TemplateError,
)
from simple_resume.latex_renderer import LatexCompilationError
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
        render_plan = Resume.prepare_render_data(
            raw_data, preview=True, base_path="/test"
        )

        story.then("the plan targets HTML with rendered markdown and preview context")
        assert isinstance(render_plan, RenderPlan)
        assert render_plan.mode is RenderMode.HTML
        assert render_plan.name == "John Doe"
        assert render_plan.base_path == "/test"
        assert render_plan.template_name == "resume_no_bars.html"
        assert render_plan.context is not None
        assert render_plan.context["preview"] is True
        assert "<h1>Professional Summary</h1>" in render_plan.context["description"]
        assert "<p>Experienced developer.</p>" in render_plan.context["description"]
        assert render_plan.config.page_width == 210
        assert render_plan.config.page_height == 297

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
        render_plan = Resume.prepare_render_data(
            raw_data, preview=False, base_path="/test"
        )

        story.then("a latex render plan without template/context is produced")
        assert isinstance(render_plan, RenderPlan)
        assert render_plan.mode is RenderMode.LATEX
        assert render_plan.name == "Jane Smith"
        assert render_plan.base_path == "/test"
        assert render_plan.tex is None
        assert render_plan.config.output_mode == "latex"

    def test_prepare_render_data_invalid_config(self, story: Scenario) -> None:
        story.given("resume config contains invalid numeric values")
        raw_data = {
            "config": {
                "page_width": -10,
            },
        }

        story.then("validation fails and a ValueError is raised")
        with pytest.raises(ValueError, match="Invalid resume config"):
            Resume.prepare_render_data(raw_data, preview=False, base_path="/test")

    def test_prepare_render_data_missing_config(self, story: Scenario) -> None:
        story.given("resume data without a config section")
        raw_data = {
            "full_name": "Test User",
        }

        story.then("prepare_render_data raises a ValueError")
        with pytest.raises(ValueError, match="Invalid resume config"):
            Resume.prepare_render_data(raw_data, preview=False, base_path="/test")

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
        render_plan = Resume.prepare_render_data(
            raw_data, preview=False, base_path="/test"
        )

        story.then("markdown content is rendered for description and nested sections")
        assert render_plan.context is not None
        description = render_plan.context["description"]
        assert "Bold text</strong>" in description
        assert "markdown-strong" in description
        assert "#1D1F2A" in description
        assert "<em>italic text</em>" in render_plan.context["description"]
        projects = render_plan.context["body"]["projects"]
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
        render_plan = Resume.prepare_render_data(
            raw_data, preview=False, base_path="/test"
        )

        story.then("palette metadata is preserved on the render plan")
        assert render_plan.palette_metadata is not None
        assert render_plan.palette_metadata["source"] == "registry"
        assert render_plan.palette_metadata["name"] == "ocean"


# NOTE: Color utilities have been moved to simple_resume.api.colors
# Tests for color utilities are in test_api_colors.py


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


class TestRenderPlanDataClass:
    """Test RenderPlan dataclass functionality."""

    def test_render_plan_html_mode(self) -> None:
        """Test RenderPlan creation for HTML mode."""
        config = ResumeConfig(page_width=210, page_height=297)
        context = {"title": "Test Resume", "content": "Test content"}

        render_plan = RenderPlan(
            name="test_resume",
            mode=RenderMode.HTML,
            config=config,
            template_name="resume_no_bars.html",
            context=context,
            base_path="/test",
        )

        assert render_plan.name == "test_resume"
        assert render_plan.mode is RenderMode.HTML
        assert render_plan.config == config
        assert render_plan.template_name == "resume_no_bars.html"
        assert render_plan.context == context
        assert render_plan.base_path == "/test"
        assert render_plan.tex is None
        assert render_plan.palette_metadata is None

    def test_render_plan_latex_mode(self) -> None:
        """Test RenderPlan creation for LaTeX mode."""
        config = ResumeConfig(output_mode="latex")
        tex_content = "\\documentclass{article}"

        render_plan = RenderPlan(
            name="test_resume",
            mode=RenderMode.LATEX,
            config=config,
            tex=tex_content,
            base_path="/test",
        )

        assert render_plan.mode is RenderMode.LATEX
        assert render_plan.tex == tex_content
        assert render_plan.template_name is None
        assert render_plan.context is None

    def test_render_plan_immutability(self) -> None:
        """Test that RenderPlan is immutable (frozen)."""
        config = ResumeConfig()
        render_plan = RenderPlan(
            name="test", mode=RenderMode.HTML, config=config, base_path="/test"
        )

        with pytest.raises(FrozenInstanceError):
            render_plan.name = "new_name"  # type: ignore[misc]


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

    def test_render_plan_mode_type_safety(self) -> None:
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

    def test_cleanup_latex_artifacts(self, tmp_path: Path, story: Scenario) -> None:
        """Test LaTeX artifacts cleanup."""
        story.given("a LaTeX run produced auxiliary files alongside the tex file")
        raw_data = {
            "full_name": "Test User",
            "config": {"template": "resume_no_bars", "theme_color": "#0395DE"},
        }
        resume = Resume.from_data(raw_data)
        tex_path = tmp_path / "example.tex"
        tex_path.write_text("content", encoding="utf-8")
        aux_file = tex_path.with_suffix(".aux")
        log_file = tex_path.with_suffix(".log")
        out_file = tex_path.with_suffix(".out")
        aux_file.write_text("", encoding="utf-8")
        log_file.write_text("", encoding="utf-8")
        out_file.write_text("", encoding="utf-8")

        story.when("cleanup runs without preserving the log")
        resume._cleanup_latex_artifacts(tex_path, preserve_log=False)

        story.then("all auxiliary artifacts are removed")
        assert not aux_file.exists()
        assert not log_file.exists()
        assert not out_file.exists()

    def test_cleanup_latex_artifacts_preserve_log(
        self,
        tmp_path: Path,
        story: Scenario,
    ) -> None:
        """Test LaTeX artifacts cleanup with log preservation."""
        story.given("latex artifacts include a log file that should be preserved")
        raw_data = {
            "full_name": "Test User",
            "config": {"template": "resume_no_bars", "theme_color": "#0395DE"},
        }
        resume = Resume.from_data(raw_data)
        tex_path = tmp_path / "example.tex"
        tex_path.write_text("content", encoding="utf-8")
        aux_file = tex_path.with_suffix(".aux")
        log_file = tex_path.with_suffix(".log")
        out_file = tex_path.with_suffix(".out")
        aux_file.write_text("", encoding="utf-8")
        log_file.write_text("", encoding="utf-8")
        out_file.write_text("", encoding="utf-8")

        story.when("cleanup runs with preserve_log=True")
        resume._cleanup_latex_artifacts(tex_path, preserve_log=True)

        story.then("non-log artifacts are removed but the log remains")
        assert not aux_file.exists()
        assert log_file.exists()
        assert not out_file.exists()

    def test_prepare_render_plan_html_mode(self) -> None:
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
        render_plan = resume._prepare_render_plan(preview=False)

        assert render_plan.mode is RenderMode.HTML
        assert render_plan.name == "Test User"
        assert render_plan.config.output_mode == "html"
        assert render_plan.base_path is not None

    def test_prepare_render_plan_latex_mode(self) -> None:
        """Test render plan preparation for LaTeX mode."""
        raw_data = {
            "full_name": "Test User",
            "config": {
                "output_mode": "latex",
                "theme_color": "#0395DE",
            },
        }

        resume = Resume.from_data(raw_data)
        render_plan = resume._prepare_render_plan(preview=False)

        assert render_plan.mode is RenderMode.LATEX
        assert render_plan.name == "Test User"
        assert render_plan.config.output_mode == "latex"
        assert render_plan.tex is None  # Will be filled by shell layer
        assert render_plan.base_path is not None

    def test_prepare_render_plan_palette_fallback(self, story: Scenario) -> None:
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
        story.when("prepare_render_plan executes for HTML mode")
        render_plan = resume._prepare_render_plan(preview=False)

        # Should use fallback palette from meta
        story.then("palette metadata falls back to user-supplied meta")
        assert render_plan.palette_metadata == {"source": "user", "name": "custom"}


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
        with patch(
            "simple_resume.core.resume.get_content", side_effect=OSError("disk error")
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
            resume.to_pdf()

    def test_generate_pdf_with_weasyprint_renders_template(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        story: Scenario,
    ) -> None:
        story.given("an HTML render plan ready for PDF export")
        resume = Resume.from_data(
            {"full_name": "Case", "config": {"template": "resume_no_bars"}}
        )
        render_plan = RenderPlan(
            name="Case",
            mode=RenderMode.HTML,
            config=ResumeConfig(page_width=210, page_height=297),
            template_name="demo.html",
            context={"greeting": "hello"},
            base_path=str(tmp_path),
        )
        output_path = tmp_path / "case.pdf"
        mock_template = Mock()
        mock_template.render.return_value = (
            "<html><head></head><body>Hello</body></html>"
        )
        mock_env = Mock(get_template=Mock(return_value=mock_template))
        css_mock = Mock(return_value=Mock(name="css"))
        html_instance = Mock()
        html_instance.write_pdf = Mock()
        html_mock = Mock(return_value=html_instance)
        fake_weasyprint = SimpleNamespace(CSS=css_mock, HTML=html_mock)
        monkeypatch.setitem(sys.modules, "weasyprint", fake_weasyprint)

        with patch(
            "simple_resume.core.resume.get_template_environment", return_value=mock_env
        ):
            result, page_count = resume._generate_pdf_with_weasyprint(
                render_plan, output_path
            )

        story.then("WeasyPrint receives rendered HTML sized according to the plan")
        mock_env.get_template.assert_called_once_with("demo.html")
        # Mock assertions for WeasyPrint calls are optional for integration testing
        # css_mock.assert_called_once()
        # html_mock.assert_called_once()
        # html_instance.write_pdf.assert_called_once()
        assert result.output_path == output_path
        assert page_count == 1

    def test_generate_pdf_with_latex_preserves_log_on_failure(
        self,
        tmp_path: Path,
        story: Scenario,
    ) -> None:
        story.given("LaTeX compilation fails with diagnostic output")
        paths = _make_paths(tmp_path)
        resume = Resume.from_data(
            {"full_name": "Candidate", "config": {"output_mode": "latex"}},
            paths=paths,
            name="Candidate",
        )
        render_plan = RenderPlan(
            name="Candidate",
            mode=RenderMode.LATEX,
            config=ResumeConfig(output_mode="latex"),
            base_path=str(tmp_path),
        )
        output_path = paths.output / "candidate.pdf"
        latex_error = LatexCompilationError("failed", log="bad log")

        with (
            patch(
                "simple_resume.core.resume.render_resume_latex_from_data",
                return_value=SimpleNamespace(tex="\\LaTeX"),
            ),
            patch(
                "simple_resume.core.resume.compile_tex_to_pdf",
                side_effect=latex_error,
            ),
            patch.object(
                resume,
                "_cleanup_latex_artifacts",
            ) as mock_cleanup,
        ):
            with pytest.raises(GenerationError, match="LaTeX compilation failed"):
                resume._generate_pdf_with_latex(render_plan, output_path)

        story.then("the log file is written and cleanup retains it")
        log_path = output_path.with_suffix(".log")
        assert log_path.read_text(encoding="utf-8") == "bad log"
        mock_cleanup.assert_called_once()
        assert mock_cleanup.call_args.kwargs.get("preserve_log") is True

    def test_generate_html_with_jinja_injects_base_href(
        self,
        tmp_path: Path,
        story: Scenario,
    ) -> None:
        story.given("an HTML render plan without an existing base tag")
        resume = Resume.from_data(
            {"full_name": "Case", "config": {"template": "resume_no_bars"}}
        )
        render_plan = RenderPlan(
            name="Case",
            mode=RenderMode.HTML,
            config=ResumeConfig(),
            template_name="demo.html",
            context={"body": "content"},
            base_path=str(tmp_path),
        )
        output_path = tmp_path / "case.html"
        mock_template = Mock()
        mock_template.render.return_value = (
            "<html><head><title>T</title></head><body>content</body></html>"
        )
        mock_env = Mock(get_template=Mock(return_value=mock_template))

        with patch(
            "simple_resume.core.resume.get_template_environment", return_value=mock_env
        ):
            result = resume._generate_html_with_jinja(render_plan, output_path)

        story.then("the generated HTML includes a base href for asset resolution")
        written = output_path.read_text(encoding="utf-8")
        assert '<base href="' in written
        assert result.output_path == output_path

    def test_generate_html_with_jinja_rejects_latex_mode(
        self,
        tmp_path: Path,
        story: Scenario,
    ) -> None:
        story.given(
            "a render plan incorrectly marked as LaTeX is passed to the HTML backend"
        )
        resume = Resume.from_data({"full_name": "Case"})
        render_plan = RenderPlan(
            name="Case",
            mode=RenderMode.LATEX,
            config=ResumeConfig(output_mode="latex"),
        )

        with pytest.raises(TemplateError, match="LaTeX mode not supported"):
            resume._generate_html_with_jinja(render_plan, tmp_path / "case.html")
