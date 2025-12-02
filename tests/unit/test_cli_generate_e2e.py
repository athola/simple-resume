"""End-to-end-ish CLI generate path tests (patched to avoid I/O)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from simple_resume.core.constants import OutputFormat
from simple_resume.shell.cli import main as cli_main
from tests.bdd import Scenario


def test_cli_main_generate_invokes_execute(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    story.given("CLI is invoked with generate command and PDF format")
    story.when("building the generation plan and executing it")
    called = {}

    monkeypatch.setattr(cli_main, "register_default_services", lambda: None)

    def fake_build(options):
        called["options"] = options
        return ["plan"]

    def fake_exec(commands):
        called["commands"] = commands
        return 0

    monkeypatch.setattr(cli_main, "build_generation_plan", fake_build)
    monkeypatch.setattr(cli_main, "_execute_generation_plan", fake_exec)

    argv = [
        "simple-resume",
        "generate",
        "demo",
        "--format",
        "pdf",
        "--data-dir",
        str(tmp_path),
    ]
    monkeypatch.setattr(sys, "argv", argv)

    exit_code = cli_main.main()

    assert exit_code == 0
    assert called["commands"] == ["plan"]
    assert called["options"].name == "demo"
    assert OutputFormat.PDF in called["options"].formats


def test_cli_generate_multiple_formats(
    story: Scenario, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    story.given("CLI is invoked with multiple formats flag")
    story.when("parsing arguments and executing generation plan")
    captured = {}
    monkeypatch.setattr(cli_main, "register_default_services", lambda: None)

    def fake_build(options):
        captured["formats"] = options.formats
        return ["plan"]

    monkeypatch.setattr(cli_main, "build_generation_plan", fake_build)
    monkeypatch.setattr(cli_main, "_execute_generation_plan", lambda cmds: 0)

    argv = [
        "simple-resume",
        "generate",
        "demo",
        "--formats",
        "pdf",
        "html",
        "--data-dir",
        str(tmp_path),
    ]
    monkeypatch.setattr(sys, "argv", argv)

    exit_code = cli_main.main()

    assert exit_code == 0
    assert set(captured["formats"]) == {OutputFormat.PDF, OutputFormat.HTML}
