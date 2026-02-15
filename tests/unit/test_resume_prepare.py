"""Unit tests for render plan preparation - prepare_render_data pure function."""

from __future__ import annotations

import pytest

from simple_resume.core.models import (
    RenderMode,
    RenderPlan,
)
from simple_resume.core.render.plan import prepare_render_data
from simple_resume.shell.palettes.loader import get_palette_registry
from tests.bdd import Scenario


class TestResumeDataPreparation:
    """Test pure resume data transformation to render plans."""

    def test_prepare_render_data_html_mode(self, story: Scenario) -> None:
        story.given("complete resume data targeting HTML preview")
        raw_data = {
            "full_name": "John Doe",
            "email": "john@example.com",
            "config": {
                "template": "resume_no_bars",
                "page_width": 210,
                "page_height": 297,
                "theme_color": "#0395DE",
            },
            "description": "# Professional Summary\nExperienced developer.",
            "body": {
                "experience": [
                    {
                        "title": "Senior Developer",
                        "description": "Led development of key features.",
                    }
                ]
            },
        }

        story.when("prepare_render_data runs with preview enabled")
        get_palette_registry()
        registry = get_palette_registry()
        plan = prepare_render_data(
            raw_data, preview=True, base_path="/test", registry=registry
        )

        story.then("the plan targets HTML with rendered markdown and preview context")
        assert isinstance(plan, RenderPlan)
        assert plan.mode is RenderMode.HTML
        assert plan.name == "John Doe"
        assert plan.base_path == "/test"
        assert plan.template_name == "html/resume_no_bars.html"
        assert plan.context is not None
        assert plan.context["preview"] is True
        assert "<h1>Professional Summary</h1>" in plan.context["description"]
        assert "<p>Experienced developer.</p>" in plan.context["description"]
        assert plan.config.page_width == 210
        assert plan.config.page_height == 297

    def test_prepare_render_data_latex_mode(self, story: Scenario) -> None:
        story.given("resume data configured for latex output")
        raw_data = {
            "full_name": "Jane Smith",
            "config": {
                "output_mode": "latex",
                "page_width": 210,
                "page_height": 297,
            },
        }

        story.when("prepare_render_data runs without preview")
        get_palette_registry()
        registry = get_palette_registry()
        plan = prepare_render_data(
            raw_data, preview=False, base_path="/test", registry=registry
        )

        story.then("a latex render plan without template/context is produced")
        assert isinstance(plan, RenderPlan)
        assert plan.mode is RenderMode.LATEX
        assert plan.name == "Jane Smith"
        assert plan.base_path == "/test"
        assert plan.tex is None
        assert plan.config.output_mode == "latex"

    def test_prepare_render_data_invalid_config(self, story: Scenario) -> None:
        story.given("resume config contains invalid numeric values")
        raw_data = {
            "config": {
                "page_width": -10,
            },
        }

        story.then("validation fails and a ValueError is raised")
        registry = get_palette_registry()
        with pytest.raises(ValueError, match="Invalid resume config"):
            prepare_render_data(
                raw_data, preview=False, base_path="/test", registry=registry
            )

    def test_prepare_render_data_missing_config(self, story: Scenario) -> None:
        story.given("resume data without a config section")
        raw_data = {
            "full_name": "Test User",
        }

        story.then("prepare_render_data raises a ValueError")
        registry = get_palette_registry()
        with pytest.raises(ValueError, match="Invalid resume config"):
            prepare_render_data(
                raw_data, preview=False, base_path="/test", registry=registry
            )

    def test_prepare_render_data_markdown_transformation(self, story: Scenario) -> None:
        story.given("resume data with markdown fields and HTML target")
        raw_data = {
            "full_name": "Test User",
            "config": {
                "template": "resume_no_bars",
                "frame_color": "#1D1F2A",
            },
            "description": "**Bold text** and *italic text*",
            "body": {
                "projects": [
                    {
                        "name": "Project X",
                        "description": "## Features\n- Feature 1\n- Feature 2",
                    }
                ]
            },
        }

        story.when("prepare_render_data produces an HTML plan")
        get_palette_registry()
        registry = get_palette_registry()
        plan = prepare_render_data(
            raw_data, preview=False, base_path="/test", registry=registry
        )

        story.then("markdown content is rendered for description and nested sections")
        assert plan.context is not None
        description = plan.context["description"]
        assert "Bold text</strong>" in description
        assert "markdown-strong" in description
        assert "#1D1F2A" in description
        assert "<em>italic text</em>" in plan.context["description"]
        projects = plan.context["body"]["projects"]
        assert len(projects) > 0
        assert "<h2>Features</h2>" in projects[0]["description"]
        assert "<li>Feature 1</li>" in projects[0]["description"]

    def test_prepare_render_data_palette_metadata(self, story: Scenario) -> None:
        story.given("config includes palette details and fallback metadata")
        raw_data = {
            "full_name": "Test User",
            "config": {
                "template": "resume_no_bars",
                "palette": {
                    "source": "registry",
                    "name": "ocean",
                },
            },
            "meta": {
                "palette": {
                    "source": "registry",
                    "name": "ocean",
                    "size": 5,
                },
            },
        }

        story.when("prepare_render_data builds the plan")
        get_palette_registry()
        registry = get_palette_registry()
        plan = prepare_render_data(
            raw_data, preview=False, base_path="/test", registry=registry
        )

        story.then("palette metadata is preserved on the render plan")
        assert plan.palette_metadata is not None
        assert plan.palette_metadata["source"] == "registry"
        assert plan.palette_metadata["name"] == "ocean"
