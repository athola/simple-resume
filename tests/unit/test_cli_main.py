"""Unit tests for shell.cli.main helpers."""

from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from simple_resume.core.ats import ScorerResult, TournamentResult
from simple_resume.core.constants import OutputFormat
from simple_resume.core.exceptions import ValidationError
from simple_resume.core.generate.exceptions import GenerationError
from simple_resume.core.generate.plan import CommandType, GenerationCommand
from simple_resume.core.models import GenerationConfig
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


# ============================================================================
# Additional tests for improved coverage
# ============================================================================


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


def test_log_validation_result_valid_with_warnings(
    story: Scenario, capsys: pytest.CaptureFixture
) -> None:
    story.given("validation result with warnings")
    story.when("logging validation result")

    validation = SimpleNamespace(is_valid=True, warnings=["Warning 1", "Warning 2"])
    result = cli._log_validation_result("test", validation)
    captured = capsys.readouterr()

    assert result is True
    assert "Warning - test: Warning 1" in captured.out
    assert "Warning - test: Warning 2" in captured.out


def test_log_validation_result_valid_no_warnings(
    story: Scenario, capsys: pytest.CaptureFixture
) -> None:
    story.given("validation result without warnings")
    story.when("logging validation result")

    validation = SimpleNamespace(is_valid=True, warnings=[])
    result = cli._log_validation_result("test", validation)
    captured = capsys.readouterr()

    assert result is True
    assert "test is valid" in captured.out


def test_log_validation_result_invalid(
    story: Scenario, capsys: pytest.CaptureFixture
) -> None:
    story.given("invalid validation result")
    story.when("logging validation result")

    validation = SimpleNamespace(is_valid=False, errors=["Error 1", "Error 2"])
    result = cli._log_validation_result("test", validation)
    captured = capsys.readouterr()

    assert result is False
    assert "Error - test:" in captured.out


def test_normalize_warnings_empty(story: Scenario) -> None:
    story.given("empty or None warnings")
    story.when("normalizing warnings")

    assert cli._normalize_warnings(None) == []
    assert cli._normalize_warnings([]) == []
    assert cli._normalize_warnings("") == []


def test_normalize_warnings_list(story: Scenario) -> None:
    story.given("list of warnings")
    story.when("normalizing warnings")

    result = cli._normalize_warnings(["warn1", "warn2"])
    assert result == ["warn1", "warn2"]


def test_normalize_warnings_single_string(story: Scenario) -> None:
    story.given("single string warning")
    story.when("normalizing warnings")

    result = cli._normalize_warnings("single warning")
    assert result == ["single warning"]


def test_normalize_errors_list(story: Scenario) -> None:
    story.given("list of errors")
    story.when("normalizing errors")

    result = cli._normalize_errors(["err1", "err2"], ["default"])
    assert result == ["err1", "err2"]


def test_normalize_errors_single(story: Scenario) -> None:
    story.given("single error")
    story.when("normalizing errors")

    result = cli._normalize_errors("single error", ["default"])
    assert result == ["single error"]


def test_normalize_errors_empty_returns_empty(story: Scenario) -> None:
    story.given("empty errors")
    story.when("normalizing errors")

    # Actual behavior: empty list returns empty, not the default
    result = cli._normalize_errors([], ["default error"])
    assert result == []


def test_validate_single_resume_cli_with_errors(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    story.given("resume validation raises ValidationError")
    story.when("validating single resume via CLI")

    class MockResume:
        @staticmethod
        def read_yaml(name, paths=None):
            return MockResume()

        def validate_or_raise(self):
            raise ValidationError("Invalid resume", errors=["error1", "error2"])

    monkeypatch.setattr(cli, "Resume", MockResume)

    exit_code = cli._validate_single_resume_cli("test", None)
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error - test:" in captured.out


def test_validate_single_resume_cli_with_warnings(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    story.given("resume validation succeeds with warnings")
    story.when("validating single resume via CLI")

    class MockResume:
        @staticmethod
        def read_yaml(name, paths=None):
            return MockResume()

        def validate_or_raise(self):
            return SimpleNamespace(warnings=["warning1"])

    monkeypatch.setattr(cli, "Resume", MockResume)

    exit_code = cli._validate_single_resume_cli("test", None)
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Warning - test: warning1" in captured.out


def test_validate_single_resume_cli_success(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    story.given("resume validation succeeds without warnings")
    story.when("validating single resume via CLI")

    class MockResume:
        @staticmethod
        def read_yaml(name, paths=None):
            return MockResume()

        def validate_or_raise(self):
            return SimpleNamespace(warnings=[])

    monkeypatch.setattr(cli, "Resume", MockResume)

    exit_code = cli._validate_single_resume_cli("test", None)
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "test is valid" in captured.out


def test_validate_all_resumes_cli_empty(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    story.given("no resume files found")
    story.when("validating all resumes")

    class EmptySession:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def _find_yaml_files(self):
            return []

    monkeypatch.setattr(cli, "ResumeSession", lambda *a, **k: EmptySession())

    exit_code = cli._validate_all_resumes_cli(None)
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "No resumes found to validate" in captured.out


def test_validate_all_resumes_cli_with_errors(
    story: Scenario,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    story.given("resume validation has errors")
    story.when("validating all resumes")

    class SessionWithErrors:
        def __enter__(self):
            return self

        def __exit__(self, *args):  # noqa: ARG002
            pass

        def _find_yaml_files(self):
            return [Path("test.yaml")]

        def resume(self, name):  # noqa: ARG002
            class MockResume:
                def validate_or_raise(self):
                    raise ValidationError("Invalid", errors=["error1"])

            return MockResume()

    monkeypatch.setattr(
        cli, "ResumeSession", lambda *_args, **_kwargs: SessionWithErrors()
    )

    exit_code = cli._validate_all_resumes_cli(None)
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error - test:" in captured.out


def test_validate_all_resumes_cli_with_warnings(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    story.given("resume validation has warnings")
    story.when("validating all resumes")

    class SessionWithWarnings:
        def __enter__(self):
            return self

        def __exit__(self, *args):  # noqa: ARG002
            pass

        def _find_yaml_files(self):
            return [Path("test.yaml")]

        def resume(self, name):  # noqa: ARG002
            class MockResume:
                def validate_or_raise(self):
                    return SimpleNamespace(warnings=["warning1"])

            return MockResume()

    monkeypatch.setattr(
        cli, "ResumeSession", lambda *_args, **_kwargs: SessionWithWarnings()
    )

    exit_code = cli._validate_all_resumes_cli(None)
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Warning - test: warning1" in captured.out


# ============================================================================
# Tests for _read_file_text helper (issue #67)
# ============================================================================


def test_read_file_text_pdf_raises_validation_error(
    tmp_path: Path, story: Scenario
) -> None:
    """Test that PDF files raise a user-friendly ValidationError."""
    story.given("a PDF file path")
    story.when("attempting to read it as job description text")

    pdf_file = tmp_path / "job.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 fake pdf content")

    with pytest.raises(ValidationError) as exc_info:
        cli._read_file_text(pdf_file)

    story.then("a ValidationError with helpful guidance is raised")
    assert ".pdf" in str(exc_info.value)
    assert "not yet supported" in str(exc_info.value)
    assert exc_info.value.errors is not None
    assert any("Supported formats" in e for e in exc_info.value.errors)


def test_read_file_text_html_raises_validation_error(
    tmp_path: Path, story: Scenario
) -> None:
    """Test that HTML files raise a user-friendly ValidationError."""
    story.given("an HTML file path")
    story.when("attempting to read it as job description text")

    html_file = tmp_path / "job.html"
    html_file.write_text("<html><body>Job posting</body></html>")

    with pytest.raises(ValidationError) as exc_info:
        cli._read_file_text(html_file)

    story.then("a ValidationError with helpful guidance is raised")
    assert ".html" in str(exc_info.value)
    assert "not yet supported" in str(exc_info.value)


def test_read_file_text_htm_raises_validation_error(
    tmp_path: Path, story: Scenario
) -> None:
    """Test that .htm files also raise a ValidationError."""
    story.given("a .htm file path")
    story.when("attempting to read it")

    htm_file = tmp_path / "job.htm"
    htm_file.write_text("<html><body>Job posting</body></html>")

    with pytest.raises(ValidationError) as exc_info:
        cli._read_file_text(htm_file)

    story.then("a ValidationError is raised")
    assert ".htm" in str(exc_info.value)


def test_read_file_text_txt_works(tmp_path: Path, story: Scenario) -> None:
    """Test that plain text files are read successfully."""
    story.given("a plain text job description file")
    story.when("reading it")

    txt_file = tmp_path / "job.txt"
    txt_file.write_text("Looking for a Python developer")

    content = cli._read_file_text(txt_file)

    story.then("the content is returned")
    assert content == "Looking for a Python developer"


def test_read_file_text_missing_file_raises_fnf(
    tmp_path: Path, story: Scenario
) -> None:
    """Test that missing files raise FileNotFoundError."""
    story.given("a non-existent file path")
    story.when("attempting to read it")

    missing = tmp_path / "nonexistent.txt"

    with pytest.raises(FileNotFoundError):
        cli._read_file_text(missing)

    story.then("FileNotFoundError is raised")


# ============================================================================
# Tests for _collect_ats_warnings and error surfacing (issue #58)
# ============================================================================


def test_collect_ats_warnings_empty_result(story: Scenario) -> None:
    """Test that no warnings are collected from clean results."""
    story.given("a TournamentResult with no errors")
    result = TournamentResult(
        overall_score=0.75,
        algorithm_results=[],
        component_breakdown={},
        metadata={},
    )

    story.when("collecting warnings")
    warnings = cli._collect_ats_warnings(result)

    story.then("an empty list is returned")
    assert warnings == []


def test_collect_ats_warnings_from_algorithm_details(story: Scenario) -> None:
    """Test that warnings are collected from ScorerResult details."""
    story.given("a TournamentResult with error in algorithm details")
    scorer_result = ScorerResult(
        name="tfidf_cosine",
        score=0.5,
        weight=1.0,
        details={"error": "Fell back to permissive settings"},
    )
    result = TournamentResult(
        overall_score=0.5,
        algorithm_results=[scorer_result],
        metadata={},
    )

    story.when("collecting warnings")
    warnings = cli._collect_ats_warnings(result)

    story.then("the error is included in warnings")
    assert len(warnings) == 1
    assert "tfidf_cosine" in warnings[0]
    assert "Fell back" in warnings[0]


def test_collect_ats_warnings_from_metadata(story: Scenario) -> None:
    """Test that tournament-level errors are collected."""
    story.given("a TournamentResult with error in metadata")
    result = TournamentResult(
        overall_score=0.0,
        algorithm_results=[],
        metadata={"error": "All scorers failed"},
    )

    story.when("collecting warnings")
    warnings = cli._collect_ats_warnings(result)

    story.then("the tournament error is included")
    assert len(warnings) == 1
    assert "Tournament" in warnings[0]
    assert "All scorers failed" in warnings[0]


def test_format_text_report_includes_warnings(story: Scenario) -> None:
    """Test that _format_text_report includes WARNINGS section."""
    story.given("a TournamentResult with warnings")
    scorer_result = ScorerResult(
        name="test_scorer",
        score=0.5,
        weight=1.0,
        details={"error": "Test warning message"},
    )
    result = TournamentResult(
        overall_score=0.5,
        algorithm_results=[scorer_result],
        metadata={},
    )

    story.when("formatting the text report")
    report = cli._format_text_report(result, verbose=False)

    story.then("WARNINGS section is included")
    assert "WARNINGS" in report
    assert "Test warning message" in report


def test_format_text_report_includes_failed_scorers(story: Scenario) -> None:
    """Test that _format_text_report includes FAILED SCORERS section."""
    story.given("a TournamentResult with failed scorers")
    result = TournamentResult(
        overall_score=0.5,
        algorithm_results=[],
        failed_scorers=[("FailingScorer", "RuntimeError: Test failure")],
        metadata={},
    )

    story.when("formatting the text report")
    report = cli._format_text_report(result, verbose=False)

    story.then("FAILED SCORERS section is included")
    assert "FAILED SCORERS" in report
    assert "FailingScorer" in report
    assert "use --verbose" in report


def test_format_text_report_verbose_shows_error_details(story: Scenario) -> None:
    """Test that verbose mode shows full error details."""
    story.given("a TournamentResult with failed scorers")
    result = TournamentResult(
        overall_score=0.5,
        algorithm_results=[],
        failed_scorers=[("FailingScorer", "RuntimeError: Detailed error message")],
        metadata={},
    )

    story.when("formatting the text report in verbose mode")
    report = cli._format_text_report(result, verbose=True)

    story.then("full error message is shown")
    assert "FAILED SCORERS" in report
    assert "RuntimeError: Detailed error message" in report
