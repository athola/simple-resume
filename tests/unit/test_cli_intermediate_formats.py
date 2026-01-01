"""Unit tests for intermediate format CLI arguments."""

from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from simple_resume.core.constants import OutputFormat
from simple_resume.shell.cli import main as cli
from tests.bdd import Scenario


class TestResolveCliFormatsWithRender:
    """Test _resolve_cli_formats with --render flag."""

    def test_render_upgrades_markdown_to_html(self, story: Scenario) -> None:
        story.given("format is markdown with --render flag")
        story.when("resolving CLI formats")
        args = argparse.Namespace(formats=None, format="markdown", render=True)
        result = cli._resolve_cli_formats(args)
        assert result == [OutputFormat.HTML]

    def test_render_upgrades_tex_to_pdf(self, story: Scenario) -> None:
        story.given("format is tex with --render flag")
        story.when("resolving CLI formats")
        args = argparse.Namespace(formats=None, format="tex", render=True)
        result = cli._resolve_cli_formats(args)
        assert result == [OutputFormat.PDF]

    def test_render_keeps_pdf_as_pdf(self, story: Scenario) -> None:
        story.given("format is already pdf with --render flag")
        story.when("resolving CLI formats")
        args = argparse.Namespace(formats=None, format="pdf", render=True)
        result = cli._resolve_cli_formats(args)
        assert result == [OutputFormat.PDF]

    def test_render_keeps_html_as_html(self, story: Scenario) -> None:
        story.given("format is already html with --render flag")
        story.when("resolving CLI formats")
        args = argparse.Namespace(formats=None, format="html", render=True)
        result = cli._resolve_cli_formats(args)
        assert result == [OutputFormat.HTML]

    def test_without_render_keeps_markdown(self, story: Scenario) -> None:
        story.given("format is markdown without --render flag")
        story.when("resolving CLI formats")
        args = argparse.Namespace(formats=None, format="markdown", render=False)
        result = cli._resolve_cli_formats(args)
        assert result == [OutputFormat.MARKDOWN]

    def test_without_render_keeps_tex(self, story: Scenario) -> None:
        story.given("format is tex without --render flag")
        story.when("resolving CLI formats")
        args = argparse.Namespace(formats=None, format="tex", render=False)
        result = cli._resolve_cli_formats(args)
        assert result == [OutputFormat.TEX]


class TestBuildConfigOverridesWithOutputMode:
    """Test _build_config_overrides with --output-mode argument."""

    def test_output_mode_included_in_overrides(self, story: Scenario) -> None:
        story.given("args with --output-mode set")
        story.when("building config overrides")
        args = argparse.Namespace(
            theme_color=None,
            palette=None,
            page_width=None,
            page_height=None,
            template=None,
            output_mode="tex",
        )
        overrides = cli._build_config_overrides(args)
        assert overrides["output_mode"] == "tex"

    def test_output_mode_not_included_when_none(self, story: Scenario) -> None:
        story.given("args without --output-mode")
        story.when("building config overrides")
        args = argparse.Namespace(
            theme_color=None,
            palette=None,
            page_width=None,
            page_height=None,
            template=None,
            output_mode=None,
        )
        overrides = cli._build_config_overrides(args)
        assert "output_mode" not in overrides


class TestHandleRenderFile:
    """Test _handle_render_file for rendering existing intermediate files."""

    def test_render_markdown_file_success(
        self,
        story: Scenario,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        story.given("an existing .md file")
        story.when("rendering it to HTML")

        md_file = tmp_path / "test.md"
        md_file.write_text("# Test Resume\nContent here")

        mock_result = SimpleNamespace(
            exists=True,
            output_path=tmp_path / "test.html",
        )
        monkeypatch.setattr(cli, "render_markdown_file", lambda f, **kw: mock_result)

        args = argparse.Namespace(
            output=None,
            open=False,
            browser=None,
        )
        exit_code = cli._handle_render_file(args, md_file)

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "HTML generated" in captured.out

    def test_render_tex_file_success(
        self,
        story: Scenario,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        story.given("an existing .tex file")
        story.when("rendering it to PDF")

        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}")

        mock_result = SimpleNamespace(
            exists=True,
            output_path=tmp_path / "test.pdf",
        )
        monkeypatch.setattr(cli, "render_tex_file", lambda f, **kw: mock_result)

        args = argparse.Namespace(
            output=None,
            open=False,
        )
        exit_code = cli._handle_render_file(args, tex_file)

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "PDF generated" in captured.out

    def test_render_file_not_found(
        self,
        story: Scenario,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        story.given("a non-existent file")
        story.when("trying to render it")

        missing_file = tmp_path / "missing.md"
        args = argparse.Namespace()

        exit_code = cli._handle_render_file(args, missing_file)

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "File not found" in captured.out

    def test_render_file_unsupported_extension(
        self,
        story: Scenario,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        story.given("a file with unsupported extension")
        story.when("trying to render it")

        txt_file = tmp_path / "test.txt"
        txt_file.write_text("plain text")
        args = argparse.Namespace()

        exit_code = cli._handle_render_file(args, txt_file)

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Unsupported file type" in captured.out

    def test_render_file_generation_failure(
        self,
        story: Scenario,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        story.given("a valid .md file")
        story.when("rendering fails")

        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")

        mock_result = SimpleNamespace(exists=False, output_path=None)
        monkeypatch.setattr(cli, "render_markdown_file", lambda f, **kw: mock_result)

        args = argparse.Namespace(
            output=None,
            open=False,
            browser=None,
        )
        exit_code = cli._handle_render_file(args, md_file)

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Failed to" in captured.out


class TestHandleGenerateWithRenderFile:
    """Test handle_generate_command with --render-file flag."""

    def test_render_file_takes_priority(
        self,
        story: Scenario,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        story.given("args with --render-file set")
        story.when("handling generate command")

        md_file = tmp_path / "test.md"
        md_file.write_text("# Test")

        mock_result = SimpleNamespace(
            exists=True, output_path=md_file.with_suffix(".html")
        )
        monkeypatch.setattr(cli, "render_markdown_file", lambda f, **kw: mock_result)

        args = argparse.Namespace(
            render_file=md_file,
            name="ignored",  # Should be ignored when render_file is set
            output=None,
            open=False,
            browser=None,
        )
        exit_code = cli.handle_generate_command(args)

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "HTML generated" in captured.out


class TestOutputFormatIntermediate:
    """Test OutputFormat intermediate format helpers."""

    def test_intermediate_formats(self, story: Scenario) -> None:
        story.given("the OutputFormat enum")
        story.when("getting intermediate formats")
        intermediates = OutputFormat.intermediate_formats()
        assert OutputFormat.MARKDOWN in intermediates
        assert OutputFormat.TEX in intermediates
        assert OutputFormat.PDF not in intermediates
        assert OutputFormat.HTML not in intermediates

    def test_is_intermediate_markdown(self, story: Scenario) -> None:
        story.given("MARKDOWN format")
        story.when("checking if intermediate")
        assert OutputFormat.is_intermediate(OutputFormat.MARKDOWN) is True

    def test_is_intermediate_tex(self, story: Scenario) -> None:
        story.given("TEX format")
        story.when("checking if intermediate")
        assert OutputFormat.is_intermediate(OutputFormat.TEX) is True

    def test_is_intermediate_pdf(self, story: Scenario) -> None:
        story.given("PDF format")
        story.when("checking if intermediate")
        assert OutputFormat.is_intermediate(OutputFormat.PDF) is False

    def test_is_intermediate_html(self, story: Scenario) -> None:
        story.given("HTML format")
        story.when("checking if intermediate")
        assert OutputFormat.is_intermediate(OutputFormat.HTML) is False


class TestRunSessionGenerationIntermediateFormats:
    """Test _run_session_generation with MARKDOWN and TEX formats."""

    def test_markdown_generation_success(
        self,
        story: Scenario,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        story.given("MARKDOWN format in session generation")
        story.when("running session generation")

        from simple_resume.core.generate.plan import (  # noqa: PLC0415
            CommandType,
            GenerationCommand,
        )
        from simple_resume.core.models import GenerationConfig  # noqa: PLC0415

        resume = SimpleNamespace(_name="test")
        session = SimpleNamespace(
            paths=SimpleNamespace(output=Path("tmp/out")),
        )
        command = GenerationCommand(
            kind=CommandType.SINGLE,
            format=OutputFormat.MARKDOWN,
            config=GenerationConfig(output_path=None, open_after=False),
            overrides={},
        )

        result = SimpleNamespace(exists=True, output_path="test.md")
        monkeypatch.setattr(cli, "to_markdown", lambda *a, **k: result)

        cli._run_session_generation(cast(Any, resume), cast(Any, session), [command])
        captured = capsys.readouterr()

        assert "Markdown generated: test.md" in captured.out

    def test_tex_generation_success(
        self,
        story: Scenario,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        story.given("TEX format in session generation")
        story.when("running session generation")

        from simple_resume.core.generate.plan import (  # noqa: PLC0415
            CommandType,
            GenerationCommand,
        )
        from simple_resume.core.models import GenerationConfig  # noqa: PLC0415

        resume = SimpleNamespace(_name="test")
        session = SimpleNamespace(
            paths=SimpleNamespace(output=Path("tmp/out")),
        )
        command = GenerationCommand(
            kind=CommandType.SINGLE,
            format=OutputFormat.TEX,
            config=GenerationConfig(output_path=None, open_after=False),
            overrides={},
        )

        result = SimpleNamespace(exists=True, output_path="test.tex")
        monkeypatch.setattr(cli, "to_tex", lambda *a, **k: result)

        cli._run_session_generation(cast(Any, resume), cast(Any, session), [command])
        captured = capsys.readouterr()

        assert "LaTeX generated: test.tex" in captured.out
