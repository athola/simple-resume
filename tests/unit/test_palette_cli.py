"""Test cases for palette CLI functionality."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from simple_resume.cli.palette import build_parser, cmd_list, cmd_snapshot, main
from tests.bdd import Scenario


class TestCmdSnapshot:
    """Test the snapshot command functionality."""

    def test_cmd_snapshot_prints_to_stdout(self, story: Scenario) -> None:
        args = argparse.Namespace(output=None)

        with patch(
            "simple_resume.cli.palette.build_palettable_registry_snapshot"
        ) as mock_snapshot:
            mock_snapshot.return_value = {"test": "data"}

            with patch("builtins.print") as mock_print:
                story.when("cmd_snapshot executes without an output file")
                result = cmd_snapshot(args)

        story.then("a JSON payload is printed and success code returned")
        mock_snapshot.assert_called_once()
        mock_print.assert_called_once()
        printed_data = json.loads(mock_print.call_args[0][0])
        assert printed_data == {"test": "data"}
        assert result == 0

    def test_cmd_snapshot_writes_to_file(self, story: Scenario, tmp_path: Path) -> None:
        output_file = tmp_path / "snapshot.json"
        # Use argparse.FileType to create a real file object
        with output_file.open("w", encoding="utf-8") as file_obj:
            args = argparse.Namespace(output=file_obj)

            with patch(
                "simple_resume.cli.palette.build_palettable_registry_snapshot"
            ) as mock_snapshot:
                mock_snapshot.return_value = {"palettes": ["red", "blue", "green"]}

                story.when("cmd_snapshot writes to a file handle")
                result = cmd_snapshot(args)

        story.then("the file contains the JSON payload and success is returned")
        mock_snapshot.assert_called_once()
        assert result == 0

        # Check file content
        content = output_file.read_text(encoding="utf-8")
        data = json.loads(content.strip())
        assert data == {"palettes": ["red", "blue", "green"]}

    def test_cmd_snapshot_calls_build_function(self, story: Scenario) -> None:
        args = argparse.Namespace(output=None)

        with patch(
            "simple_resume.cli.palette.build_palettable_registry_snapshot"
        ) as mock_snapshot:
            mock_snapshot.return_value = {}

            story.when("cmd_snapshot executes")
            cmd_snapshot(args)

        story.then("the snapshot builder is invoked exactly once")
        mock_snapshot.assert_called_once()


class TestCmdList:
    """Test the list command functionality."""

    def test_cmd_list_prints_palettes(self, story: Scenario) -> None:
        args = argparse.Namespace()

        # Mock palette registry
        mock_palette1 = Mock()
        mock_palette1.name = "Red Sunset"
        mock_palette1.swatches = [
            "#FF0000",
            "#CC0000",
            "#990000",
            "#660000",
            "#330000",
            "#000000",
        ]

        mock_palette2 = Mock()
        mock_palette2.name = "Ocean Blue"
        mock_palette2.swatches = [
            "#0000FF",
            "#0000CC",
            "#000099",
            "#000066",
            "#000033",
            "#000000",
        ]

        with patch("simple_resume.cli.palette.get_palette_registry") as mock_registry:
            mock_registry.return_value.list.return_value = [
                mock_palette1,
                mock_palette2,
            ]

            with patch("builtins.print") as mock_print:
                story.when("cmd_list renders the registry contents")
                result = cmd_list(args)

        story.then("each palette is printed with up to six swatches")
        assert mock_print.call_count == 2
        calls = [call[0][0] for call in mock_print.call_args_list]
        assert (
            "Red Sunset: #FF0000, #CC0000, #990000, #660000, #330000, #000000" in calls
        )
        assert (
            "Ocean Blue: #0000FF, #0000CC, #000099, #000066, #000033, #000000" in calls
        )
        assert result == 0

    def test_cmd_list_handles_empty_registry(self, story: Scenario) -> None:
        args = argparse.Namespace()

        with patch("simple_resume.cli.palette.get_palette_registry") as mock_registry:
            mock_registry.return_value.list.return_value = []

            with patch("builtins.print") as mock_print:
                story.when("cmd_list executes with no palettes")
                result = cmd_list(args)

        story.then("nothing is printed and the exit code is zero")
        mock_print.assert_not_called()
        assert result == 0

    def test_cmd_list_limits_swatches_display(self, story: Scenario) -> None:
        args = argparse.Namespace()

        mock_palette = Mock()
        mock_palette.name = "Rainbow"
        mock_palette.swatches = [
            "#FF0000",
            "#FF7F00",
            "#FFFF00",
            "#00FF00",
            "#0000FF",
            "#4B0082",
            "#9400D3",
        ]

        with patch("simple_resume.cli.palette.get_palette_registry") as mock_registry:
            mock_registry.return_value.list.return_value = [mock_palette]

            with patch("builtins.print") as mock_print:
                story.when("cmd_list prints a palette with more than six swatches")
                cmd_list(args)

        story.then("only the first six swatches are displayed")
        printed_line = mock_print.call_args[0][0]
        assert printed_line.count("#") == 6
        assert "#9400D3" not in printed_line


class TestBuildParser:
    """Test argument parser construction."""

    def test_build_parser_creates_subparsers(self, story: Scenario) -> None:
        parser = build_parser()

        story.then("the parser has a description and subcommands")
        assert parser.description == "Palette utilities"
        assert parser._subparsers is not None

    def test_build_parser_has_snapshot_command(self, story: Scenario) -> None:
        parser = build_parser()

        # Test parsing snapshot command
        args = parser.parse_args(["snapshot"])
        story.then("snapshot subcommand configures default writer")
        assert args.command == "snapshot"
        assert args.output is None
        assert callable(args.func)

    def test_build_parser_snapshot_with_output(
        self,
        story: Scenario,
        tmp_path: Path,
    ) -> None:
        parser = build_parser()
        tmp_file = tmp_path / "test.json"

        args = parser.parse_args(["snapshot", "-o", str(tmp_file)])
        assert args.command == "snapshot"
        # argparse.FileType returns file object with full path in .name
        story.then("the output FileType points at the requested path")
        assert args.output.name == str(tmp_file)

    def test_build_parser_has_list_command(self, story: Scenario) -> None:
        parser = build_parser()

        args = parser.parse_args(["list"])
        story.then("list subcommand registers a callable handler")
        assert args.command == "list"
        assert callable(args.func)

    def test_build_parser_requires_command(self, story: Scenario) -> None:
        parser = build_parser()

        with pytest.raises(SystemExit):
            parser.parse_args([])
        story.then("running without subcommand exits with SystemExit")


class TestMainFunction:
    """Test the main CLI entry point."""

    def test_main_calls_correct_command_function(self, story: Scenario) -> None:
        with patch("simple_resume.cli.palette.build_parser") as mock_build_parser:
            mock_parser = Mock()
            mock_parser.parse_args.return_value = Mock(func=Mock(return_value=42))
            mock_build_parser.return_value = mock_parser

            story.when("main is invoked with 'list'")
            result = main(["list"])

        story.then(
            "the parser is built and the command handler return value is propagated"
        )
        mock_build_parser.assert_called_once_with()
        mock_parser.parse_args.assert_called_once_with(["list"])
        mock_parser.parse_args.return_value.func.assert_called_once()
        assert result == 42

    def test_main_uses_default_argv(self, story: Scenario) -> None:
        with patch("simple_resume.cli.palette.build_parser") as mock_build_parser:
            mock_parser = Mock()
            mock_parser.parse_args.return_value = Mock(func=Mock(return_value=0))
            mock_build_parser.return_value = mock_parser

            story.when("main executes without custom argv")
            main()

            # build_parser takes no arguments
            mock_build_parser.assert_called_once_with()
            # parse_args gets None when main() called with no args
            mock_parser.parse_args.assert_called_once_with(None)

    def test_main_handles_custom_argv(self) -> None:
        """Main function handles custom argv list."""
        with patch("simple_resume.cli.palette.build_parser") as mock_build_parser:
            mock_parser = Mock()
            mock_parser.parse_args.return_value = Mock(func=Mock(return_value=0))
            mock_build_parser.return_value = mock_parser

            main(["snapshot"])

            # build_parser takes no arguments
            mock_build_parser.assert_called_once_with()
            # parse_args gets the argv
            mock_parser.parse_args.assert_called_once_with(["snapshot"])

    def test_main_propagates_function_return_value(self) -> None:
        """Main function returns the same value as the command function."""
        with patch("simple_resume.cli.palette.build_parser") as mock_build_parser:
            mock_parser = Mock()
            mock_parser.parse_args.return_value = Mock(func=Mock(return_value=123))
            mock_build_parser.return_value = mock_parser

            result = main(["list"])
            assert result == 123


class TestIntegrationScenarios:
    """Integration tests for CLI functionality."""

    def test_snapshot_integration_with_real_function(self) -> None:
        """Integration test for snapshot command with real build function."""
        parser = build_parser()
        args = parser.parse_args(["snapshot"])

        # This should not raise an exception
        with patch("builtins.print"):  # Suppress actual output
            result = cmd_snapshot(args)
            assert result == 0
            # The snapshot function should have been called and printed valid JSON

    def test_list_integration_with_real_function(self) -> None:
        """Integration test for list command with real registry."""
        parser = build_parser()
        args = parser.parse_args(["list"])

        with patch("builtins.print"):  # Suppress actual output
            result = cmd_list(args)
            assert result == 0
            # The registry should have been accessed and palettes listed

    def test_end_to_end_main_with_list(self) -> None:
        """End-to-end test for main function with list command."""
        with patch("builtins.print"):  # Suppress output
            result = main(["list"])
            assert result == 0

    def test_end_to_end_main_with_snapshot(self) -> None:
        """End-to-end test for main function with snapshot command."""
        with patch("builtins.print"):  # Suppress output
            result = main(["snapshot"])
            assert result == 0
