"""Unit tests for simple_resume.rendering helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from simple_resume.rendering import (
    get_template_environment,
    load_resume,
    render_resume_html,
)
from tests.conftest import create_complete_resume_data


@patch("simple_resume.rendering.get_content")
def test_load_resume_returns_template_and_context(mock_get_content: Mock) -> None:
    """Return both template name and context data."""
    mock_get_content.return_value = {
        "template": "resume_no_bars",
        "full_name": "Test User",
        "config": {"page_width": 190, "page_height": 270},
    }

    template, context = load_resume("test", preview=False)

    assert template == "resume_no_bars.html"
    assert context["full_name"] == "Test User"
    assert context["preview"] is False
    assert context["resume_config"] == {"page_width": 190, "page_height": 270}
    mock_get_content.assert_called_once()
    args, kwargs = mock_get_content.call_args
    assert args == ("test",)
    assert "paths" in kwargs


@patch("simple_resume.rendering.get_content")
def test_load_resume_uses_default_name(mock_get_content: Mock) -> None:
    """Default filename is used when none is provided."""
    mock_get_content.return_value = {
        "template": "resume_no_bars",
        "config": {"page_width": 190, "page_height": 270},
    }

    load_resume("")
    mock_get_content.assert_called_once()


@patch(
    "simple_resume.rendering.get_content", return_value={"template": "resume_no_bars"}
)
def test_load_resume_requires_config(mock_get_content: Mock) -> None:
    """Raise an error when config section is absent."""
    with pytest.raises(ValueError):
        load_resume("broken")


@patch("simple_resume.rendering.get_content")
def test_render_resume_html_renders_template(mock_get_content: Mock) -> None:
    """Rendered HTML contains expected content for preview."""
    resume_data = create_complete_resume_data(
        template="resume_no_bars", full_name="Render User"
    )
    mock_get_content.return_value = resume_data

    html, base_url, context = render_resume_html("render", preview=True)

    assert "Render User" in html
    assert context["preview"] is True
    assert Path(base_url).match("*/src/simple_resume")


def test_get_template_environment_url_for_static() -> None:
    """Static assets resolve using url_for helper."""
    env = get_template_environment()
    url = env.globals["url_for"]("static", filename="icon.png")
    assert url == "static/icon.png"


def test_get_template_environment_url_for_invalid_endpoint() -> None:
    """Raising ValueError for unsupported endpoints."""
    env = get_template_environment()
    with pytest.raises(ValueError):
        env.globals["url_for"]("api", filename="x")


def test_get_template_environment_requires_filename() -> None:
    """Raising ValueError when filename argument missing."""
    env = get_template_environment()
    with pytest.raises(ValueError):
        env.globals["url_for"]("static")
