"""Unit tests for shell layer resume_extensions module.

Focuses on testing error handling paths and edge cases that were previously uncovered.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from simple_resume import ConfigurationError, GenerationError, Resume
from simple_resume.core.constants import OutputFormat
from simple_resume.core.paths import Paths
from simple_resume.shell.resume_extensions import (
    _generate_markdown_from_context,
    generate,
    render_markdown_file,
    render_tex_file,
    to_html,
    to_markdown,
    to_pdf,
    to_tex,
)
from tests.conftest import create_complete_resume_data


@pytest.fixture
def sample_resume(temp_dir: Path) -> Resume:
    """Create a sample resume for testing."""
    # Create paths with proper structure
    paths = Paths(
        data=temp_dir / "data",
        input=temp_dir / "data",
        output=temp_dir / "output",
        content=temp_dir / "content",
        templates=temp_dir / "templates",
        static=temp_dir / "static",
    )

    # Create directories
    paths.data.mkdir(parents=True, exist_ok=True)
    paths.output.mkdir(parents=True, exist_ok=True)

    resume_data = create_complete_resume_data(
        template="resume_no_bars",
        full_name="Jane Doe",
    )

    return Resume.from_data(
        data=resume_data,
        name="jane",
        paths=paths,
        raw_data=resume_data,
    )


class TestToPdf:
    """Tests for to_pdf function."""

    def test_to_pdf_raises_configuration_error_when_no_paths(
        self, sample_resume: Resume
    ) -> None:
        """Test to_pdf raises ConfigurationError when resume has no paths."""
        resume_without_paths = Resume.from_data(
            sample_resume.data, name=sample_resume.name, paths=None
        )

        with pytest.raises(ConfigurationError) as exc_info:
            to_pdf(resume_without_paths)

        assert "No paths available" in str(exc_info.value)

    @patch("simple_resume.shell.resume_extensions._get_pdf_strategy")
    def test_to_pdf_wraps_exceptions_in_generation_error(
        self, mock_strategy: Mock, sample_resume: Resume
    ) -> None:
        """Test to_pdf wraps unexpected exceptions in GenerationError."""
        # Make strategy raise an unexpected error
        mock_strategy_instance = MagicMock()
        mock_strategy_instance.generate.side_effect = RuntimeError("Unexpected error")
        mock_strategy.return_value = mock_strategy_instance

        with pytest.raises(GenerationError) as exc_info:
            to_pdf(sample_resume)

        assert "Failed to generate PDF" in str(exc_info.value)
        assert exc_info.value.__cause__ is not None

    @patch("simple_resume.shell.resume_extensions._get_pdf_strategy")
    def test_to_pdf_uses_custom_strategy_when_provided(
        self, mock_default_strategy: Mock, sample_resume: Resume
    ) -> None:
        """Test to_pdf uses custom strategy when provided."""
        custom_strategy = MagicMock()
        custom_strategy.generate.return_value = (
            MagicMock(output_path=Path("test.pdf")),
            1,
        )

        to_pdf(sample_resume, strategy=custom_strategy)

        # Custom strategy should be used, not default
        mock_default_strategy.assert_not_called()
        custom_strategy.generate.assert_called_once()


class TestToHtml:
    """Tests for to_html function."""

    def test_to_html_raises_configuration_error_when_no_paths(
        self, sample_resume: Resume
    ) -> None:
        """Test to_html raises ConfigurationError when resume has no paths."""
        resume_without_paths = Resume.from_data(
            sample_resume.data, name=sample_resume.name, paths=None
        )

        with pytest.raises(ConfigurationError) as exc_info:
            to_html(resume_without_paths)

        assert "No paths available" in str(exc_info.value)

    @patch("simple_resume.shell.resume_extensions.shell_open_file")
    def test_to_html_opens_file_when_open_after_true(
        self, mock_open: Mock, sample_resume: Resume, temp_dir: Path
    ) -> None:
        """Test to_html opens file when open_after=True."""
        output_path = temp_dir / "output" / "jane.html"

        with patch(
            "simple_resume.shell.resume_extensions.generate_html_with_jinja"
        ) as mock_gen:
            mock_gen.return_value = MagicMock(
                output_path=output_path, exists=lambda: True
            )
            output_path.touch()  # Create file so exists() returns True

            to_html(sample_resume, open_after=True)

            mock_open.assert_called_once_with(output_path, format_type="html")

    @patch("simple_resume.shell.resume_extensions.generate_html_with_jinja")
    def test_to_html_wraps_exceptions_in_generation_error(
        self, mock_gen: Mock, sample_resume: Resume
    ) -> None:
        """Test to_html wraps unexpected exceptions in GenerationError."""
        mock_gen.side_effect = RuntimeError("Template error")

        with pytest.raises(GenerationError) as exc_info:
            to_html(sample_resume)

        assert "Failed to generate HTML" in str(exc_info.value)
        assert exc_info.value.__cause__ is not None


class TestToMarkdown:
    """Tests for to_markdown function."""

    def test_to_markdown_raises_configuration_error_when_no_paths(
        self, sample_resume: Resume
    ) -> None:
        """Test to_markdown raises ConfigurationError when resume has no paths."""
        resume_without_paths = Resume.from_data(
            sample_resume.data, name=sample_resume.name, paths=None
        )

        with pytest.raises(ConfigurationError) as exc_info:
            to_markdown(resume_without_paths)

        assert "No paths available" in str(exc_info.value)

    @patch("simple_resume.shell.resume_extensions.shell_open_file")
    def test_to_markdown_opens_file_when_open_after_true(
        self, mock_open: Mock, sample_resume: Resume, temp_dir: Path
    ) -> None:
        """Test to_markdown opens file when open_after=True."""
        # Create a markdown file
        result = to_markdown(sample_resume, open_after=False)
        output_path = result.output_path

        # Now test opening
        to_markdown(sample_resume, open_after=True)

        mock_open.assert_called_once_with(output_path, format_type="markdown")

    def test_to_markdown_wraps_exceptions_in_generation_error(
        self, sample_resume: Resume
    ) -> None:
        """Test to_markdown wraps unexpected exceptions in GenerationError."""
        # Create a resume with problematic data that will cause an error
        bad_resume = Resume.from_data(
            data={"full_name": "Bad Resume"}, name="bad", paths=sample_resume.paths
        )

        # The validate_or_raise call should work, but let's patch to force an error.
        # Must patch at the actual Resume class location since Resume is
        # imported via TYPE_CHECKING.
        with patch(
            "simple_resume.core.resume.Resume.validate_or_raise",
            side_effect=RuntimeError("Validation error"),
        ):
            with pytest.raises(GenerationError) as exc_info:
                to_markdown(bad_resume)

            assert "Failed to generate Markdown" in str(exc_info.value)
            assert exc_info.value.__cause__ is not None


class TestGenerateMarkdownFromContext:
    """Tests for _generate_markdown_from_context helper function."""

    def test_generates_basic_markdown_with_full_name(self) -> None:
        """Test markdown generation with full name."""
        context = {"full_name": "John Smith"}
        result = _generate_markdown_from_context(context, "resume1")

        assert "# John Smith" in result
        assert result.startswith("#")

    def test_includes_contact_info_when_present(self) -> None:
        """Test markdown includes email, phone, location when present."""
        context: dict[str, object] = {
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "555-1234",
            "location": "San Francisco, CA",
        }
        result = _generate_markdown_from_context(context, "resume1")

        assert "jane@example.com" in result
        assert "555-1234" in result
        assert "San Francisco, CA" in result

    def test_handles_empty_context_gracefully(self) -> None:
        """Test markdown generation handles empty context."""
        context: dict[str, object] = {}
        result = _generate_markdown_from_context(context, "resume1")

        # Should still have a header
        assert "# resume1" in result
        assert result  # Should not be empty


class TestCustomStrategyInjection:
    """Tests for custom strategy injection in to_pdf."""

    @patch("simple_resume.shell.resume_extensions.DefaultPdfGenerationStrategy")
    def test_custom_strategy_overrides_default(
        self, mock_default: Mock, sample_resume: Resume
    ) -> None:
        """Test that custom strategy overrides default strategy selection."""
        custom_strategy = MagicMock()
        custom_strategy.generate.return_value = (
            MagicMock(output_path=Path("custom.pdf")),
            2,
        )

        to_pdf(sample_resume, strategy=custom_strategy)

        # Default strategy should not be instantiated
        mock_default.assert_not_called()
        # Custom strategy should be used
        custom_strategy.generate.assert_called_once()

    @patch("simple_resume.shell.resume_extensions._get_pdf_strategy")
    def test_default_strategy_used_when_none_provided(
        self, mock_get_strategy: Mock, sample_resume: Resume
    ) -> None:
        """Test that default strategy is used when none is provided."""
        mock_strategy = MagicMock()
        mock_strategy.generate.return_value = (
            MagicMock(output_path=Path("default.pdf")),
            1,
        )
        mock_get_strategy.return_value = mock_strategy

        to_pdf(sample_resume)

        # Should call _get_pdf_strategy with the render_plan.mode.value
        # For PDF with preview=False, mode is 'pdf' by default
        mock_get_strategy.assert_called_once()


class TestErrorBoundaryConditions:
    """Tests for error boundary conditions and edge cases."""

    def test_to_pdf_preserves_original_exception_chain(
        self, sample_resume: Resume
    ) -> None:
        """Test that to_pdf preserves exception chaining."""
        resume_with_invalid_paths = Resume.from_data(
            sample_resume.data,
            name=sample_resume.name,
            paths=MagicMock(output=Path("/invalid/path")),
        )

        with pytest.raises(GenerationError) as exc_info:
            to_pdf(resume_with_invalid_paths)

        # Check that the original exception is chained
        assert exc_info.value.__cause__ is not None

    def test_to_html_preserves_original_exception_chain(
        self, sample_resume: Resume
    ) -> None:
        """Test that to_html preserves exception chaining."""
        resume_with_invalid_paths = Resume.from_data(
            sample_resume.data,
            name=sample_resume.name,
            paths=MagicMock(output=Path("/invalid/path")),
        )

        with pytest.raises(GenerationError) as exc_info:
            to_html(resume_with_invalid_paths)

        # Check that the original exception is chained
        assert exc_info.value.__cause__ is not None

    def test_to_markdown_preserves_original_exception_chain(
        self, sample_resume: Resume
    ) -> None:
        """Test that to_markdown preserves exception chaining."""
        resume_with_invalid_paths = Resume.from_data(
            sample_resume.data,
            name=sample_resume.name,
            paths=MagicMock(output=Path("/invalid/path")),
        )

        with pytest.raises(GenerationError) as exc_info:
            to_markdown(resume_with_invalid_paths)

        # Check that the original exception is chained
        assert exc_info.value.__cause__ is not None


class TestOutputPathResolution:
    """Tests for output path resolution logic."""

    def test_to_pdf_uses_provided_output_path(
        self, sample_resume: Resume, temp_dir: Path
    ) -> None:
        """Test to_pdf uses provided output path directly."""
        custom_path = temp_dir / "custom" / "output.pdf"

        with patch(
            "simple_resume.shell.resume_extensions._get_pdf_strategy"
        ) as mock_strategy:
            mock_strategy_instance = MagicMock()
            mock_strategy_instance.generate.return_value = (
                MagicMock(output_path=custom_path),
                1,
            )
            mock_strategy.return_value = mock_strategy_instance

            result = to_pdf(sample_resume, output_path=custom_path)

            assert result.output_path == custom_path

    def test_to_html_uses_provided_output_path(
        self, sample_resume: Resume, temp_dir: Path
    ) -> None:
        """Test to_html uses provided output path directly."""
        custom_path = temp_dir / "custom" / "output.html"

        with patch(
            "simple_resume.shell.resume_extensions.generate_html_with_jinja"
        ) as mock_gen:
            mock_gen.return_value = MagicMock(output_path=custom_path)

            result = to_html(sample_resume, output_path=custom_path)

            assert result.output_path == custom_path

    def test_to_markdown_uses_provided_output_path(
        self, sample_resume: Resume, temp_dir: Path
    ) -> None:
        """Test to_markdown uses provided output path directly."""
        custom_path = temp_dir / "custom" / "output.md"

        result = to_markdown(sample_resume, output_path=custom_path)

        assert result.output_path == custom_path


class TestGenerateMarkdownFromContextSections:
    """Tests for detailed sections in _generate_markdown_from_context."""

    def test_includes_summary_section(self) -> None:
        """Test markdown includes summary section when present."""
        context: dict[str, object] = {
            "full_name": "John Doe",
            "summary": "Experienced software engineer with 10 years in industry.",
        }
        result = _generate_markdown_from_context(context, "resume1")

        assert "## Summary" in result
        assert "Experienced software engineer" in result

    def test_includes_links_section(self) -> None:
        """Test markdown includes links when present."""
        context: dict[str, object] = {
            "full_name": "Jane Doe",
            "links": [
                {"url": "https://github.com/janedoe", "label": "GitHub"},
                {"url": "https://linkedin.com/in/janedoe", "label": "LinkedIn"},
            ],
        }
        result = _generate_markdown_from_context(context, "resume1")

        assert "[GitHub](https://github.com/janedoe)" in result
        assert "[LinkedIn](https://linkedin.com/in/janedoe)" in result

    def test_includes_experience_section(self) -> None:
        """Test markdown includes experience section."""
        context: dict[str, object] = {
            "full_name": "John Doe",
            "experience": [
                {
                    "title": "Senior Developer",
                    "company": "TechCorp",
                    "dates": "2020-Present",
                    "highlights": ["Built scalable systems", "Led team of 5"],
                }
            ],
        }
        result = _generate_markdown_from_context(context, "resume1")

        assert "## Experience" in result
        assert "### Senior Developer at TechCorp" in result
        assert "*2020-Present*" in result
        assert "- Built scalable systems" in result

    def test_includes_education_section(self) -> None:
        """Test markdown includes education section."""
        context: dict[str, object] = {
            "full_name": "Jane Doe",
            "education": [
                {
                    "degree": "BS Computer Science",
                    "school": "University of Tech",
                    "dates": "2015-2019",
                }
            ],
        }
        result = _generate_markdown_from_context(context, "resume1")

        assert "## Education" in result
        assert "### BS Computer Science" in result
        assert "*University of Tech*" in result
        assert "*2015-2019*" in result

    def test_includes_skills_section(self) -> None:
        """Test markdown includes skills section."""
        context: dict[str, object] = {
            "full_name": "John Doe",
            "skills": [
                {"category": "Languages", "items": ["Python", "JavaScript"]},
                {"category": "Frameworks", "items": ["Django", "React"]},
            ],
        }
        result = _generate_markdown_from_context(context, "resume1")

        assert "## Skills" in result
        assert "**Languages:** Python, JavaScript" in result
        assert "**Frameworks:** Django, React" in result


class TestToTex:
    """Tests for to_tex function."""

    def test_to_tex_raises_configuration_error_when_no_paths(
        self, sample_resume: Resume
    ) -> None:
        """Test to_tex raises ConfigurationError when resume has no paths."""
        resume_without_paths = Resume.from_data(
            sample_resume.data, name=sample_resume.name, paths=None
        )

        with pytest.raises(ConfigurationError) as exc_info:
            to_tex(resume_without_paths)

        assert "No paths available" in str(exc_info.value)

    @patch("simple_resume.shell.resume_extensions.render_resume_latex_from_data")
    def test_to_tex_generates_tex_file(
        self, mock_render: Mock, sample_resume: Resume
    ) -> None:
        """Test to_tex generates .tex file content."""
        mock_render.return_value = MagicMock(
            tex=r"\documentclass{article}\begin{document}Test\end{document}"
        )

        result = to_tex(sample_resume, open_after=False)

        assert result.output_path.suffix == ".tex"
        assert result.format_type == "tex"
        mock_render.assert_called_once()


class TestRenderMarkdownFile:
    """Tests for render_markdown_file function."""

    def test_render_markdown_file_not_found_raises_error(self, temp_dir: Path) -> None:
        """Test render_markdown_file raises error when file doesn't exist."""
        non_existent = temp_dir / "nonexistent.md"

        with pytest.raises(GenerationError) as exc_info:
            render_markdown_file(non_existent)

        assert "not found" in str(exc_info.value)

    @patch("simple_resume.shell.resume_extensions._markdown.markdown")
    def test_render_markdown_file_creates_html(
        self, mock_md: Mock, temp_dir: Path
    ) -> None:
        """Test render_markdown_file creates HTML from markdown."""
        # Create test markdown file
        md_file = temp_dir / "test.md"
        md_file.write_text("# Hello World\n\nThis is a test.", encoding="utf-8")

        mock_md.return_value = "<h1>Hello World</h1><p>This is a test.</p>"

        result = render_markdown_file(md_file, open_after=False)

        assert result.output_path.suffix == ".html"
        assert result.output_path.exists()
        assert "Hello World" in result.output_path.read_text()


class TestRenderTexFile:
    """Tests for render_tex_file function."""

    def test_render_tex_file_not_found_raises_error(self, temp_dir: Path) -> None:
        """Test render_tex_file raises error when file doesn't exist."""
        non_existent = temp_dir / "nonexistent.tex"

        with pytest.raises(GenerationError) as exc_info:
            render_tex_file(non_existent)

        assert "not found" in str(exc_info.value)

    @patch("simple_resume.shell.resume_extensions.compile_tex_to_pdf")
    def test_render_tex_file_creates_pdf(
        self, mock_compile: Mock, temp_dir: Path
    ) -> None:
        """Test render_tex_file creates PDF from tex."""
        # Create test tex file
        tex_file = temp_dir / "test.tex"
        tex_file.write_text(
            r"\documentclass{article}\begin{document}Test\end{document}",
            encoding="utf-8",
        )

        expected_pdf = temp_dir / "test.pdf"
        mock_compile.return_value = expected_pdf

        result = render_tex_file(tex_file, open_after=False)

        assert result.output_path.suffix == ".pdf"
        mock_compile.assert_called_once_with(tex_file)


class TestGenerateDispatcher:
    """Tests for generate dispatcher function."""

    def test_generate_with_pdf_format(self, sample_resume: Resume) -> None:
        """Test generate routes to PDF format correctly."""
        with patch("simple_resume.shell.resume_extensions.to_pdf") as mock_to_pdf:
            mock_to_pdf.return_value = MagicMock(
                output_path=Path("test.pdf"), format_type="pdf"
            )

            result = generate(sample_resume, format_type=OutputFormat.PDF)

            mock_to_pdf.assert_called_once()
            assert result.format_type == "pdf"

    def test_generate_with_html_format(self, sample_resume: Resume) -> None:
        """Test generate routes to HTML format correctly."""
        with patch("simple_resume.shell.resume_extensions.to_html") as mock_to_html:
            mock_to_html.return_value = MagicMock(
                output_path=Path("test.html"), format_type="html"
            )

            result = generate(sample_resume, format_type=OutputFormat.HTML)

            mock_to_html.assert_called_once()
            assert result.format_type == "html"

    def test_generate_with_markdown_format(self, sample_resume: Resume) -> None:
        """Test generate routes to Markdown format correctly."""
        with patch("simple_resume.shell.resume_extensions.to_markdown") as mock_to_md:
            mock_to_md.return_value = MagicMock(
                output_path=Path("test.md"), format_type="markdown"
            )

            result = generate(sample_resume, format_type=OutputFormat.MARKDOWN)

            mock_to_md.assert_called_once()
            assert result.format_type == "markdown"

    def test_generate_with_tex_format(self, sample_resume: Resume) -> None:
        """Test generate routes to TeX format correctly."""
        with patch("simple_resume.shell.resume_extensions.to_tex") as mock_to_tex:
            mock_to_tex.return_value = MagicMock(
                output_path=Path("test.tex"), format_type="tex"
            )

            result = generate(sample_resume, format_type=OutputFormat.TEX)

            mock_to_tex.assert_called_once()
            assert result.format_type == "tex"

    def test_generate_with_latex_format_alias(self, sample_resume: Resume) -> None:
        """Test generate routes LaTeX alias to TeX format."""
        with patch("simple_resume.shell.resume_extensions.to_tex") as mock_to_tex:
            mock_to_tex.return_value = MagicMock(
                output_path=Path("test.tex"), format_type="tex"
            )

            result = generate(sample_resume, format_type=OutputFormat.LATEX)

            mock_to_tex.assert_called_once()
            assert result.format_type == "tex"

    def test_generate_with_string_format(self, sample_resume: Resume) -> None:
        """Test generate accepts string format and normalizes."""
        with patch("simple_resume.shell.resume_extensions.to_pdf") as mock_to_pdf:
            mock_to_pdf.return_value = MagicMock(
                output_path=Path("test.pdf"), format_type="pdf"
            )

            result = generate(sample_resume, format_type="pdf")

            mock_to_pdf.assert_called_once()
            assert result.format_type == "pdf"

    def test_generate_with_unsupported_format_raises_error(
        self, sample_resume: Resume
    ) -> None:
        """Test generate raises ValueError for unsupported format."""
        with pytest.raises(ValueError) as exc_info:
            generate(sample_resume, format_type="unsupported")

        assert "Unsupported format" in str(exc_info.value)
