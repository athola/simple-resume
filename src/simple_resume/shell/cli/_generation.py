"""Generation helpers for the CLI – format coercion, plan building, execution."""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from os import PathLike
from pathlib import Path
from typing import Any, cast

from simple_resume.core.constants import OutputFormat
from simple_resume.core.exceptions import ValidationError
from simple_resume.core.generate.exceptions import GenerationError
from simple_resume.core.generate.plan import (
    CommandType,
    GeneratePlanOptions,
    GenerationCommand,
)
from simple_resume.core.result import BatchGenerationResult, GenerationResult
from simple_resume.shell.runtime.generate import execute_generation_commands


def _resolve_cli_formats(args: argparse.Namespace) -> list[OutputFormat]:
    """Normalize format arguments to `OutputFormat` values with safe defaults.

    By default, intermediate formats (markdown/tex) are upgraded to their
    final counterparts (html/pdf). When --no-render flag is set, intermediate
    formats are preserved as-is.
    """
    raw_formats = getattr(args, "formats", None)
    no_render_flag = getattr(args, "no_render", False)
    candidates: Iterable[OutputFormat | str | None]

    if raw_formats:
        candidates = raw_formats
    else:
        candidates = [getattr(args, "format", OutputFormat.MARKDOWN.value)]

    resolved: list[OutputFormat] = []
    for value in candidates:
        fmt = _coerce_output_format(value)
        # By default, upgrade intermediate formats to final formats
        # Unless --no-render is set, which preserves intermediate formats
        if not no_render_flag:
            if fmt is OutputFormat.MARKDOWN:
                fmt = OutputFormat.HTML
            elif fmt in (OutputFormat.TEX, OutputFormat.LATEX):
                fmt = OutputFormat.PDF
        resolved.append(fmt)
    return resolved


def _coerce_output_format(value: OutputFormat | str | None) -> OutputFormat:
    """Convert CLI-provided format values to `OutputFormat` with helpful errors."""
    if isinstance(value, OutputFormat):
        return value
    if isinstance(value, str):
        try:
            return OutputFormat(value)
        except ValueError as exc:
            raise ValidationError(
                f"{value!r} is not a supported output format",
                context={"format": value},
            ) from exc
    # Argparse guarantees a string, but unit tests often rely on bare mocks.
    # Default to PDF format so patches still exercise the code path.
    return OutputFormat.PDF


def _summarize_batch_result(
    result: GenerationResult | BatchGenerationResult,
    format_type: OutputFormat | str,
) -> int:
    """Summarize batch generation results for CLI output.

    Args:
        result: The batch generation result object.
        format_type: The format type (e.g., PDF, HTML).

    Returns:
        An exit code (0 for success, 1 for partial failure).

    """
    label = format_type.value if isinstance(format_type, OutputFormat) else format_type
    if isinstance(result, BatchGenerationResult):
        latex_skips: list[str] = []
        other_failures: list[tuple[str, Exception]] = []

        for name, error in (result.errors or {}).items():
            if isinstance(error, GenerationError) and "LaTeX" in str(error):
                latex_skips.append(name)
            else:
                other_failures.append((name, error))

        print(f"{label.upper()} generation summary")
        print(f"Successful: {result.successful}")
        print(f"Failed: {len(other_failures)}")
        if latex_skips:
            print(f"Skipped (LaTeX): {len(latex_skips)}")
            info_icon = "\N{INFORMATION SOURCE}\N{VARIATION SELECTOR-16}"
            templates = ", ".join(sorted(latex_skips))
            print(f"{info_icon} Skipped LaTeX template(s): {templates}")

        for name, error in other_failures:
            print(f"{name}: {error}")

        return 0 if not other_failures else 1

    return 0 if _did_generation_succeed(result) else 1


def _did_generation_succeed(result: GenerationResult) -> bool:
    """Check if generation succeeded.

    Args:
        result: Generation result with `exists` property.

    Returns:
        `True` if generation succeeded (output file exists), `False` otherwise.

    """
    return result.exists


def _to_path_or_none(value: Any) -> Path | None:
    """Convert value to `Path` or `None`."""
    if value in (None, "", False):
        return None
    if isinstance(value, Path):
        return value
    if isinstance(value, str):
        return Path(value)
    fspath = getattr(value, "__fspath__", None)
    if callable(fspath):
        fspath_result = fspath()
        if isinstance(fspath_result, (str, Path)):
            return Path(fspath_result)
        if isinstance(fspath_result, PathLike):
            return Path(fspath_result)
    return None


def _select_output_path(output: Path | None) -> Path | None:
    if isinstance(output, Path):
        return output if output.is_file() or output.suffix else output
    return None


def _select_output_dir(output: Path | None) -> Path | None:
    if isinstance(output, Path):
        return output if output.is_dir() else output.parent
    return None


def _looks_like_palette_file(palette: str | Path) -> bool:
    """Check if palette argument looks like a YAML palette path."""
    path = Path(palette)
    return path.suffix.lower() in {".yaml", ".yml"}


def _build_config_overrides(args: argparse.Namespace) -> dict[str, Any]:
    """Construct a dictionary of configuration overrides from CLI arguments.

    Args:
        args: The parsed command-line arguments.

    Returns:
        A dictionary of configuration overrides.

    """
    overrides: dict[str, Any] = {}
    theme_color = getattr(args, "theme_color", None)
    palette = getattr(args, "palette", None)
    page_width = getattr(args, "page_width", None)
    page_height = getattr(args, "page_height", None)
    output_mode = getattr(args, "output_mode", None)

    if isinstance(output_mode, str) and output_mode:
        overrides["output_mode"] = output_mode

    if isinstance(theme_color, str) and theme_color:
        overrides["theme_color"] = theme_color

    if isinstance(palette, (str, Path)) and palette:
        if _looks_like_palette_file(palette):
            palette_path = Path(palette)
            if palette_path.is_file():
                overrides["palette_file"] = str(palette_path)
            else:
                print(
                    f"Palette file '{palette_path}' not found. "
                    "Defaulting to resume or preset colors already configured."
                )
        else:
            overrides["color_scheme"] = str(palette)

    if isinstance(page_width, (int, float)):
        overrides["page_width"] = page_width
    if isinstance(page_height, (int, float)):
        overrides["page_height"] = page_height

    return overrides


def _build_plan_options(
    args: argparse.Namespace,
    overrides: dict[str, Any],
    formats: list[OutputFormat],
) -> GeneratePlanOptions:
    """Build `GeneratePlanOptions` from CLI arguments and overrides."""
    data_dir = _to_path_or_none(getattr(args, "data_dir", None))
    output_value = _to_path_or_none(getattr(args, "output", None))

    if getattr(args, "name", None):
        output_path = _select_output_path(output_value)
        output_dir = None
    else:
        output_path = None
        output_dir = _select_output_dir(output_value)

    return GeneratePlanOptions(
        name=getattr(args, "name", None),
        data_dir=data_dir,
        template=getattr(args, "template", None),
        output_path=output_path,
        output_dir=output_dir,
        preview=_bool_flag(getattr(args, "preview", False)),
        open_after=_bool_flag(getattr(args, "open", False)),
        browser=getattr(args, "browser", None),
        formats=formats,
        overrides=overrides,
    )


def _execute_generation_plan(commands: list[GenerationCommand]) -> int:
    """Execute a list of generation commands and summarize their results for CLI output.

    Args:
        commands: A list of `GenerationCommand` objects to execute.

    Returns:
        An exit code (0 for full success, non-zero for any failures).

    """
    exit_code = 0
    executions = execute_generation_commands(commands)
    for command, result in executions:
        if command.kind is CommandType.SINGLE:
            label = command.format.value.upper() if command.format else "OUTPUT"
            single_result = cast(GenerationResult, result)
            if _did_generation_succeed(single_result):
                output = getattr(result, "output_path", "generated")
                print(f"{label} generated: {output}")
            else:
                print(f"Failed to generate {label}")
                exit_code = max(exit_code, 1)
            continue

        if command.kind is CommandType.BATCH_SINGLE:
            format_type = command.format
            if format_type is None:
                print("Error: Missing format for batch command")
                exit_code = max(exit_code, 1)
                continue
            batch_payload = cast(GenerationResult | BatchGenerationResult, result)
            result_code = _summarize_batch_result(batch_payload, format_type)
            exit_code = max(exit_code, result_code)
            continue

        if not isinstance(result, dict):
            print("Error: Batch-all command returned unexpected payload")
            exit_code = max(exit_code, 1)
            continue

        # Cast to proper type since we know it's a
        # dict[str, BatchGenerationResult | GenerationResult]
        result_dict = cast(dict[str, BatchGenerationResult | GenerationResult], result)

        plan_code = 0
        for result_format, plan_result in result_dict.items():
            if isinstance(plan_result, BatchGenerationResult):
                batch_code = _summarize_batch_result(plan_result, result_format)
                plan_code = max(plan_code, batch_code)
            elif isinstance(plan_result, GenerationResult) and _did_generation_succeed(
                plan_result
            ):
                output = getattr(plan_result, "output_path", "generated")
                print(f"{result_format.upper()} generated: {output}")
            else:
                print(f"Failed to generate {result_format.upper()}")
                plan_code = 1
        exit_code = max(exit_code, plan_code)

    return exit_code


def _bool_flag(value: Any) -> bool:
    """Coerce a value to a boolean flag.

    Args:
        value: The value to coerce.

    Returns:
        True if the value is truthy, False otherwise.

    """
    return value if isinstance(value, bool) else False
