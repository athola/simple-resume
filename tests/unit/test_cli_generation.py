"""Unit tests for CLI generation helpers – format coercion, plan building, execution."""

from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from simple_resume.core.constants import OutputFormat
from simple_resume.core.exceptions import ValidationError
from simple_resume.core.generate.exceptions import GenerationError
from simple_resume.core.generate.plan import (
    CommandType,
    GenerationCommand,
)
from simple_resume.core.result import BatchGenerationResult, GenerationResult
from simple_resume.shell.cli._generation import (
    _bool_flag,
    _build_config_overrides,
    _build_plan_options,
    _coerce_output_format,
    _execute_generation_plan,
    _looks_like_palette_file,
    _resolve_cli_formats,
    _select_output_dir,
    _select_output_path,
    _summarize_batch_result,
    _to_path_or_none,
)
from tests.bdd import Scenario

# ============================================================================
# _coerce_output_format
# ============================================================================


def test_coerce_output_format_from_enum(story: Scenario) -> None:
    story.given("an OutputFormat enum value")
    story.when("coercing to OutputFormat")
    result = _coerce_output_format(OutputFormat.PDF)
    story.then("the same enum value is returned")
    assert result is OutputFormat.PDF


def test_coerce_output_format_from_valid_string(story: Scenario) -> None:
    story.given("a valid format string 'html'")
    story.when("coercing to OutputFormat")
    result = _coerce_output_format("html")
    story.then("the matching OutputFormat enum is returned")
    assert result is OutputFormat.HTML


def test_coerce_output_format_from_invalid_string(story: Scenario) -> None:
    story.given("an unsupported format string 'docx'")
    story.when("coercing to OutputFormat")
    story.then("a ValidationError is raised")
    with pytest.raises(ValidationError):
        _coerce_output_format("docx")


def test_coerce_output_format_from_none(story: Scenario) -> None:
    story.given("a None value")
    story.when("coercing to OutputFormat")
    result = _coerce_output_format(None)
    story.then("defaults to PDF")
    assert result is OutputFormat.PDF


def test_coerce_output_format_from_non_string(story: Scenario) -> None:
    story.given("an integer value (not str or OutputFormat)")
    story.when("coercing to OutputFormat")
    result = _coerce_output_format(42)  # type: ignore[arg-type]
    story.then("defaults to PDF")
    assert result is OutputFormat.PDF


# ============================================================================
# _resolve_cli_formats
# ============================================================================


def test_resolve_cli_formats_defaults_to_format_attr(story: Scenario) -> None:
    story.given("args with no 'formats' but a 'format' attribute of 'html'")
    story.when("resolving CLI formats")
    args = argparse.Namespace(formats=None, format="html")
    result = _resolve_cli_formats(args)
    story.then("returns [OutputFormat.HTML]")
    assert result == [OutputFormat.HTML]


def test_resolve_cli_formats_uses_formats_list(story: Scenario) -> None:
    story.given("args with a 'formats' list")
    story.when("resolving CLI formats")
    args = argparse.Namespace(formats=["html", "pdf"], format=None)
    result = _resolve_cli_formats(args)
    story.then("both formats are resolved")
    assert result == [OutputFormat.HTML, OutputFormat.PDF]


def test_resolve_cli_formats_upgrades_markdown_to_html(story: Scenario) -> None:
    story.given("args with format='markdown' and no_render not set")
    story.when("resolving CLI formats")
    args = argparse.Namespace(formats=None, format="markdown")
    result = _resolve_cli_formats(args)
    story.then("markdown is upgraded to HTML")
    assert result == [OutputFormat.HTML]


def test_resolve_cli_formats_upgrades_tex_to_pdf(story: Scenario) -> None:
    story.given("args with format='tex' and no_render not set")
    story.when("resolving CLI formats")
    args = argparse.Namespace(formats=["tex"], format=None)
    result = _resolve_cli_formats(args)
    story.then("tex is upgraded to PDF")
    assert result == [OutputFormat.PDF]


def test_resolve_cli_formats_no_render_preserves_markdown(story: Scenario) -> None:
    story.given("args with format='markdown' and no_render=True")
    story.when("resolving CLI formats")
    args = argparse.Namespace(formats=None, format="markdown", no_render=True)
    result = _resolve_cli_formats(args)
    story.then("markdown is preserved as-is")
    assert result == [OutputFormat.MARKDOWN]


def test_resolve_cli_formats_no_render_preserves_tex(story: Scenario) -> None:
    story.given("args with format='tex' and no_render=True")
    story.when("resolving CLI formats")
    args = argparse.Namespace(formats=["tex"], format=None, no_render=True)
    result = _resolve_cli_formats(args)
    story.then("tex is preserved as-is")
    assert result == [OutputFormat.TEX]


def test_resolve_cli_formats_defaults_when_both_missing(story: Scenario) -> None:
    story.given("args with neither 'formats' nor 'format' attributes")
    story.when("resolving CLI formats")
    args = argparse.Namespace()
    result = _resolve_cli_formats(args)
    story.then("uses the default (markdown value -> upgraded to HTML)")
    assert len(result) == 1


# ============================================================================
# _summarize_batch_result
# ============================================================================


def test_summarize_batch_result_all_success(
    story: Scenario, capsys: pytest.CaptureFixture
) -> None:
    story.given("a batch result with all successes and no errors")
    batch = BatchGenerationResult(successful=3, failed=0, errors={})
    story.when("summarizing the batch result")
    exit_code = _summarize_batch_result(batch, OutputFormat.PDF)
    captured = capsys.readouterr()
    story.then("exit code is 0 and output shows summary")
    assert exit_code == 0
    assert "Successful: 3" in captured.out
    assert "Failed: 0" in captured.out


def test_summarize_batch_result_with_latex_skip(
    story: Scenario, capsys: pytest.CaptureFixture
) -> None:
    story.given("a batch result with a LaTeX error")
    latex_err = GenerationError("LaTeX failure", format_type=OutputFormat.PDF)
    batch = BatchGenerationResult(
        successful=2, failed=1, errors={"creative": latex_err}
    )
    story.when("summarizing the batch result")
    exit_code = _summarize_batch_result(batch, OutputFormat.PDF)
    captured = capsys.readouterr()
    story.then("LaTeX skips are shown and exit code is 0")
    assert exit_code == 0
    assert "Skipped (LaTeX)" in captured.out
    assert "creative" in captured.out


def test_summarize_batch_result_with_other_errors(
    story: Scenario, capsys: pytest.CaptureFixture
) -> None:
    story.given("a batch result with a non-LaTeX error")
    other_err = RuntimeError("boom")
    batch = BatchGenerationResult(
        successful=0, failed=1, errors={"template_a": other_err}
    )
    story.when("summarizing the batch result")
    exit_code = _summarize_batch_result(batch, OutputFormat.HTML)
    captured = capsys.readouterr()
    story.then("exit code is 1 and error is reported")
    assert exit_code == 1
    assert "template_a" in captured.out


def test_summarize_batch_result_with_mixed_errors(
    story: Scenario, capsys: pytest.CaptureFixture
) -> None:
    story.given("a batch result with both LaTeX and non-LaTeX errors")
    latex_err = GenerationError("LaTeX failure", format_type=OutputFormat.PDF)
    other_err = RuntimeError("disk full")
    batch = BatchGenerationResult(
        successful=1,
        failed=2,
        errors={"creative": latex_err, "modern": other_err},
    )
    story.when("summarizing the batch result")
    exit_code = _summarize_batch_result(batch, "pdf")
    captured = capsys.readouterr()
    story.then("exit code is 1, both categories shown")
    assert exit_code == 1
    assert "Skipped (LaTeX)" in captured.out
    assert "modern" in captured.out


def test_summarize_batch_result_single_generation_success(story: Scenario) -> None:
    story.given("a single GenerationResult that succeeded")
    dummy = cast(GenerationResult, SimpleNamespace(exists=True))
    story.when("summarizing as batch result")
    exit_code = _summarize_batch_result(dummy, OutputFormat.HTML)
    story.then("exit code is 0")
    assert exit_code == 0


def test_summarize_batch_result_single_generation_failure(story: Scenario) -> None:
    story.given("a single GenerationResult that failed")
    dummy = cast(GenerationResult, SimpleNamespace(exists=False))
    story.when("summarizing as batch result")
    exit_code = _summarize_batch_result(dummy, OutputFormat.HTML)
    story.then("exit code is 1")
    assert exit_code == 1


def test_summarize_batch_result_format_as_string(
    story: Scenario, capsys: pytest.CaptureFixture
) -> None:
    story.given("a batch result with format_type passed as a plain string")
    batch = BatchGenerationResult(successful=1, failed=0, errors={})
    story.when("summarizing the batch result")
    exit_code = _summarize_batch_result(batch, "html")
    captured = capsys.readouterr()
    story.then("the string label is uppercased in output")
    assert exit_code == 0
    assert "HTML" in captured.out


# ============================================================================
# _to_path_or_none
# ============================================================================


def test_to_path_or_none_with_none(story: Scenario) -> None:
    story.given("a None value")
    story.when("converting to Path or None")
    assert _to_path_or_none(None) is None


def test_to_path_or_none_with_empty_string(story: Scenario) -> None:
    story.given("an empty string")
    story.when("converting to Path or None")
    assert _to_path_or_none("") is None


def test_to_path_or_none_with_false(story: Scenario) -> None:
    story.given("a False value")
    story.when("converting to Path or None")
    assert _to_path_or_none(False) is None


def test_to_path_or_none_with_path_object(story: Scenario, tmp_path: Path) -> None:
    story.given("a Path object")
    p = tmp_path / "output.pdf"
    story.when("converting to Path or None")
    result = _to_path_or_none(p)
    story.then("returns the same Path")
    assert result == p


def test_to_path_or_none_with_string(story: Scenario, tmp_path: Path) -> None:
    story.given("a string path")
    target = str(tmp_path / "output.pdf")
    story.when("converting to Path or None")
    result = _to_path_or_none(target)
    story.then("returns a Path object")
    assert result == Path(target)


def test_to_path_or_none_with_fspath_object(story: Scenario, tmp_path: Path) -> None:
    story.given("an object implementing __fspath__")
    fspath_value = str(tmp_path / "custom.pdf")

    class FakePath:
        def __fspath__(self) -> str:
            return fspath_value

    story.when("converting to Path or None")
    result = _to_path_or_none(FakePath())
    story.then("returns the fspath as a Path")
    assert result == Path(fspath_value)


def test_to_path_or_none_with_non_path_object(story: Scenario) -> None:
    story.given("an object without __fspath__ and not str/Path")
    story.when("converting to Path or None")
    result = _to_path_or_none(42)
    story.then("returns None")
    assert result is None


# ============================================================================
# _select_output_path / _select_output_dir
# ============================================================================


def test_select_output_path_with_none(story: Scenario) -> None:
    story.given("a None output path")
    story.when("selecting output path")
    assert _select_output_path(None) is None


def test_select_output_path_with_file_path(story: Scenario, tmp_path: Path) -> None:
    story.given("a Path pointing to a file")
    f = tmp_path / "resume.pdf"
    f.touch()
    story.when("selecting output path")
    result = _select_output_path(f)
    story.then("returns the file path")
    assert result == f


def test_select_output_path_with_suffix(story: Scenario, tmp_path: Path) -> None:
    story.given("a Path with a suffix (not yet on disk)")
    p = tmp_path / "nonexistent" / "resume.pdf"
    story.when("selecting output path")
    result = _select_output_path(p)
    story.then("returns the path (has suffix)")
    assert result == p


def test_select_output_dir_with_none(story: Scenario) -> None:
    story.given("a None output path")
    story.when("selecting output dir")
    assert _select_output_dir(None) is None


def test_select_output_dir_with_directory(story: Scenario, tmp_path: Path) -> None:
    story.given("a Path that is a directory")
    story.when("selecting output dir")
    result = _select_output_dir(tmp_path)
    story.then("returns the directory itself")
    assert result == tmp_path


def test_select_output_dir_with_file_path(story: Scenario, tmp_path: Path) -> None:
    story.given("a Path pointing to a file")
    p = tmp_path / "output" / "resume.pdf"
    story.when("selecting output dir")
    result = _select_output_dir(p)
    story.then("returns the parent directory")
    assert result == tmp_path / "output"


# ============================================================================
# _looks_like_palette_file
# ============================================================================


def test_looks_like_palette_file_yaml(story: Scenario) -> None:
    story.given("a .yaml file path")
    story.when("checking if it looks like a palette file")
    assert _looks_like_palette_file("colors.yaml") is True


def test_looks_like_palette_file_yml(story: Scenario) -> None:
    story.given("a .yml file path")
    story.when("checking if it looks like a palette file")
    assert _looks_like_palette_file("palette.yml") is True


def test_looks_like_palette_file_not_yaml(story: Scenario) -> None:
    story.given("a non-YAML string (palette name)")
    story.when("checking if it looks like a palette file")
    assert _looks_like_palette_file("ocean") is False


def test_looks_like_palette_file_with_path_object(story: Scenario) -> None:
    story.given("a Path object with .yaml extension")
    story.when("checking if it looks like a palette file")
    assert _looks_like_palette_file(Path("theme.yaml")) is True


# ============================================================================
# _bool_flag
# ============================================================================


def test_bool_flag_true(story: Scenario) -> None:
    story.given("a True boolean value")
    story.when("coercing to bool flag")
    assert _bool_flag(True) is True


def test_bool_flag_false(story: Scenario) -> None:
    story.given("a False boolean value")
    story.when("coercing to bool flag")
    assert _bool_flag(False) is False


def test_bool_flag_none(story: Scenario) -> None:
    story.given("a None value")
    story.when("coercing to bool flag")
    assert _bool_flag(None) is False


def test_bool_flag_string(story: Scenario) -> None:
    story.given("a truthy string value")
    story.when("coercing to bool flag")
    assert _bool_flag("yes") is False


def test_bool_flag_integer(story: Scenario) -> None:
    story.given("a truthy integer value")
    story.when("coercing to bool flag")
    assert _bool_flag(1) is False


# ============================================================================
# _build_config_overrides
# ============================================================================


def test_build_config_overrides_empty_args(story: Scenario) -> None:
    story.given("args with no override-related attributes")
    args = argparse.Namespace()
    story.when("building config overrides")
    result = _build_config_overrides(args)
    story.then("returns an empty dict")
    assert result == {}


def test_build_config_overrides_theme_color(story: Scenario) -> None:
    story.given("args with a theme_color")
    args = argparse.Namespace(theme_color="#FF0000")
    story.when("building config overrides")
    result = _build_config_overrides(args)
    story.then("theme_color is in overrides")
    assert result["theme_color"] == "#FF0000"


def test_build_config_overrides_palette_name(story: Scenario) -> None:
    story.given("args with a palette name (not a file)")
    args = argparse.Namespace(palette="ocean")
    story.when("building config overrides")
    result = _build_config_overrides(args)
    story.then("color_scheme is set")
    assert result["color_scheme"] == "ocean"


def test_build_config_overrides_palette_yaml_file_exists(
    story: Scenario, tmp_path: Path
) -> None:
    story.given("args with a palette .yaml file that exists")
    palette_file = tmp_path / "colors.yaml"
    palette_file.write_text("theme_color: '#000'")
    args = argparse.Namespace(palette=str(palette_file))
    story.when("building config overrides")
    result = _build_config_overrides(args)
    story.then("palette_file is set to the file path")
    assert result["palette_file"] == str(palette_file)


def test_build_config_overrides_palette_yaml_file_missing(
    story: Scenario, capsys: pytest.CaptureFixture
) -> None:
    story.given("args with a palette .yaml file that does not exist")
    args = argparse.Namespace(palette="/nonexistent/colors.yaml")
    story.when("building config overrides")
    result = _build_config_overrides(args)
    captured = capsys.readouterr()
    story.then("no palette_file override, warning printed")
    assert "palette_file" not in result
    assert "not found" in captured.out


def test_build_config_overrides_page_dimensions(story: Scenario) -> None:
    story.given("args with page_width and page_height")
    args = argparse.Namespace(page_width=210, page_height=297)
    story.when("building config overrides")
    result = _build_config_overrides(args)
    story.then("page dimensions are in overrides")
    assert result["page_width"] == 210
    assert result["page_height"] == 297


def test_build_config_overrides_output_mode(story: Scenario) -> None:
    story.given("args with output_mode set")
    args = argparse.Namespace(output_mode="dark")
    story.when("building config overrides")
    result = _build_config_overrides(args)
    story.then("output_mode is in overrides")
    assert result["output_mode"] == "dark"


def test_build_config_overrides_ignores_empty_strings(story: Scenario) -> None:
    story.given("args with empty string values")
    args = argparse.Namespace(theme_color="", palette="", output_mode="")
    story.when("building config overrides")
    result = _build_config_overrides(args)
    story.then("empty strings are ignored")
    assert result == {}


# ============================================================================
# _build_plan_options
# ============================================================================


def test_build_plan_options_with_name(story: Scenario, tmp_path: Path) -> None:
    story.given("args with a resume name and output path")
    out_file = str(tmp_path / "resume.pdf")
    args = argparse.Namespace(
        name="john_doe",
        data_dir=None,
        template="modern",
        output=out_file,
        preview=False,
        open=False,
        browser=None,
    )
    overrides: dict = {}
    formats = [OutputFormat.PDF]
    story.when("building plan options")
    opts = _build_plan_options(args, overrides, formats)
    story.then("name is set and output_path is used (not output_dir)")
    assert opts.name == "john_doe"
    assert opts.template == "modern"
    assert opts.output_path == Path(out_file)
    assert opts.output_dir is None
    assert opts.formats == [OutputFormat.PDF]


def test_build_plan_options_without_name(story: Scenario, tmp_path: Path) -> None:
    story.given("args without a name (batch mode)")
    out_dir = str(tmp_path / "output")
    args = argparse.Namespace(
        name=None,
        data_dir=str(tmp_path / "data"),
        template=None,
        output=out_dir,
        preview=True,
        open=False,
        browser="chrome",
    )
    overrides = {"theme_color": "#000"}
    formats = [OutputFormat.HTML]
    story.when("building plan options")
    opts = _build_plan_options(args, overrides, formats)
    story.then("output_dir is used instead of output_path")
    assert opts.name is None
    assert opts.output_path is None
    assert opts.output_dir is not None
    assert opts.preview is True
    assert opts.browser == "chrome"


def test_build_plan_options_coerces_bool_flags(story: Scenario) -> None:
    story.given("args with non-boolean preview and open values")
    args = argparse.Namespace(
        name="test",
        data_dir=None,
        template=None,
        output=None,
        preview="yes",
        open=1,
        browser=None,
    )
    story.when("building plan options")
    opts = _build_plan_options(args, {}, [OutputFormat.PDF])
    story.then("non-boolean values are coerced to False")
    assert opts.preview is False
    assert opts.open_after is False


# ============================================================================
# _execute_generation_plan
# ============================================================================


def _make_gen_command(
    kind: CommandType = CommandType.SINGLE,
    fmt: OutputFormat | None = OutputFormat.PDF,
) -> GenerationCommand:
    """Create a GenerationCommand with a mock config."""
    mock_config = MagicMock()
    return GenerationCommand(
        kind=kind,
        format=fmt,
        config=mock_config,
        overrides={},
    )


@patch("simple_resume.shell.cli._generation.execute_generation_commands")
def test_execute_generation_plan_single_success(
    mock_exec: MagicMock,
    story: Scenario,
    capsys: pytest.CaptureFixture,
) -> None:
    story.given("a single generation command that succeeds")
    cmd = _make_gen_command(CommandType.SINGLE, OutputFormat.PDF)
    mock_result = SimpleNamespace(exists=True, output_path="test_output/resume.pdf")
    mock_exec.return_value = [(cmd, mock_result)]
    story.when("executing the generation plan")
    exit_code = _execute_generation_plan([cmd])
    captured = capsys.readouterr()
    story.then("exit code is 0 and success message is printed")
    assert exit_code == 0
    assert "PDF generated" in captured.out


@patch("simple_resume.shell.cli._generation.execute_generation_commands")
def test_execute_generation_plan_single_failure(
    mock_exec: MagicMock,
    story: Scenario,
    capsys: pytest.CaptureFixture,
) -> None:
    story.given("a single generation command that fails")
    cmd = _make_gen_command(CommandType.SINGLE, OutputFormat.HTML)
    mock_result = SimpleNamespace(exists=False)
    mock_exec.return_value = [(cmd, mock_result)]
    story.when("executing the generation plan")
    exit_code = _execute_generation_plan([cmd])
    captured = capsys.readouterr()
    story.then("exit code is 1 and failure message is printed")
    assert exit_code == 1
    assert "Failed to generate HTML" in captured.out


@patch("simple_resume.shell.cli._generation.execute_generation_commands")
def test_execute_generation_plan_batch_single(
    mock_exec: MagicMock,
    story: Scenario,
    capsys: pytest.CaptureFixture,
) -> None:
    story.given("a batch_single command with successful results")
    cmd = _make_gen_command(CommandType.BATCH_SINGLE, OutputFormat.PDF)
    batch = BatchGenerationResult(successful=3, failed=0, errors={})
    mock_exec.return_value = [(cmd, batch)]
    story.when("executing the generation plan")
    exit_code = _execute_generation_plan([cmd])
    story.then("exit code is 0")
    assert exit_code == 0


@patch("simple_resume.shell.cli._generation.execute_generation_commands")
def test_execute_generation_plan_batch_single_missing_format(
    mock_exec: MagicMock,
    story: Scenario,
    capsys: pytest.CaptureFixture,
) -> None:
    story.given("a batch_single command with format=None")
    cmd = _make_gen_command(CommandType.BATCH_SINGLE, None)
    batch = BatchGenerationResult(successful=1, failed=0, errors={})
    mock_exec.return_value = [(cmd, batch)]
    story.when("executing the generation plan")
    exit_code = _execute_generation_plan([cmd])
    captured = capsys.readouterr()
    story.then("exit code is 1 and error message is printed")
    assert exit_code == 1
    assert "Missing format" in captured.out


@patch("simple_resume.shell.cli._generation.execute_generation_commands")
def test_execute_generation_plan_batch_all_dict(
    mock_exec: MagicMock,
    story: Scenario,
    capsys: pytest.CaptureFixture,
) -> None:
    story.given("a batch_all command returning a dict of results")
    cmd = _make_gen_command(CommandType.BATCH_ALL, None)
    batch_pdf = BatchGenerationResult(successful=2, failed=0, errors={})
    result_dict = {"pdf": batch_pdf}
    mock_exec.return_value = [(cmd, result_dict)]
    story.when("executing the generation plan")
    exit_code = _execute_generation_plan([cmd])
    story.then("exit code is 0")
    assert exit_code == 0


@patch("simple_resume.shell.cli._generation.execute_generation_commands")
def test_execute_generation_plan_batch_all_with_failure(
    mock_exec: MagicMock,
    story: Scenario,
    capsys: pytest.CaptureFixture,
) -> None:
    story.given("a batch_all command with a failed GenerationResult in the dict")
    cmd = _make_gen_command(CommandType.BATCH_ALL, None)
    failed_result = cast(GenerationResult, SimpleNamespace(exists=False))
    result_dict = {"html": failed_result}
    mock_exec.return_value = [(cmd, result_dict)]
    story.when("executing the generation plan")
    exit_code = _execute_generation_plan([cmd])
    captured = capsys.readouterr()
    story.then("exit code is 1")
    assert exit_code == 1
    assert "Failed to generate HTML" in captured.out


@patch("simple_resume.shell.cli._generation.execute_generation_commands")
def test_execute_generation_plan_batch_all_unexpected_payload(
    mock_exec: MagicMock,
    story: Scenario,
    capsys: pytest.CaptureFixture,
) -> None:
    story.given("a batch_all command returning a non-dict result")
    cmd = _make_gen_command(CommandType.BATCH_ALL, None)
    mock_exec.return_value = [(cmd, "unexpected")]
    story.when("executing the generation plan")
    exit_code = _execute_generation_plan([cmd])
    captured = capsys.readouterr()
    story.then("exit code is 1 and error about unexpected payload")
    assert exit_code == 1
    assert "unexpected payload" in captured.out


@patch("simple_resume.shell.cli._generation.execute_generation_commands")
def test_execute_generation_plan_multiple_commands(
    mock_exec: MagicMock,
    story: Scenario,
    capsys: pytest.CaptureFixture,
) -> None:
    story.given("two single commands - one succeeds, one fails")
    cmd1 = _make_gen_command(CommandType.SINGLE, OutputFormat.PDF)
    cmd2 = _make_gen_command(CommandType.SINGLE, OutputFormat.HTML)
    r1 = SimpleNamespace(exists=True, output_path="test_output/resume.pdf")
    r2 = SimpleNamespace(exists=False)
    mock_exec.return_value = [(cmd1, r1), (cmd2, r2)]
    story.when("executing the generation plan")
    exit_code = _execute_generation_plan([cmd1, cmd2])
    story.then("exit code is 1 (worst of both)")
    assert exit_code == 1


@patch("simple_resume.shell.cli._generation.execute_generation_commands")
def test_execute_generation_plan_single_no_format(
    mock_exec: MagicMock,
    story: Scenario,
    capsys: pytest.CaptureFixture,
) -> None:
    story.given("a single command with format=None")
    cmd = _make_gen_command(CommandType.SINGLE, None)
    mock_result = SimpleNamespace(exists=True, output_path="test_output/out")
    mock_exec.return_value = [(cmd, mock_result)]
    story.when("executing the generation plan")
    exit_code = _execute_generation_plan([cmd])
    captured = capsys.readouterr()
    story.then("uses 'OUTPUT' as label")
    assert exit_code == 0
    assert "OUTPUT generated" in captured.out
