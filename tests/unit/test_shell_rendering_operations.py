"""Tests for shell rendering operations."""

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from simple_resume.core.models import RenderMode, RenderPlan, ResumeConfig
from simple_resume.latex_renderer import LatexCompilationError
from simple_resume.shell.rendering_operations import (
    generate_html_with_jinja,
    generate_pdf_with_weasyprint,
    open_file_in_browser,
)
from simple_resume.shell.strategies import LatexStrategy


class TestShellRenderingOperations:
    """Test shell rendering operations functionality."""

    def test_generate_html_with_jinja_injects_base_href(
        self,
        tmp_path: Path,
    ) -> None:
        """Test that HTML generation includes base href for asset resolution."""
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
            "simple_resume.shell.rendering_operations.get_template_environment",
            return_value=mock_env,
        ):
            result = generate_html_with_jinja(render_plan, output_path)

        # Verify base href injection
        written = output_path.read_text(encoding="utf-8")
        assert '<base href="' in written
        assert result.output_path == output_path

    def test_generate_pdf_with_weasyprint_renders_template(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test WeasyPrint PDF generation creates business-ready documents.

        With proper content and professional formatting.
        """
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
        html_instance.write_pdf = Mock()
        html_mock = Mock(return_value=html_instance)
        fake_weasyprint = SimpleNamespace(CSS=css_mock, HTML=html_mock)
        monkeypatch.setitem(sys.modules, "weasyprint", fake_weasyprint)

        # Test using the public API with mocked dependencies for business validation
        with patch(
            "simple_resume.shell.rendering_operations.get_template_environment",
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
        assert output_path.stat().st_size > 1000, (
            "PDF should contain substantial professional content"
        )

        # Verify the file has valid PDF structure (business requirement)
        with open(output_path, "rb") as f:
            header = f.read(4)
            assert header == b"%PDF", (
                "File should have valid PDF header for business documents"
            )

        # Verify template was properly selected for professional use
        mock_env.get_template.assert_called_once_with("resume_no_bars.html")

    @pytest.mark.xfail(
        reason="LaTeX strategy refactoring incomplete - paths not passed to context"
    )
    def test_generate_pdf_with_latex_preserves_log_on_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test LaTeX PDF generation preserves log on failure."""
        render_plan = RenderPlan(
            name="Case",
            mode=RenderMode.LATEX,
            config=ResumeConfig(),
            template_name="demo.tex",
            context={"body": "content"},
            base_path=str(tmp_path),
        )
        output_path = tmp_path / "case.pdf"
        tex_path = tmp_path / "case.tex"

        # Create a fake LaTeX log file
        log_path = tex_path.with_suffix(".log")
        log_path.write_text("LaTeX compilation error", encoding="utf-8")

        # Mock LaTeX compilation to fail
        compile_error = LatexCompilationError(
            "Compilation failed", log="LaTeX compilation error"
        )

        with (
            patch(
                "simple_resume.core.pdf_generation.render_resume_latex_from_data",
                side_effect=compile_error,
            ),
            patch(
                "simple_resume.core.pdf_generation.compile_tex_to_pdf",
                side_effect=compile_error,
            ),
        ):
            strategy = LatexStrategy()
            request = Mock(
                render_plan=render_plan,
                output_path=output_path,
                filename="case.tex",
                resume_name="Case",
                paths=[tmp_path],
            )

            with pytest.raises(LatexCompilationError):
                strategy.generate_pdf(request)

        # Verify log file is preserved
        assert log_path.exists()
        assert "LaTeX compilation error" in log_path.read_text(encoding="utf-8")

    def test_open_file_in_browser_with_specified_browser(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test opening file with specified browser."""
        test_file = tmp_path / "test.html"
        test_file.write_text("<html></html>")

        mock_popen = Mock()
        monkeypatch.setattr("subprocess.Popen", mock_popen)

        open_file_in_browser(test_file, browser="firefox")

        mock_popen.assert_called_once_with(
            ["firefox", test_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def test_open_file_in_browser_with_default_system_opener(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test opening file with default system opener."""
        test_file = tmp_path / "test.html"
        test_file.write_text("<html></html>")

        mock_run = Mock()
        mock_xdg_exists = Mock(return_value=True)
        monkeypatch.setattr("subprocess.run", mock_run)
        monkeypatch.setattr("pathlib.Path.exists", mock_xdg_exists)

        open_file_in_browser(test_file)

        mock_run.assert_called_once_with(["xdg-open", test_file], check=False)
