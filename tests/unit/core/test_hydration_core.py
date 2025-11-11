from __future__ import annotations

from typing import Any

from simple_resume.core.hydration_core import (
    build_skill_group_payload,
    hydrate_resume_structure,
)
from tests.bdd import Scenario


def _dummy_normalize(
    config: dict[str, Any], filename: str
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    normalized = dict(config)
    normalized["normalized"] = True
    return normalized, {"source": "direct", "file": filename or "unknown"}


def _dummy_render(data: dict[str, Any]) -> dict[str, Any]:
    rendered = dict(data)
    rendered["description"] = "HTML"
    rendered.update(build_skill_group_payload(rendered))
    return rendered


def test_build_skill_group_payload_formats_groups() -> None:
    payload = build_skill_group_payload(
        {
            "expertise": ["Python"],
            "programming": ["Rust"],
            "keyskills": ["Testing"],
            "certification": ["AWS"],
        }
    )
    assert payload["expertise_groups"][0]["items"] == ["Python"]
    assert payload["programming_groups"][0]["items"] == ["Rust"]
    assert payload["keyskills_groups"][0]["items"] == ["Testing"]
    assert payload["certification_groups"][0]["items"] == ["AWS"]


def test_hydrate_resume_structure_injects_palette_meta(story: Scenario) -> None:
    story.given("raw resume data with config and markdown fields")
    source = {
        "config": {"theme_color": "#000000"},
        "description": "Intro",
        "expertise": ["Python"],
        "programming": ["Rust"],
        "keyskills": ["Testing"],
        "certification": ["AWS"],
    }

    story.when("hydrate_resume_structure runs with dummy helpers")
    hydrated = hydrate_resume_structure(
        source,
        filename="resume.yaml",
        transform_markdown=True,
        normalize_config_fn=_dummy_normalize,
        render_markdown_fn=_dummy_render,
    )

    story.then("config is normalized and palette metadata is attached")
    assert hydrated["config"]["normalized"] is True
    assert hydrated["meta"]["palette"]["file"] == "resume.yaml"
    assert hydrated["description"] == "HTML"
    assert hydrated["expertise_groups"][0]["items"] == ["Python"]
