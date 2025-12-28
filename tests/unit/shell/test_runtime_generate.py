"""Tests for shell/runtime/generate.py module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from simple_resume.core.constants import OutputFormat
from simple_resume.core.exceptions import (
    ConfigurationError,
    FileSystemError,
    ValidationError,
)
from simple_resume.core.generate.exceptions import GenerationError as GenErr
from simple_resume.core.generate.plan import CommandType, GenerationCommand
from simple_resume.core.models import GenerationConfig
from simple_resume.core.paths import Paths
from simple_resume.core.result import BatchGenerationResult, GenerationResult
from simple_resume.shell.runtime.generate import (
    GenerateOptions,
    execute_generation_commands,
    generate,
    generate_all,
    generate_html,
    generate_pdf,
    generate_resume,
    preview,
)


class TestGeneratePdf:
    """Test generate_pdf function."""

    @patch("simple_resume.shell.runtime.generate.session_mod.ResumeSession")
    @patch("simple_resume.shell.runtime.generate.generate_core")
    def test_generate_pdf_with_name_and_overrides(
        self, mock_generate_core: MagicMock, mock_session_cls: MagicMock, tmp_path: Path
    ) -> None:
        """Test generate_pdf with name and overrides."""
        # Setup
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__.return_value = mock_session
        mock_resume = MagicMock()
        mock_resume_with_config = MagicMock()
        mock_resume.with_config.return_value = mock_resume_with_config
        mock_session.resume.return_value = mock_resume
        mock_result = Mock(spec=GenerationResult)
        mock_generate_core.to_pdf.return_value = mock_result

        config = GenerationConfig(
            name="test_resume",
            data_dir=tmp_path,
            output_path=tmp_path / "output.pdf",
            open_after=True,
        )

        # Execute
        result = generate_pdf(config, template="custom")

        # Assert
        mock_session.resume.assert_called_once_with("test_resume")
        mock_resume.with_config.assert_called_once_with(template="custom")
        mock_generate_core.to_pdf.assert_called_once_with(
            mock_resume_with_config,
            output_path=tmp_path / "output.pdf",
            open_after=True,
        )
        assert result == mock_result

    @patch("simple_resume.shell.runtime.generate.session_mod.ResumeSession")
    def test_generate_pdf_batch_mode(
        self, mock_session_cls: MagicMock, tmp_path: Path
    ) -> None:
        """Test generate_pdf in batch mode (no name specified)."""
        # Setup
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__.return_value = mock_session
        mock_result = Mock(spec=BatchGenerationResult)
        mock_session.generate_all.return_value = mock_result

        config = GenerationConfig(data_dir=tmp_path, pattern="*.yaml", open_after=False)

        # Execute
        result = generate_pdf(config, custom_field="value")

        # Assert
        mock_session.generate_all.assert_called_once_with(
            format=OutputFormat.PDF,
            pattern="*.yaml",
            open_after=False,
            custom_field="value",
        )
        assert result == mock_result


class TestGenerateHtml:
    """Test generate_html function."""

    @patch("simple_resume.shell.runtime.generate.session_mod.ResumeSession")
    @patch("simple_resume.shell.runtime.generate.generate_core")
    def test_generate_html_with_name_and_overrides(
        self, mock_generate_core: MagicMock, mock_session_cls: MagicMock, tmp_path: Path
    ) -> None:
        """Test generate_html with name and overrides."""
        # Setup
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__.return_value = mock_session
        mock_resume = MagicMock()
        mock_resume_with_config = MagicMock()
        mock_resume.with_config.return_value = mock_resume_with_config
        mock_session.resume.return_value = mock_resume
        mock_result = Mock(spec=GenerationResult)
        mock_generate_core.to_html.return_value = mock_result

        config = GenerationConfig(
            name="test_resume",
            data_dir=tmp_path,
            output_path=tmp_path / "output.html",
            open_after=True,
            browser="firefox",
        )

        # Execute
        result = generate_html(config, template="modern")

        # Assert
        mock_session.resume.assert_called_once_with("test_resume")
        mock_resume.with_config.assert_called_once_with(template="modern")
        mock_generate_core.to_html.assert_called_once_with(
            mock_resume_with_config,
            output_path=tmp_path / "output.html",
            open_after=True,
            browser="firefox",
        )
        assert result == mock_result

    @patch("simple_resume.shell.runtime.generate.session_mod.ResumeSession")
    def test_generate_html_batch_mode(
        self, mock_session_cls: MagicMock, tmp_path: Path
    ) -> None:
        """Test generate_html in batch mode."""
        # Setup
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__.return_value = mock_session
        mock_result = Mock(spec=BatchGenerationResult)
        mock_session.generate_all.return_value = mock_result

        config = GenerationConfig(
            data_dir=tmp_path, pattern="*.yaml", open_after=True, browser="chrome"
        )

        # Execute
        result = generate_html(config)

        # Assert
        mock_session.generate_all.assert_called_once_with(
            format=OutputFormat.HTML,
            pattern="*.yaml",
            open_after=True,
            browser="chrome",
        )
        assert result == mock_result


class TestGenerateAll:
    """Test generate_all function."""

    @patch("simple_resume.shell.runtime.generate.session_mod.ResumeSession")
    @patch("simple_resume.shell.runtime.generate.generate_core")
    def test_generate_all_with_empty_formats_defaults_to_pdf(
        self, mock_generate_core: MagicMock, mock_session_cls: MagicMock, tmp_path: Path
    ) -> None:
        """Test generate_all defaults to PDF when formats is empty."""
        # Setup - empty formats defaults to PDF per the implementation
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__.return_value = mock_session
        mock_result = Mock(spec=BatchGenerationResult)
        mock_session.generate_all.return_value = mock_result

        config = GenerationConfig(data_dir=tmp_path, formats=[])

        # Execute - should default to PDF, not raise error
        result = generate_all(config)

        # Assert
        assert "pdf" in result
        mock_session.generate_all.assert_called_once()

    @patch("simple_resume.shell.runtime.generate.session_mod.ResumeSession")
    @patch("simple_resume.shell.runtime.generate.generate_core")
    def test_generate_all_single_resume_pdf(
        self, mock_generate_core: MagicMock, mock_session_cls: MagicMock, tmp_path: Path
    ) -> None:
        """Test generate_all for single resume with PDF format."""
        # Setup
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__.return_value = mock_session
        mock_resume = MagicMock()
        mock_resume_with_config = MagicMock()
        mock_resume.with_config.return_value = mock_resume_with_config
        mock_session.resume.return_value = mock_resume
        mock_pdf_result = Mock(spec=GenerationResult)
        mock_generate_core.to_pdf.return_value = mock_pdf_result

        config = GenerationConfig(
            name="test",
            data_dir=tmp_path,
            formats=[OutputFormat.PDF],
            open_after=True,
        )

        # Execute
        result = generate_all(config, custom="override")

        # Assert
        mock_session.resume.assert_called_once_with("test")
        mock_resume.with_config.assert_called_once_with(custom="override")
        mock_generate_core.to_pdf.assert_called_once_with(
            mock_resume_with_config, output_path=None, open_after=True
        )
        assert result == {"pdf": mock_pdf_result}

    @patch("simple_resume.shell.runtime.generate.session_mod.ResumeSession")
    @patch("simple_resume.shell.runtime.generate.generate_core")
    def test_generate_all_single_resume_html(
        self, mock_generate_core: MagicMock, mock_session_cls: MagicMock, tmp_path: Path
    ) -> None:
        """Test generate_all for single resume with HTML format."""
        # Setup
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__.return_value = mock_session
        mock_resume = MagicMock()
        mock_resume_with_config = MagicMock()
        mock_resume.with_config.return_value = mock_resume_with_config
        mock_session.resume.return_value = mock_resume
        mock_html_result = Mock(spec=GenerationResult)
        mock_generate_core.to_html.return_value = mock_html_result

        config = GenerationConfig(
            name="test",
            data_dir=tmp_path,
            formats=[OutputFormat.HTML],
            browser="safari",
        )

        # Execute
        result = generate_all(config)

        # Assert
        mock_generate_core.to_html.assert_called_once_with(
            mock_resume, output_path=None, open_after=False, browser="safari"
        )
        assert result == {"html": mock_html_result}

    @patch("simple_resume.shell.runtime.generate.session_mod.ResumeSession")
    @patch("simple_resume.shell.runtime.generate.generate_core")
    def test_generate_all_single_resume_multiple_formats(
        self, mock_generate_core: MagicMock, mock_session_cls: MagicMock, tmp_path: Path
    ) -> None:
        """Test generate_all for single resume with multiple formats."""
        # Setup
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__.return_value = mock_session
        mock_resume = MagicMock()
        mock_session.resume.return_value = mock_resume
        mock_pdf_result = Mock(spec=GenerationResult)
        mock_html_result = Mock(spec=GenerationResult)
        mock_generate_core.to_pdf.return_value = mock_pdf_result
        mock_generate_core.to_html.return_value = mock_html_result

        config = GenerationConfig(
            name="test",
            data_dir=tmp_path,
            formats=[OutputFormat.PDF, OutputFormat.HTML],
        )

        # Execute
        result = generate_all(config)

        # Assert
        assert result == {"pdf": mock_pdf_result, "html": mock_html_result}

    def test_generate_all_unsupported_string_format_raises_error(
        self, tmp_path: Path
    ) -> None:
        """Test generate_all raises error for unsupported string format."""
        # "docx" is unsupported and should raise ValueError
        config = GenerationConfig(data_dir=tmp_path, formats=["docx"])

        # Execute - should raise ValueError for unsupported format
        with pytest.raises(ValueError, match="Unsupported format"):
            generate_all(config)

    @patch("simple_resume.shell.runtime.generate.session_mod.ResumeSession")
    def test_generate_all_batch_mode(
        self, mock_session_cls: MagicMock, tmp_path: Path
    ) -> None:
        """Test generate_all in batch mode."""
        # Setup
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__.return_value = mock_session
        mock_pdf_result = Mock(spec=BatchGenerationResult)
        mock_html_result = Mock(spec=BatchGenerationResult)
        mock_session.generate_all.side_effect = [mock_pdf_result, mock_html_result]

        config = GenerationConfig(
            data_dir=tmp_path,
            formats=[OutputFormat.PDF, OutputFormat.HTML],
            pattern="test_*",
            browser="chrome",
        )

        # Execute
        result = generate_all(config, custom="value")

        # Assert
        assert mock_session.generate_all.call_count == 2
        assert result == {"pdf": mock_pdf_result, "html": mock_html_result}


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


class TestExecuteGenerationCommands:
    """Test execute_generation_commands function."""

    def test_execute_single_pdf_command(self, tmp_path: Path) -> None:
        """Test executing a single PDF generation command."""
        # Setup
        mock_result = Mock(spec=GenerationResult)

        config = GenerationConfig(name="test", data_dir=tmp_path)
        command = GenerationCommand(
            kind=CommandType.SINGLE,
            format=OutputFormat.PDF,
            config=config,
            overrides={"custom": "value"},
        )

        # Patch the _FORMAT_EXECUTORS dict
        with patch.dict(
            "simple_resume.shell.runtime.generate._FORMAT_EXECUTORS",
            {OutputFormat.PDF: Mock(return_value=mock_result)},
        ):
            # Execute
            results = execute_generation_commands([command])

            # Assert
            assert len(results) == 1
            assert results[0][0] == command
            assert results[0][1] == mock_result

    def test_execute_batch_single_html_command(self, tmp_path: Path) -> None:
        """Test executing a batch single HTML generation command."""
        # Setup
        mock_result = Mock(spec=BatchGenerationResult)

        config = GenerationConfig(data_dir=tmp_path)
        command = GenerationCommand(
            kind=CommandType.BATCH_SINGLE,
            format=OutputFormat.HTML,
            config=config,
            overrides={},
        )

        # Patch the _FORMAT_EXECUTORS dict
        with patch.dict(
            "simple_resume.shell.runtime.generate._FORMAT_EXECUTORS",
            {OutputFormat.HTML: Mock(return_value=mock_result)},
        ):
            # Execute
            results = execute_generation_commands([command])

            # Assert
            assert len(results) == 1
            assert results[0][1] == mock_result

    def test_execute_command_with_no_format_raises_error(self, tmp_path: Path) -> None:
        """Test executing command without format raises error."""
        config = GenerationConfig(name="test", data_dir=tmp_path)
        command = GenerationCommand(
            kind=CommandType.SINGLE, format=None, config=config, overrides={}
        )

        with pytest.raises(ValueError, match="Missing format"):
            execute_generation_commands([command])

    def test_execute_command_with_unsupported_format_raises_error(
        self, tmp_path: Path
    ) -> None:
        """Test executing command with unsupported format raises error."""
        # Create a mock format that's not in the executor map
        mock_format = MagicMock(spec=OutputFormat)
        mock_format.value = "unsupported"

        config = GenerationConfig(name="test", data_dir=tmp_path)
        command = GenerationCommand(
            kind=CommandType.SINGLE,
            format=mock_format,
            config=config,
            overrides={},
        )

        with pytest.raises(ValueError, match="Unsupported format"):
            execute_generation_commands([command])

    @patch("simple_resume.shell.runtime.generate.generate_all")
    def test_execute_batch_all_command(
        self, mock_generate_all: MagicMock, tmp_path: Path
    ) -> None:
        """Test executing a batch all command."""
        # Setup
        mock_result = {"pdf": Mock(), "html": Mock()}
        mock_generate_all.return_value = mock_result

        config = GenerationConfig(data_dir=tmp_path)
        command = GenerationCommand(
            kind=CommandType.BATCH_ALL,
            format=None,
            config=config,
            overrides={"template": "modern"},
        )

        # Execute
        results = execute_generation_commands([command])

        # Assert
        assert len(results) == 1
        assert results[0][1] == mock_result
        mock_generate_all.assert_called_once_with(config, template="modern")

    def test_execute_command_with_unsupported_type_raises_error(
        self, tmp_path: Path
    ) -> None:
        """Test executing command with unsupported type raises error."""
        # Create a mock command type
        mock_type = MagicMock()
        mock_type.configure_mock(**{"__str__.return_value": "UNSUPPORTED"})

        config = GenerationConfig(name="test", data_dir=tmp_path)
        command = GenerationCommand(
            kind=mock_type, format=OutputFormat.PDF, config=config, overrides={}
        )

        with pytest.raises(ValueError, match="Unsupported command type"):
            execute_generation_commands([command])

    def test_execute_multiple_commands(self, tmp_path: Path) -> None:
        """Test executing multiple commands."""
        # Setup
        mock_pdf_result = Mock(spec=GenerationResult)
        mock_html_result = Mock(spec=GenerationResult)

        config = GenerationConfig(name="test", data_dir=tmp_path)
        pdf_command = GenerationCommand(
            kind=CommandType.SINGLE,
            format=OutputFormat.PDF,
            config=config,
            overrides={},
        )
        html_command = GenerationCommand(
            kind=CommandType.SINGLE,
            format=OutputFormat.HTML,
            config=config,
            overrides={},
        )

        # Patch the _FORMAT_EXECUTORS dict
        with patch.dict(
            "simple_resume.shell.runtime.generate._FORMAT_EXECUTORS",
            {
                OutputFormat.PDF: Mock(return_value=mock_pdf_result),
                OutputFormat.HTML: Mock(return_value=mock_html_result),
            },
        ):
            # Execute
            results = execute_generation_commands([pdf_command, html_command])

            # Assert
            assert len(results) == 2
            assert results[0][1] == mock_pdf_result
            assert results[1][1] == mock_html_result


class TestSessionErrorHandling:
    """Test error handling in session-based functions."""

    @patch("simple_resume.shell.runtime.generate.session_mod.ResumeSession")
    def test_generate_pdf_validation_error_propagates(
        self, mock_session_cls: MagicMock, tmp_path: Path
    ) -> None:
        """Test that ValidationError is propagated from session."""
        mock_session_cls.return_value.__enter__.side_effect = ValidationError(
            "Invalid data"
        )

        config = GenerationConfig(name="test", data_dir=tmp_path)

        with pytest.raises(ValidationError, match="Invalid data"):
            generate_pdf(config)

    @patch("simple_resume.shell.runtime.generate.session_mod.ResumeSession")
    def test_generate_pdf_configuration_error_propagates(
        self, mock_session_cls: MagicMock, tmp_path: Path
    ) -> None:
        """Test that ConfigurationError is propagated from session."""
        mock_session_cls.return_value.__enter__.side_effect = ConfigurationError(
            "Bad config"
        )

        config = GenerationConfig(name="test", data_dir=tmp_path)

        with pytest.raises(ConfigurationError, match="Bad config"):
            generate_pdf(config)

    @patch("simple_resume.shell.runtime.generate.session_mod.ResumeSession")
    def test_generate_pdf_filesystem_error_propagates(
        self, mock_session_cls: MagicMock, tmp_path: Path
    ) -> None:
        """Test that FileSystemError is propagated from session."""
        mock_session_cls.return_value.__enter__.side_effect = FileSystemError(
            "File not found"
        )

        config = GenerationConfig(name="test", data_dir=tmp_path)

        with pytest.raises(FileSystemError, match="File not found"):
            generate_pdf(config)

    @patch("simple_resume.shell.runtime.generate.session_mod.ResumeSession")
    def test_generate_pdf_generation_error_propagates(
        self, mock_session_cls: MagicMock, tmp_path: Path
    ) -> None:
        """Test that GenerationError is propagated from session."""
        mock_session_cls.return_value.__enter__.side_effect = GenErr(
            "Generation failed"
        )

        config = GenerationConfig(name="test", data_dir=tmp_path)

        with pytest.raises(GenErr, match="Generation failed"):
            generate_pdf(config)


class TestHelperFunctions:
    """Test internal helper functions."""

    @patch("simple_resume.shell.runtime.generate.validate_directory_path")
    @patch("simple_resume.shell.runtime.generate.session_mod.ResumeSession")
    def test_resolve_data_dir_with_paths_returns_none(
        self, mock_session_cls: MagicMock, mock_validate: MagicMock, tmp_path: Path
    ) -> None:
        """Test that data_dir resolution returns None when paths provided."""
        # Setup mock session to not raise errors
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__.return_value = mock_session
        mock_session.generate_all.return_value = Mock()

        mock_paths = Mock(spec=Paths)
        config = GenerationConfig(paths=mock_paths, data_dir=tmp_path)

        # Execute - this will trigger _resolve_data_dir internally
        generate_pdf(config)

        # Assert - validate should not be called when paths is provided
        mock_validate.assert_not_called()

    @patch("simple_resume.shell.runtime.generate.validate_directory_path")
    @patch("simple_resume.shell.runtime.generate.session_mod.ResumeSession")
    def test_resolve_data_dir_without_data_dir_returns_none(
        self, mock_session_cls: MagicMock, mock_validate: MagicMock
    ) -> None:
        """Test that data_dir resolution returns None when no data_dir."""
        # Setup mock session
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__.return_value = mock_session
        mock_session.generate_all.return_value = Mock()

        config = GenerationConfig(data_dir=None)

        # Execute
        generate_pdf(config)

        # Assert - validate should not be called
        mock_validate.assert_not_called()

    @patch("simple_resume.shell.runtime.generate.session_mod.ResumeSession")
    @patch("simple_resume.shell.runtime.generate.generate_core")
    def test_normalize_formats_with_empty_list_defaults_to_pdf(
        self, mock_generate_core: MagicMock, mock_session_cls: MagicMock, tmp_path: Path
    ) -> None:
        """Test _normalize_formats handles empty list by defaulting to PDF."""
        # Empty list defaults to (OutputFormat.PDF,) per the implementation
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__.return_value = mock_session
        mock_session.generate_all.return_value = Mock()

        config = GenerationConfig(name="test", data_dir=tmp_path, formats=[])

        # Should not raise - defaults to PDF
        result = generate_all(config)
        assert "pdf" in result

    @patch("simple_resume.shell.runtime.generate.session_mod.ResumeSession")
    @patch("simple_resume.shell.runtime.generate.generate_core")
    def test_normalize_format_with_output_format_enum(
        self, mock_generate_core: MagicMock, mock_session_cls: MagicMock, tmp_path: Path
    ) -> None:
        """Test _normalize_format handles OutputFormat enum directly."""
        # Setup
        mock_session = MagicMock()
        mock_session_cls.return_value.__enter__.return_value = mock_session
        mock_resume = MagicMock()
        mock_session.resume.return_value = mock_resume
        mock_generate_core.to_pdf.return_value = Mock()

        # Use enum directly in formats
        config = GenerationConfig(
            name="test", data_dir=tmp_path, formats=[OutputFormat.PDF]
        )

        # Execute
        result = generate_all(config)

        # Assert - should work fine with enum
        assert "pdf" in result
