"""Tests for format-specific generation functions (PDF, HTML, all)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from simple_resume.core.constants import OutputFormat
from simple_resume.core.models import GenerationConfig
from simple_resume.core.result import BatchGenerationResult, GenerationResult
from simple_resume.shell.runtime.generate import (
    generate_all,
    generate_html,
    generate_pdf,
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
            parallel=False,
            browser=None,
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
            parallel=False,
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
