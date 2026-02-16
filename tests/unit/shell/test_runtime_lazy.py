"""Tests for shell/runtime/lazy.py module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from simple_resume.shell.runtime.lazy import (
    _lazy_generate,
    generate,
    generate_all,
    generate_html,
    generate_pdf,
    generate_resume,
    preview,
)


class TestLazyModuleLoader:
    """Test the LazyModule-based lazy loader."""

    def test_lazy_generate_resolves_to_module(self) -> None:
        """Test that _lazy_generate resolves to the generate module."""
        assert hasattr(_lazy_generate, "generate_pdf")
        assert callable(_lazy_generate.generate_pdf)

    def test_lazy_generate_caches_module(self) -> None:
        """Test that module is cached after first access."""
        fn1 = _lazy_generate.generate_pdf
        fn2 = _lazy_generate.generate_pdf
        assert fn1 is fn2

    def test_all_generation_functions_accessible(self) -> None:
        """Test that all expected functions are accessible via lazy module."""
        for name in (
            "generate_pdf",
            "generate_html",
            "generate_all",
            "generate_resume",
            "generate",
            "preview",
        ):
            assert hasattr(_lazy_generate, name)
            assert callable(getattr(_lazy_generate, name))


class TestLazyWrapperFunctions:
    """Test lazy wrapper functions."""

    @patch("simple_resume.shell.runtime.lazy._lazy_generate")
    def test_generate_pdf_delegates_to_core(self, mock_lazy: MagicMock) -> None:
        """Test generate_pdf delegates to core implementation."""
        mock_lazy.generate_pdf.return_value = "pdf_result"
        config = MagicMock()

        result = generate_pdf(config, output_dir="/tmp")  # noqa: S108

        mock_lazy.generate_pdf.assert_called_once_with(config, output_dir="/tmp")  # noqa: S108
        assert result == "pdf_result"

    @patch("simple_resume.shell.runtime.lazy._lazy_generate")
    def test_generate_html_delegates_to_core(self, mock_lazy: MagicMock) -> None:
        """Test generate_html delegates to core implementation."""
        mock_lazy.generate_html.return_value = "html_result"
        config = MagicMock()

        result = generate_html(config, output_dir="/tmp")  # noqa: S108

        mock_lazy.generate_html.assert_called_once_with(config, output_dir="/tmp")  # noqa: S108
        assert result == "html_result"

    @patch("simple_resume.shell.runtime.lazy._lazy_generate")
    def test_generate_all_delegates_to_core(self, mock_lazy: MagicMock) -> None:
        """Test generate_all delegates to core implementation."""
        mock_lazy.generate_all.return_value = "all_result"
        config = MagicMock()

        result = generate_all(config, output_dir="/tmp")  # noqa: S108

        mock_lazy.generate_all.assert_called_once_with(config, output_dir="/tmp")  # noqa: S108
        assert result == "all_result"

    @patch("simple_resume.shell.runtime.lazy._lazy_generate")
    def test_generate_resume_delegates_to_core(self, mock_lazy: MagicMock) -> None:
        """Test generate_resume delegates to core implementation."""
        mock_lazy.generate_resume.return_value = "resume_result"
        config = MagicMock()

        result = generate_resume(config, output_dir="/tmp")  # noqa: S108

        mock_lazy.generate_resume.assert_called_once_with(config, output_dir="/tmp")  # noqa: S108
        assert result == "resume_result"

    @patch("simple_resume.shell.runtime.lazy._lazy_generate")
    def test_generate_delegates_to_core(self, mock_lazy: MagicMock) -> None:
        """Test generate delegates to core implementation."""
        mock_lazy.generate.return_value = "generate_result"

        result = generate("source.yaml", None, format="pdf")

        mock_lazy.generate.assert_called_once_with("source.yaml", None, format="pdf")
        assert result == "generate_result"

    @patch("simple_resume.shell.runtime.lazy._lazy_generate")
    def test_preview_delegates_to_core(self, mock_lazy: MagicMock) -> None:
        """Test preview delegates to core implementation."""
        mock_lazy.preview.return_value = "preview_result"

        result = preview(
            "source.yaml",
            data_dir="/data",
            template="basic",
            browser="chrome",
            open_after=False,
            extra="arg",
        )

        mock_lazy.preview.assert_called_once_with(
            "source.yaml",
            data_dir="/data",
            template="basic",
            browser="chrome",
            open_after=False,
            extra="arg",
        )
        assert result == "preview_result"
