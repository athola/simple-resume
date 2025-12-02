"""Tests for core/generate/exceptions.py."""

from __future__ import annotations

from pathlib import Path

from simple_resume.core.generate.exceptions import GenerationError, TemplateError


class TestGenerationError:
    """Tests for GenerationError exception."""

    def test_basic_creation(self) -> None:
        """Test basic GenerationError creation."""
        error = GenerationError("Test error")
        assert str(error) == "Test error"
        assert error.output_path is None
        assert error.format_type is None
        assert error.resume_name is None

    def test_with_output_path(self) -> None:
        """Test GenerationError with output_path metadata."""
        output_path = Path("/tmp/test.pdf")  # noqa: S108
        error = GenerationError("Test error", output_path=output_path)
        assert error.output_path == str(output_path)

    def test_with_format_type(self) -> None:
        """Test GenerationError with format_type metadata."""
        error = GenerationError("Test error", format_type="pdf")
        assert error.format_type == "pdf"
        assert "format=pdf" in str(error)

    def test_with_resume_name(self) -> None:
        """Test GenerationError with resume_name metadata."""
        error = GenerationError("Test error", resume_name="john_doe")
        assert error.resume_name == "john_doe"

    def test_with_context(self) -> None:
        """Test GenerationError with context metadata."""
        context = {"key": "value"}
        error = GenerationError("Test error", context=context)
        assert error.context == context

    def test_with_filename(self) -> None:
        """Test GenerationError with filename metadata."""
        error = GenerationError("Test error", filename="test.yaml")
        assert error.filename == "test.yaml"

    def test_filename_defaults_to_resume_name(self) -> None:
        """Test that filename defaults to resume_name when not provided."""
        error = GenerationError("Test error", resume_name="john_doe")
        assert error.filename == "john_doe"

    def test_filename_overrides_resume_name(self) -> None:
        """Test that explicit filename overrides resume_name."""
        error = GenerationError(
            "Test error", resume_name="john_doe", filename="custom.yaml"
        )
        assert error.filename == "custom.yaml"

    def test_all_metadata(self) -> None:
        """Test GenerationError with all metadata."""
        output_path = Path("/tmp/test.pdf")  # noqa: S108
        context = {"key": "value"}
        error = GenerationError(
            "Test error",
            output_path=output_path,
            format_type="pdf",
            resume_name="john_doe",
            context=context,
            filename="test.yaml",
        )
        assert error.output_path == str(output_path)
        assert error.format_type == "pdf"
        assert error.resume_name == "john_doe"
        assert error.context == context
        assert error.filename == "test.yaml"
        assert "format=pdf" in str(error)

    def test_str_without_format(self) -> None:
        """Test string representation without format_type."""
        error = GenerationError("Test error")
        assert str(error) == "Test error"

    def test_str_with_format(self) -> None:
        """Test string representation with format_type."""
        error = GenerationError("Test error", format_type="html")
        error_str = str(error)
        assert "Test error" in error_str
        assert "format=html" in error_str


class TestTemplateError:
    """Tests for TemplateError exception."""

    def test_basic_creation(self) -> None:
        """Test basic TemplateError creation."""
        error = TemplateError("Template failed")
        assert str(error) == "Template failed"
        assert error.template_name is None
        assert error.template_path is None

    def test_with_template_name(self) -> None:
        """Test TemplateError with template_name metadata."""
        error = TemplateError("Template failed", template_name="basic")
        assert error.template_name == "basic"

    def test_with_template_path(self) -> None:
        """Test TemplateError with template_path metadata."""
        template_path = Path("/templates/basic.html")
        error = TemplateError("Template failed", template_path=template_path)
        assert error.template_path == template_path

    def test_with_context(self) -> None:
        """Test TemplateError with context metadata."""
        context = {"var": "val"}
        error = TemplateError("Template failed", context=context)
        assert error.context == context

    def test_with_filename(self) -> None:
        """Test TemplateError with filename metadata."""
        error = TemplateError("Template failed", filename="resume.yaml")
        assert error.filename == "resume.yaml"

    def test_all_metadata(self) -> None:
        """Test TemplateError with all metadata."""
        template_path = Path("/templates/basic.html")
        context = {"var": "val"}
        error = TemplateError(
            "Template failed",
            template_name="basic",
            template_path=template_path,
            context=context,
            filename="resume.yaml",
        )
        assert error.template_name == "basic"
        assert error.template_path == template_path
        assert error.context == context
        assert error.filename == "resume.yaml"
