"""Tests for core/constants/__init__.py - constant definitions and enums."""

from __future__ import annotations

import pytest

from simple_resume.core.constants import OutputFormat, RenderMode, TemplateType


class TestOutputFormat:
    """Tests for OutputFormat enum."""

    def test_normalize_from_string(self) -> None:
        """Test normalizing from string value."""
        assert OutputFormat.normalize("pdf") is OutputFormat.PDF
        assert OutputFormat.normalize("html") is OutputFormat.HTML

    def test_normalize_from_enum(self) -> None:
        """Test normalizing from enum returns same enum."""
        assert OutputFormat.normalize(OutputFormat.PDF) is OutputFormat.PDF
        assert OutputFormat.normalize(OutputFormat.HTML) is OutputFormat.HTML

    def test_normalize_case_insensitive(self) -> None:
        """Test normalize is case-insensitive."""
        assert OutputFormat.normalize("PDF") is OutputFormat.PDF
        assert OutputFormat.normalize("Html") is OutputFormat.HTML
        assert OutputFormat.normalize("  pdf  ") is OutputFormat.PDF

    def test_normalize_invalid_type_raises_type_error(self) -> None:
        """Test normalize raises TypeError for invalid input type."""
        with pytest.raises(TypeError, match="Output format must be provided as string"):
            OutputFormat.normalize(123)  # type: ignore[arg-type]

    def test_normalize_invalid_value_raises_value_error(self) -> None:
        """Test normalize raises ValueError for invalid format string."""
        with pytest.raises(ValueError, match="Unsupported format"):
            OutputFormat.normalize("docx")


class TestRenderMode:
    """Tests for RenderMode enum."""

    def test_render_modes_available(self) -> None:
        """Test that RenderMode has expected values."""
        assert RenderMode.HTML is not None
        assert RenderMode.LATEX is not None

    def test_render_mode_values(self) -> None:
        """Test RenderMode enum values."""
        assert RenderMode.HTML.value == "html"
        assert RenderMode.LATEX.value == "latex"


class TestTemplateType:
    """Tests for TemplateType enum."""

    def test_is_valid_returns_true_for_valid_template(self) -> None:
        """Test is_valid returns True for valid template strings."""
        assert TemplateType.is_valid("resume_no_bars") is True
        assert TemplateType.is_valid("resume_with_bars") is True

    def test_is_valid_returns_false_for_invalid_template(self) -> None:
        """Test is_valid returns False for invalid template strings."""
        assert TemplateType.is_valid("invalid_template") is False
        assert TemplateType.is_valid("") is False
