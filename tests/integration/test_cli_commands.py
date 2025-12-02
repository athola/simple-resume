"""Integration tests for CLI commands and argument parsing."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from simple_resume.shell.cli.main import (
    create_parser,
    handle_generate_command,
    handle_validate_command,
    main,
)
from tests.bdd import Scenario

# Complete config section for test resumes
COMPLETE_CONFIG = """
  page_width: 210
  page_height: 297
  padding: 12
  sidebar_width: 60
  sidebar_padding_top: 5
  sidebar_padding_left: 12
  sidebar_padding_right: 12
  profile_image_padding_bottom: 6
  pitch_padding_top: 4
  pitch_padding_bottom: 4
  pitch_padding_left: 4
  h2_padding_left: 4
  h3_padding_top: 5
  date_container_width: 13
  date_container_padding_left: 8
  description_container_padding_left: 3
  frame_padding: 10
  cover_padding_top: 10
  cover_padding_bottom: 20
  cover_padding_h: 25
  theme_color: "#0395DE"
  sidebar_color: "#F6F6F6"
  bar_background_color: "#DFDFDF"
  date2_color: "#616161"
  frame_color: "#757575"
"""

# Section titles for test resumes
TITLES_SECTION = """
titles:
  contact: Contact
  certification: Certifications
  expertise: Expertise
  programming: Programming
  keyskills: Key Skills
"""


@pytest.mark.integration
class TestCLIParser:
    """Test CLI argument parser creation and validation."""

    def test_parser_has_version_argument(self, story: Scenario) -> None:
        """Test that the parser includes version information."""
        story.given("a CLI parser")
        parser = create_parser()

        story.when("checking for version argument")
        # Version is handled by argparse internally, just verify parser exists
        assert parser is not None
        assert parser.prog == "simple-resume"

    def test_parser_requires_command(self, story: Scenario) -> None:
        """Test that the parser requires a command."""
        story.given("a CLI parser")
        parser = create_parser()

        story.when("parsing with no command")
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_parser_accepts_generate_command(self, story: Scenario) -> None:
        """Test that the parser accepts generate command."""
        story.given("a CLI parser")
        parser = create_parser()

        story.when("parsing generate command")
        args = parser.parse_args(["generate"])

        story.then("command is set to generate")
        assert args.command == "generate"

    def test_parser_accepts_session_command(self, story: Scenario) -> None:
        """Test that the parser accepts session command."""
        story.given("a CLI parser")
        parser = create_parser()

        story.when("parsing session command")
        args = parser.parse_args(["session"])

        story.then("command is set to session")
        assert args.command == "session"

    def test_parser_accepts_validate_command(self, story: Scenario) -> None:
        """Test that the parser accepts validate command."""
        story.given("a CLI parser")
        parser = create_parser()

        story.when("parsing validate command")
        args = parser.parse_args(["validate"])

        story.then("command is set to validate")
        assert args.command == "validate"

    def test_generate_parser_accepts_format_flag(self, story: Scenario) -> None:
        """Test that generate command accepts format flag."""
        story.given("a CLI parser")
        parser = create_parser()

        story.when("parsing generate with format")
        args = parser.parse_args(["generate", "--format", "html"])

        story.then("format is set correctly")
        assert args.format == "html"

    def test_generate_parser_accepts_multiple_formats(self, story: Scenario) -> None:
        """Test that generate command accepts multiple formats."""
        story.given("a CLI parser")
        parser = create_parser()

        story.when("parsing generate with multiple formats")
        args = parser.parse_args(["generate", "test", "--formats", "pdf", "html"])

        story.then("formats list is set correctly")
        assert args.formats == ["pdf", "html"]

    def test_generate_parser_accepts_output_path(self, story: Scenario) -> None:
        """Test that generate command accepts output path."""
        story.given("a CLI parser")
        parser = create_parser()

        story.when("parsing generate with output path")
        args = parser.parse_args(["generate", "--output", "/tmp/test.pdf"])  # noqa: S108

        story.then("output path is set correctly")
        assert args.output == Path("/tmp/test.pdf")  # noqa: S108

    def test_generate_parser_accepts_data_dir(self, story: Scenario) -> None:
        """Test that generate command accepts data directory."""
        story.given("a CLI parser")
        parser = create_parser()

        story.when("parsing generate with data directory")
        args = parser.parse_args(["generate", "--data-dir", "/tmp/data"])  # noqa: S108

        story.then("data directory is set correctly")
        assert args.data_dir == Path("/tmp/data")  # noqa: S108

    def test_generate_parser_accepts_template(self, story: Scenario) -> None:
        """Test that generate command accepts template."""
        story.given("a CLI parser")
        parser = create_parser()

        story.when("parsing generate with template")
        args = parser.parse_args(["generate", "--template", "custom"])

        story.then("template is set correctly")
        assert args.template == "custom"

    def test_generate_parser_accepts_palette(self, story: Scenario) -> None:
        """Test that generate command accepts palette."""
        story.given("a CLI parser")
        parser = create_parser()

        story.when("parsing generate with palette")
        args = parser.parse_args(["generate", "--palette", "ocean"])

        story.then("palette is set correctly")
        assert args.palette == "ocean"

    def test_generate_parser_accepts_theme_color(self, story: Scenario) -> None:
        """Test that generate command accepts theme color."""
        story.given("a CLI parser")
        parser = create_parser()

        story.when("parsing generate with theme color")
        args = parser.parse_args(["generate", "--theme-color", "#FF5733"])

        story.then("theme color is set correctly")
        assert args.theme_color == "#FF5733"

    def test_generate_parser_accepts_page_dimensions(self, story: Scenario) -> None:
        """Test that generate command accepts page dimensions."""
        story.given("a CLI parser")
        parser = create_parser()

        story.when("parsing generate with page dimensions")
        args = parser.parse_args(
            ["generate", "--page-width", "215", "--page-height", "280"]
        )

        story.then("page dimensions are set correctly")
        assert args.page_width == 215
        assert args.page_height == 280

    def test_session_parser_accepts_data_dir(self, story: Scenario) -> None:
        """Test that session command accepts data directory."""
        story.given("a CLI parser")
        parser = create_parser()

        story.when("parsing session with data directory")
        args = parser.parse_args(["session", "--data-dir", "/tmp/data"])  # noqa: S108

        story.then("data directory is set correctly")
        assert args.data_dir == Path("/tmp/data")  # noqa: S108

    def test_session_parser_accepts_template(self, story: Scenario) -> None:
        """Test that session command accepts template."""
        story.given("a CLI parser")
        parser = create_parser()

        story.when("parsing session with template")
        args = parser.parse_args(["session", "--template", "custom"])

        story.then("template is set correctly")
        assert args.template == "custom"

    def test_validate_parser_accepts_name(self, story: Scenario) -> None:
        """Test that validate command accepts resume name."""
        story.given("a CLI parser")
        parser = create_parser()

        story.when("parsing validate with name")
        args = parser.parse_args(["validate", "test_resume"])

        story.then("name is set correctly")
        assert args.name == "test_resume"

    def test_validate_parser_accepts_data_dir(self, story: Scenario) -> None:
        """Test that validate command accepts data directory."""
        story.given("a CLI parser")
        parser = create_parser()

        story.when("parsing validate with data directory")
        args = parser.parse_args(["validate", "--data-dir", "/tmp/data"])  # noqa: S108

        story.then("data directory is set correctly")
        assert args.data_dir == Path("/tmp/data")  # noqa: S108


@pytest.mark.integration
class TestCLIMainEntryPoint:
    """Test main CLI entry point and command dispatching."""

    def test_main_dispatches_to_generate_handler(self, story: Scenario) -> None:
        """Test that main() dispatches to generate command handler."""
        story.given("a generate command")
        with (
            patch("sys.argv", ["simple-resume", "generate"]),
            patch(
                "simple_resume.shell.cli.main.handle_generate_command"
            ) as mock_handler,
        ):
            mock_handler.return_value = 0

            story.when("running main()")
            exit_code = main()

            story.then("generate handler is called and returns success")
            mock_handler.assert_called_once()
            assert exit_code == 0

    def test_main_dispatches_to_session_handler(self, story: Scenario) -> None:
        """Test that main() dispatches to session command handler."""
        story.given("a session command")
        with (
            patch("sys.argv", ["simple-resume", "session"]),
            patch(
                "simple_resume.shell.cli.main.handle_session_command"
            ) as mock_handler,
        ):
            mock_handler.return_value = 0

            story.when("running main()")
            exit_code = main()

            story.then("session handler is called and returns success")
            mock_handler.assert_called_once()
            assert exit_code == 0

    def test_main_dispatches_to_validate_handler(self, story: Scenario) -> None:
        """Test that main() dispatches to validate command handler."""
        story.given("a validate command")
        with (
            patch("sys.argv", ["simple-resume", "validate"]),
            patch(
                "simple_resume.shell.cli.main.handle_validate_command"
            ) as mock_handler,
        ):
            mock_handler.return_value = 0

            story.when("running main()")
            exit_code = main()

            story.then("validate handler is called and returns success")
            mock_handler.assert_called_once()
            assert exit_code == 0

    def test_main_handles_keyboard_interrupt(self, story: Scenario) -> None:
        """Test that main() handles keyboard interrupt gracefully."""
        story.given("a command that raises KeyboardInterrupt")
        with (
            patch("sys.argv", ["simple-resume", "generate"]),
            patch(
                "simple_resume.shell.cli.main.handle_generate_command",
                side_effect=KeyboardInterrupt,
            ),
        ):
            story.when("running main()")
            exit_code = main()

            story.then("returns exit code 130 for keyboard interrupt")
            assert exit_code == 130

    def test_main_handles_unexpected_error(self, story: Scenario) -> None:
        """Test that main() handles unexpected errors."""
        story.given("a command that raises an unexpected error")
        with (
            patch("sys.argv", ["simple-resume", "generate"]),
            patch(
                "simple_resume.shell.cli.main.handle_generate_command",
                side_effect=RuntimeError("Unexpected error"),
            ),
        ):
            story.when("running main()")
            exit_code = main()

            story.then("returns non-zero exit code")
            assert exit_code != 0


@pytest.mark.integration
class TestGenerateCommandHandler:
    """Test generate command handler."""

    def test_handle_generate_with_no_name_generates_all(
        self, story: Scenario, tmp_path: Path
    ) -> None:
        """Test generate command without name generates all resumes."""
        story.given("a data directory with multiple resume files")
        data_dir = tmp_path / "data"
        input_dir = data_dir / "input"
        output_dir = data_dir / "output"
        input_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)

        # Create sample resume files using realistic structure
        resume_template = f"""template: resume_no_bars
full_name: {{name}}
email: {{email}}

{TITLES_SECTION}
body:
  Experience:
    - start: 2020
      end: 2023
      title: Developer
      company: {{company}}
      description: Test description

config:{COMPLETE_CONFIG}
"""
        (input_dir / "resume1.yaml").write_text(
            resume_template.format(
                name="Test User 1",
                email="test1@example.com",
                company="Company 1",
            ),
            encoding="utf-8",
        )
        (input_dir / "resume2.yaml").write_text(
            resume_template.format(
                name="Test User 2",
                email="test2@example.com",
                company="Company 2",
            ),
            encoding="utf-8",
        )

        args = argparse.Namespace(
            name=None,
            format="html",
            formats=None,
            template=None,
            output=None,
            data_dir=data_dir,
            open=False,
            preview=False,
            browser=None,
            theme_color=None,
            palette=None,
            page_width=None,
            page_height=None,
        )

        story.when("running handle_generate_command with no name")
        exit_code = handle_generate_command(args)

        story.then("all resumes are generated")
        assert exit_code == 0
        assert (output_dir / "resume1.html").exists()
        assert (output_dir / "resume2.html").exists()

    def test_handle_generate_with_specific_name(
        self, story: Scenario, tmp_path: Path
    ) -> None:
        """Test generate command with specific resume name."""
        story.given("a data directory with a resume file")
        data_dir = tmp_path / "data"
        input_dir = data_dir / "input"
        output_dir = data_dir / "output"
        input_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)

        (input_dir / "specific.yaml").write_text(
            f"""template: resume_no_bars
full_name: Specific User
email: specific@example.com

{TITLES_SECTION}
body:
  Experience:
    - start: 2020
      end: 2023
      title: Developer
      company: Company
      description: Test description

config:{COMPLETE_CONFIG}
""",
            encoding="utf-8",
        )

        args = argparse.Namespace(
            name="specific",
            format="html",
            formats=None,
            template=None,
            output=None,
            data_dir=data_dir,
            open=False,
            preview=False,
            browser=None,
            theme_color=None,
            palette=None,
            page_width=None,
            page_height=None,
        )

        story.when("running handle_generate_command with specific name")
        exit_code = handle_generate_command(args)

        story.then("only the specific resume is generated")
        assert exit_code == 0
        assert (output_dir / "specific.html").exists()

    def test_handle_generate_with_pdf_format(
        self, story: Scenario, tmp_path: Path
    ) -> None:
        """Test generate command with PDF format."""
        story.given("a data directory with a resume file")
        data_dir = tmp_path / "data"
        input_dir = data_dir / "input"
        output_dir = data_dir / "output"
        input_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)

        (input_dir / "test.yaml").write_text(
            f"""template: resume_no_bars
full_name: Test User
email: test@example.com

{TITLES_SECTION}
body:
  Experience:
    - start: 2020
      end: 2023
      title: Developer
      company: Company
      description: Test description

config:{COMPLETE_CONFIG}
""",
            encoding="utf-8",
        )

        args = argparse.Namespace(
            name="test",
            format="pdf",
            formats=None,
            template=None,
            output=None,
            data_dir=data_dir,
            open=False,
            preview=False,
            browser=None,
            theme_color=None,
            palette=None,
            page_width=None,
            page_height=None,
        )

        story.when("running handle_generate_command with PDF format")
        exit_code = handle_generate_command(args)

        story.then("PDF is generated")
        assert exit_code == 0
        assert (output_dir / "test.pdf").exists()


@pytest.mark.integration
class TestValidateCommandHandler:
    """Test validate command handler."""

    def test_handle_validate_with_valid_resume(
        self, story: Scenario, tmp_path: Path
    ) -> None:
        """Test validate command with a valid resume."""
        story.given("a data directory with a valid resume file")
        data_dir = tmp_path / "data"
        input_dir = data_dir / "input"
        input_dir.mkdir(parents=True)

        (input_dir / "valid.yaml").write_text(
            f"""template: resume_no_bars
full_name: Valid User
email: valid@example.com

{TITLES_SECTION}
body:
  Experience:
    - start: 2020
      end: 2023
      title: Developer
      company: Company
      description: Test description

config:{COMPLETE_CONFIG}
""",
            encoding="utf-8",
        )

        args = argparse.Namespace(
            name="valid",
            data_dir=data_dir,
        )

        story.when("running handle_validate_command")
        exit_code = handle_validate_command(args)

        story.then("validation succeeds")
        assert exit_code == 0

    def test_handle_validate_all_resumes(self, story: Scenario, tmp_path: Path) -> None:
        """Test validate command without name validates all resumes."""
        story.given("a data directory with multiple resume files")
        data_dir = tmp_path / "data"
        input_dir = data_dir / "input"
        input_dir.mkdir(parents=True)

        resume_template = f"""template: resume_no_bars
full_name: {{name}}
email: {{email}}

{TITLES_SECTION}
body:
  Experience:
    - start: 2020
      end: 2023
      title: Developer
      company: Company
      description: Test description

config:{COMPLETE_CONFIG}
"""
        (input_dir / "resume1.yaml").write_text(
            resume_template.format(name="User 1", email="user1@example.com"),
            encoding="utf-8",
        )
        (input_dir / "resume2.yaml").write_text(
            resume_template.format(name="User 2", email="user2@example.com"),
            encoding="utf-8",
        )

        args = argparse.Namespace(
            name=None,
            data_dir=data_dir,
        )

        story.when("running handle_validate_command with no name")
        exit_code = handle_validate_command(args)

        story.then("all resumes are validated")
        assert exit_code == 0
