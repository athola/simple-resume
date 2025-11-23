"""Provide pure generation planning helpers for CLI and session shells."""

from __future__ import annotations

import copy
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from simple_resume.core.constants import OutputFormat
from simple_resume.core.models import GenerationConfig
from simple_resume.core.paths import Paths


class CommandType(str, Enum):
    """Define kinds of generation commands the shell can execute."""

    SINGLE = "single"
    BATCH_SINGLE = "batch_single"
    BATCH_ALL = "batch_all"


@dataclass(frozen=True)
class GenerationCommand:
    """Define a pure description of a generation step."""

    kind: CommandType
    format: OutputFormat | None
    config: GenerationConfig
    overrides: dict[str, Any]


@dataclass(frozen=True)
class GeneratePlanOptions:
    """Define normalized inputs for planning CLI/session work."""

    name: str | None
    data_dir: Path | None
    template: str | None
    output_path: Path | None
    output_dir: Path | None
    preview: bool
    open_after: bool
    browser: str | None
    formats: Sequence[OutputFormat]
    overrides: dict[str, Any]
    paths: Paths | None = None
    pattern: str = "*"


def build_generation_plan(options: GeneratePlanOptions) -> list[GenerationCommand]:
    """Return the deterministic commands needed to satisfy the request."""
    if not options.formats:
        raise ValueError("At least one output format must be specified")

    plan: list[GenerationCommand] = []
    overrides = copy.deepcopy(options.overrides)

    if options.name:
        for format_type in options.formats:
            plan.append(
                GenerationCommand(
                    kind=CommandType.SINGLE,
                    format=format_type,
                    config=GenerationConfig(
                        name=options.name,
                        data_dir=options.data_dir,
                        template=options.template,
                        format=format_type,
                        output_path=options.output_path,
                        open_after=options.open_after,
                        preview=options.preview,
                        browser=options.browser,
                        paths=options.paths,
                        pattern=options.pattern,
                    ),
                    overrides=copy.deepcopy(overrides),
                )
            )
        return plan

    if len(options.formats) == 1:
        format_type = options.formats[0]
        plan.append(
            GenerationCommand(
                kind=CommandType.BATCH_SINGLE,
                format=format_type,
                config=GenerationConfig(
                    data_dir=options.data_dir,
                    template=options.template,
                    output_dir=options.output_dir,
                    open_after=options.open_after,
                    preview=options.preview,
                    browser=options.browser,
                    paths=options.paths,
                    pattern=options.pattern,
                ),
                overrides=copy.deepcopy(overrides),
            )
        )
        return plan

    plan.append(
        GenerationCommand(
            kind=CommandType.BATCH_ALL,
            format=None,
            config=GenerationConfig(
                data_dir=options.data_dir,
                template=options.template,
                output_dir=options.output_dir,
                open_after=options.open_after,
                preview=options.preview,
                browser=options.browser,
                formats=list(options.formats),
                paths=options.paths,
                pattern=options.pattern,
            ),
            overrides=copy.deepcopy(overrides),
        )
    )
    return plan


__all__ = [
    "CommandType",
    "GenerationCommand",
    "GeneratePlanOptions",
    "build_generation_plan",
]
