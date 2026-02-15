"""Unit tests for CLI validation commands and helpers."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from simple_resume.core.exceptions import ValidationError
from simple_resume.shell.cli import main as cli
from tests.bdd import Scenario


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
