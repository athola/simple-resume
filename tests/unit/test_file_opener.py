"""Unit tests for shell.file_opener."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from simple_resume.core.exceptions import FileSystemError
from simple_resume.shell.file_opener import FileOpener, open_file
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


def test_open_file_not_a_file_raises_error(story: Scenario, tmp_path: Path) -> None:
    story.given("a path that exists but is a directory, not a file")
    story.when("attempting to open it")
    directory = tmp_path / "some_dir"
    directory.mkdir()
    with pytest.raises(FileSystemError, match="not a file"):
        FileOpener.open_file(directory, format_type="pdf")


def test_open_file_auto_detects_pdf_format(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    story.given("a PDF file without explicit format_type")
    story.when("opening the file to auto-detect format")
    pdf_file = tmp_path / "auto.pdf"
    pdf_file.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(sys, "platform", "darwin")
    called = {}

    def fake_run(cmd, check, capture_output):  # type: ignore[override]
        called["cmd"] = cmd
        return MagicMock(returncode=0)

    monkeypatch.setattr("simple_resume.shell.file_opener.subprocess.run", fake_run)

    assert FileOpener.open_file(pdf_file) is True
    assert called["cmd"][0] == "/usr/bin/open"


def test_open_file_auto_detects_html_format(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    story.given("an HTML file without explicit format_type")
    story.when("opening the file to auto-detect format")
    html_file = tmp_path / "auto.html"
    html_file.write_text("<html></html>", encoding="utf-8")

    called = SimpleNamespace(args=None)

    def fake_open(url: str, new: int = 0, autoraise: bool = True) -> bool:
        called.args = url
        return True

    monkeypatch.setattr("simple_resume.shell.file_opener.webbrowser.open", fake_open)

    assert FileOpener.open_file(html_file) is True
    assert called.args == html_file.as_uri()


def test_open_file_generic_exception_handling(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    story.given("a file that causes an exception during opening")
    story.when("the subprocess call raises an unexpected exception")
    pdf_file = tmp_path / "error.pdf"
    pdf_file.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(sys, "platform", "darwin")

    def fake_run(cmd, check, capture_output):  # type: ignore[override]
        raise RuntimeError("Unexpected subprocess error")

    monkeypatch.setattr("simple_resume.shell.file_opener.subprocess.run", fake_run)

    with pytest.raises(FileSystemError, match="Failed to open file"):
        FileOpener.open_file(pdf_file, format_type="pdf")


def test_open_pdf_windows(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    story.given("a PDF file on Windows")
    story.when("opening the PDF via Windows cmd")
    pdf_file = tmp_path / "win.pdf"
    pdf_file.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr("simple_resume.shell.file_opener.shutil.which", lambda _: "cmd")

    called = {}

    def fake_run(cmd, check, shell, capture_output):  # type: ignore[override]
        called["cmd"] = cmd
        return MagicMock(returncode=0)

    monkeypatch.setattr("simple_resume.shell.file_opener.subprocess.run", fake_run)

    assert FileOpener.open_file(pdf_file, format_type="pdf") is True
    assert called["cmd"][:3] == ["cmd", "/c", "start"]


def test_open_pdf_linux_fallback_viewers(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    story.given("a PDF file on Linux with xdg-open failing")
    story.when("falling back to evince viewer")
    pdf_file = tmp_path / "fallback.pdf"
    pdf_file.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(sys, "platform", "linux")

    # Mock xdg-open to fail, evince to succeed
    def fake_which(cmd: str) -> str | None:
        if cmd == "xdg-open":
            return "/usr/bin/xdg-open"
        elif cmd == "evince":
            return "/usr/bin/evince"
        return None

    monkeypatch.setattr("simple_resume.shell.file_opener.shutil.which", fake_which)

    call_count = {"count": 0}

    def fake_run(cmd, check, capture_output):  # type: ignore[override]
        call_count["count"] += 1
        if "xdg-open" in cmd[0]:
            return MagicMock(returncode=1)  # xdg-open fails
        else:
            return MagicMock(returncode=0)  # evince succeeds

    monkeypatch.setattr("simple_resume.shell.file_opener.subprocess.run", fake_run)

    assert FileOpener.open_file(pdf_file, format_type="pdf") is True
    assert call_count["count"] == 2  # xdg-open + evince


def test_open_pdf_linux_fallback_exception(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    story.given("a PDF file on Linux with viewers raising exceptions")
    story.when("all viewers fail and return False")
    pdf_file = tmp_path / "fail.pdf"
    pdf_file.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(sys, "platform", "linux")

    def fake_which(cmd: str) -> str | None:
        if cmd in ("xdg-open", "evince", "okular", "acroread"):
            return f"/usr/bin/{cmd}"
        return None

    monkeypatch.setattr("simple_resume.shell.file_opener.shutil.which", fake_which)

    def fake_run(cmd, check, capture_output):  # type: ignore[override]
        if check:
            raise subprocess.CalledProcessError(1, cmd)
        return MagicMock(returncode=1)

    monkeypatch.setattr("simple_resume.shell.file_opener.subprocess.run", fake_run)

    # Should return False when all viewers fail
    assert FileOpener.open_file(pdf_file, format_type="pdf") is False


def test_open_html_macos_fallback(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    story.given("an HTML file on macOS with webbrowser failing")
    story.when("falling back to macOS open command")
    html_file = tmp_path / "mac.html"
    html_file.write_text("<html></html>", encoding="utf-8")

    monkeypatch.setattr(sys, "platform", "darwin")

    def fake_webbrowser_open(url: str, new: int = 0, autoraise: bool = True) -> bool:
        return False  # Webbrowser fails

    monkeypatch.setattr(
        "simple_resume.shell.file_opener.webbrowser.open",
        fake_webbrowser_open,
    )

    called = {}

    def fake_run(cmd, check, capture_output):  # type: ignore[override]
        called["cmd"] = cmd
        return MagicMock(returncode=0)

    monkeypatch.setattr("simple_resume.shell.file_opener.subprocess.run", fake_run)

    assert FileOpener.open_file(html_file, format_type="html") is True
    assert called["cmd"][0] == "/usr/bin/open"


def test_open_html_linux_fallback(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    story.given("an HTML file on Linux with webbrowser failing")
    story.when("falling back to xdg-open")
    html_file = tmp_path / "linux.html"
    html_file.write_text("<html></html>", encoding="utf-8")

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(
        "simple_resume.shell.file_opener.shutil.which",
        lambda _: "/usr/bin/xdg-open",
    )

    def fake_webbrowser_open(url: str, new: int = 0, autoraise: bool = True) -> bool:
        return False  # Webbrowser fails

    monkeypatch.setattr(
        "simple_resume.shell.file_opener.webbrowser.open",
        fake_webbrowser_open,
    )

    called = {}

    def fake_run(cmd, check, capture_output):  # type: ignore[override]
        called["cmd"] = cmd
        return MagicMock(returncode=0)

    monkeypatch.setattr("simple_resume.shell.file_opener.subprocess.run", fake_run)

    assert FileOpener.open_file(html_file, format_type="html") is True
    assert "xdg-open" in called["cmd"][0]


def test_open_html_linux_no_xdg_open(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    story.given("an HTML file on Linux without xdg-open available")
    story.when("attempting to open with fallback")
    html_file = tmp_path / "no_xdg.html"
    html_file.write_text("<html></html>", encoding="utf-8")

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(
        "simple_resume.shell.file_opener.shutil.which",
        lambda _: None,
    )

    def fake_webbrowser_open(url: str, new: int = 0, autoraise: bool = True) -> bool:
        return False  # Webbrowser fails

    monkeypatch.setattr(
        "simple_resume.shell.file_opener.webbrowser.open",
        fake_webbrowser_open,
    )

    # Should return False when no xdg-open is available
    assert FileOpener.open_file(html_file, format_type="html") is False


def test_open_generic_linux_no_xdg_open(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    story.given("a generic file on Linux without xdg-open")
    story.when("attempting to open the file")
    file_path = tmp_path / "no_xdg.txt"
    file_path.write_text("content", encoding="utf-8")

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(
        "simple_resume.shell.file_opener.shutil.which",
        lambda _: None,
    )

    assert FileOpener.open_file(file_path) is False


def test_open_generic_linux_timeout(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    story.given("a generic file on Linux with subprocess timeout")
    story.when("xdg-open times out")
    file_path = tmp_path / "timeout.txt"
    file_path.write_text("content", encoding="utf-8")

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(
        "simple_resume.shell.file_opener.shutil.which",
        lambda _: "/usr/bin/xdg-open",
    )

    def fake_run(cmd, check, capture_output, timeout):  # type: ignore[override]
        raise subprocess.TimeoutExpired(cmd, timeout)

    monkeypatch.setattr("simple_resume.shell.file_opener.subprocess.run", fake_run)

    assert FileOpener.open_file(file_path) is False


def test_module_level_open_file_function(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    story.given("using the module-level open_file function")
    story.when("calling it directly")

    pdf_file = tmp_path / "module.pdf"
    pdf_file.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(sys, "platform", "darwin")

    called = {}

    def fake_run(cmd, check, capture_output):  # type: ignore[override]
        called["cmd"] = cmd
        return MagicMock(returncode=0)

    monkeypatch.setattr("simple_resume.shell.file_opener.subprocess.run", fake_run)

    assert open_file(pdf_file, format_type="pdf") is True
    assert called["cmd"][0] == "/usr/bin/open"


def test_open_html_macos_failure(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    story.given("an HTML file on macOS with subprocess returning non-zero")
    story.when("the open command fails")
    html_file = tmp_path / "fail_mac.html"
    html_file.write_text("<html></html>", encoding="utf-8")

    monkeypatch.setattr(sys, "platform", "darwin")

    def fake_webbrowser_open(url: str, new: int = 0, autoraise: bool = True) -> bool:
        return False

    monkeypatch.setattr(
        "simple_resume.shell.file_opener.webbrowser.open",
        fake_webbrowser_open,
    )

    def fake_run(cmd, check, capture_output):  # type: ignore[override]
        return MagicMock(returncode=1)

    monkeypatch.setattr("simple_resume.shell.file_opener.subprocess.run", fake_run)

    assert FileOpener.open_file(html_file, format_type="html") is False


def test_open_html_windows_fallback(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    story.given("an HTML file on Windows with webbrowser failing")
    story.when("falling back to Windows cmd start")
    html_file = tmp_path / "win.html"
    html_file.write_text("<html></html>", encoding="utf-8")

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(
        "simple_resume.shell.file_opener.shutil.which",
        lambda _: "cmd",
    )

    def fake_webbrowser_open(url: str, new: int = 0, autoraise: bool = True) -> bool:
        raise Exception("Webbrowser failed")

    monkeypatch.setattr(
        "simple_resume.shell.file_opener.webbrowser.open",
        fake_webbrowser_open,
    )

    called = {}

    def fake_run(cmd, check, shell, capture_output):  # type: ignore[override]
        called["cmd"] = cmd
        return MagicMock(returncode=0)

    monkeypatch.setattr("simple_resume.shell.file_opener.subprocess.run", fake_run)

    assert FileOpener.open_file(html_file, format_type="html") is True
    assert called["cmd"][:3] == ["cmd", "/c", "start"]
