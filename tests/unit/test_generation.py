"""Tests for the unified generation functions module."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from simple_resume.config import Paths
from simple_resume.constants import OutputFormat
from simple_resume.core.generation_plan import GenerationCommand
from simple_resume.exceptions import (
    ConfigurationError,
    FileSystemError,
    GenerationError,
    ValidationError,
)
from simple_resume.generation import (
    GenerationConfig,
    generate_all,
    generate_html,
    generate_pdf,
    generate_resume,
)
from simple_resume.result import BatchGenerationResult, GenerationResult
from tests.bdd import Scenario


class TestGeneratePdf:
    """Test the generate_pdf function."""

    @patch("simple_resume.generation.validate_directory_path")
    @patch("simple_resume.generation.ResumeSession")
    @patch("simple_resume.generation.SessionConfig")
    def test_generate_pdf_single_resume(
        self,
        mock_session_config: Mock,
        mock_resume_session: Mock,
        mock_validate_path: Mock,
        story: Scenario,
    ) -> None:
        story.given("a single resume name and data directory")
        mock_validate_path.return_value = Path("/test")
        mock_session = Mock()
        mock_resume_session.return_value.__enter__.return_value = mock_session
        mock_validate_path.return_value = Path("/workspace")
        mock_resume_session.return_value.__exit__.return_value = None

        mock_result = Mock(spec=GenerationResult)
        mock_session.resume.return_value.to_pdf.return_value = mock_result

        story.when("generate_pdf is invoked")
        config = GenerationConfig(name="test_resume", data_dir="/test")
        result = generate_pdf(config)

        story.then("the resume is rendered once and the result returned")
        assert result == mock_result
        mock_session.resume.assert_called_once_with("test_resume")
        mock_session.resume.return_value.to_pdf.assert_called_once()

    @patch("simple_resume.generation.validate_directory_path")
    @patch("simple_resume.generation.ResumeSession")
    @patch("simple_resume.generation.SessionConfig")
    def test_generate_pdf_multiple_resumes(
        self,
        mock_session_config: Mock,
        mock_resume_session: Mock,
        mock_validate_path: Mock,
        story: Scenario,
    ) -> None:
        story.given("batch generation with generate_all")
        mock_validate_path.return_value = Path("/workspace")
        mock_session = Mock()
        mock_resume_session.return_value.__enter__.return_value = mock_session
        mock_validate_path.return_value = Path("/workspace")
        mock_resume_session.return_value.__exit__.return_value = None

        mock_result = Mock(spec=BatchGenerationResult)
        mock_session.generate_all.return_value = mock_result

        story.when("generate_pdf is called without a name")
        config = GenerationConfig(data_dir="/workspace")
        result = generate_pdf(config)

        story.then("generate_all is executed and its result is bubbled up")
        assert result == mock_result
        mock_session.generate_all.assert_called_once()

    @patch("simple_resume.generation.validate_directory_path")
    @patch("simple_resume.generation.ResumeSession")
    @patch("simple_resume.generation.SessionConfig")
    def test_generate_pdf_with_config_overrides(
        self,
        mock_session_config: Mock,
        mock_resume_session: Mock,
        mock_validate_path: Mock,
        story: Scenario,
    ) -> None:
        mock_validate_path.return_value = Path("/workspace")
        mock_session = Mock()
        mock_resume_session.return_value.__enter__.return_value = mock_session
        mock_validate_path.return_value = Path("/workspace")
        mock_resume_session.return_value.__exit__.return_value = None

        mock_result = Mock(spec=GenerationResult)
        resume_handle = mock_session.resume.return_value
        resume_handle.with_config.return_value.to_pdf.return_value = mock_result

        story.when(
            "generate_pdf is called with template, auto-open, and metadata overrides"
        )
        config = GenerationConfig(
            name="test_resume",
            template="professional",
            open_after=True,
        )
        result = generate_pdf(config, theme_color="#FF0000")

        story.then("the overrides move to SessionConfig and the PDF output is returned")
        assert result == mock_result
        mock_session_config.assert_called_once()
        call_args = mock_session_config.call_args[1]
        assert call_args["default_template"] == "professional"
        assert call_args["auto_open"] is True
        assert call_args["session_metadata"]["theme_color"] == "#FF0000"

    @patch("simple_resume.generation.ResumeSession")
    @patch("simple_resume.generation.SessionConfig")
    def test_generate_pdf_with_paths(
        self, mock_session_config: Mock, mock_resume_session: Mock, story: Scenario
    ) -> None:
        mock_paths = Mock(spec=Paths)

        mock_session = Mock()
        mock_resume_session.return_value.__enter__.return_value = mock_session
        mock_resume_session.return_value.__exit__.return_value = None

        mock_result = Mock(spec=GenerationResult)
        mock_session.resume.return_value.to_pdf.return_value = mock_result

        story.when("generate_pdf is provided with resolved Paths")
        config = GenerationConfig(paths=mock_paths, name="test_resume")
        result = generate_pdf(config)

        story.then(
            "ResumeSession is constructed with the provided paths and result returned"
        )
        assert result == mock_result
        mock_resume_session.assert_called_once_with(
            data_dir=None, paths=mock_paths, config=mock_session_config.return_value
        )

    @patch("simple_resume.generation.validate_directory_path")
    @patch("simple_resume.generation.ResumeSession")
    def test_generate_pdf_handles_generation_error(
        self, mock_resume_session: Mock, mock_validate_path: Mock, story: Scenario
    ) -> None:
        story.given("ResumeSession raises GenerationError")
        mock_validate_path.return_value = Path("/workspace")
        mock_resume_session.side_effect = GenerationError(
            "Test error", format_type="pdf"
        )

        config = GenerationConfig(data_dir="/workspace")
        with pytest.raises(GenerationError, match="Test error"):
            generate_pdf(config)

    @patch("simple_resume.generation.validate_directory_path")
    @patch("simple_resume.generation.ResumeSession")
    def test_generate_pdf_wraps_generic_error(
        self, mock_resume_session: Mock, mock_validate_path: Mock, story: Scenario
    ) -> None:
        story.given("an unexpected ValueError occurs during session setup")
        mock_validate_path.return_value = Path("/workspace")
        mock_resume_session.side_effect = ValueError("Generic error")

        config = GenerationConfig(data_dir="/workspace")
        with pytest.raises(
            GenerationError, match="Failed to generate PDFs: Generic error"
        ):
            generate_pdf(config)


class TestGenerateHtml:
    """Test the generate_html function."""

    @patch("simple_resume.generation.ResumeSession")
    @patch("simple_resume.generation.SessionConfig")
    def test_generate_html_single_resume(
        self, mock_session_config: Mock, mock_resume_session: Mock, story: Scenario
    ) -> None:
        mock_session = Mock()
        mock_resume_session.return_value.__enter__.return_value = mock_session
        mock_resume_session.return_value.__exit__.return_value = None

        mock_result = Mock(spec=GenerationResult)
        mock_session.resume.return_value.to_html.return_value = mock_result

        story.when("generate_html renders a named resume")
        config = GenerationConfig(name="test_resume", data_dir="/test")
        result = generate_html(config)

        story.then("HTML output for that resume is returned")
        assert result == mock_result
        mock_session.resume.assert_called_once_with("test_resume")
        mock_session.resume.return_value.to_html.assert_called_once()

    @patch("simple_resume.generation.ResumeSession")
    @patch("simple_resume.generation.SessionConfig")
    def test_generate_html_multiple_resumes(
        self, mock_session_config: Mock, mock_resume_session: Mock, story: Scenario
    ) -> None:
        mock_session = Mock()
        mock_resume_session.return_value.__enter__.return_value = mock_session
        mock_resume_session.return_value.__exit__.return_value = None

        mock_result = Mock(spec=BatchGenerationResult)
        mock_session.generate_all.return_value = mock_result

        story.when("generate_html runs without a specific name")
        config = GenerationConfig(data_dir="/test")
        result = generate_html(config)

        story.then("generate_all handles batch HTML generation")
        assert result == mock_result
        mock_session.generate_all.assert_called_once()

    @patch("simple_resume.generation.ResumeSession")
    @patch("simple_resume.generation.SessionConfig")
    def test_generate_html_with_browser(
        self, mock_session_config: Mock, mock_resume_session: Mock, story: Scenario
    ) -> None:
        mock_session = Mock()
        mock_resume_session.return_value.__enter__.return_value = mock_session
        mock_resume_session.return_value.__exit__.return_value = None

        mock_result = Mock(spec=GenerationResult)
        mock_session.resume.return_value.to_html.return_value = mock_result

        story.when("generate_html is called with a browser hint")
        config = GenerationConfig(
            name="test_resume",
            browser="firefox",
            data_dir="/test",
        )
        result = generate_html(config)

        story.then("the browser hint is forwarded to the renderer")
        assert result == mock_result
        mock_session.resume.return_value.to_html.assert_called_once_with(
            open_after=False, browser="firefox"
        )

    @patch("simple_resume.generation.ResumeSession")
    @patch("simple_resume.generation.SessionConfig")
    def test_generate_html_preview_mode_default(
        self, mock_session_config: Mock, mock_resume_session: Mock, story: Scenario
    ) -> None:
        mock_session = Mock()
        mock_resume_session.return_value.__enter__.return_value = mock_session
        mock_resume_session.return_value.__exit__.return_value = None

        mock_result = Mock(spec=GenerationResult)
        mock_session.resume.return_value.to_html.return_value = mock_result

        config = GenerationConfig(name="test_resume", data_dir="/test", preview=True)
        result = generate_html(config)

        story.then("HTML generation uses preview_mode when specified")
        assert result == mock_result
        mock_session_config.assert_called_once()
        call_args = mock_session_config.call_args[1]
        assert call_args["preview_mode"] is True  # Default for HTML


class TestGenerateAll:
    """Test the generate_all function."""

    def test_generate_all_invalid_formats(self, story: Scenario) -> None:
        story.given("an unsupported format is included")
        config = GenerationConfig(formats=["pdf", "docx"])
        with pytest.raises(ValueError, match="Unsupported format"):
            generate_all(config)

    @patch("simple_resume.generation.validate_directory_path")
    @patch("simple_resume.generation.validate_directory_path")
    @patch("simple_resume.generation.ResumeSession")
    @patch("simple_resume.generation.SessionConfig")
    def test_generate_all_multiple_formats(
        self,
        mock_session_config: Mock,
        mock_resume_session: Mock,
        mock_validate_path: Mock,
        story: Scenario,
    ) -> None:
        mock_session = Mock()
        mock_validate_path.return_value = Path("/workspace")
        mock_resume_session.return_value.__enter__.return_value = mock_session
        mock_resume_session.return_value.__exit__.return_value = None

        # Mock results for different formats
        mock_pdf_result = Mock(spec=BatchGenerationResult)
        mock_html_result = Mock(spec=BatchGenerationResult)
        mock_session.generate_all.side_effect = [mock_pdf_result, mock_html_result]

        story.when("generate_all runs for both pdf and html")
        config = GenerationConfig(formats=["pdf", "html"], data_dir="/workspace")
        result = generate_all(config)

        story.then("both formats are generated and results keyed appropriately")
        assert "pdf" in result
        assert "html" in result
        assert result["pdf"] == mock_pdf_result
        assert result["html"] == mock_html_result
        assert mock_session.generate_all.call_count == 2

    @patch("simple_resume.generation.validate_directory_path")
    @patch("simple_resume.generation.validate_directory_path")
    @patch("simple_resume.generation.ResumeSession")
    @patch("simple_resume.generation.SessionConfig")
    def test_generate_all_single_resume_multiple_formats(
        self,
        mock_session_config: Mock,
        mock_resume_session: Mock,
        mock_validate_path: Mock,
        story: Scenario,
    ) -> None:
        mock_session = Mock()
        mock_validate_path.return_value = Path("/workspace")
        mock_resume_session.return_value.__enter__.return_value = mock_session
        mock_resume_session.return_value.__exit__.return_value = None

        mock_pdf_result = Mock(spec=GenerationResult)
        mock_html_result = Mock(spec=GenerationResult)
        mock_resume = Mock()
        mock_resume.to_pdf.return_value = mock_pdf_result
        mock_resume.to_html.return_value = mock_html_result
        mock_session.resume.return_value = mock_resume

        story.when("generate_all is given a specific resume name")
        config = GenerationConfig(
            name="test_resume", formats=["pdf", "html"], data_dir="/workspace"
        )
        result = generate_all(config)

        story.then("both format conversions originate from the same resume instance")
        assert "pdf" in result
        assert "html" in result
        assert result["pdf"] == mock_pdf_result
        assert result["html"] == mock_html_result

    @patch("simple_resume.generation.validate_directory_path")
    @patch("simple_resume.generation.validate_directory_path")
    @patch("simple_resume.generation.ResumeSession")
    @patch("simple_resume.generation.SessionConfig")
    def test_generate_all_with_config_overrides(
        self,
        mock_session_config: Mock,
        mock_resume_session: Mock,
        mock_validate_path: Mock,
        story: Scenario,
    ) -> None:
        mock_session = Mock()
        mock_validate_path.return_value = Path("/workspace")
        mock_resume_session.return_value.__enter__.return_value = mock_session
        mock_resume_session.return_value.__exit__.return_value = None

        mock_result = Mock(spec=BatchGenerationResult)
        mock_session.generate_all.return_value = mock_result

        story.when("generate_all receives template and preview overrides")
        config = GenerationConfig(
            formats=["pdf"], template="modern", preview=True, data_dir="/workspace"
        )
        result = generate_all(config)

        story.then(
            "SessionConfig picks up the overrides and results include pdf output"
        )
        assert "pdf" in result
        mock_session_config.assert_called_once()
        call_args = mock_session_config.call_args[1]
        assert call_args["default_template"] == "modern"
        assert call_args["preview_mode"] is True


class TestGenerateResume:
    """Test the generate_resume function."""

    @patch("simple_resume.generation.execute_generation_commands")
    def test_generate_resume_pdf(self, mock_execute: Mock) -> None:
        """Test generate_resume with PDF format."""
        mock_result = Mock(spec=GenerationResult)
        captured: list[GenerationCommand] = []

        def fake_execute(
            commands: list[GenerationCommand],
        ) -> list[tuple[GenerationCommand, object]]:
            captured.extend(commands)
            return [(commands[0], mock_result)]

        mock_execute.side_effect = fake_execute

        config = GenerationConfig(name="test_resume", format="pdf", data_dir="/test")
        result = generate_resume(config)

        assert result == mock_result
        assert captured[0].format is OutputFormat.PDF
        mock_execute.assert_called_once()

    @patch("simple_resume.generation.execute_generation_commands")
    def test_generate_resume_html(self, mock_execute: Mock, story: Scenario) -> None:
        mock_result = Mock(spec=GenerationResult)
        captured: list[GenerationCommand] = []

        def fake_execute(
            commands: list[GenerationCommand],
        ) -> list[tuple[GenerationCommand, object]]:
            captured.extend(commands)
            return [(commands[0], mock_result)]

        mock_execute.side_effect = fake_execute

        story.when("generate_resume targets the HTML format")
        config = GenerationConfig(name="test_resume", format="html", data_dir="/data")
        result = generate_resume(config)

        story.then("a single HTML command runs and the result is returned")
        assert result == mock_result
        assert captured[0].format is OutputFormat.HTML
        mock_execute.assert_called_once()

    @patch("simple_resume.generation.execute_generation_commands")
    def test_generate_resume_with_output_path(
        self, mock_execute: Mock, story: Scenario
    ) -> None:
        mock_result = Mock(spec=GenerationResult)
        captured: list[GenerationCommand] = []

        def fake_execute(
            commands: list[GenerationCommand],
        ) -> list[tuple[GenerationCommand, object]]:
            captured.extend(commands)
            return [(commands[0], mock_result)]

        mock_execute.side_effect = fake_execute

        story.when("generate_resume is provided an explicit output path")
        config = GenerationConfig(
            name="test_resume",
            format="pdf",
            output_path="/custom/output/test_resume.pdf",
            data_dir="/test",
        )
        result = generate_resume(config)

        story.then("the planner receives the derived output directory")
        assert result == mock_result
        command_config = captured[0].config
        assert command_config.output_path == Path("/custom/output/test_resume.pdf")

    def test_generate_resume_invalid_format(self, story: Scenario) -> None:
        story.given("an unsupported format is requested")
        config = GenerationConfig(name="test_resume", format="docx")
        with pytest.raises(ValueError, match="Unsupported format:.*docx"):
            generate_resume(config)

    @patch("simple_resume.generation.execute_generation_commands")
    def test_generate_resume_format_case_insensitive(
        self,
        mock_execute: Mock,
        story: Scenario,
    ) -> None:
        mock_result = Mock(spec=GenerationResult)
        captured: list[GenerationCommand] = []

        def fake_execute(
            commands: list[GenerationCommand],
        ) -> list[tuple[GenerationCommand, object]]:
            captured.extend(commands)
            return [(commands[0], mock_result)]

        mock_execute.side_effect = fake_execute

        story.when("format argument is provided in uppercase")
        config = GenerationConfig(
            name="test_resume",
            format="PDF",  # Uppercase
            data_dir="/test",
        )
        result = generate_resume(config)

        story.then("the call is normalised and generation proceeds")
        assert result == mock_result
        assert captured[0].format is OutputFormat.PDF
        mock_execute.assert_called_once()

    @patch("simple_resume.generation.execute_generation_commands")
    def test_generate_resume_with_all_params(
        self, mock_execute: Mock, story: Scenario
    ) -> None:
        mock_result = Mock(spec=GenerationResult)
        captured: list[GenerationCommand] = []

        def fake_execute(
            commands: list[GenerationCommand],
        ) -> list[tuple[GenerationCommand, object]]:
            captured.extend(commands)
            return [(commands[0], mock_result)]

        mock_execute.side_effect = fake_execute

        story.when("generate_resume receives full parameter set")
        config = GenerationConfig(
            name="test_resume",
            format="pdf",
            data_dir="/test",
            template="professional",
            output_path="/custom/output.pdf",
            open_after=True,
            preview=False,
            paths=Mock(),
        )
        result = generate_resume(config)

        story.then("all arguments are forwarded to the planner correctly")
        assert result == mock_result
        command_config = captured[0].config
        assert command_config.template == "professional"
        assert command_config.output_path == Path("/custom/output.pdf")
        assert command_config.open_after is True
        assert command_config.preview is False
        mock_execute.assert_called_once()


class TestGenerationErrorHandling:
    """Test error handling in generation functions."""

    @patch("simple_resume.generation.validate_directory_path")
    @patch("simple_resume.generation.ResumeSession")
    def test_error_preservation(
        self,
        mock_resume_session: Mock,
        mock_validate_path: Mock,
        story: Scenario,
    ) -> None:
        mock_validate_path.return_value = Path("/workspace")
        mock_resume_session.side_effect = ValidationError("Validation error")

        story.then("generate_pdf propagates ValidationError unchanged")
        config = GenerationConfig(data_dir="/workspace")
        with pytest.raises(ValidationError, match="Validation error"):
            generate_pdf(config)

    @patch("simple_resume.generation.validate_directory_path")
    @patch("simple_resume.generation.ResumeSession")
    def test_error_preservation_config_error(
        self, mock_resume_session: Mock, mock_validate_path: Mock, story: Scenario
    ) -> None:
        mock_validate_path.return_value = Path("/workspace")
        mock_resume_session.side_effect = ConfigurationError("Config error")

        story.then("generate_html propagates ConfigurationError")
        config = GenerationConfig(data_dir="/workspace")
        with pytest.raises(ConfigurationError, match="Config error"):
            generate_html(config)

    @patch("simple_resume.generation.validate_directory_path")
    @patch("simple_resume.generation.ResumeSession")
    def test_error_preservation_filesystem_error(
        self, mock_resume_session: Mock, mock_validate_path: Mock, story: Scenario
    ) -> None:
        mock_validate_path.return_value = Path("/workspace")
        mock_resume_session.side_effect = FileSystemError("Filesystem error")

        story.then("generate_all surfaces FileSystemError without wrapping")
        config = GenerationConfig(data_dir="/workspace")
        with pytest.raises(
            FileSystemError, match="(Filesystem error|Directory does not exist)"
        ):
            generate_all(config)


class TestGenerationIntegration:
    """Test integration patterns between generation functions."""

    @patch("simple_resume.generation.validate_directory_path")
    @patch("simple_resume.generation.ResumeSession")
    @patch("simple_resume.generation.SessionConfig")
    def test_session_configuration_consistency(
        self,
        mock_session_config: Mock,
        mock_resume_session: Mock,
        mock_validate_path: Mock,
        story: Scenario,
    ) -> None:
        mock_session = Mock()
        mock_resume_session.return_value.__enter__.return_value = mock_session
        mock_resume_session.return_value.__exit__.return_value = None
        mock_validate_path.return_value = Path("/workspace")

        mock_result = Mock(spec=GenerationResult)
        mock_session.resume.return_value.to_pdf.return_value = mock_result

        story.when("generate_pdf initialises a session with overrides")
        config = GenerationConfig(
            name="test_resume", template="modern", preview=True, data_dir="/workspace"
        )
        generate_pdf(config)

        pdf_call_args = mock_session_config.call_args[1]
        assert pdf_call_args["default_template"] == "modern"
        assert pdf_call_args["preview_mode"] is True
        assert pdf_call_args["default_format"] is OutputFormat.PDF

        mock_session_config.reset_mock()

        story.when("generate_html initialises a session with different preview flag")
        config = GenerationConfig(
            name="test_resume", template="modern", preview=False, data_dir="/workspace"
        )
        generate_html(config)

        html_call_args = mock_session_config.call_args[1]
        assert html_call_args["default_template"] == "modern"
        assert html_call_args["preview_mode"] is False
        assert html_call_args["default_format"] is OutputFormat.HTML
