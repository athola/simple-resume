"""Tests for shell/services.py module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from simple_resume.shell.services import (
    DefaultContentLoader,
    DefaultEffectExecutor,
    DefaultFileOpenerService,
    DefaultHtmlGenerator,
    DefaultLaTeXRenderer,
    DefaultPaletteLoader,
    DefaultPathResolver,
    DefaultPdfGenerationStrategy,
    DefaultTemplateLocator,
)


class TestDefaultTemplateLocator:
    """Test DefaultTemplateLocator class."""

    def test_get_template_location_returns_path(self) -> None:
        """Test that get_template_location returns a Path."""
        locator = DefaultTemplateLocator()
        result = locator.get_template_location()
        assert isinstance(result, Path)


class TestDefaultEffectExecutor:
    """Test DefaultEffectExecutor class."""

    def test_execute_delegates_to_shell_executor(self) -> None:
        """Test execute method delegates to shell executor."""
        executor = DefaultEffectExecutor()
        mock_effect = MagicMock()

        with patch.object(executor._executor, "execute") as mock_execute:
            executor.execute(mock_effect)
            mock_execute.assert_called_once_with(mock_effect)

    def test_execute_many_delegates_to_shell_executor(self) -> None:
        """Test execute_many method delegates to shell executor."""
        executor = DefaultEffectExecutor()
        mock_effects = [MagicMock(), MagicMock()]

        with patch.object(executor._executor, "execute_many") as mock_execute:
            executor.execute_many(mock_effects)
            mock_execute.assert_called_once_with(mock_effects)


class TestDefaultPathResolver:
    """Test DefaultPathResolver class."""

    def test_candidate_yaml_path_returns_path_for_valid_name(self) -> None:
        """Test candidate_yaml_path returns Path for valid name."""
        resolver = DefaultPathResolver()
        # When no file exists, should return a Path based on name
        result = resolver.candidate_yaml_path("nonexistent_resume")
        assert isinstance(result, Path)

    def test_candidate_yaml_path_fallback_to_path(self) -> None:
        """Test candidate_yaml_path returns Path when None returned."""
        resolver = DefaultPathResolver()
        # Even with empty string, should return a Path
        result = resolver.candidate_yaml_path("")
        assert isinstance(result, Path)


class TestDefaultContentLoader:
    """Test DefaultContentLoader class."""

    @patch("simple_resume.shell.services.get_content")
    @patch("simple_resume.shell.services.render_markdown_content")
    @patch("simple_resume.shell.services.resolve_paths_for_read")
    @patch("simple_resume.shell.services.candidate_yaml_path")
    def test_load_without_markdown_transform(
        self,
        mock_candidate: MagicMock,
        mock_resolve: MagicMock,
        mock_render: MagicMock,
        mock_get_content: MagicMock,
    ) -> None:
        """Test load without markdown transformation."""
        mock_candidate.return_value = Path("test.yaml")
        mock_resolve.return_value = MagicMock()
        mock_get_content.return_value = {"name": "test"}

        loader = DefaultContentLoader()
        processed, raw = loader.load("test", None, transform_markdown=False)

        # Should not call render_markdown_content
        mock_render.assert_not_called()
        assert processed == {"name": "test"}
        assert raw == {"name": "test"}


class TestDefaultPdfGenerationStrategy:
    """Test DefaultPdfGenerationStrategy class."""

    def test_init_with_weasyprint_mode(self) -> None:
        """Test initialization with weasyprint mode."""
        strategy = DefaultPdfGenerationStrategy(mode="weasyprint")
        assert strategy._strategy is not None

    def test_init_with_latex_mode(self) -> None:
        """Test initialization with latex mode."""
        strategy = DefaultPdfGenerationStrategy(mode="latex")
        assert strategy._strategy is not None


class TestDefaultHtmlGenerator:
    """Test DefaultHtmlGenerator class."""

    @patch("simple_resume.shell.services.shell_generate")
    def test_generate_delegates_to_shell(self, mock_shell_generate: MagicMock) -> None:
        """Test generate method delegates to shell function."""
        mock_shell_generate.return_value = MagicMock()
        generator = DefaultHtmlGenerator()

        render_plan = MagicMock()
        output_path = Path("/tmp/test.html")  # noqa: S108

        generator.generate(render_plan, output_path, "test.yaml")

        mock_shell_generate.assert_called_once_with(
            render_plan, output_path, "test.yaml"
        )


class TestDefaultFileOpenerService:
    """Test DefaultFileOpenerService class."""

    @patch("simple_resume.shell.services.shell_open_file")
    def test_open_file_delegates_to_shell(self, mock_open: MagicMock) -> None:
        """Test open_file method delegates to shell function."""
        mock_open.return_value = True
        service = DefaultFileOpenerService()

        result = service.open_file(Path("/tmp/test.pdf"), "pdf")  # noqa: S108

        mock_open.assert_called_once_with(Path("/tmp/test.pdf"), "pdf")  # noqa: S108
        assert result is True


class TestDefaultPaletteLoader:
    """Test DefaultPaletteLoader class."""

    @patch("simple_resume.shell.services.load_palette_from_file")
    def test_load_palette_from_file(self, mock_load: MagicMock) -> None:
        """Test load_palette_from_file delegates to shell function."""
        mock_load.return_value = {"palette": {"primary": "#000"}}
        loader = DefaultPaletteLoader()

        result = loader.load_palette_from_file(Path("/tmp/palette.yaml"))  # noqa: S108

        mock_load.assert_called_once_with(Path("/tmp/palette.yaml"))  # noqa: S108
        assert result == {"palette": {"primary": "#000"}}


class TestDefaultLaTeXRenderer:
    """Test DefaultLaTeXRenderer class."""

    def test_get_latex_functions_returns_tuple(self) -> None:
        """Test get_latex_functions returns a tuple."""
        renderer = DefaultLaTeXRenderer()
        result = renderer.get_latex_functions()
        assert isinstance(result, tuple)
        assert len(result) == 3
