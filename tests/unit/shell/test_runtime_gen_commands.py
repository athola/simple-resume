"""Tests for command execution, error handling, and internal helpers."""

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
    _ensure_services_initialized,
    execute_generation_commands,
    generate_all,
    generate_pdf,
)


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


class TestEnsureServicesInitialized:
    """Test _ensure_services_initialized auto-registration."""

    def setup_method(self) -> None:
        """Clear lru_cache between tests so each test starts fresh."""
        _ensure_services_initialized.cache_clear()

    def teardown_method(self) -> None:
        """Restore cache state after each test."""
        _ensure_services_initialized.cache_clear()

    @patch("simple_resume.shell.runtime.generate.register_default_services")
    def test_calls_register_on_first_invocation(self, mock_register: MagicMock) -> None:
        """Test that register_default_services is called on first use."""
        _ensure_services_initialized()
        mock_register.assert_called_once()

    @patch("simple_resume.shell.runtime.generate.register_default_services")
    def test_idempotent_on_repeated_calls(self, mock_register: MagicMock) -> None:
        """Test that repeated calls don't re-register (lru_cache)."""
        _ensure_services_initialized()
        _ensure_services_initialized()
        _ensure_services_initialized()
        mock_register.assert_called_once()

    @patch("simple_resume.shell.runtime.generate.register_default_services")
    def test_run_with_session_triggers_init(
        self, mock_register: MagicMock, tmp_path: Path
    ) -> None:
        """Test that _run_with_session calls _ensure_services_initialized."""
        mock_session = MagicMock()
        with patch(
            "simple_resume.shell.runtime.generate.session_mod.ResumeSession"
        ) as mock_cls:
            mock_cls.return_value.__enter__.return_value = mock_session
            mock_session.generate_all.return_value = Mock()
            config = GenerationConfig(data_dir=tmp_path)
            generate_pdf(config)

        mock_register.assert_called_once()
