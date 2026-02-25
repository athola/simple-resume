"""Unit tests for CLI LinkedIn import subcommand."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from simple_resume.shell.cli._import import handle_import_command
from tests.bdd import Scenario


class TestHandleImportCommand:
    """Feature: LinkedIn profile import CLI command.

    As a job seeker
    I want to import my LinkedIn profile from a file
    So that I get a simple-resume YAML file automatically
    """

    @pytest.mark.unit
    def test_import_text_profile(self, tmp_path: Path, story: Scenario) -> None:
        """Import a plain-text LinkedIn profile."""
        story.given("a text file with LinkedIn profile data")

        profile_file = tmp_path / "profile.txt"
        profile_file.write_text(
            "Jane Doe\n"
            "Software Engineer\n"
            "San Francisco, CA\n"
            "About\n"
            "Experienced developer.\n"
            "Skills\n"
            "Python, JavaScript\n"
        )

        args = argparse.Namespace(
            command="import",
            linkedin=str(profile_file),
            output=None,
        )

        story.when("the import command is run")
        result = handle_import_command(args)

        story.then("exit code is 0 and YAML file is created")
        assert result == 0

        yaml_output = tmp_path / "profile.yaml"
        assert yaml_output.exists()
        content = yaml_output.read_text()
        assert "Jane Doe" in content

    @pytest.mark.unit
    def test_import_with_explicit_output(self, tmp_path: Path, story: Scenario) -> None:
        """Import with an explicit output path."""
        story.given("a LinkedIn text file and a custom output path")

        profile_file = tmp_path / "profile.txt"
        profile_file.write_text("Alice Smith\nDesigner\nNew York\n")

        output_file = tmp_path / "subdir" / "resume.yaml"

        args = argparse.Namespace(
            command="import",
            linkedin=str(profile_file),
            output=output_file,
        )

        story.when("the import command is run with --output")
        result = handle_import_command(args)

        story.then("the YAML is written to the custom path")
        assert result == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "Alice Smith" in content

    @pytest.mark.unit
    def test_import_missing_file(self, tmp_path: Path, story: Scenario) -> None:
        """Import a nonexistent file returns exit code 1."""
        story.given("a nonexistent file path")

        args = argparse.Namespace(
            command="import",
            linkedin=str(tmp_path / "nonexistent.txt"),
            output=None,
        )

        story.when("the import command is run")
        result = handle_import_command(args)

        story.then("exit code is 1")
        assert result == 1

    @pytest.mark.unit
    def test_import_unsupported_format(self, tmp_path: Path, story: Scenario) -> None:
        """Import a file with unsupported format returns exit code 1."""
        story.given("a PDF file (unsupported format)")

        pdf_file = tmp_path / "profile.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")

        args = argparse.Namespace(
            command="import",
            linkedin=str(pdf_file),
            output=None,
        )

        story.when("the import command is run")
        result = handle_import_command(args)

        story.then("exit code is 1")
        assert result == 1

    @pytest.mark.unit
    def test_import_empty_profile(self, tmp_path: Path, story: Scenario) -> None:
        """Import an empty file returns exit code 1."""
        story.given("an empty text file")

        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")

        args = argparse.Namespace(
            command="import",
            linkedin=str(empty_file),
            output=None,
        )

        story.when("the import command is run")
        result = handle_import_command(args)

        story.then("exit code is 1")
        assert result == 1
