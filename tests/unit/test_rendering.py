"""Unit tests for simple_resume.rendering helpers."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import cast
from unittest.mock import ANY, Mock, patch

import pytest

from simple_resume.rendering import (
    get_template_environment,
    load_resume,
    render_resume_html,
)
from tests.bdd import Scenario
from tests.conftest import create_complete_resume_data


@patch("simple_resume.rendering.get_content")
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
    mock_get_content.assert_called_once_with("test", paths=ANY)


@patch("simple_resume.rendering.get_content")
def test_load_resume_uses_default_name(mock_get_content: Mock, story: Scenario) -> None:
    story.given("the caller does not provide an explicit resume name")
    mock_get_content.return_value = {
        "template": "resume_no_bars",
        "config": {"page_width": 190, "page_height": 270},
    }

    story.when("load_resume is invoked with empty string")
    load_resume("")

    story.then("get_content is still called once with default name")
    mock_get_content.assert_called_once()


@patch(
    "simple_resume.rendering.get_content", return_value={"template": "resume_no_bars"}
)
def test_load_resume_requires_config(mock_get_content: Mock, story: Scenario) -> None:
    story.given("resume content lacks the required config section")

    story.then("load_resume raises ValueError to signal invalid structure")
    with pytest.raises(ValueError):
        load_resume("broken")


@patch("simple_resume.rendering.get_content")
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
    assert Path(base_url).match("*/src/simple_resume")


def test_get_template_environment_url_for_static(story: Scenario) -> None:
    story.given("the template environment exposes url_for")
    env = get_template_environment()

    story.when("requesting a static asset path")
    url_for = env.globals["url_for"]
    assert callable(url_for)
    url_for_callable = cast(Callable[..., str], url_for)
    url = url_for_callable("static", filename="icon.png")

    story.then("the helper returns a relative static URL")
    assert url == "static/icon.png"


def test_get_template_environment_url_for_invalid_endpoint(story: Scenario) -> None:
    story.given("only the 'static' endpoint is supported")
    env = get_template_environment()

    story.then("requesting an unknown endpoint raises ValueError")
    url_for = env.globals["url_for"]
    assert callable(url_for)
    url_for_callable = cast(Callable[..., str], url_for)
    with pytest.raises(ValueError):
        url_for_callable("api", filename="x")


def test_get_template_environment_requires_filename(story: Scenario) -> None:
    story.given("url_for requires a filename arg even for static endpoint")
    env = get_template_environment()

    story.then("omitting filename raises ValueError")
    url_for = env.globals["url_for"]
    assert callable(url_for)
    url_for_callable = cast(Callable[..., str], url_for)
    with pytest.raises(ValueError):
        url_for_callable("static")
