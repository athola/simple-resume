"""Provide pure helpers for transforming hydrated resume data."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any, Callable

from simple_resume.core.skills import format_skill_groups

NormalizeConfigFn = Callable[
    [dict[str, Any], str], tuple[dict[str, Any], dict[str, Any] | None]
]
RenderMarkdownFn = Callable[[dict[str, Any]], dict[str, Any]]


def build_skill_group_payload(resume_data: Mapping[str, Any]) -> dict[str, Any]:
    """Return the computed skill group payload for sidebar sections."""
    return {
        "expertise_groups": format_skill_groups(resume_data.get("expertise")),
        "programming_groups": format_skill_groups(resume_data.get("programming")),
        "keyskills_groups": format_skill_groups(resume_data.get("keyskills")),
        "certification_groups": format_skill_groups(resume_data.get("certification")),
    }


def hydrate_resume_structure(
    source_yaml: dict[str, Any],
    *,
    filename: str = "",
    transform_markdown: bool = True,
    normalize_config_fn: NormalizeConfigFn,
    render_markdown_fn: RenderMarkdownFn,
) -> dict[str, Any]:
    """Return normalized resume data using injected pure helpers."""
    processed_resume = copy.deepcopy(source_yaml)

    config = processed_resume.get("config")
    if isinstance(config, dict):
        normalized_config, palette_meta = normalize_config_fn(config, filename)
        processed_resume["config"] = normalized_config
        if palette_meta:
            meta = dict(processed_resume.get("meta", {}))
            meta["palette"] = palette_meta
            processed_resume["meta"] = meta

    if transform_markdown:
        processed_resume = render_markdown_fn(processed_resume)
    else:
        processed_resume.update(build_skill_group_payload(processed_resume))

    return processed_resume


__all__ = ["build_skill_group_payload", "hydrate_resume_structure"]
