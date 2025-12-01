"""Tests for shell/strategies.py - PDF generation strategies."""

from __future__ import annotations

from pathlib import Path as _Path
from pathlib import PosixPath
from unittest import mock

import pytest

from simple_resume.core.exceptions import GenerationError
from simple_resume.core.models import RenderMode, RenderPlan, ResumeConfig
from simple_resume.core.result import GenerationResult
from simple_resume.shell.render.latex import LatexCompilationError
from simple_resume.shell.strategies import (
    LatexStrategy,
    PdfGenerationRequest,
    WeasyPrintStrategy,
)

# CI on POSIX can blow up if mock patches flip to WindowsPath; force a
# POSIX-capable Path alias to keep strategy tests platform-agnostic.
Path = PosixPath if _Path.__name__ == "WindowsPath" else _Path


class TestPdfGenerationRequest:
    """Tests for PdfGenerationRequest dataclass."""

    def test_request_creation_with_defaults(self) -> None:
        """Test creating request with default values."""
        plan = RenderPlan(
            name="test",
            mode=RenderMode.HTML,
            config=ResumeConfig(),
        )
        request = PdfGenerationRequest(
            render_plan=plan,
            output_path=Path("/tmp/test.pdf"),  # noqa: S108,
        )
        assert request.open_after is False
        assert request.filename is None
        assert request.resume_name == "resume"


class TestWeasyPrintStrategy:
    """Tests for WeasyPrintStrategy."""

    @mock.patch("simple_resume.shell.strategies.generate_pdf_with_weasyprint")
    def test_generate_pdf_basic(self, mock_generate) -> None:
        """Test basic PDF generation without opening."""
        plan = RenderPlan(
            name="test",
            mode=RenderMode.HTML,
            config=ResumeConfig(),
            template_name="test.html",
        )
        output_path = Path("/tmp/test.pdf")  # noqa: S108
        mock_result = GenerationResult(output_path=output_path, format_type="pdf")
        mock_generate.return_value = (mock_result, None)

        strategy = WeasyPrintStrategy()
        request = PdfGenerationRequest(
            render_plan=plan,
            output_path=output_path,
            open_after=False,
        )

        result = strategy.generate_pdf(request)
        assert result == mock_result
        mock_generate.assert_called_once()

    @mock.patch("sys.platform", "darwin")
    @mock.patch("shutil.which")
    @mock.patch("subprocess.Popen")
    @mock.patch("simple_resume.shell.strategies.generate_pdf_with_weasyprint")
    def test_generate_pdf_with_open_macos(
        self, mock_generate, mock_popen, mock_which
    ) -> None:
        """Test PDF generation with file opening on macOS."""
        plan = RenderPlan(
            name="test",
            mode=RenderMode.HTML,
            config=ResumeConfig(),
        )
        output_path = Path("/tmp/test.pdf")  # noqa: S108
        mock_result = mock.Mock(spec=GenerationResult)
        mock_result.exists = True
        mock_result.output_path = output_path
        mock_generate.return_value = (mock_result, None)
        mock_which.return_value = "/usr/bin/open"

        strategy = WeasyPrintStrategy()
        request = PdfGenerationRequest(
            render_plan=plan,
            output_path=output_path,
            open_after=True,
        )

        result = strategy.generate_pdf(request)
        assert result == mock_result
        mock_popen.assert_called_once()

    @mock.patch("sys.platform", "win32")
    @mock.patch("simple_resume.shell.strategies.os.name", "nt")
    @mock.patch("simple_resume.shell.strategies.os.startfile", create=True)
    @mock.patch("simple_resume.shell.strategies.generate_pdf_with_weasyprint")
    def test_generate_pdf_with_open_windows(
        self, mock_generate, mock_startfile
    ) -> None:
        """Test PDF generation with file opening on Windows."""
        plan = RenderPlan(
            name="test",
            mode=RenderMode.HTML,
            config=ResumeConfig(),
        )
        output_path = Path("/tmp/test.pdf")  # noqa: S108
        mock_result = mock.Mock(spec=GenerationResult)
        mock_result.exists = True
        mock_result.output_path = output_path
        mock_generate.return_value = (mock_result, None)

        strategy = WeasyPrintStrategy()
        request = PdfGenerationRequest(
            render_plan=plan,
            output_path=output_path,
            open_after=True,
        )

        # On Windows, this would call os.startfile
        result = strategy.generate_pdf(request)
        assert result == mock_result
        mock_startfile.assert_called_once_with(str(output_path))

    @mock.patch("sys.platform", "win32")
    @mock.patch("simple_resume.shell.strategies.os.name", "nt")
    @mock.patch("simple_resume.shell.strategies.os.startfile", create=True)
    @mock.patch("pathlib.Path", wraps=Path)
    @mock.patch("simple_resume.shell.strategies.generate_pdf_with_weasyprint")
    def test_generate_pdf_windows_path_safe(
        self,
        mock_generate,
        mock_path_class,
        mock_startfile,
    ) -> None:
        """Guard against WindowsPath instantiation on non-Windows runners."""
        plan = RenderPlan(
            name="test",
            mode=RenderMode.HTML,
            config=ResumeConfig(),
        )
        output_path = Path("/tmp/test.pdf")  # noqa: S108
        mock_result = mock.Mock(spec=GenerationResult)
        mock_result.exists = True
        mock_result.output_path = output_path
        mock_generate.return_value = (mock_result, None)

        strategy = WeasyPrintStrategy()
        request = PdfGenerationRequest(
            render_plan=plan,
            output_path=output_path,
            open_after=True,
        )

        # Should not attempt to construct WindowsPath; uses provided Path object
        result = strategy.generate_pdf(request)
        assert result == mock_result
        mock_startfile.assert_called_once_with(str(output_path))

    @mock.patch("sys.platform", "linux")
    @mock.patch("shutil.which")
    @mock.patch("subprocess.Popen")
    @mock.patch("simple_resume.shell.strategies.generate_pdf_with_weasyprint")
    def test_generate_pdf_with_open_linux(
        self, mock_generate, mock_popen, mock_which
    ) -> None:
        """Test PDF generation with file opening on Linux."""
        plan = RenderPlan(
            name="test",
            mode=RenderMode.HTML,
            config=ResumeConfig(),
        )
        output_path = Path("/tmp/test.pdf")  # noqa: S108
        mock_result = mock.Mock(spec=GenerationResult)
        mock_result.exists = True
        mock_result.output_path = output_path
        mock_generate.return_value = (mock_result, None)
        mock_which.return_value = "/usr/bin/xdg-open"

        strategy = WeasyPrintStrategy()
        request = PdfGenerationRequest(
            render_plan=plan,
            output_path=output_path,
            open_after=True,
        )

        strategy.generate_pdf(request)
        mock_popen.assert_called_once()

    @mock.patch("sys.platform", "linux")
    @mock.patch("shutil.which")
    @mock.patch("simple_resume.shell.strategies.generate_pdf_with_weasyprint")
    def test_generate_pdf_open_linux_no_xdg(self, mock_generate, mock_which) -> None:
        """Test PDF generation on Linux without xdg-open."""
        plan = RenderPlan(
            name="test",
            mode=RenderMode.HTML,
            config=ResumeConfig(),
        )
        output_path = Path("/tmp/test.pdf")  # noqa: S108
        mock_result = mock.Mock(spec=GenerationResult)
        mock_result.exists = True
        mock_result.output_path = output_path
        mock_generate.return_value = (mock_result, None)
        mock_which.return_value = None  # xdg-open not found

        strategy = WeasyPrintStrategy()
        request = PdfGenerationRequest(
            render_plan=plan,
            output_path=output_path,
            open_after=True,
        )

        # Should not raise, just skip opening
        result = strategy.generate_pdf(request)
        assert result == mock_result

    @mock.patch("sys.platform", "darwin")
    @mock.patch("shutil.which")
    @mock.patch("subprocess.Popen")
    @mock.patch("simple_resume.shell.strategies.generate_pdf_with_weasyprint")
    @mock.patch("builtins.print")
    def test_generate_pdf_open_error_handling(
        self, mock_print, mock_generate, mock_popen, mock_which
    ) -> None:
        """Test error handling when opening file fails."""
        plan = RenderPlan(
            name="test",
            mode=RenderMode.HTML,
            config=ResumeConfig(),
        )
        output_path = Path("/tmp/test.pdf")  # noqa: S108
        mock_result = mock.Mock(spec=GenerationResult)
        mock_result.exists = True
        mock_result.output_path = output_path
        mock_generate.return_value = (mock_result, None)
        mock_which.return_value = "open"
        mock_popen.side_effect = OSError("Failed to open")

        strategy = WeasyPrintStrategy()
        request = PdfGenerationRequest(
            render_plan=plan,
            output_path=output_path,
            open_after=True,
        )

        # Should not raise, just print warning
        result = strategy.generate_pdf(request)
        assert result == mock_result
        mock_print.assert_called_once()

    def test_get_template_name(self) -> None:
        """Test getting template name."""
        plan = RenderPlan(
            name="test",
            mode=RenderMode.HTML,
            config=ResumeConfig(),
            template_name="custom.html",
        )
        strategy = WeasyPrintStrategy()
        assert strategy.get_template_name(plan) == "custom.html"

    def test_get_template_name_fallback(self) -> None:
        """Test getting template name with fallback."""
        plan = RenderPlan(
            name="test",
            mode=RenderMode.HTML,
            config=ResumeConfig(),
        )
        strategy = WeasyPrintStrategy()
        assert strategy.get_template_name(plan) == "unknown"


class TestLatexStrategy:
    """Tests for LatexStrategy."""

    @mock.patch("simple_resume.shell.strategies.EffectExecutor")
    @mock.patch("simple_resume.shell.strategies.prepare_pdf_with_latex")
    def test_generate_pdf_basic(
        self, mock_prepare, mock_executor_class, tmp_path
    ) -> None:
        """Test basic LaTeX PDF generation."""
        plan = RenderPlan(
            name="test",
            mode=RenderMode.LATEX,
            config=ResumeConfig(),
        )
        output_path = tmp_path / "test.pdf"
        output_path.write_text("test")

        mock_metadata = mock.Mock()
        mock_effects: list[mock.Mock] = []  # Return empty list for effects
        mock_prepare.return_value = ("tex_content", mock_effects, mock_metadata)

        strategy = LatexStrategy()
        request = PdfGenerationRequest(
            render_plan=plan,
            output_path=output_path,
            open_after=False,
        )

        result = strategy.generate_pdf(request)
        assert isinstance(result, GenerationResult)
        assert result.output_path == output_path
        mock_prepare.assert_called_once()
        mock_executor_class.return_value.execute_many.assert_called_once_with(
            mock_effects
        )

    @mock.patch("simple_resume.shell.strategies.prepare_pdf_with_latex")
    def test_generate_pdf_with_compilation_error(self, mock_prepare, tmp_path) -> None:
        """Test LaTeX generation with compilation error."""
        plan = RenderPlan(
            name="test",
            mode=RenderMode.LATEX,
            config=ResumeConfig(),
        )
        output_path = tmp_path / "test.pdf"
        mock_prepare.side_effect = LatexCompilationError("Compilation failed")

        strategy = LatexStrategy()
        request = PdfGenerationRequest(
            render_plan=plan,
            output_path=output_path,
        )

        with pytest.raises(GenerationError, match="LaTeX compilation failed"):
            strategy.generate_pdf(request)

    @mock.patch("sys.platform", "darwin")
    @mock.patch("shutil.which")
    @mock.patch("subprocess.Popen")
    @mock.patch("simple_resume.shell.strategies.EffectExecutor")
    @mock.patch("simple_resume.shell.strategies.prepare_pdf_with_latex")
    def test_generate_pdf_with_open(
        self, mock_prepare, mock_executor_class, mock_popen, mock_which, tmp_path
    ) -> None:
        """Test LaTeX PDF generation with file opening."""
        plan = RenderPlan(
            name="test",
            mode=RenderMode.LATEX,
            config=ResumeConfig(),
        )
        output_path = tmp_path / "test.pdf"
        output_path.write_text("test")

        mock_metadata = mock.Mock()
        mock_effects: list[mock.Mock] = []  # Return empty list for effects
        mock_prepare.return_value = ("tex_content", mock_effects, mock_metadata)
        mock_which.return_value = "/usr/bin/open"

        strategy = LatexStrategy()
        request = PdfGenerationRequest(
            render_plan=plan,
            output_path=output_path,
            open_after=True,
        )

        result = strategy.generate_pdf(request)
        assert result.output_path == output_path
        mock_popen.assert_called_once()
        mock_executor_class.return_value.execute_many.assert_called_once_with(
            mock_effects
        )

    def test_get_template_name(self) -> None:
        """Test getting template name for LaTeX."""
        plan = RenderPlan(
            name="test",
            mode=RenderMode.LATEX,
            config=ResumeConfig(),
            template_name="custom.tex",
        )
        strategy = LatexStrategy()
        assert strategy.get_template_name(plan) == "custom.tex"

    def test_get_template_name_fallback(self) -> None:
        """Test getting template name with fallback."""
        plan = RenderPlan(
            name="test",
            mode=RenderMode.LATEX,
            config=ResumeConfig(),
        )
        strategy = LatexStrategy()
        assert strategy.get_template_name(plan) == "latex/basic.tex"
