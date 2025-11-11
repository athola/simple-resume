from __future__ import annotations

from pathlib import Path

import pytest

from simple_resume.config import Paths
from simple_resume.exceptions import FileSystemError
from simple_resume.hydration import hydrate_resume_data, load_resume_yaml
from tests.bdd import Scenario


def _base_resume_config() -> dict[str, object]:
    return {
        "palette": {
            "theme_color": "#0395DE",
            "sidebar_color": "#FFFFFF",
            "sidebar_text_color": "#000000",
            "bar_background_color": "#DFDFDF",
            "date2_color": "#616161",
            "frame_color": "#757575",
            "heading_icon_color": "#0395DE",
            "bold_color": "#123456",
        }
    }


def test_hydrate_resume_data_renders_bold_markdown(story: Scenario) -> None:
    story.case(
        given="a resume description that includes markdown emphasis",
        when="hydrate_resume_data runs with transform_markdown enabled",
        then="the bold text is converted into styled <strong> HTML",
    )
    source = {
        "template": "resume_no_bars",
        "config": _base_resume_config(),
        "description": "Intro with **bold** emphasis.",
    }

    hydrated = hydrate_resume_data(source, transform_markdown=True)

    assert "description" in hydrated
    assert (
        '<strong class="markdown-strong" style="color: #123456; '
        'font-weight: 700 !important;">bold</strong>'
    ) in hydrated["description"]


def test_hydrate_resume_data_can_skip_markdown(story: Scenario) -> None:
    story.case(
        given="a resume description that contains markdown",
        when="hydrate_resume_data is called with transform_markdown=False",
        then="the original markdown text remains unchanged",
    )
    source = {
        "template": "resume_no_bars",
        "config": _base_resume_config(),
        "description": "Intro with **bold** emphasis.",
    }

    hydrated = hydrate_resume_data(source, transform_markdown=False)

    assert hydrated["description"] == "Intro with **bold** emphasis."


def test_hydrate_resume_data_builds_skill_payload_when_markdown_disabled(
    story: Scenario,
) -> None:
    story.case(
        given="a resume payload containing skill sections",
        when="hydrate_resume_data runs without Markdown transforms",
        then="skill group payloads are attached deterministically",
    )
    source = {
        "template": "resume_no_bars",
        "config": _base_resume_config(),
        "expertise": {"Languages": ["Python", "Go"]},
        "programming": ["Python"],
        "keyskills": [{"Ops": ["Terraform"]}],
        "certification": "AWS CCP",
    }

    hydrated = hydrate_resume_data(source, transform_markdown=False)

    assert hydrated["expertise_groups"][0]["title"] == "Languages"
    assert hydrated["programming_groups"][0]["items"] == ["Python"]
    assert hydrated["certification_groups"][0]["items"] == ["AWS CCP"]


def test_load_resume_yaml_reads_explicit_path(tmp_path: Path, story: Scenario) -> None:
    story.case(
        given="an explicit YAML path that lives outside the input directory",
        when="load_resume_yaml is called with that path",
        then="the payload and filename round-trip and input path reflects the file",
    )
    custom_file = tmp_path / "custom.yaml"
    custom_file.write_text("full_name: Ada Lovelace\n", encoding="utf-8")

    payload, filename, resolved_paths = load_resume_yaml(custom_file)

    assert payload["full_name"] == "Ada Lovelace"
    assert filename == "custom.yaml"
    assert resolved_paths.input == custom_file.parent


def test_load_resume_yaml_uses_supplied_paths(tmp_path: Path, story: Scenario) -> None:
    data_dir = tmp_path / "workspace"
    input_dir = data_dir / "input"
    output_dir = data_dir / "output"
    input_dir.mkdir(parents=True)
    output_dir.mkdir()
    (input_dir / "demo.yaml").write_text("full_name: Demo User\n", encoding="utf-8")
    paths = Paths(data=data_dir, input=input_dir, output=output_dir)

    payload, filename, resolved_paths = load_resume_yaml("demo", paths=paths)

    assert resolved_paths is paths
    assert filename == "demo.yaml"
    assert payload["full_name"] == "Demo User"


def test_load_resume_yaml_missing_file_raises(tmp_path: Path) -> None:
    missing_file = tmp_path / "absent.yaml"

    with pytest.raises(FileSystemError):
        load_resume_yaml(missing_file)
