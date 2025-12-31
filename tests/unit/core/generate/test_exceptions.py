"""Tests for core/generate/exceptions.py."""

from __future__ import annotations

from pathlib import Path

from simple_resume.core.generate.exceptions import GenerationError, TemplateError
from tests.bdd import Scenario


class TestGenerationError:
    """Tests for GenerationError exception."""

    def test_basic_creation(self, story: Scenario) -> None:
        """Test basic GenerationError creation."""
        story.given("a simple error message")
        story.when("creating a GenerationError without metadata")
        error = GenerationError("Test error")
        assert str(error) == "Test error"
        assert error.output_path is None
        assert error.format_type is None
        assert error.resume_name is None

    def test_with_output_path(self, story: Scenario) -> None:
        """Test GenerationError with output_path metadata."""
        story.given("an output path for the generated file")
        story.when("creating a GenerationError with output_path")
        output_path = Path("/tmp/test.pdf")  # noqa: S108
        error = GenerationError("Test error", output_path=output_path)
        assert error.output_path == str(output_path)

    def test_with_format_type(self, story: Scenario) -> None:
        """Test GenerationError with format_type metadata."""
        story.given("a format type 'pdf'")
        story.when("creating a GenerationError with format_type")
        error = GenerationError("Test error", format_type="pdf")
        assert error.format_type == "pdf"
        assert "format=pdf" in str(error)

    def test_with_resume_name(self, story: Scenario) -> None:
        """Test GenerationError with resume_name metadata."""
        story.given("a resume name 'john_doe'")
        story.when("creating a GenerationError with resume_name")
        error = GenerationError("Test error", resume_name="john_doe")
        assert error.resume_name == "john_doe"

    def test_with_context(self, story: Scenario) -> None:
        """Test GenerationError with context metadata."""
        story.given("a context dictionary with key-value pairs")
        story.when("creating a GenerationError with context")
        context = {"key": "value"}
        error = GenerationError("Test error", context=context)
        assert error.context == context

    def test_with_filename(self, story: Scenario) -> None:
        """Test GenerationError with filename metadata."""
        story.given("a filename 'test.yaml'")
        story.when("creating a GenerationError with filename")
        error = GenerationError("Test error", filename="test.yaml")
        assert error.filename == "test.yaml"

    def test_filename_defaults_to_resume_name(self, story: Scenario) -> None:
        """Test that filename defaults to resume_name when not provided."""
        story.given("a GenerationError with resume_name but no explicit filename")
        story.when("accessing the filename property")
        error = GenerationError("Test error", resume_name="john_doe")
        assert error.filename == "john_doe"

    def test_filename_overrides_resume_name(self, story: Scenario) -> None:
        """Test that explicit filename overrides resume_name."""
        story.given("both resume_name and filename provided")
        story.when("accessing the filename property")
        error = GenerationError(
            "Test error", resume_name="john_doe", filename="custom.yaml"
        )
        assert error.filename == "custom.yaml"

    def test_all_metadata(self, story: Scenario) -> None:
        """Test GenerationError with all metadata."""
        story.given("all metadata fields populated")
        story.when("creating a GenerationError with all fields")
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

    def test_str_without_format(self, story: Scenario) -> None:
        """Test string representation without format_type."""
        story.given("a GenerationError without format_type")
        story.when("converting to string")
        error = GenerationError("Test error")
        assert str(error) == "Test error"

    def test_str_with_format(self, story: Scenario) -> None:
        """Test string representation with format_type."""
        story.given("a GenerationError with format_type 'html'")
        story.when("converting to string")
        error = GenerationError("Test error", format_type="html")
        error_str = str(error)
        assert "Test error" in error_str
        assert "format=html" in error_str


class TestTemplateError:
    """Tests for TemplateError exception."""

    def test_basic_creation(self, story: Scenario) -> None:
        """Test basic TemplateError creation."""
        story.given("a simple template error message")
        story.when("creating a TemplateError without metadata")
        error = TemplateError("Template failed")
        assert str(error) == "Template failed"
        assert error.template_name is None
        assert error.template_path is None

    def test_with_template_name(self, story: Scenario) -> None:
        """Test TemplateError with template_name metadata."""
        story.given("a template name 'basic'")
        story.when("creating a TemplateError with template_name")
        error = TemplateError("Template failed", template_name="basic")
        assert error.template_name == "basic"

    def test_with_template_path(self, story: Scenario) -> None:
        """Test TemplateError with template_path metadata."""
        story.given("a template path")
        story.when("creating a TemplateError with template_path")
        template_path = Path("/templates/basic.html")
        error = TemplateError("Template failed", template_path=template_path)
        assert error.template_path == template_path

    def test_with_context(self, story: Scenario) -> None:
        """Test TemplateError with context metadata."""
        story.given("a context dictionary")
        story.when("creating a TemplateError with context")
        context = {"var": "val"}
        error = TemplateError("Template failed", context=context)
        assert error.context == context

    def test_with_filename(self, story: Scenario) -> None:
        """Test TemplateError with filename metadata."""
        story.given("a filename 'resume.yaml'")
        story.when("creating a TemplateError with filename")
        error = TemplateError("Template failed", filename="resume.yaml")
        assert error.filename == "resume.yaml"

    def test_all_metadata(self, story: Scenario) -> None:
        """Test TemplateError with all metadata."""
        story.given("all template error metadata fields populated")
        story.when("creating a TemplateError with all fields")
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
