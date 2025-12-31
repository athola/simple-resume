"""Tests for core/exceptions.py - custom exception classes."""

from __future__ import annotations

from pathlib import Path

from simple_resume.core.exceptions import (
    ConfigurationError,
    FileSystemError,
    PaletteError,
    TemplateError,
    ValidationError,
)
from tests.bdd import Scenario


class TestConfigurationError:
    """Tests for ConfigurationError exception."""

    def test_basic_creation(self, story: Scenario) -> None:
        """Test basic ConfigurationError creation."""
        story.given("an error message for configuration")
        story.when("creating a ConfigurationError")
        error = ConfigurationError("Config error")
        assert str(error) == "Config error"

    def test_with_config_key(self, story: Scenario) -> None:
        """Test ConfigurationError with config_key."""
        story.given("an error message and config key")
        story.when("creating a ConfigurationError with config_key")
        error = ConfigurationError("Invalid setting", config_key="theme_color")
        assert "Invalid setting" in str(error)
        assert "config_key=theme_color" in str(error)
        assert error.config_key == "theme_color"

    def test_with_filename(self, story: Scenario) -> None:
        """Test ConfigurationError with filename."""
        story.given("an error message and filename")
        story.when("creating a ConfigurationError with filename")
        error = ConfigurationError("Config error", filename="config.yaml")
        assert error.filename == "config.yaml"


class TestPaletteError:
    """Tests for PaletteError exception."""

    def test_basic_creation(self, story: Scenario) -> None:
        """Test basic PaletteError creation."""
        story.given("an error message for palette")
        story.when("creating a PaletteError")
        error = PaletteError("Palette error")
        assert str(error) == "Palette error"

    def test_with_palette_name(self, story: Scenario) -> None:
        """Test PaletteError with palette_name."""
        story.given("an error message and palette name")
        story.when("creating a PaletteError with palette_name")
        error = PaletteError("Palette not found", palette_name="ocean_blue")
        assert error.palette_name == "ocean_blue"

    def test_with_color_values(self, story: Scenario) -> None:
        """Test PaletteError with color_values."""
        story.given("a list of invalid color values")
        story.when("creating a PaletteError with color_values")
        colors = ["#FF0000", "#00FF00", "#0000FF"]
        error = PaletteError("Invalid colors", color_values=colors)
        assert error.color_values == colors

    def test_with_context_and_filename(self, story: Scenario) -> None:
        """Test PaletteError with context and filename."""
        story.given("full error context including palette name and filename")
        story.when("creating a PaletteError with all metadata")
        error = PaletteError(
            "Palette error",
            palette_name="test",
            context={"key": "value"},
            filename="palette.json",
        )
        assert error.palette_name == "test"
        assert error.context == {"key": "value"}
        assert error.filename == "palette.json"


class TestFileSystemError:
    """Tests for FileSystemError exception."""

    def test_basic_creation(self, story: Scenario) -> None:
        """Test basic FileSystemError creation."""
        story.given("an error message for file system operation")
        story.when("creating a FileSystemError")
        error = FileSystemError("File error")
        assert str(error) == "File error"

    def test_with_path(self, story: Scenario) -> None:
        """Test FileSystemError with path."""
        story.given("an error message and file path")
        story.when("creating a FileSystemError with path")
        error = FileSystemError("Cannot read file", path="/tmp/test.yaml")  # noqa: S108
        assert error.path == "/tmp/test.yaml"  # noqa: S108

    def test_with_operation(self, story: Scenario) -> None:
        """Test FileSystemError with operation."""
        story.given("an error message and operation type")
        story.when("creating a FileSystemError with operation")
        error = FileSystemError("Operation failed", operation="write")
        assert error.operation == "write"

    def test_with_all_metadata(self, story: Scenario) -> None:
        """Test FileSystemError with all metadata."""
        story.given("complete file operation context")
        story.when("creating a FileSystemError with all metadata")
        error = FileSystemError(
            "File operation failed",
            path="/tmp/file.txt",  # noqa: S108
            operation="delete",
            context={"mode": "strict"},
            filename="source.yaml",
        )
        assert error.path == "/tmp/file.txt"  # noqa: S108
        assert error.operation == "delete"
        assert error.context == {"mode": "strict"}
        assert error.filename == "source.yaml"


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_basic_creation(self, story: Scenario) -> None:
        """Test basic ValidationError creation."""
        story.given("an error message for validation failure")
        story.when("creating a ValidationError")
        error = ValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert error.errors == []
        assert error.warnings == []

    def test_with_errors_list(self, story: Scenario) -> None:
        """Test ValidationError with errors list."""
        story.given("a list of validation errors")
        story.when("creating a ValidationError with errors list")
        errors = ["Invalid email format", "Missing required field"]
        error = ValidationError("Validation failed", errors=errors)
        assert error.errors == errors

    def test_with_warnings_list(self, story: Scenario) -> None:
        """Test ValidationError with warnings list."""
        story.given("a list of validation warnings")
        story.when("creating a ValidationError with warnings list")
        warnings = ["Field is deprecated", "Consider using new format"]
        error = ValidationError("Validation warning", warnings=warnings)
        assert error.warnings == warnings

    def test_with_context_and_filename(self, story: Scenario) -> None:
        """Test ValidationError with context and filename."""
        story.given("validation error context including field info")
        story.when("creating a ValidationError with context and filename")
        error = ValidationError(
            "Validation failed",
            errors=["Error 1"],
            context={"field": "email"},
            filename="resume.yaml",
        )
        assert error.context == {"field": "email"}
        assert error.filename == "resume.yaml"


class TestTemplateError:
    """Tests for TemplateError exception."""

    def test_basic_creation(self, story: Scenario) -> None:
        """Test basic TemplateError creation."""
        story.given("an error message for template failure")
        story.when("creating a TemplateError")
        error = TemplateError("Template error")
        assert str(error) == "Template error"

    def test_with_template_name(self, story: Scenario) -> None:
        """Test TemplateError with template_name."""
        story.given("an error message and template name")
        story.when("creating a TemplateError with template_name")
        error = TemplateError("Template not found", template_name="basic.html")
        assert error.template_name == "basic.html"

    def test_with_template_path(self, story: Scenario) -> None:
        """Test TemplateError with template_path."""
        story.given("an error message and template path")
        story.when("creating a TemplateError with template_path")
        template_path = Path("/templates/basic.html")
        error = TemplateError("Template error", template_path=template_path)
        assert error.template_path == template_path

    def test_with_metadata_dict(self, story: Scenario) -> None:
        """Test TemplateError with metadata dictionary."""
        story.given("complete template error context")
        story.when("creating a TemplateError with all metadata")
        error = TemplateError(
            "Template rendering failed",
            template_name="custom.html",
            template_path=Path("/templates/custom.html"),
            context={"var": "value"},
            filename="resume.yaml",
        )
        assert error.template_name == "custom.html"
        assert error.template_path == Path("/templates/custom.html")
        assert error.context == {"var": "value"}
        assert error.filename == "resume.yaml"

    def test_extracts_metadata_from_dict(self, story: Scenario) -> None:
        """Test TemplateError extracts template metadata."""
        story.given("template error with full context including name and path")
        story.when("creating a TemplateError with extracted metadata")
        error = TemplateError(
            "Template failed",
            template_name="basic.tex",
            template_path=Path("/templates/basic.tex"),
            context={"name": "John"},
            filename="john.yaml",
        )
        assert error.template_name == "basic.tex"
        assert error.template_path == Path("/templates/basic.tex")
        assert error.context == {"name": "John"}
        assert error.filename == "john.yaml"
