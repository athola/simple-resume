"""Tests for CLI module."""

import argparse
import io
from pathlib import Path
from typing import Any, cast
from unittest.mock import Mock, patch

import pytest

from simple_resume.cli import (
    _handle_unexpected_error,
    create_parser,
    handle_generate_command,
    handle_session_command,
    handle_validate_command,
    main,
)
from simple_resume.exceptions import (
    GenerationError,
    SimpleResumeError,
    TemplateError,
    ValidationError,
)
from simple_resume.result import BatchGenerationResult


class TestCreateParser:
    """Behavioural tests for the CLI parser."""

    def test_parser_creation(self, story):
        story.given("the request to construct the CLI parser")
        parser = create_parser()

        story.then("an argparse parser for the simple-resume command is returned")
        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.prog == "simple-resume"

    def test_parser_has_version(self, story):
        story.given("the parser exposes a --version flag")
        parser = create_parser()
        with patch("sys.stdout", new=Mock()):
            with pytest.raises(SystemExit) as exc_info:
                parser.parse_args(["--version"])
        story.then("invoking --version exits cleanly with code 0")
        assert isinstance(exc_info.value, SystemExit)
        assert exc_info.value.code == 0

    def test_generate_command_args(self, story):
        story.given("the user invokes the generate subcommand")
        parser = create_parser()

        # Basic generate command
        args = parser.parse_args(["generate"])
        assert args.command == "generate"
        assert args.format == "pdf"
        assert args.name is None

        # Generate with name and options
        args = parser.parse_args(
            ["generate", "my_resume", "--format", "html", "--template", "modern"]
        )
        assert args.name == "my_resume"
        assert args.format == "html"
        assert args.template == "modern"

    def test_generate_command_multiple_formats(self, story):
        story.given("the generate command receives multiple formats")
        parser = create_parser()
        args = parser.parse_args(["generate", "--formats", "pdf", "html"])
        story.then("the parsed namespace lists both formats")
        assert args.formats == ["pdf", "html"]

    def test_session_command_args(self, story, tmp_path: Path):
        parser = create_parser()
        data_dir = tmp_path / "session"
        args = parser.parse_args(["session", "--data-dir", str(data_dir)])
        story.then("the parser records the session command and data directory")
        assert args.command == "session"
        assert args.data_dir == data_dir

    def test_validate_command_args(self, story):
        parser = create_parser()
        args = parser.parse_args(["validate", "my_resume"])
        story.then("the target resume name is captured")
        assert args.command == "validate"
        assert args.name == "my_resume"


class TestHandleGenerateCommand:
    """Test the generate command handler."""

    @patch("simple_resume.cli.generate_resume")
    def test_generate_single_resume_success(self, mock_generate, story):
        story.given("a single resume request with default PDF format")
        args = Mock()
        args.name = "test_resume"
        args.format = "pdf"
        args.formats = None
        args.template = "modern"
        args.output = None
        args.data_dir = Path("/test")
        args.open = False
        args.preview = False
        args.theme_color = None
        args.palette = None
        args.page_width = None
        args.page_height = None

        # Mock result
        mock_result = Mock()
        mock_result.output_path = Path("/test/output.pdf")
        mock_result.exists.return_value = True
        mock_generate.return_value = mock_result

        story.when("handle_generate_command executes")
        result = handle_generate_command(args)
        story.then("generation succeeds and underlying service is called once")
        assert result == 0
        mock_generate.assert_called_once()

    @patch("simple_resume.cli.generate_pdf")
    def test_generate_multiple_resumes_success(self, mock_generate_pdf, story):
        story.given("batch generation has available YAML files")
        args = Mock()
        args.name = None
        args.format = "pdf"
        args.formats = None
        args.template = "modern"
        args.output = None
        args.data_dir = Path("/test")
        args.open = False
        args.preview = False
        args.theme_color = None
        args.palette = None
        args.page_width = None
        args.page_height = None

        # Mock batch result
        mock_result = Mock()
        mock_result.successful = 3
        mock_result.failed = 0
        mock_result.success_rate = 100.0
        mock_result.total_time = 1.5
        mock_result.get_successful.return_value = {
            "resume1": Mock(),
            "resume2": Mock(),
            "resume3": Mock(),
        }
        mock_result.get_failed.return_value = {}
        mock_generate_pdf.return_value = mock_result

        story.when("handle_generate_command executes for batch mode")
        result = handle_generate_command(args)
        story.then("the PDF generator runs and returns success")
        assert result == 0
        mock_generate_pdf.assert_called_once()

    @patch("simple_resume.cli.generate_resume")
    def test_generate_with_config_overrides(self, mock_generate, story):
        story.given("the caller provides configuration overrides")
        args = Mock()
        args.name = "test_resume"
        args.format = "pdf"
        args.formats = None
        args.template = None
        args.output = None
        args.data_dir = None
        args.open = False
        args.preview = False
        args.theme_color = "#0395DE"
        args.palette = "ocean"
        args.page_width = 210
        args.page_height = 297

        mock_result = Mock()
        mock_result.output_path = Path("/test/output.pdf")
        mock_result.exists.return_value = False
        mock_generate.return_value = mock_result

        story.when("handle_generate_command executes")
        result = handle_generate_command(args)
        story.then("the overrides are forwarded to generate_resume")
        assert result == 0
        call_args = mock_generate.call_args
        assert call_args.kwargs["theme_color"] == "#0395DE"
        assert call_args.kwargs["color_scheme"] == "ocean"
        assert call_args.kwargs["page_width"] == 210
        assert call_args.kwargs["page_height"] == 297

    @patch("simple_resume.cli.generate_resume")
    def test_generate_multiple_formats(self, mock_generate, story):
        story.given("a user requests both PDF and HTML outputs")
        args = Mock()
        args.name = "test_resume"
        args.formats = ["pdf", "html"]
        args.template = None
        args.output = None
        args.data_dir = None
        args.open = False
        args.preview = False
        args.theme_color = None
        args.palette = None
        args.page_width = None
        args.page_height = None

        mock_result = Mock()
        mock_result.output_path = Path("/test/output")
        mock_result.exists.return_value = True
        mock_generate.return_value = mock_result

        story.when("handle_generate_command executes")
        result = handle_generate_command(args)
        story.then("each requested format triggers a generation call")
        assert result == 0
        assert mock_generate.call_count == 2

    @patch("simple_resume.cli.generate_html")
    def test_generate_html_batch_skips_latex(
        self, mock_generate_html, story, tmp_path: Path
    ):
        story.given("batch HTML generation encounters LaTeX-only templates")
        args = Mock()
        args.name = None
        args.format = "html"
        args.formats = None
        args.template = None
        args.output = None
        args.data_dir = None
        args.open = False
        args.preview = False
        args.theme_color = None
        args.palette = None
        args.page_width = None
        args.page_height = None
        args.browser = None

        successful_result = Mock()
        successful_result.exists = True
        successful_result.output_path = tmp_path / "resume1.html"

        try:
            try:
                raise TemplateError(
                    "LaTeX mode not supported in HTML generation method"
                )
            except TemplateError:
                raise GenerationError(
                    "resume2: LaTeX mode not supported in HTML generation method",
                    format_type="html",
                ) from None
        except GenerationError as latex_error:
            errors: dict[str, Exception] = {"resume2": latex_error}

        batch_result = BatchGenerationResult(
            results={"resume1": successful_result},
            total_time=1.2,
            successful=1,
            failed=1,
            errors=errors,
        )
        mock_generate_html.return_value = batch_result

        with patch("sys.stdout", new=io.StringIO()) as buffer:
            result = handle_generate_command(args)

        story.then("the handler reports skips instead of failures")
        assert result == 0
        output = buffer.getvalue()
        assert "Skipped (LaTeX): 1" in output
        assert "Failed: 0" in output
        assert "ℹ️ Skipped LaTeX template(s): resume2" in output

    def test_generate_command_error_handling(self):
        """Test error handling in generate command."""
        args = Mock()
        args.formats = None

        with patch(
            "simple_resume.cli.generate_resume",
            side_effect=SimpleResumeError("Test error"),
        ):
            result = handle_generate_command(args)
            assert result == 1

    def test_generate_keyboard_interrupt(self):
        """Test keyboard interrupt handling."""
        args = Mock()
        args.formats = None

        with patch(
            "simple_resume.cli.generate_resume", side_effect=KeyboardInterrupt()
        ):
            result = handle_generate_command(args)
            assert result == 130


class TestHandleSessionCommand:
    """Test the session command handler."""

    @patch("simple_resume.cli.ResumeSession")
    @patch("simple_resume.cli.SessionConfig")
    @patch("simple_resume.cli.input")
    def test_session_command_basic_flow(
        self, mock_input, mock_session_config, mock_resume_session
    ):
        """Test basic session command flow."""
        # Mock args
        args = Mock()
        args.data_dir = Path("/test")
        args.template = "modern"
        args.preview = False

        # Mock session
        mock_session = Mock()
        mock_session.session_id = "test-session-id"
        mock_session.paths.input = Path("/test/input")
        mock_session.paths.output = Path("/test/output")
        mock_session.operation_count = 0
        mock_session.get_cache_info.return_value = {"cache_size": 0}
        mock_session.average_generation_time = 0.0
        mock_session._find_yaml_files.return_value = [Path("/test/resume1.yaml")]

        mock_resume_session.return_value.__enter__.return_value = mock_session
        mock_resume_session.return_value.__exit__.return_value = None

        # Mock user input for exit
        mock_input.side_effect = ["exit"]

        result = handle_session_command(args)
        assert result == 0
        mock_resume_session.assert_called_once()

    @patch("simple_resume.cli.ResumeSession")
    def test_session_command_error(self, mock_resume_session):
        """Test session command error handling."""
        # Mock args
        args = Mock()
        args.data_dir = None
        args.template = None
        args.preview = False

        mock_resume_session.side_effect = SimpleResumeError("Session error")

        result = handle_session_command(args)
        assert result == 1


class TestHandleValidateCommand:
    """Test the validate command handler."""

    @patch("simple_resume.cli.Resume")
    def test_validate_single_resume_success(self, mock_resume_class):
        """Test successful single resume validation."""
        # Mock args
        args = Mock()
        args.name = "test_resume"
        args.data_dir = Path("/test")

        # Mock resume and validation (no exception = success)
        mock_resume = Mock()
        mock_resume.validate_or_raise.return_value = None  # No exception = success
        mock_resume_class.read_yaml.return_value = mock_resume

        result = handle_validate_command(args)
        assert result == 0

    @patch("simple_resume.cli.Resume")
    def test_validate_single_resume_failure(self, mock_resume_class):
        """Test single resume validation with errors."""
        # Mock args
        args = Mock()
        args.name = "test_resume"
        args.data_dir = Path("/test")

        # Mock resume and validation exception
        mock_resume = Mock()
        mock_resume.validate_or_raise.side_effect = ValidationError(
            "Resume validation failed",
            errors=["Missing required field: name"],
            filename="test_resume.yaml",
        )
        mock_resume_class.read_yaml.return_value = mock_resume

        result = handle_validate_command(args)
        assert result == 1

    @patch("simple_resume.session.ResumeSession")
    def test_validate_all_resumes(self, mock_resume_session_class):
        """Test validating all resumes."""
        # Mock args
        args = Mock()
        args.name = None
        args.data_dir = Path("/test")

        # Mock session
        mock_session = Mock()
        mock_session._find_yaml_files.return_value = [
            Path("/test/resume1.yaml"),
            Path("/test/resume2.yaml"),
        ]

        # Mock resumes
        mock_resume1 = Mock()
        mock_validation1 = Mock()
        mock_validation1.is_valid = True
        mock_validation1.warnings = []
        mock_resume1.validate.return_value = mock_validation1

        mock_resume2 = Mock()
        mock_validation2 = Mock()
        mock_validation2.is_valid = True
        mock_validation2.warnings = []
        mock_resume2.validate.return_value = mock_validation2

        mock_session.resume.side_effect = [mock_resume1, mock_resume2]

        mock_resume_session_class.return_value.__enter__.return_value = mock_session
        mock_resume_session_class.return_value.__exit__.return_value = None

        result = handle_validate_command(args)
        assert result == 0

    def test_validate_command_error(self):
        """Test validate command error handling."""
        args = Mock()
        args.name = "test_resume"
        args.data_dir = None

        with patch(
            "simple_resume.core.resume.Resume.read_yaml",
            side_effect=SimpleResumeError("File not found"),
        ):
            result = handle_validate_command(args)
            assert result == 1


class TestMainFunction:
    """Test the main CLI entry point."""

    @patch("simple_resume.cli.create_parser")
    def test_main_generate_command(self, mock_create_parser):
        """Test main with generate command."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_args.command = "generate"
        mock_parser.parse_args.return_value = mock_args
        mock_create_parser.return_value = mock_parser

        with patch(
            "simple_resume.cli.handle_generate_command", return_value=0
        ) as mock_handle:
            result = main()
            assert result == 0
            mock_handle.assert_called_once_with(mock_args)

    @patch("simple_resume.cli.create_parser")
    def test_main_session_command(self, mock_create_parser):
        """Test main with session command."""
        mock_parser = Mock()
        mock_args = Mock()
        mock_args.command = "session"
        mock_parser.parse_args.return_value = mock_args
        mock_create_parser.return_value = mock_parser

        with patch(
            "simple_resume.cli.handle_session_command", return_value=0
        ) as mock_handle:
            result = main()
            assert result == 0
            mock_handle.assert_called_once_with(mock_args)

    @patch("simple_resume.cli.create_parser")
    def test_main_validate_command(self, mock_create_parser, story):
        mock_parser = Mock()
        mock_args = Mock()
        mock_args.command = "validate"
        mock_parser.parse_args.return_value = mock_args
        mock_create_parser.return_value = mock_parser

        with patch(
            "simple_resume.cli.handle_validate_command", return_value=0
        ) as mock_handle:
            result = main()

        story.then("validate handler runs and exit code 0 propagates")
        assert result == 0
        mock_handle.assert_called_once_with(mock_args)

    @patch("simple_resume.cli.create_parser")
    def test_main_unknown_command(self, mock_create_parser, story):
        mock_parser = Mock()
        mock_args = Mock()
        mock_args.command = "unknown"
        mock_parser.parse_args.return_value = mock_args
        mock_create_parser.return_value = mock_parser

        result = main()
        story.then("unknown commands trigger help output and non-zero exit")
        assert result == 1
        mock_parser.print_help.assert_called_once()

    @patch("simple_resume.cli.create_parser")
    def test_main_keyboard_interrupt(self, mock_create_parser, story):
        mock_parser = Mock()
        mock_args = Mock()
        mock_args.command = "generate"
        mock_parser.parse_args.side_effect = KeyboardInterrupt()
        mock_create_parser.return_value = mock_parser

        result = main()
        story.then("the keyboard interrupt maps to exit code 130")
        assert result == 130

    @patch("simple_resume.cli.create_parser")
    def test_main_unexpected_error(self, mock_create_parser, story):
        mock_parser = Mock()
        mock_args = Mock()
        mock_args.command = "generate"
        mock_parser.parse_args.return_value = mock_args
        mock_create_parser.return_value = mock_parser

        with patch(
            "simple_resume.cli.handle_generate_command",
            side_effect=Exception("Unexpected error"),
        ):
            result = main()
        story.then("unexpected errors result in exit code 1")
        assert result == 1


class TestHandleUnexpectedError:
    """Test the new error handling function."""

    @patch("simple_resume.cli.print")
    @patch("simple_resume.cli.logging.getLogger")
    def test_handle_file_system_error(self, mock_logger, mock_print):
        error = PermissionError("Permission denied")
        result = _handle_unexpected_error(error, "test context")

        assert result == 2
        mock_print.assert_any_call("File System Error: Permission denied")
        mock_print.assert_any_call("Suggestion: Check file permissions and disk space")
        mock_logger.return_value.error.assert_called_once()

    @patch("simple_resume.cli.print")
    @patch("simple_resume.cli.logging.getLogger")
    def test_handle_internal_error(self, mock_logger, mock_print):
        error = AttributeError("Missing attribute")
        result = _handle_unexpected_error(error, "test context")

        assert result == 3
        mock_print.assert_any_call("Internal Error: Missing attribute")
        mock_print.assert_any_call("Suggestion: This may be a bug - please report it")
        mock_logger.return_value.error.assert_called_once()

    @patch("simple_resume.cli.print")
    @patch("simple_resume.cli.logging.getLogger")
    def test_handle_memory_error(self, mock_logger, mock_print):
        error = MemoryError("Out of memory")
        result = _handle_unexpected_error(error, "test context")

        assert result == 4
        mock_print.assert_any_call("Resource Error: Out of memory")
        mock_print.assert_any_call("Suggestion: System ran out of memory")
        mock_logger.return_value.error.assert_called_once()

    @patch("simple_resume.cli.print")
    @patch("simple_resume.cli.logging.getLogger")
    def test_handle_input_error(self, mock_logger, mock_print):
        error = ValueError("Invalid value")
        result = _handle_unexpected_error(error, "test context")

        assert result == 5
        mock_print.assert_any_call("Input Error: Invalid value")
        mock_print.assert_any_call("Suggestion: Check your input files and parameters")
        mock_logger.return_value.error.assert_called_once()

    @patch("simple_resume.cli.print")
    @patch("simple_resume.cli.logging.getLogger")
    def test_handle_generic_error(self, mock_logger, mock_print):
        error = RuntimeError("Something went wrong")
        result = _handle_unexpected_error(error, "test context")

        assert result == 1
        mock_print.assert_any_call("Unexpected Error: Something went wrong")
        mock_print.assert_any_call("Suggestion: Check logs for details")
        mock_logger.return_value.error.assert_called_once()


class TestCLIIntegration:
    """Integration-level assertions for CLI documentation."""

    def test_parser_help_message(self, story):
        parser = create_parser()
        help_text = parser.format_help()
        story.then("the help text references all subcommands")
        assert "simple-resume" in help_text
        assert "generate" in help_text
        assert "session" in help_text
        assert "validate" in help_text

    def test_generate_command_examples(self, story):
        parser = create_parser()
        subparsers = getattr(parser, "_subparsers", None)
        assert subparsers is not None
        group_actions = cast(
            list[Any],
            getattr(subparsers, "_group_actions", []),
        )
        assert group_actions, "expected at least one subparser action"
        choices = getattr(group_actions[0], "choices", None)
        assert isinstance(choices, dict) and "generate" in choices
        generate_parser = choices["generate"]

        help_text = generate_parser.format_help()
        story.then("generate help advertises key options")
        assert "--format" in help_text
        assert "--template" in help_text
        assert "--output" in help_text
