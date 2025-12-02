"""Tests for shell/runtime/lazy.py module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from simple_resume.shell.runtime.lazy import (
    _LazyRuntimeLoader,
    generate,
    generate_all,
    generate_html,
    generate_pdf,
    generate_resume,
    preview,
)


class TestLazyRuntimeLoader:
    """Test _LazyRuntimeLoader class."""

    def test_loader_starts_unloaded(self) -> None:
        """Test that loader starts in unloaded state."""
        loader = _LazyRuntimeLoader()
        assert loader._loaded is False
        assert loader._core is None

    def test_load_core_loads_generate_module(self) -> None:
        """Test that _load_core loads the generate module."""
        loader = _LazyRuntimeLoader()
        core = loader._load_core()
        assert core is not None
        assert loader._loaded is True
        assert hasattr(core, "generate_pdf")

    def test_load_core_caches_module(self) -> None:
        """Test that module is cached after first load."""
        loader = _LazyRuntimeLoader()
        core1 = loader._load_core()
        core2 = loader._load_core()
        assert core1 is core2

    def test_generate_pdf_property(self) -> None:
        """Test generate_pdf property loads function."""
        loader = _LazyRuntimeLoader()
        fn = loader.generate_pdf
        assert callable(fn)

    def test_generate_html_property(self) -> None:
        """Test generate_html property loads function."""
        loader = _LazyRuntimeLoader()
        fn = loader.generate_html
        assert callable(fn)

    def test_generate_all_property(self) -> None:
        """Test generate_all property loads function."""
        loader = _LazyRuntimeLoader()
        fn = loader.generate_all
        assert callable(fn)

    def test_generate_resume_property(self) -> None:
        """Test generate_resume property loads function."""
        loader = _LazyRuntimeLoader()
        fn = loader.generate_resume
        assert callable(fn)

    def test_generate_property(self) -> None:
        """Test generate property loads function."""
        loader = _LazyRuntimeLoader()
        fn = loader.generate
        assert callable(fn)

    def test_preview_property(self) -> None:
        """Test preview property loads function."""
        loader = _LazyRuntimeLoader()
        fn = loader.preview
        assert callable(fn)


class TestLazyWrapperFunctions:
    """Test lazy wrapper functions."""

    @patch("simple_resume.shell.runtime.lazy._get_lazy_core")
    def test_generate_pdf_delegates_to_core(
        self, mock_get_lazy_core: MagicMock
    ) -> None:
        """Test generate_pdf delegates to core implementation."""
        mock_core = MagicMock()
        mock_core.generate_pdf.return_value = "pdf_result"
        mock_get_lazy_core.return_value = mock_core
        config = MagicMock()

        result = generate_pdf(config, output_dir="/tmp")  # noqa: S108

        mock_get_lazy_core.assert_called_once()
        mock_core.generate_pdf.assert_called_once_with(config, output_dir="/tmp")  # noqa: S108
        assert result == "pdf_result"

    @patch("simple_resume.shell.runtime.lazy._get_lazy_core")
    def test_generate_html_delegates_to_core(
        self, mock_get_lazy_core: MagicMock
    ) -> None:
        """Test generate_html delegates to core implementation."""
        mock_core = MagicMock()
        mock_core.generate_html.return_value = "html_result"
        mock_get_lazy_core.return_value = mock_core
        config = MagicMock()

        result = generate_html(config, output_dir="/tmp")  # noqa: S108

        mock_get_lazy_core.assert_called_once()
        mock_core.generate_html.assert_called_once_with(config, output_dir="/tmp")  # noqa: S108
        assert result == "html_result"

    @patch("simple_resume.shell.runtime.lazy._get_lazy_core")
    def test_generate_all_delegates_to_core(
        self, mock_get_lazy_core: MagicMock
    ) -> None:
        """Test generate_all delegates to core implementation."""
        mock_core = MagicMock()
        mock_core.generate_all.return_value = "all_result"
        mock_get_lazy_core.return_value = mock_core
        config = MagicMock()

        result = generate_all(config, output_dir="/tmp")  # noqa: S108

        mock_get_lazy_core.assert_called_once()
        mock_core.generate_all.assert_called_once_with(config, output_dir="/tmp")  # noqa: S108
        assert result == "all_result"

    @patch("simple_resume.shell.runtime.lazy._get_lazy_core")
    def test_generate_resume_delegates_to_core(
        self, mock_get_lazy_core: MagicMock
    ) -> None:
        """Test generate_resume delegates to core implementation."""
        mock_core = MagicMock()
        mock_core.generate_resume.return_value = "resume_result"
        mock_get_lazy_core.return_value = mock_core
        config = MagicMock()

        result = generate_resume(config, output_dir="/tmp")  # noqa: S108

        mock_get_lazy_core.assert_called_once()
        mock_core.generate_resume.assert_called_once_with(config, output_dir="/tmp")  # noqa: S108
        assert result == "resume_result"

    @patch("simple_resume.shell.runtime.lazy._get_lazy_core")
    def test_generate_delegates_to_core(self, mock_get_lazy_core: MagicMock) -> None:
        """Test generate delegates to core implementation."""
        mock_core = MagicMock()
        mock_core.generate.return_value = "generate_result"
        mock_get_lazy_core.return_value = mock_core

        result = generate("source.yaml", None, format="pdf")

        mock_get_lazy_core.assert_called_once()
        mock_core.generate.assert_called_once_with("source.yaml", None, format="pdf")
        assert result == "generate_result"

    @patch("simple_resume.shell.runtime.lazy._get_lazy_core")
    def test_preview_delegates_to_core(self, mock_get_lazy_core: MagicMock) -> None:
        """Test preview delegates to core implementation."""
        mock_core = MagicMock()
        mock_core.preview.return_value = "preview_result"
        mock_get_lazy_core.return_value = mock_core

        result = preview(
            "source.yaml",
            data_dir="/data",
            template="basic",
            browser="chrome",
            open_after=False,
            extra="arg",
        )

        mock_get_lazy_core.assert_called_once()
        mock_core.preview.assert_called_once_with(
            "source.yaml",
            data_dir="/data",
            template="basic",
            browser="chrome",
            open_after=False,
            extra="arg",
        )
        assert result == "preview_result"
