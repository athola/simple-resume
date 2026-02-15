"""Unit tests for CLI interactive session management."""

from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from simple_resume.core.constants import OutputFormat
from simple_resume.core.exceptions import ValidationError
from simple_resume.core.generate.plan import CommandType, GenerationCommand
from simple_resume.core.models import GenerationConfig
from simple_resume.shell.cli import main as cli
from simple_resume.shell.session.manage import ResumeSession
from tests.bdd import Scenario


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
            with_template=lambda tpl: SimpleNamespace(),
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


def test_handle_session_command_eof(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    story.given("EOF occurs in interactive session")
    story.when("session reads user input")

    def raise_eof(*args):
        raise EOFError()

    monkeypatch.setattr("builtins.input", raise_eof)
    dummy_session = _DummySession()
    monkeypatch.setattr(cli, "ResumeSession", lambda *a, **k: dummy_session)

    result = cli.handle_session_command(
        argparse.Namespace(data_dir=None, template=None, preview=False)
    )

    assert result == 0


def test_handle_session_command_empty_input(
    story: Scenario, monkeypatch: pytest.MonkeyPatch
) -> None:
    story.given("empty input lines in interactive session")
    story.when("session processes empty commands")

    inputs = iter(["", "   ", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    dummy_session = _DummySession()
    monkeypatch.setattr(cli, "ResumeSession", lambda *a, **k: dummy_session)

    result = cli.handle_session_command(
        argparse.Namespace(data_dir=None, template=None, preview=False)
    )

    assert result == 0


def test_handle_session_command_help(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    story.given("help command in interactive session")
    story.when("user requests help")

    inputs = iter(["help", "?", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    dummy_session = _DummySession()
    monkeypatch.setattr(cli, "ResumeSession", lambda *a, **k: dummy_session)

    result = cli.handle_session_command(
        argparse.Namespace(data_dir=None, template=None, preview=False)
    )
    captured = capsys.readouterr()

    assert "Available commands:" in captured.out
    assert result == 0


def test_handle_session_command_generate_incomplete(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    story.given("generate command without resume name")
    story.when("session processes incomplete generate command")

    inputs = iter(["generate", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    dummy_session = _DummySession()
    monkeypatch.setattr(cli, "ResumeSession", lambda *a, **k: dummy_session)

    result = cli.handle_session_command(
        argparse.Namespace(data_dir=None, template=None, preview=False)
    )
    captured = capsys.readouterr()

    assert "Usage: generate <resume_name>" in captured.out
    assert result == 0


def test_handle_session_command_unknown_command(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    story.given("unknown command in interactive session")
    story.when("session processes unknown command")

    inputs = iter(["unknown_cmd", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    dummy_session = _DummySession()
    monkeypatch.setattr(cli, "ResumeSession", lambda *a, **k: dummy_session)

    result = cli.handle_session_command(
        argparse.Namespace(data_dir=None, template=None, preview=False)
    )
    captured = capsys.readouterr()

    assert "Unknown command: unknown_cmd" in captured.out
    assert result == 0


def test_handle_session_command_keyboard_interrupt(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    story.given("KeyboardInterrupt occurs in session")
    story.when("session processes interruption")

    def raise_keyboard_interrupt(*args):
        raise KeyboardInterrupt()

    monkeypatch.setattr("builtins.input", raise_keyboard_interrupt)
    dummy_session = _DummySession()
    monkeypatch.setattr(cli, "ResumeSession", lambda *a, **k: dummy_session)

    result = cli.handle_session_command(
        argparse.Namespace(data_dir=None, template=None, preview=False)
    )
    captured = capsys.readouterr()

    assert "Session cancelled by user" in captured.out
    assert result == 130


def test_handle_session_command_simple_resume_error(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    story.given("SimpleResumeError occurs in session")
    story.when("session processes the error")

    class ErrorSession:
        def __enter__(self):
            raise ValidationError("Session error")

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(cli, "ResumeSession", lambda *a, **k: ErrorSession())

    result = cli.handle_session_command(
        argparse.Namespace(data_dir=None, template=None, preview=False)
    )
    captured = capsys.readouterr()

    assert "Session error:" in captured.out
    assert result == 1


def test_session_generate_resume_key_error(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    story.given("resume does not exist in session")
    story.when("trying to generate missing resume")

    class SessionWithKeyError:
        def resume(self, name):
            raise KeyError(f"Resume {name} not found")

    session = cast(ResumeSession, SessionWithKeyError())
    cli._session_generate_resume(session, "missing")
    captured = capsys.readouterr()

    assert "Resume not found: missing" in captured.out


def test_session_generate_resume_with_template(
    story: Scenario, monkeypatch: pytest.MonkeyPatch
) -> None:
    story.given("session generation with default template")
    story.when("template is applied to resume")

    class TemplatedResume:
        def with_template(self, tpl):
            self.template = tpl
            return self

    class SessionWithTemplate:
        config = SimpleNamespace(
            default_format=OutputFormat.PDF,
            preview_mode=False,
            auto_open=False,
            default_template=None,
            session_metadata={},
        )
        paths = SimpleNamespace(input=Path("tmp/in"), output=Path("tmp/out"))

        def resume(self, name):
            return TemplatedResume()

    invoked = {}

    def fake_run(resume, session, commands):
        invoked["resume"] = resume

    monkeypatch.setattr(cli, "_run_session_generation", fake_run)
    monkeypatch.setattr(cli, "build_generation_plan", lambda _: ["cmd"])
    session = cast(ResumeSession, SessionWithTemplate())

    cli._session_generate_resume(session, "test", default_template="modern")

    assert invoked["resume"].template == "modern"


def test_session_list_resumes_empty(
    story: Scenario, capsys: pytest.CaptureFixture
) -> None:
    story.given("session has no resume files")
    story.when("listing resumes")

    class EmptySession:
        def _find_yaml_files(self):
            return []

    session = cast(ResumeSession, EmptySession())
    cli._session_list_resumes(session)
    captured = capsys.readouterr()

    assert "No resumes found" in captured.out


def test_iter_yaml_files_fallback(story: Scenario, tmp_path: Path) -> None:
    story.given("session without _find_yaml_files method")
    story.when("iterating YAML files with fallback")

    (tmp_path / "test.yaml").touch()
    (tmp_path / "other.yml").touch()

    class FallbackSession:
        paths = SimpleNamespace(input=tmp_path)

    session = cast(ResumeSession, FallbackSession())
    files = list(cli._iter_yaml_files(session))

    assert len(files) == 2
    assert any(f.name == "test.yaml" for f in files)
    assert any(f.name == "other.yml" for f in files)


def test_print_session_help(story: Scenario, capsys: pytest.CaptureFixture) -> None:
    story.given("user requests help in session")
    story.when("printing session help")

    cli._print_session_help()
    captured = capsys.readouterr()

    assert "generate <name>" in captured.out
    assert "list" in captured.out
    assert "help" in captured.out
    assert "exit" in captured.out


def test_run_session_generation_unsupported_command_type(
    story: Scenario, capsys: pytest.CaptureFixture
) -> None:
    story.given("non-single command type in session")
    story.when("running session generation")

    resume = SimpleNamespace(_name="test")
    session = SimpleNamespace(
        paths=SimpleNamespace(output=Path("tmp/out")),
    )
    command = GenerationCommand(
        kind=CommandType.BATCH_SINGLE,
        format=OutputFormat.PDF,
        config=GenerationConfig(),
        overrides={},
    )

    cli._run_session_generation(cast(Any, resume), cast(Any, session), [command])
    captured = capsys.readouterr()

    assert "Session generate only supports single-resume commands" in captured.out


def test_run_session_generation_pdf_success(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    story.given("PDF generation in session")
    story.when("running session generation for PDF")

    resume = SimpleNamespace(_name="test")
    session = SimpleNamespace(
        paths=SimpleNamespace(output=Path("tmp/out")),
    )
    command = GenerationCommand(
        kind=CommandType.SINGLE,
        format=OutputFormat.PDF,
        config=GenerationConfig(output_path=None, open_after=False),
        overrides={},
    )

    result = SimpleNamespace(exists=True, output_path="test.pdf")
    monkeypatch.setattr(cli, "to_pdf", lambda *a, **k: result)

    cli._run_session_generation(cast(Any, resume), cast(Any, session), [command])
    captured = capsys.readouterr()

    assert "PDF generated: test.pdf" in captured.out


def test_run_session_generation_html_success(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    story.given("HTML generation in session")
    story.when("running session generation for HTML")

    resume = SimpleNamespace(_name="test")
    session = SimpleNamespace(
        paths=SimpleNamespace(output=Path("tmp/out")),
    )
    command = GenerationCommand(
        kind=CommandType.SINGLE,
        format=OutputFormat.HTML,
        config=GenerationConfig(output_path=None, open_after=False, browser=None),
        overrides={},
    )

    result = SimpleNamespace(exists=True, output_path="test.html")
    monkeypatch.setattr(cli, "to_html", lambda *a, **k: result)

    cli._run_session_generation(cast(Any, resume), cast(Any, session), [command])
    captured = capsys.readouterr()

    assert "HTML generated: test.html" in captured.out


def test_run_session_generation_unsupported_format(
    story: Scenario, capsys: pytest.CaptureFixture
) -> None:
    story.given("unsupported format in session generation")
    story.when("running session generation")

    resume = SimpleNamespace(_name="test")
    session = SimpleNamespace(
        paths=SimpleNamespace(output=Path("tmp/out")),
    )

    class UnsupportedFormat:
        value = "DOCX"

    command = GenerationCommand(
        kind=CommandType.SINGLE,
        format=cast(Any, UnsupportedFormat()),
        config=GenerationConfig(output_path=None),
        overrides={},
    )

    cli._run_session_generation(cast(Any, resume), cast(Any, session), [command])
    captured = capsys.readouterr()

    assert "Unsupported format" in captured.out


def test_run_session_generation_error(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    story.given("error during session generation")
    story.when("generation fails with SimpleResumeError")

    def raise_error(*args, **kwargs):
        raise ValidationError("Generation failed")

    resume = SimpleNamespace(_name="test")
    session = SimpleNamespace(
        paths=SimpleNamespace(output=Path("tmp/out")),
    )
    command = GenerationCommand(
        kind=CommandType.SINGLE,
        format=OutputFormat.PDF,
        config=GenerationConfig(output_path=None, open_after=False),
        overrides={},
    )

    monkeypatch.setattr(cli, "to_pdf", raise_error)

    cli._run_session_generation(cast(Any, resume), cast(Any, session), [command])
    captured = capsys.readouterr()

    assert "Generation error for test" in captured.out


def test_run_session_generation_failure(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    story.given("generation produces non-existent result")
    story.when("result.exists is False")

    resume = SimpleNamespace(_name="test")
    session = SimpleNamespace(
        paths=SimpleNamespace(output=Path("tmp/out")),
    )
    command = GenerationCommand(
        kind=CommandType.SINGLE,
        format=OutputFormat.PDF,
        config=GenerationConfig(output_path=None, open_after=False),
        overrides={},
    )

    result = SimpleNamespace(exists=False)
    monkeypatch.setattr(cli, "to_pdf", lambda *a, **k: result)

    cli._run_session_generation(cast(Any, resume), cast(Any, session), [command])
    captured = capsys.readouterr()

    assert "Failed to generate PDF" in captured.out
