"""Unit tests for shell.cli.main helpers."""

from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from simple_resume.core.constants import OutputFormat
from simple_resume.core.exceptions import ValidationError
from simple_resume.core.generate.exceptions import GenerationError
from simple_resume.core.result import BatchGenerationResult, GenerationResult
from simple_resume.shell.cli import main as cli
from simple_resume.shell.session.manage import ResumeSession
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
    # One LaTeX-specific GenerationError and one generic error should
    # produce exit code 1
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


class _DummySession:
    def __init__(self) -> None:
        self.closed = False
        self.paths = SimpleNamespace(input=Path("tmp/in"), output=Path("tmp/out"))
        self.config = SimpleNamespace(
            default_template=None,
            preview_mode=False,
            auto_open=False,
            session_metadata={"overrides": {}},
            default_format=OutputFormat.PDF,
        )

    def __enter__(self) -> _DummySession:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.closed = True

    def resume(self, name: str) -> SimpleNamespace:
        return SimpleNamespace(
            with_template=lambda tpl: SimpleNamespace(),  # not used further
        )

    def _find_yaml_files(self):
        return [Path("a.yaml"), Path("b.yml")]


def test_session_list_resumes_prints(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    story.given("a session exposes multiple resume YAML files")
    story.when("listing resumes via the CLI helper")
    session = cast(ResumeSession, _DummySession())
    cli._session_list_resumes(session)
    out = capsys.readouterr().out
    assert "a" in out and "b" in out


def test_session_generate_command_invokes_generation(
    story: Scenario,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    story.given("session generation is requested for a resume name")
    story.when("the CLI delegates to build and run helpers")
    invoked = {}

    def fake_run(resume, session, commands):
        invoked["called"] = (resume, session, commands)

    monkeypatch.setattr(cli, "_run_session_generation", fake_run)
    monkeypatch.setattr(cli, "build_generation_plan", lambda _: ["cmd"])
    session = cast(ResumeSession, _DummySession())
    cli._session_generate_resume(session, "john")
    assert invoked["called"][2] == ["cmd"]


def test_handle_session_command_exits_on_exit(
    story: Scenario, monkeypatch: pytest.MonkeyPatch
) -> None:
    story.given("a user interacts with an interactive session")
    story.when("the user enters exit after some commands")
    inputs = iter(["list", "generate demo", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    dummy_session = _DummySession()
    monkeypatch.setattr(cli, "_session_generate_resume", lambda *a, **k: None)
    monkeypatch.setattr(cli, "_session_list_resumes", lambda *a, **k: None)
    monkeypatch.setattr(cli, "ResumeSession", lambda *a, **k: dummy_session)

    result = cli.handle_session_command(
        argparse.Namespace(data_dir=None, template=None, preview=False)
    )
    assert result == 0
    assert dummy_session.closed is True
