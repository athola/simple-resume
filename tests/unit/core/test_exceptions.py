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


class TestConfigurationError:
    """Tests for ConfigurationError exception."""

    def test_basic_creation(self) -> None:
        """Test basic ConfigurationError creation."""
        error = ConfigurationError("Config error")
        assert str(error) == "Config error"

    def test_with_config_key(self) -> None:
        """Test ConfigurationError with config_key."""
        error = ConfigurationError("Invalid setting", config_key="theme_color")
        assert "Invalid setting" in str(error)
        assert "config_key=theme_color" in str(error)
        assert error.config_key == "theme_color"

    def test_with_filename(self) -> None:
        """Test ConfigurationError with filename."""
        error = ConfigurationError("Config error", filename="config.yaml")
        assert error.filename == "config.yaml"


class TestPaletteError:
    """Tests for PaletteError exception."""

    def test_basic_creation(self) -> None:
        """Test basic PaletteError creation."""
        error = PaletteError("Palette error")
        assert str(error) == "Palette error"

    def test_with_palette_name(self) -> None:
        """Test PaletteError with palette_name."""
        error = PaletteError("Palette not found", palette_name="ocean_blue")
        assert error.palette_name == "ocean_blue"

    def test_with_color_values(self) -> None:
        """Test PaletteError with color_values."""
        colors = ["#FF0000", "#00FF00", "#0000FF"]
        error = PaletteError("Invalid colors", color_values=colors)
        assert error.color_values == colors

    def test_with_context_and_filename(self) -> None:
        """Test PaletteError with context and filename."""
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

    def test_basic_creation(self) -> None:
        """Test basic FileSystemError creation."""
        error = FileSystemError("File error")
        assert str(error) == "File error"

    def test_with_path(self) -> None:
        """Test FileSystemError with path."""
        error = FileSystemError("Cannot read file", path="/tmp/test.yaml")  # noqa: S108
        assert error.path == "/tmp/test.yaml"  # noqa: S108

    def test_with_operation(self) -> None:
        """Test FileSystemError with operation."""
        error = FileSystemError("Operation failed", operation="write")
        assert error.operation == "write"

    def test_with_all_metadata(self) -> None:
        """Test FileSystemError with all metadata."""
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

    def test_basic_creation(self) -> None:
        """Test basic ValidationError creation."""
        error = ValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert error.errors == []
        assert error.warnings == []

    def test_with_errors_list(self) -> None:
        """Test ValidationError with errors list."""
        errors = ["Invalid email format", "Missing required field"]
        error = ValidationError("Validation failed", errors=errors)
        assert error.errors == errors

    def test_with_warnings_list(self) -> None:
        """Test ValidationError with warnings list."""
        warnings = ["Field is deprecated", "Consider using new format"]
        error = ValidationError("Validation warning", warnings=warnings)
        assert error.warnings == warnings

    def test_with_context_and_filename(self) -> None:
        """Test ValidationError with context and filename."""
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

    def test_basic_creation(self) -> None:
        """Test basic TemplateError creation."""
        error = TemplateError("Template error")
        assert str(error) == "Template error"

    def test_with_template_name(self) -> None:
        """Test TemplateError with template_name."""
        error = TemplateError("Template not found", template_name="basic.html")
        assert error.template_name == "basic.html"

    def test_with_template_path(self) -> None:
        """Test TemplateError with template_path."""
        template_path = Path("/templates/basic.html")
        error = TemplateError("Template error", template_path=template_path)
        assert error.template_path == template_path

    def test_with_metadata_dict(self) -> None:
        """Test TemplateError with metadata dictionary."""
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

    def test_extracts_metadata_from_dict(self) -> None:
        """Test TemplateError extracts template metadata."""
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
