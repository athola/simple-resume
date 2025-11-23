"""Test CLI palette utilities."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from simple_resume.shell.cli.palette import (
    build_parser,
    cmd_list,
    cmd_snapshot,
    main,
    palette_list,
    snapshot,
)


class TestBuildParser:
    """Test argument parser construction."""

    def test_build_parser_creates_subparsers(self) -> None:
        """Test that parser has required subcommands."""
        parser = build_parser()

        assert parser.description == "Palette utilities"

        # Test parsing with snapshot command
        args = parser.parse_args(["snapshot"])
        assert args.command == "snapshot"
        assert callable(args.func)

        # Test parsing with list command
        args = parser.parse_args(["list"])
        assert args.command == "list"
        assert callable(args.func)

    def test_build_parser_snapshot_with_output(self) -> None:
        """Test snapshot command with output file argument."""
        parser = build_parser()
        args = parser.parse_args(["snapshot", "-o", "output.json"])
        assert args.command == "snapshot"
        assert args.output.name == "output.json"


class TestCmdSnapshot:
    """Test snapshot command functionality."""

    @patch("simple_resume.shell.cli.palette.build_palettable_snapshot")
    def test_cmd_snapshot_writes_to_stdout(
        self, mock_build_snapshot: MagicMock
    ) -> None:
        """Test snapshot command writes to stdout by default."""
        mock_build_snapshot.return_value = {"test": "data"}

        args = argparse.Namespace(output=None)
        result = cmd_snapshot(args)

        assert result == 0
        mock_build_snapshot.assert_called_once()

    @patch("simple_resume.shell.cli.palette.build_palettable_snapshot")
    def test_cmd_snapshot_writes_to_file(self, mock_build_snapshot: MagicMock) -> None:
        """Test snapshot command writes to specified output file."""
        mock_build_snapshot.return_value = {"palettes": ["test1", "test2"]}

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            with temp_path.open("w") as output_file:
                args = argparse.Namespace(output=output_file)
                result = cmd_snapshot(args)

            assert result == 0
            mock_build_snapshot.assert_called_once()

            # Verify file content
            content = temp_path.read_text(encoding="utf-8")
            data = json.loads(content)
            assert data == {"palettes": ["test1", "test2"]}
        finally:
            temp_path.unlink(missing_ok=True)


class TestCmdList:
    """Test list command functionality."""

    @patch("simple_resume.shell.cli.palette.get_palette_registry")
    def test_cmd_list_outputs_palette_names(self, mock_get_registry: MagicMock) -> None:
        """Test list command outputs palette names and swatches."""
        # Mock palette objects
        mock_palette1 = MagicMock()
        mock_palette1.name = "ocean"
        mock_palette1.swatches = [
            "#001122",
            "#003344",
            "#005566",
            "#007788",
            "#0099AA",
            "#00BBCC",
        ]

        mock_palette2 = MagicMock()
        mock_palette2.name = "sunset"
        mock_palette2.swatches = [
            "#CC1100",
            "#AA3300",
            "#885500",
            "#667700",
            "#449900",
            "#22BB00",
        ]

        mock_registry = MagicMock()
        mock_registry.list.return_value = [mock_palette1, mock_palette2]
        mock_get_registry.return_value = mock_registry

        args = argparse.Namespace()
        result = cmd_list(args)

        assert result == 0
        mock_get_registry.assert_called_once()
        mock_registry.list.assert_called_once()


class TestMain:
    """Test main CLI entry point."""

    @patch("simple_resume.shell.cli.palette.build_parser")
    def test_main_dispatches_snapshot_command(
        self, mock_build_parser: MagicMock
    ) -> None:
        """Test main function dispatches to snapshot command."""
        mock_args = argparse.Namespace(command="snapshot", func=MagicMock())
        mock_args.func.return_value = 0
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = mock_args
        mock_build_parser.return_value = mock_parser

        result = main(["snapshot"])

        assert result == 0
        mock_parser.parse_args.assert_called_once_with(["snapshot"])
        mock_args.func.assert_called_once_with(mock_args)

    @patch("simple_resume.shell.cli.palette.build_parser")
    def test_main_dispatches_list_command(self, mock_build_parser: MagicMock) -> None:
        """Test main function dispatches to list command."""
        mock_args = argparse.Namespace(command="list", func=MagicMock())
        mock_args.func.return_value = 0
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = mock_args
        mock_build_parser.return_value = mock_parser

        result = main(["list"])

        assert result == 0
        mock_parser.parse_args.assert_called_once_with(["list"])
        mock_args.func.assert_called_once_with(mock_args)

    @patch("simple_resume.shell.cli.palette.build_parser")
    def test_main_returns_int_result(self, mock_build_parser: MagicMock) -> None:
        """Test main function returns integer result."""
        mock_args = argparse.Namespace(command="snapshot", func=MagicMock())
        mock_args.func.return_value = 1
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = mock_args
        mock_build_parser.return_value = mock_parser

        result = main(["snapshot"])

        assert result == 1

    @patch("simple_resume.shell.cli.palette.build_parser")
    def test_main_handles_none_result(self, mock_build_parser: MagicMock) -> None:
        """Test main function handles None result from command."""
        mock_args = argparse.Namespace(command="list", func=MagicMock())
        mock_args.func.return_value = None
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = mock_args
        mock_build_parser.return_value = mock_parser

        result = main(["list"])

        assert result == 0


class TestEntryPoints:
    """Test entry point functions."""

    @patch("simple_resume.shell.cli.palette.main")
    def test_snapshot_entry_point(self, mock_main: MagicMock) -> None:
        """Test snapshot entry point calls main with correct args."""
        mock_main.return_value = 0

        with patch("sys.exit") as mock_exit:
            snapshot()
            mock_main.assert_called_once_with(["snapshot"])
            mock_exit.assert_called_once_with(0)

    @patch("simple_resume.shell.cli.palette.main")
    def test_palette_list_entry_point(self, mock_main: MagicMock) -> None:
        """Test palette_list entry point calls main with correct args."""
        mock_main.return_value = 0

        with patch("sys.exit") as mock_exit:
            palette_list()
            mock_main.assert_called_once_with(["list"])
            mock_exit.assert_called_once_with(0)
