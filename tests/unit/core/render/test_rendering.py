"""Unit tests for simple_resume.core.rendering helpers."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock, patch

import pytest
from jinja2.loaders import FileSystemLoader

import simple_resume.shell.runtime.content as runtime_content
from simple_resume.core.render import get_template_environment
from simple_resume.shell.config import TEMPLATE_LOC
from tests.bdd import Scenario
from tests.conftest import create_complete_resume_data


def load_resume(
    name: str,
    preview: bool = False,
    *,
    paths: Any = None,
) -> tuple[str, dict[str, Any]]:
    """Mirror legacy load_resume behavior using the new runtime API."""
    resume_data = runtime_content.get_content(
        name, paths=paths, transform_markdown=preview
    )
    if "config" not in resume_data:
        raise ValueError("Resume configuration missing")
    template_name = resume_data.get("template", "resume_no_bars")
    template = f"html/{template_name}.html"
    context = dict(resume_data)
    context["preview"] = preview
    context["resume_config"] = resume_data.get("config", {})
    return template, context


def render_resume_html(
    name: str,
    *,
    preview: bool = False,
    paths: Any = None,
) -> tuple[str, str, dict[str, Any]]:
    """Render resume HTML using the production template environment."""
    template, context = load_resume(name, preview=preview, paths=paths)
    env = get_template_environment(str(TEMPLATE_LOC))
    env.globals.setdefault(
        "url_for",
        lambda endpoint, filename=None: filename or "" if endpoint == "static" else "",
    )
    html = env.get_template(template).render(**context)
    base_url = TEMPLATE_LOC.resolve().as_uri()
    return html, base_url, context


@patch("simple_resume.shell.runtime.content.get_content")
def test_load_resume_returns_template_and_context(
    mock_get_content: Mock, story: Scenario
) -> None:
    story.given("a resume file containing template and config data")
    mock_get_content.return_value = {
        "template": "resume_no_bars",
        "full_name": "Test User",
        "config": {"page_width": 190, "page_height": 270},
    }

    story.when("load_resume processes the file without preview")
    template, context = load_resume("test", preview=False)

    story.then("the HTML template name and context metadata are returned")
    assert template == "html/resume_no_bars.html"
    assert context["full_name"] == "Test User"
    assert context["preview"] is False
    assert context["resume_config"] == {"page_width": 190, "page_height": 270}
    mock_get_content.assert_called_once_with(
        "test", paths=None, transform_markdown=False
    )


@patch("simple_resume.shell.runtime.content.get_content")
def test_load_resume_uses_default_name(mock_get_content: Mock, story: Scenario) -> None:
    story.given("the caller does not provide an explicit resume name")
    mock_get_content.return_value = {
        "template": "resume_no_bars",
        "config": {"page_width": 190, "page_height": 270},
    }

    story.when("load_resume is invoked with empty string")
    load_resume("")

    story.then("get_content is still called once with default name")
    mock_get_content.assert_called_once_with("", paths=None, transform_markdown=False)


@patch(
    "simple_resume.shell.runtime.content.get_content",
    return_value={"template": "resume_no_bars"},
)
def test_load_resume_requires_config(mock_get_content: Mock, story: Scenario) -> None:
    story.given("resume content lacks the required config section")

    story.then("load_resume raises ValueError to signal invalid structure")
    with pytest.raises(ValueError):
        load_resume("broken")


@patch("simple_resume.shell.runtime.content.get_content")
def test_render_resume_html_renders_template(
    mock_get_content: Mock, story: Scenario
) -> None:
    story.given("complete resume data for preview rendering")
    resume_data = create_complete_resume_data(
        template="resume_no_bars", full_name="Render User"
    )
    mock_get_content.return_value = resume_data

    story.when("render_resume_html is invoked in preview mode")
    html, base_url, context = render_resume_html("render", preview=True)

    story.then("HTML output contains the name and preview context metadata")
    assert "Render User" in html
    assert context["preview"] is True
    assert base_url.startswith("file:")


def test_get_template_environment_uses_provided_path(story: Scenario) -> None:
    story.given("a template path is provided explicitly")
    env = get_template_environment(str(TEMPLATE_LOC))

    story.then("the loader search path includes that directory")
    assert env.loader is not None
    if isinstance(env.loader, FileSystemLoader):
        assert str(TEMPLATE_LOC) in env.loader.searchpath
    else:
        # This shouldn't happen in our case, but type checkers need to be sure
        raise AssertionError("Expected FileSystemLoader")


def test_get_template_environment_requires_explicit_path(story: Scenario) -> None:
    story.given("no template path is provided")

    story.then("TypeError is raised because the argument is required")
    with pytest.raises(TypeError):
        get_template_environment()  # type: ignore[call-arg]
