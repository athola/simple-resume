"""Test LaTeX rendering operations in the shell layer."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from simple_resume.core.latex import LatexRenderResult
from simple_resume.shell.render.latex import (
    LatexCompilationError,
    _jinja_environment,
    build_latex_context,
    compile_tex_to_html,
    compile_tex_to_pdf,
    render_resume_latex,
    render_resume_latex_from_data,
)


class TestJinjaEnvironment:
    """Test Jinja2 environment creation."""

    def test_jinja_environment_creation(self) -> None:
        """Test Jinja2 environment is created correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_root = Path(temp_dir)
            env = _jinja_environment(template_root)

            assert env.loader is not None
            # autoescape is a function, not a boolean
            assert callable(env.autoescape)

    def test_jinja_environment_loads_templates(self) -> None:
        """Test Jinja2 environment can load templates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_root = Path(temp_dir)
            template_file = template_root / "test.tex"
            template_file.write_text("Hello {{ name }}!")

            env = _jinja_environment(template_root)
            template = env.get_template("test.tex")
            result = template.render(name="World")

            assert result == "Hello World!"


class TestLatexCompilationError:
    """Test LaTeX compilation error."""

    def test_latex_compilation_error_creation(self) -> None:
        """Test LaTeX compilation error can be created."""
        error = LatexCompilationError("Test error")
        assert str(error) == "Test error"
        assert error.log is None

    def test_latex_compilation_error_with_log(self) -> None:
        """Test LaTeX compilation error can include log."""
        log_content = "LaTeX log output"
        error = LatexCompilationError("Test error", log=log_content)
        assert str(error) == "Test error"
        assert error.log == log_content


class TestBuildLatexContext:
    """Test LaTeX context building with I/O operations."""

    @patch("simple_resume.shell.render.latex.build_latex_context_pure")
    @patch("simple_resume.shell.render.latex.fontawesome_support_block")
    def test_build_latex_context_without_static_dir(
        self, mock_fontawesome_block: MagicMock, mock_build_pure: MagicMock
    ) -> None:
        """Test context building without static directory."""
        mock_build_pure.return_value = {"test": "value"}
        mock_fontawesome_block.return_value = "% FontAwesome block"

        data = {"name": "Test Resume"}
        context = build_latex_context(data)

        mock_build_pure.assert_called_once_with(data)
        mock_fontawesome_block.assert_called_once_with(None)
        assert context["test"] == "value"
        assert context["fontawesome_block"] == "% FontAwesome block"

    @patch("simple_resume.shell.render.latex.build_latex_context_pure")
    @patch("simple_resume.shell.render.latex.fontawesome_support_block")
    @patch("pathlib.Path.is_dir")
    def test_build_latex_context_with_fontawesome_dir(
        self,
        mock_is_dir: MagicMock,
        mock_fontawesome_block: MagicMock,
        mock_build_pure: MagicMock,
    ) -> None:
        """Test context building with FontAwesome directory present."""
        mock_build_pure.return_value = {"test": "value"}
        mock_fontawesome_block.return_value = "% FontAwesome block"
        mock_is_dir.return_value = True

        data = {"name": "Test Resume"}
        static_dir = Path("/static")

        with patch("pathlib.Path.resolve") as mock_resolve:
            mock_resolve.return_value = Path("/static/fonts/fontawesome")
            context = build_latex_context(data, static_dir=static_dir)

            mock_is_dir.assert_called_once()
            mock_fontawesome_block.assert_called_once_with("/static/fonts/fontawesome/")
            assert context["fontawesome_block"] == "% FontAwesome block"

    @patch("simple_resume.shell.render.latex.build_latex_context_pure")
    @patch("simple_resume.shell.render.latex.fontawesome_support_block")
    @patch("pathlib.Path.is_dir")
    def test_build_latex_context_without_fontawesome_dir(
        self,
        mock_is_dir: MagicMock,
        mock_fontawesome_block: MagicMock,
        mock_build_pure: MagicMock,
    ) -> None:
        """Test context building without FontAwesome directory."""
        mock_build_pure.return_value = {"test": "value"}
        mock_fontawesome_block.return_value = "% FontAwesome block"
        mock_is_dir.return_value = False

        data = {"name": "Test Resume"}
        static_dir = Path("/static")

        context = build_latex_context(data, static_dir=static_dir)

        mock_is_dir.assert_called_once()
        mock_fontawesome_block.assert_called_once_with(None)
        assert context["fontawesome_block"] == "% FontAwesome block"


class TestRenderResumeLatexFromData:
    """Test LaTeX rendering from data."""

    @patch("simple_resume.shell.render.latex.build_latex_context")
    @patch("simple_resume.shell.render.latex._jinja_environment")
    @patch("simple_resume.shell.config.resolve_paths")
    def test_render_resume_latex_from_data(
        self,
        mock_resolve_paths: MagicMock,
        mock_jinja_env: MagicMock,
        mock_build_context: MagicMock,
    ) -> None:
        """Test LaTeX rendering from data dictionary."""
        # Mock paths
        mock_paths = MagicMock()
        mock_paths.templates = Path("/templates")
        mock_resolve_paths.return_value = mock_paths

        # Mock context
        mock_context = {"name": "Test", "content": "Resume content"}
        mock_build_context.return_value = mock_context

        # Mock Jinja template
        mock_template = MagicMock()
        mock_template.render.return_value = (
            "\\documentclass{article}\n\\begin{document}\nTest Resume\n\\end{document}"
        )
        mock_env = MagicMock()
        mock_env.get_template.return_value = mock_template
        mock_jinja_env.return_value = mock_env

        data = {"name": "Test Resume"}
        result = render_resume_latex_from_data(data)

        assert isinstance(result, LatexRenderResult)
        assert "\\documentclass" in result.tex
        assert result.context == mock_context

        mock_resolve_paths.assert_called_once()
        mock_build_context.assert_called_once_with(data, static_dir=mock_paths.static)
        mock_jinja_env.assert_called_once_with(mock_paths.templates)
        mock_env.get_template.assert_called_once_with("latex/basic.tex")
        mock_template.render.assert_called_once_with(**mock_context)


class TestRenderResumeLatex:
    """Test LaTeX rendering with file I/O."""

    @patch("simple_resume.shell.render.latex.render_resume_latex_from_data")
    @patch("simple_resume.shell.config.resolve_paths")
    def test_render_resume_latex(
        self, mock_resolve_paths: MagicMock, mock_render_from_data: MagicMock
    ) -> None:
        """Test LaTeX rendering from resume name."""
        # Mock data and paths
        mock_data = {"name": "Test Resume", "content": "Resume content"}
        mock_paths = MagicMock()
        mock_resolve_paths.return_value = mock_paths

        # Mock rendering result - this is what we're testing
        mock_result = LatexRenderResult(
            tex="\\documentclass...", context={"name": "Test"}
        )
        mock_render_from_data.return_value = mock_result

        # Patch the get_content call within the function
        with patch(
            "simple_resume.shell.render.latex.get_content", return_value=mock_data
        ) as mock_get_content:
            result = render_resume_latex("test_resume")

            assert result == mock_result
            mock_get_content.assert_called_once_with(
                "test_resume", paths=mock_paths, transform_markdown=False
            )
            mock_render_from_data.assert_called_once_with(
                mock_data, paths=mock_paths, template_name="latex/basic.tex"
            )


class TestCompileTexToPdf:
    """Test PDF compilation from LaTeX."""

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_compile_tex_to_pdf_success(
        self, mock_subprocess: MagicMock, mock_which: MagicMock
    ) -> None:
        """Test successful PDF compilation."""
        mock_which.return_value = "/usr/bin/xelatex"
        mock_subprocess.return_value = MagicMock(returncode=0)

        with tempfile.TemporaryDirectory() as temp_dir:
            tex_path = Path(temp_dir) / "test.tex"
            tex_path.write_text(
                "\\documentclass{article}\\begin{document}Test\\end{document}"
            )

            result = compile_tex_to_pdf(tex_path)

            assert result == tex_path.with_suffix(".pdf")
            mock_which.assert_called()
            mock_subprocess.assert_called_once()

    @patch("shutil.which")
    def test_compile_tex_to_pdf_no_engine(self, mock_which: MagicMock) -> None:
        """Test PDF compilation with no LaTeX engine available."""
        mock_which.return_value = None

        with tempfile.TemporaryDirectory() as temp_dir:
            tex_path = Path(temp_dir) / "test.tex"
            tex_path.write_text(
                "\\documentclass{article}\\begin{document}Test\\end{document}"
            )

            with pytest.raises(LatexCompilationError) as exc_info:
                compile_tex_to_pdf(tex_path)

            assert "No LaTeX engine found" in str(exc_info.value)

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_compile_tex_to_pdf_compilation_failure(
        self, mock_subprocess: MagicMock, mock_which: MagicMock
    ) -> None:
        """Test PDF compilation failure."""
        mock_which.return_value = "/usr/bin/xelatex"
        mock_subprocess.return_value = MagicMock(
            returncode=1, stdout=b"Error output", stderr=b"Error details"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            tex_path = Path(temp_dir) / "test.tex"
            tex_path.write_text(
                "\\documentclass{article}\\begin{document}Test\\end{document}"
            )

            with pytest.raises(LatexCompilationError) as exc_info:
                compile_tex_to_pdf(tex_path)

            assert "LaTeX compilation failed" in str(exc_info.value)
            assert getattr(exc_info.value, "log", "") == "Error output\nError details"


class TestCompileTexToHtml:
    """Test HTML compilation from LaTeX."""

    @patch("shutil.which")
    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.write_text")
    def test_compile_tex_to_html_pandoc_success(
        self,
        mock_write_text: MagicMock,
        mock_exists: MagicMock,
        mock_subprocess: MagicMock,
        mock_which: MagicMock,
    ) -> None:
        """Test successful HTML compilation with pandoc."""
        mock_which.side_effect = (
            lambda tool: "/usr/bin/pandoc" if tool == "pandoc" else None
        )
        mock_subprocess.return_value = MagicMock(returncode=0)
        mock_exists.return_value = True

        with tempfile.TemporaryDirectory() as temp_dir:
            tex_path = Path(temp_dir) / "test.tex"
            tex_path.write_text(
                "\\documentclass{article}\\begin{document}Test\\end{document}"
            )

            result = compile_tex_to_html(tex_path)

            assert result == tex_path.with_suffix(".html")

    @patch("shutil.which")
    def test_compile_tex_to_html_no_tool(self, mock_which: MagicMock) -> None:
        """Test HTML compilation with no conversion tool available."""
        mock_which.return_value = None

        with tempfile.TemporaryDirectory() as temp_dir:
            tex_path = Path(temp_dir) / "test.tex"
            tex_path.write_text(
                "\\documentclass{article}\\begin{document}Test\\end{document}"
            )

            with pytest.raises(LatexCompilationError) as exc_info:
                compile_tex_to_html(tex_path)

            assert "No LaTeX-to-HTML tool found" in str(exc_info.value)

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_compile_tex_to_html_pandoc_failure(
        self, mock_subprocess: MagicMock, mock_which: MagicMock
    ) -> None:
        """Test HTML compilation failure with pandoc."""
        mock_which.side_effect = (
            lambda tool: "/usr/bin/pandoc" if tool == "pandoc" else None
        )
        mock_subprocess.return_value = MagicMock(
            returncode=1, stdout=b"Pandoc error", stderr=b"Pandoc failed"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            tex_path = Path(temp_dir) / "test.tex"
            tex_path.write_text(
                "\\documentclass{article}\\begin{document}Test\\end{document}"
            )

            with pytest.raises(LatexCompilationError) as exc_info:
                compile_tex_to_html(tex_path)

            assert "LaTeX to HTML conversion via pandoc failed" in str(exc_info.value)
