"""Tests for high-level orchestration functions (generate, generate_resume, preview)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from simple_resume.core.constants import OutputFormat
from simple_resume.core.models import GenerationConfig
from simple_resume.core.result import BatchGenerationResult, GenerationResult
from simple_resume.shell.runtime.generate import (
    GenerateOptions,
    generate,
    generate_resume,
    preview,
)


class TestGenerateResume:
    """Test generate_resume function."""

    @patch("simple_resume.shell.runtime.generate.execute_generation_commands")
    @patch("simple_resume.shell.runtime.generate.build_generation_plan")
    def test_generate_resume_with_string_paths(
        self,
        mock_build_plan: MagicMock,
        mock_execute: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test generate_resume with string paths."""
        # Setup
        mock_command = MagicMock()
        mock_build_plan.return_value = [mock_command]
        mock_result = Mock(spec=GenerationResult)
        mock_execute.return_value = [(mock_command, mock_result)]

        config = GenerationConfig(
            name="test",
            data_dir=str(tmp_path),
            output_dir=str(tmp_path / "output"),
            output_path=str(tmp_path / "test.pdf"),
        )

        # Execute
        result = generate_resume(config, custom="override")

        # Assert
        assert result == mock_result
        mock_build_plan.assert_called_once()
        mock_execute.assert_called_once()

    @patch("simple_resume.shell.runtime.generate.execute_generation_commands")
    @patch("simple_resume.shell.runtime.generate.build_generation_plan")
    def test_generate_resume_with_path_objects(
        self,
        mock_build_plan: MagicMock,
        mock_execute: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test generate_resume with Path objects."""
        # Setup
        mock_command = MagicMock()
        mock_build_plan.return_value = [mock_command]
        mock_result = Mock(spec=GenerationResult)
        mock_execute.return_value = [(mock_command, mock_result)]

        config = GenerationConfig(
            name="test",
            data_dir=tmp_path,
            output_dir=tmp_path / "output",
            output_path=tmp_path / "test.pdf",
        )

        # Execute
        result = generate_resume(config)

        # Assert
        assert result == mock_result

    @patch("simple_resume.shell.runtime.generate.execute_generation_commands")
    @patch("simple_resume.shell.runtime.generate.build_generation_plan")
    def test_generate_resume_with_no_executions(
        self,
        mock_build_plan: MagicMock,
        mock_execute: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test generate_resume returns empty dict when no executions."""
        # Setup
        mock_build_plan.return_value = []
        mock_execute.return_value = []

        config = GenerationConfig(name="test", data_dir=tmp_path)

        # Execute
        result = generate_resume(config)

        # Assert
        assert result == {}


class TestGenerate:
    """Test generate function."""

    def test_generate_with_no_formats_raises_error(self, tmp_path: Path) -> None:
        """Test generate raises error when no formats provided."""
        options = GenerateOptions(formats=())

        with pytest.raises(ValueError, match="at least one format"):
            generate(tmp_path, options)

    @patch("simple_resume.shell.runtime.generate.generate_pdf")
    def test_generate_file_single_pdf_format(
        self, mock_generate_pdf: MagicMock, tmp_path: Path
    ) -> None:
        """Test generate with file source and PDF format."""
        # Setup
        test_file = tmp_path / "test.yaml"
        test_file.write_text("name: Test")
        mock_result = Mock(spec=GenerationResult)
        mock_generate_pdf.return_value = mock_result

        options = GenerateOptions(
            formats=(OutputFormat.PDF,),
            template="modern",
            preview=False,
            open_after=True,
            browser="chrome",
            overrides={"custom": "value"},
        )

        # Execute
        result = generate(test_file, options)

        # Assert
        assert result == {"pdf": mock_result}
        mock_generate_pdf.assert_called_once()
        call_config = mock_generate_pdf.call_args[0][0]
        assert call_config.name == "test"
        assert call_config.data_dir == tmp_path
        assert call_config.template == "modern"
        assert call_config.preview is False
        assert call_config.open_after is True
        assert call_config.browser == "chrome"
        assert mock_generate_pdf.call_args[1] == {"custom": "value"}

    @patch("simple_resume.shell.runtime.generate.generate_html")
    def test_generate_file_single_html_format(
        self, mock_generate_html: MagicMock, tmp_path: Path
    ) -> None:
        """Test generate with file source and HTML format."""
        # Setup
        test_file = tmp_path / "resume.yaml"
        test_file.write_text("name: Resume")
        mock_result = Mock(spec=GenerationResult)
        mock_generate_html.return_value = mock_result

        options = GenerateOptions(formats=(OutputFormat.HTML,))

        # Execute
        result = generate(test_file, options)

        # Assert
        assert result == {"html": mock_result}
        call_config = mock_generate_html.call_args[0][0]
        assert call_config.name == "resume"

    @patch("simple_resume.shell.runtime.generate.generate_pdf")
    def test_generate_file_unsupported_format_raises_error(
        self, mock_generate_pdf: MagicMock, tmp_path: Path
    ) -> None:
        """Test generate raises error for unsupported single format."""
        # Setup
        test_file = tmp_path / "test.yaml"
        test_file.write_text("name: Test")

        # Create mock format that's not PDF or HTML
        mock_format = MagicMock(spec=OutputFormat)
        mock_format.value = "unsupported"

        # Patch normalize to return our mock
        with patch(
            "simple_resume.shell.runtime.generate._normalize_formats",
            return_value=[mock_format],
        ):
            options = GenerateOptions(formats=(OutputFormat.PDF,))
            with pytest.raises(ValueError, match="Unsupported format"):
                generate(test_file, options)

    @patch("simple_resume.shell.runtime.generate.generate_all")
    def test_generate_file_multiple_formats(
        self, mock_generate_all: MagicMock, tmp_path: Path
    ) -> None:
        """Test generate with file source and multiple formats."""
        # Setup
        test_file = tmp_path / "test.yaml"
        test_file.write_text("name: Test")
        mock_result = {"pdf": Mock(), "html": Mock()}
        mock_generate_all.return_value = mock_result

        options = GenerateOptions(formats=(OutputFormat.PDF, OutputFormat.HTML))

        # Execute
        result = generate(test_file, options)

        # Assert
        assert result == mock_result
        call_config = mock_generate_all.call_args[0][0]
        assert call_config.formats == [OutputFormat.PDF, OutputFormat.HTML]

    @patch("simple_resume.shell.runtime.generate.generate_pdf")
    def test_generate_directory_single_format(
        self, mock_generate_pdf: MagicMock, tmp_path: Path
    ) -> None:
        """Test generate with directory source."""
        # Setup
        mock_result = Mock(spec=BatchGenerationResult)
        mock_generate_pdf.return_value = mock_result

        # Execute
        result = generate(tmp_path)

        # Assert
        assert result == {"pdf": mock_result}
        call_config = mock_generate_pdf.call_args[0][0]
        assert call_config.data_dir == tmp_path
        assert call_config.name is None

    @patch("simple_resume.shell.runtime.generate.generate_all")
    def test_generate_directory_multiple_formats(
        self, mock_generate_all: MagicMock, tmp_path: Path
    ) -> None:
        """Test generate with directory source and multiple formats."""
        # Setup
        mock_result = {"pdf": Mock(), "html": Mock()}
        mock_generate_all.return_value = mock_result

        options = GenerateOptions(formats=(OutputFormat.PDF, OutputFormat.HTML))

        # Execute
        result = generate(tmp_path, options)

        # Assert
        assert result == mock_result

    def test_generate_with_default_options(self, tmp_path: Path) -> None:
        """Test generate with None options uses defaults."""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("name: Test")

        with patch("simple_resume.shell.runtime.generate.generate_pdf") as mock_pdf:
            mock_pdf.return_value = Mock()
            result = generate(test_file, None)
            assert "pdf" in result


class TestPreview:
    """Test preview function."""

    def test_preview_with_directory_raises_error(self, tmp_path: Path) -> None:
        """Test preview raises error when given a directory."""
        with pytest.raises(ValueError, match="preview requires a specific resume file"):
            preview(tmp_path)

    @patch("simple_resume.shell.runtime.generate.generate_html")
    def test_preview_with_file(
        self, mock_generate_html: MagicMock, tmp_path: Path
    ) -> None:
        """Test preview with file path."""
        # Setup
        test_file = tmp_path / "resume.yaml"
        test_file.write_text("name: Test")
        mock_result = Mock(spec=GenerationResult)
        mock_generate_html.return_value = mock_result

        # Execute
        result = preview(test_file, custom="override")

        # Assert
        assert result == mock_result
        call_config = mock_generate_html.call_args[0][0]
        assert call_config.name == "resume"
        assert call_config.data_dir == tmp_path
        assert call_config.preview is True
        assert call_config.browser is None
        assert mock_generate_html.call_args[1] == {"custom": "override"}

    @patch("simple_resume.shell.runtime.generate.generate_html")
    def test_preview_with_browser_override(
        self, mock_generate_html: MagicMock, tmp_path: Path
    ) -> None:
        """Test preview with browser in overrides."""
        # Setup
        test_file = tmp_path / "resume.yaml"
        test_file.write_text("name: Test")
        mock_result = Mock(spec=GenerationResult)
        mock_generate_html.return_value = mock_result

        # Execute
        preview(test_file, browser="firefox", template="modern")

        # Assert
        call_config = mock_generate_html.call_args[0][0]
        assert call_config.browser == "firefox"
        assert mock_generate_html.call_args[1] == {"template": "modern"}
