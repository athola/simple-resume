"""Unit tests for CLI command handling - main entry, generate, format coercion."""

from __future__ import annotations

import argparse
from types import SimpleNamespace
from typing import cast

import pytest

from simple_resume.core.constants import OutputFormat
from simple_resume.core.exceptions import ValidationError
from simple_resume.core.generate.exceptions import GenerationError
from simple_resume.core.result import BatchGenerationResult, GenerationResult
from simple_resume.shell.cli import main as cli
from tests.bdd import Scenario


def test_coerce_output_format_invalid_value(story: Scenario) -> None:
    story.given("an unsupported CLI output format string")
    story.when("coercing it to OutputFormat")
    with pytest.raises(ValidationError):
        cli._coerce_output_format("docx")


def test_resolve_cli_formats_defaults_to_format(story: Scenario) -> None:
    story.given("formats argument omitted but format provided")
    story.when("resolving CLI formats")
    args = argparse.Namespace(formats=None, format="html")
    assert cli._resolve_cli_formats(args) == [OutputFormat.HTML]


def test_summarize_batch_result_handles_latex_and_other_errors(
    story: Scenario, capsys: pytest.CaptureFixture
) -> None:
    story.given("a batch result containing a LaTeX error and another error")
    story.when("summarizing the batch result for PDF output")
    latex_error = GenerationError("LaTeX failure", format_type=OutputFormat.PDF)
    other_error = RuntimeError("boom")
    batch = BatchGenerationResult(
        successful=0,
        failed=2,
        errors={"latex": latex_error, "other": other_error},
    )

    exit_code = cli._summarize_batch_result(batch, OutputFormat.PDF)

    captured = capsys.readouterr()
    assert "Skipped LaTeX" in captured.out
    assert "other" in captured.out
    assert exit_code == 1


def test_summarize_batch_result_single_success(story: Scenario) -> None:
    story.given("a successful single-format generation result")
    story.when("summarizing the batch result")
    dummy = cast(GenerationResult, SimpleNamespace(exists=True))
    exit_code = cli._summarize_batch_result(dummy, OutputFormat.HTML)
    assert exit_code == 0


def test_handle_unexpected_error_classifies_oserror(
    story: Scenario, capsys: pytest.CaptureFixture
) -> None:
    story.given("an unexpected PermissionError occurs during generation")
    story.when("the error handler classifies the exception")
    code = cli._handle_unexpected_error(PermissionError("denied"), "generation")
    captured = capsys.readouterr()
    assert "File System Error" in captured.out
    assert code == 2


def test_main_keyboard_interrupt_during_parse(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    story.given("KeyboardInterrupt occurs during argument parsing")
    story.when("main() is called")

    def raise_keyboard_interrupt():
        raise KeyboardInterrupt()

    parser = cli.create_parser()
    monkeypatch.setattr(parser, "parse_args", raise_keyboard_interrupt)
    monkeypatch.setattr(cli, "create_parser", lambda: parser)
    monkeypatch.setattr(cli, "register_default_services", lambda: None)

    exit_code = cli.main()
    captured = capsys.readouterr()

    assert "Operation cancelled by user" in captured.out
    assert exit_code == 130


def test_main_unknown_command(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    story.given("an unknown command is provided")
    story.when("main() handles the command")

    args = argparse.Namespace(command="unknown")
    parser = cli.create_parser()
    monkeypatch.setattr(parser, "parse_args", lambda: args)
    monkeypatch.setattr(cli, "create_parser", lambda: parser)
    monkeypatch.setattr(cli, "register_default_services", lambda: None)

    exit_code = cli.main()
    captured = capsys.readouterr()

    assert "Unknown command" in captured.out
    assert exit_code == 1


def test_handle_generate_command_keyboard_interrupt(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    story.given("KeyboardInterrupt occurs during generation planning")
    story.when("handle_generate_command processes the interruption")

    def raise_keyboard_interrupt(*args, **kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(cli, "_resolve_cli_formats", raise_keyboard_interrupt)
    args = argparse.Namespace(name="test")

    exit_code = cli.handle_generate_command(args)
    captured = capsys.readouterr()

    assert "Operation cancelled by user" in captured.out
    assert exit_code == 130


def test_handle_generate_command_simple_resume_error(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    story.given("SimpleResumeError occurs during generation")
    story.when("handle_generate_command processes the error")

    def raise_simple_resume_error(*args, **kwargs):
        raise ValidationError("Invalid data")

    monkeypatch.setattr(cli, "_resolve_cli_formats", raise_simple_resume_error)
    args = argparse.Namespace(name="test")

    exit_code = cli.handle_generate_command(args)
    captured = capsys.readouterr()

    assert "Error: Invalid data" in captured.out
    assert exit_code == 1


def test_handle_validate_command_simple_resume_error(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    story.given("SimpleResumeError occurs during validation")
    story.when("validate command processes the error")

    def raise_error(*args, **kwargs):
        raise ValidationError("Validation failed")

    monkeypatch.setattr(cli, "_validate_single_resume_cli", raise_error)

    result = cli.handle_validate_command(argparse.Namespace(name="test"))
    captured = capsys.readouterr()

    assert "Validation error:" in captured.out
    assert result == 1
