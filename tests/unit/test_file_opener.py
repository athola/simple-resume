"""Unit tests for shell.file_opener."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from simple_resume.core.exceptions import FileSystemError
from simple_resume.shell.file_opener import FileOpener
from tests.bdd import Scenario


def test_open_file_missing_path_raises_filesystemerror(
    story: Scenario, tmp_path: Path
) -> None:
    story.given("a file path that does not exist on disk")
    story.when("attempting to open the missing file")
    missing = tmp_path / "nope.pdf"
    with pytest.raises(FileSystemError, match="doesn't exist"):
        FileOpener.open_file(missing, format_type="pdf")


def test_validate_path_blocks_injection(story: Scenario, tmp_path: Path) -> None:
    story.given("a path containing a semicolon injection attempt")
    story.when("validating the path before opening")
    # Semicolon should be rejected as unsafe
    with pytest.raises(ValueError, match="Unsafe path"):
        FileOpener._validate_path(Path("bad;rm"))


def test_open_html_uses_webbrowser(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    story.given("a local HTML file on disk")
    story.when("opening it through the FileOpener")
    html_file = tmp_path / "page.html"
    html_file.write_text("<html></html>", encoding="utf-8")

    called = SimpleNamespace(args=None)

    def fake_open(url: str, new: int = 0, autoraise: bool = True) -> bool:
        called.args = url
        return True

    monkeypatch.setattr("simple_resume.shell.file_opener.webbrowser.open", fake_open)

    assert FileOpener.open_file(html_file, format_type="html") is True
    assert called.args == html_file.as_uri()


def test_open_pdf_linux_runs_subprocess(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    story.given("a PDF file on a Linux platform with an available opener")
    story.when("FileOpener dispatches to the platform handler")
    pdf_file = tmp_path / "report.pdf"
    pdf_file.write_bytes(b"%PDF-1.4")

    # Force linux branch and a dummy opener
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(
        "simple_resume.shell.file_opener.shutil.which", lambda _: "/usr/bin/echo"
    )

    called = {}

    def fake_run(cmd, check, capture_output):  # type: ignore[override]
        called["cmd"] = cmd
        return MagicMock(returncode=0)

    monkeypatch.setattr("simple_resume.shell.file_opener.subprocess.run", fake_run)

    assert FileOpener.open_file(pdf_file, format_type="pdf") is True
    assert called["cmd"][0].endswith("echo")


def test_open_generic_falls_back_to_xdg(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    story.given("a non-PDF/HTML file on Linux")
    story.when("opening the file without a specific handler")
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("hi", encoding="utf-8")

    monkeypatch.setattr(
        "simple_resume.shell.file_opener.shutil.which", lambda _: "/usr/bin/echo"
    )
    captured: dict[str, list[str]] = {}

    def fake_run(cmd, check, capture_output=None, timeout=None):  # type: ignore[override]
        captured["cmd"] = cmd
        return MagicMock(returncode=0)

    monkeypatch.setattr("simple_resume.shell.file_opener.subprocess.run", fake_run)

    assert FileOpener.open_file(txt_file) is True
    assert captured["cmd"][0].endswith("echo")


def test_open_pdf_macos(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    story.given("a PDF file on macOS")
    story.when("FileOpener invokes the system open command")
    pdf_file = tmp_path / "mac.pdf"
    pdf_file.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr(sys, "platform", "darwin")

    called = {}

    def fake_run(cmd, check, capture_output):  # type: ignore[override]
        called["cmd"] = cmd
        return MagicMock(returncode=0)

    monkeypatch.setattr("simple_resume.shell.file_opener.subprocess.run", fake_run)

    assert FileOpener.open_file(pdf_file, format_type="pdf") is True
    assert called["cmd"][0] == "/usr/bin/open"


def test_open_html_windows(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    story.given("an HTML file on Windows")
    story.when("FileOpener uses the cmd start fallback")
    html_file = tmp_path / "page.html"
    html_file.write_text("<html></html>", encoding="utf-8")

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr("simple_resume.shell.file_opener.shutil.which", lambda _: "cmd")

    called = {}

    def fake_run(cmd, check, shell, capture_output):  # type: ignore[override]
        called["cmd"] = cmd
        return MagicMock(returncode=0)

    monkeypatch.setattr("simple_resume.shell.file_opener.subprocess.run", fake_run)

    assert FileOpener.open_file(html_file, format_type="html") is True
    assert called["cmd"][:3] == ["cmd", "/c", "start"]


def test_open_generic_macos(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    story.given("a generic file path on macOS")
    story.when("opening the file via FileOpener")
    file_path = tmp_path / "generic.txt"
    file_path.write_text("ok", encoding="utf-8")
    monkeypatch.setattr(sys, "platform", "darwin")

    called = {}

    def fake_run(cmd, check, capture_output):  # type: ignore[override]
        called["cmd"] = cmd
        return MagicMock(returncode=0)

    monkeypatch.setattr("simple_resume.shell.file_opener.subprocess.run", fake_run)

    assert FileOpener.open_file(file_path) is True
    assert called["cmd"][0] == "/usr/bin/open"


def test_open_generic_windows(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    story.given("a generic file path on Windows")
    story.when("opening the file via FileOpener")
    file_path = tmp_path / "generic.txt"
    file_path.write_text("ok", encoding="utf-8")
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr("simple_resume.shell.file_opener.shutil.which", lambda _: "cmd")

    called = {}

    def fake_run(cmd, check, shell, capture_output):  # type: ignore[override]
        called["cmd"] = cmd
        return MagicMock(returncode=0)

    monkeypatch.setattr("simple_resume.shell.file_opener.subprocess.run", fake_run)

    assert FileOpener.open_file(file_path) is True
    assert called["cmd"][:3] == ["cmd", "/c", "start"]
