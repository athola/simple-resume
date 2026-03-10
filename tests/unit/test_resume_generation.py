"""Unit tests for resume generation I/O."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from simple_resume.core.exceptions import (
    ConfigurationError,
    FileSystemError,
    GenerationError,
)
from simple_resume.core.models import RenderPlan
from simple_resume.core.paths import Paths
from simple_resume.core.result import GenerationMetadata, GenerationResult
from simple_resume.core.resume import Resume
from simple_resume.shell.render.latex import LatexCompilationError
from simple_resume.shell.resume_extensions import generate as shell_generate
from simple_resume.shell.resume_extensions import to_html, to_markdown, to_pdf, to_tex
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
        assert result.output_path == output_path
        assert result.metadata is not None
        assert result.metadata.file_size == 1024

        mock_pdf_generation.assert_called_once()
        call_args = mock_pdf_generation.call_args
        assert call_args is not None

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

        with patch(
            "simple_resume.shell.strategies.prepare_pdf_with_latex",
            side_effect=latex_error,
        ):
            with pytest.raises(GenerationError) as exc_info:
                to_pdf(resume, output_path=output_path)

        story.then("diagnostic information should be preserved for troubleshooting")
        assert "LaTeX" in str(exc_info.value)
        assert not output_path.exists()

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

        with patch(
            "simple_resume.shell.resume_extensions.generate_html_with_jinja",
            return_value=mock_result,
        ) as mock_html_generation:
            result = to_html(resume, output_path=output_path)

        story.then(
            "HTML generation produces business-valid output with proper "
            "content structure"
        )
        assert result.output_path == output_path
        assert result.metadata is not None
        assert result.metadata.file_size == 2048

        mock_html_generation.assert_called_once()
        call_args = mock_html_generation.call_args
        assert call_args is not None

        plan = None
        if call_args.args and len(call_args.args) > 0:
            plan = call_args.args[0]
        elif call_args.kwargs and "plan" in call_args.kwargs:
            plan = call_args.kwargs["plan"]

        if plan:
            assert hasattr(plan, "context")
            if hasattr(plan, "context") and plan.context:
                context = plan.context
                assert "full_name" in context or "Michael Johnson" in str(context)

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

        with pytest.raises(GenerationError) as exc_info:
            to_html(resume, output_path=output_path)

        assert "LaTeX mode not supported" in str(exc_info.value)
        assert "format=html" in str(exc_info.value)
        assert not output_path.exists()

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


class TestIntermediateFormatGeneration:
    """Tests for intermediate format generation: to_markdown() and to_tex()."""

    def test_to_markdown_generates_valid_file(
        self, story: Scenario, tmp_path: Path
    ) -> None:
        """Test to_markdown generates a valid markdown file."""
        story.given("a complete resume with contact and experience data")
        resume_data = {
            "full_name": "Emily Chen",
            "email": "emily.chen@example.com",
            "phone": "+1 (555) 123-4567",
            "description": "Software engineer with Python expertise",
            "config": {
                "template": "resume_no_bars",
                "page_width": 210,
                "page_height": 297,
                "theme_color": "#2E4057",
            },
            "body": {
                "experience": [
                    {
                        "company": "TechCorp Inc",
                        "position": "Senior Developer",
                        "start_date": "2020-01",
                        "end_date": "2024-01",
                        "description": "Led backend development team",
                    }
                ],
            },
        }
        resume = Resume.from_data(resume_data)
        output_path = tmp_path / "emily_resume.md"

        story.when("to_markdown is called with explicit output path")
        result = to_markdown(resume, output_path=output_path)

        story.then("a markdown file is created with proper structure and content")
        assert result.output_path == output_path
        assert output_path.exists()
        assert result.format_type == "markdown"
        assert result.metadata is not None
        assert result.metadata.format_type == "markdown"
        assert result.metadata.resume_name == "Emily Chen"
        assert result.metadata.file_size > 0

        content = output_path.read_text(encoding="utf-8")
        assert "# Emily Chen" in content
        assert "emily.chen@example.com" in content
        assert "+1 (555) 123-4567" in content

    def test_to_markdown_with_paths_object(
        self, story: Scenario, tmp_path: Path
    ) -> None:
        """Test to_markdown uses paths.output when no explicit path given."""
        story.given("a resume with paths configuration")
        paths = _make_paths(tmp_path)
        resume = Resume.from_data(
            {
                "full_name": "Alex Johnson",
                "config": {"template": "resume_no_bars"},
            },
            paths=paths,
            name="Alex Johnson",
        )

        story.when("to_markdown is called without explicit output path")
        result = to_markdown(resume)

        story.then("markdown file is created in paths.output directory")
        expected_path = paths.output / "Alex Johnson.md"
        assert result.output_path == expected_path
        assert expected_path.exists()

    def test_to_markdown_without_paths_raises_error(self, story: Scenario) -> None:
        """Test to_markdown raises ConfigurationError when no paths available."""
        story.given("a resume without paths and no explicit output path")
        resume = Resume.from_data(
            {
                "full_name": "No Path User",
                "config": {"template": "resume_no_bars"},
            }
        )

        story.when("to_markdown is called without output_path")
        story.then("ConfigurationError is raised")
        with pytest.raises(ConfigurationError, match="No paths available"):
            to_markdown(resume)

    @patch("simple_resume.shell.resume_extensions.render_resume_latex_from_data")
    def test_to_tex_generates_valid_file(
        self, mock_render: MagicMock, story: Scenario, tmp_path: Path
    ) -> None:
        """Test to_tex generates a valid LaTeX file."""
        story.given("a resume configured for LaTeX output")
        paths = _make_paths(tmp_path)
        resume_data = {
            "full_name": "Marcus Williams",
            "email": "marcus@university.edu",
            "config": {
                "output_mode": "latex",
                "template": "resume_no_bars",
                "page_width": 210,
                "page_height": 297,
                "theme_color": "#1f4e79",
            },
            "body": {
                "experience": [
                    {
                        "company": "Research Lab",
                        "position": "Research Scientist",
                        "start_date": "2019-06",
                        "end_date": "2024-01",
                        "description": "Published 15 papers in ML",
                    }
                ],
            },
        }
        resume = Resume.from_data(resume_data, paths=paths, name="Marcus Williams")
        output_path = tmp_path / "marcus_resume.tex"

        mock_render.return_value = (
            "\\documentclass{article}\n\\begin{document}\n"
            "Marcus Williams\n\\end{document}"
        )

        story.when("to_tex is called with explicit output path")
        result = to_tex(resume, output_path=output_path)

        story.then("a LaTeX file is created with proper structure")
        assert result.output_path == output_path
        assert output_path.exists()
        assert result.format_type == "tex"
        assert result.metadata is not None
        assert result.metadata.format_type == "tex"
        assert result.metadata.resume_name == "Marcus Williams"
        assert result.metadata.file_size > 0

        content = output_path.read_text(encoding="utf-8")
        assert "\\documentclass" in content or "Marcus Williams" in content

    @patch("simple_resume.shell.resume_extensions.render_resume_latex_from_data")
    def test_to_tex_with_paths_object(
        self, mock_render: MagicMock, story: Scenario, tmp_path: Path
    ) -> None:
        """Test to_tex uses paths.output when no explicit path given."""
        story.given("a resume with paths configuration for LaTeX")
        paths = _make_paths(tmp_path)
        resume = Resume.from_data(
            {
                "full_name": "Sarah Lee",
                "config": {"output_mode": "latex", "template": "resume_no_bars"},
            },
            paths=paths,
            name="Sarah Lee",
        )

        mock_render.return_value = (
            "\\documentclass{article}\n\\begin{document}\nSarah Lee\n\\end{document}"
        )

        story.when("to_tex is called without explicit output path")
        result = to_tex(resume)

        story.then("tex file is created in paths.output directory")
        expected_path = paths.output / "Sarah Lee.tex"
        assert result.output_path == expected_path
        assert expected_path.exists()

    def test_to_tex_without_paths_raises_error(self, story: Scenario) -> None:
        """Test to_tex raises ConfigurationError when no paths available."""
        story.given("a resume without paths and no explicit output path")
        resume = Resume.from_data(
            {
                "full_name": "No Path User",
                "config": {"output_mode": "latex", "template": "resume_no_bars"},
            }
        )

        story.when("to_tex is called without output_path")
        story.then("ConfigurationError is raised")
        with pytest.raises(ConfigurationError, match="No paths available"):
            to_tex(resume)

    def test_to_markdown_metadata_includes_palette_info(
        self, story: Scenario, tmp_path: Path
    ) -> None:
        """Test to_markdown preserves palette metadata in result."""
        story.given("a resume with palette configuration")
        resume_data = {
            "full_name": "Palette User",
            "config": {
                "template": "resume_no_bars",
                "color_scheme": "ocean",
            },
        }
        resume = Resume.from_data(resume_data)
        output_path = tmp_path / "palette_test.md"

        story.when("to_markdown generates the file")
        result = to_markdown(resume, output_path=output_path)

        story.then("metadata is created with proper fields")
        assert result.metadata is not None
        assert result.metadata.template_name is not None

    def test_generate_routes_to_markdown_format(
        self, story: Scenario, tmp_path: Path
    ) -> None:
        """Test shell generate function routes 'markdown' to to_markdown."""
        story.given("a resume requesting markdown format via generate()")
        resume = Resume.from_data(
            {
                "full_name": "Route Test User",
                "config": {"template": "resume_no_bars"},
            }
        )
        output_path = tmp_path / "route_test.md"

        story.when("shell generate is called with format='markdown'")
        result = shell_generate(resume, "markdown", output_path=output_path)

        story.then("it correctly generates markdown output")
        assert result.format_type == "markdown"
        assert output_path.exists()

    @patch("simple_resume.shell.resume_extensions.render_resume_latex_from_data")
    def test_generate_routes_to_tex_format(
        self, mock_render: MagicMock, story: Scenario, tmp_path: Path
    ) -> None:
        """Test shell generate function routes 'tex' to to_tex."""
        story.given("a resume requesting tex format via generate()")
        paths = _make_paths(tmp_path)
        resume = Resume.from_data(
            {
                "full_name": "TeX Route User",
                "config": {"output_mode": "latex", "template": "resume_no_bars"},
            },
            paths=paths,
            name="TeX Route User",
        )
        output_path = tmp_path / "route_test.tex"

        mock_render.return_value = (
            "\\documentclass{article}\n\\begin{document}\n"
            "TeX Route User\n\\end{document}"
        )

        story.when("shell generate is called with format='tex'")
        result = shell_generate(resume, "tex", output_path=output_path)

        story.then("it correctly generates tex output")
        assert result.format_type == "tex"
        assert output_path.exists()
