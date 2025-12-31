"""Tests for shell rendering operations."""

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from simple_resume.core.generate.pdf import LatexGenerationContext
from simple_resume.core.models import RenderMode, RenderPlan, ResumeConfig
from simple_resume.core.paths import Paths
from simple_resume.core.result import GenerationMetadata
from simple_resume.shell.render.operations import (
    create_generation_result,
    generate_html_with_jinja,
    generate_pdf_with_weasyprint,
    open_file_in_browser,
)
from simple_resume.shell.strategies import LatexStrategy, PdfGenerationRequest
from tests.bdd import Scenario


class TestShellRenderingOperations:
    """Test shell rendering operations functionality."""

    def test_generate_html_with_jinja_preserves_html_without_base_href(
        self,
        story: Scenario,
        tmp_path: Path,
    ) -> None:
        """Test that HTML generation preserves content without base href injection.

        Assets (CSS, fonts) are copied to output directory instead of using base href.
        """
        story.given("a render plan with base path configured")
        story.when("generating HTML via the shell helper")
        render_plan = RenderPlan(
            name="Case",
            mode=RenderMode.HTML,
            config=ResumeConfig(),
            template_name="html/demo.html",
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
            "simple_resume.shell.render.operations.get_template_environment",
            return_value=mock_env,
        ):
            result = generate_html_with_jinja(render_plan, output_path)

        # Verify NO base href injection - assets are copied to output dir instead
        written = output_path.read_text(encoding="utf-8")
        assert '<base href="' not in written
        assert "content" in written
        assert result.output_path == output_path

    def test_generate_pdf_with_weasyprint_renders_template(
        self,
        story: Scenario,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test WeasyPrint PDF generation creates business-ready documents.

        With proper content and professional formatting.
        """
        story.given("a complete HTML render plan with realistic resume content")
        story.when("generating a PDF via weasyprint strategy")
        # Create realistic business render plan for a professional
        render_plan = RenderPlan(
            name="Jennifer Thompson",
            mode=RenderMode.HTML,
            config=ResumeConfig(
                page_width=210, page_height=297, theme_color="#2563eb", sidebar_width=60
            ),
            template_name="resume_no_bars.html",
            context={
                "full_name": "Jennifer Thompson",
                "email": "jennifer.thompson@techcorp.com",
                "phone": "+1 (555) 234-5678",
                "description": "Senior Product Manager with 7+ years in SaaS",
                "body": {
                    "experience": [
                        {
                            "company": "TechCorp Solutions",
                            "position": "Senior Product Manager",
                            "start_date": "2019-03",
                            "end_date": "2024-01",
                            "description": (
                                "Led product strategy for B2B SaaS platform "
                                "serving 10K+ enterprise customers"
                            ),
                        }
                    ]
                },
            },
            base_path=str(tmp_path),
        )
        output_path = tmp_path / "jennifer_thompson_resume.pdf"

        # Mock template rendering with business-relevant content
        mock_template = Mock()
        mock_template.render.return_value = (
            "<!DOCTYPE html><html><head>"
            "<title>Jennifer Thompson Resume</title></head>"
            "<body><h1>Jennifer Thompson</h1><p>Senior Product Manager</p>"
            "<p>TechCorp Solutions - Led product strategy for B2B SaaS "
            "platform</p></body></html>"
        )
        mock_env = Mock(get_template=Mock(return_value=mock_template))
        css_mock = Mock(return_value=Mock(name="css"))
        html_instance = Mock()
        mock_document = Mock()
        mock_document.pages = [Mock()]
        mock_document.write_pdf.return_value = b"%PDF-1.4 business bytes"
        html_instance.render.return_value = mock_document
        html_mock = Mock(return_value=html_instance)
        fake_weasyprint = SimpleNamespace(CSS=css_mock, HTML=html_mock)
        monkeypatch.setitem(sys.modules, "weasyprint", fake_weasyprint)

        # Test using the public API with mocked dependencies for business validation
        with patch(
            "simple_resume.shell.render.operations.get_template_environment",
            return_value=mock_env,
        ):
            # Test the business requirement: PDF generation should succeed
            result, page_count = generate_pdf_with_weasyprint(
                render_plan, output_path, resume_name="jennifer_thompson_resume"
            )

        # Verify business requirements for PDF generation
        mock_env.get_template.assert_called_once_with("resume_no_bars.html")
        assert result.output_path == output_path, (
            "PDF generation result must reference correct output file"
        )
        assert page_count == 1, (
            "Professional resume should fit on single page for business use"
        )

        # Verify output file was created with business-relevant content
        assert output_path.exists(), "PDF file must be created for business use"
        # Verify the file has valid PDF structure (business requirement)
        with open(output_path, "rb") as f:
            header = f.read(4)
            assert header == b"%PDF", (
                "File should have valid PDF header for business documents"
            )

        # Verify template was properly selected for professional use
        mock_env.get_template.assert_called_once_with("resume_no_bars.html")

    def test_latex_strategy_passes_paths_and_raw_data(
        self,
        story: Scenario,
        tmp_path: Path,
    ) -> None:
        """Ensure the LaTeX strategy forwards paths and resume data to the core."""
        story.given("a PDF generation request using LaTeX strategy")
        story.when("generate_pdf is invoked on the strategy")
        render_plan = RenderPlan(
            name="Case",
            mode=RenderMode.LATEX,
            config=ResumeConfig(output_mode="latex"),
            base_path=str(tmp_path),
        )
        output_path = tmp_path / "case.pdf"
        paths = Paths(
            data=tmp_path,
            input=tmp_path,
            output=tmp_path,
            content=tmp_path,
            templates=tmp_path,
            static=tmp_path,
        )
        raw_data = {"full_name": "Case Candidate", "config": {"output_mode": "latex"}}
        processed_data = {
            "full_name": "Case Candidate",
            "config": {"output_mode": "latex"},
        }

        request = PdfGenerationRequest(
            render_plan=render_plan,
            output_path=output_path,
            filename="case.tex",
            resume_name="Case",
            raw_data=raw_data,
            processed_data=processed_data,
            paths=paths,
        )

        with patch(
            "simple_resume.shell.strategies.prepare_pdf_with_latex",
            return_value=(
                "",
                [],
                GenerationMetadata(
                    format_type="pdf",
                    template_name="latex/basic.tex",
                    generation_time=0.0,
                    file_size=0,
                    resume_name="Case",
                ),
            ),
        ) as mock_generate:
            strategy = LatexStrategy()
            result = strategy.generate_pdf(request)

        assert result.output_path == output_path
        call = mock_generate.call_args
        assert call is not None
        _, _, context = call.args
        assert isinstance(context, LatexGenerationContext)
        assert context.paths == paths
        assert context.resume_data == raw_data

    def test_open_file_in_browser_with_specified_browser(
        self,
        story: Scenario,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test opening file with specified browser."""
        story.given("a local HTML file and an explicit browser choice")
        story.when("opening the file in the requested browser")
        test_file = tmp_path / "test.html"
        test_file.write_text("<html></html>")

        mock_popen = Mock()
        monkeypatch.setattr("subprocess.Popen", mock_popen)

        open_file_in_browser(test_file, browser="firefox")

        mock_popen.assert_called_once_with(
            ["firefox", str(test_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def test_open_file_in_browser_with_default_system_opener(
        self, story: Scenario, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test opening file with default system opener."""
        story.given("no explicit browser is provided")
        story.when("opening a file using the platform default")
        test_file = tmp_path / "test.html"
        test_file.write_text("<html></html>")

        mock_run = Mock()
        mock_xdg_exists = Mock(return_value=True)
        monkeypatch.setattr("subprocess.run", mock_run)
        monkeypatch.setattr("pathlib.Path.exists", mock_xdg_exists)

        open_file_in_browser(test_file)

        mock_run.assert_called_once_with(["xdg-open", str(test_file)], check=False)

    def test_create_generation_result_with_all_metadata(
        self, story: Scenario, tmp_path: Path
    ) -> None:
        """Test creating GenerationResult with all metadata fields."""
        story.given("complete metadata is provided from generation pipeline")
        story.when("constructing the GenerationResult helper")
        output_path = tmp_path / "test.pdf"
        output_path.write_text("test content")

        result = create_generation_result(
            output_path=output_path,
            format_type="pdf",
            generation_time=1.23,
            template_name="basic.tex",
            file_size=1234,
            resume_name="john_doe",
            palette_info={"scheme": "blue"},
            page_count=2,
        )

        assert result.output_path == output_path
        assert result.format_type == "pdf"
        assert result.metadata is not None
        assert result.metadata.template_name == "basic.tex"
        assert result.metadata.generation_time == 1.23
        assert result.metadata.file_size == 1234
        assert result.metadata.resume_name == "john_doe"
        assert result.metadata.palette_info == {"scheme": "blue"}
        assert result.metadata.page_count == 2

    def test_create_generation_result_with_minimal_metadata(
        self, story: Scenario, tmp_path: Path
    ) -> None:
        """Test creating GenerationResult with minimal metadata."""
        story.given("only required fields are provided")
        story.when("creating GenerationResult with defaults")
        output_path = tmp_path / "test.html"
        output_path.write_text("test content")

        result = create_generation_result(
            output_path=output_path,
            format_type="html",
            generation_time=0.5,
        )

        assert result.output_path == output_path
        assert result.format_type == "html"
        assert result.metadata is not None
        assert result.metadata.template_name == "unknown"
        assert result.metadata.generation_time == 0.5
        assert result.metadata.file_size == 0
        assert result.metadata.resume_name == "resume"
        assert result.metadata.palette_info is None
        assert result.metadata.page_count is None
