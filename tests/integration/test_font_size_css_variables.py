"""Integration test for font size CSS variable chain.

Verifies that font size configuration flows correctly from:
1. YAML config
2. Python config defaults (apply_config_defaults)
3. Jinja template (resume_base.html)
4. Rendered CSS variables

This is the three-layer defense that ensures font sizes are consistent
throughout the resume generation pipeline.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import yaml
from bs4 import BeautifulSoup

from simple_resume.core.generate.html import create_html_generator_factory
from simple_resume.core.paths import Paths
from simple_resume.shell.runtime.content import get_content
from simple_resume.shell.services import DefaultTemplateLocator
from tests.bdd import scenario
from tests.conftest import create_complete_resume_data

# Import Resume locally in render_resume_html to avoid circular imports
# with the rest of the codebase (resume imports many modules we test here).


def _create_resume_with_font_sizes(
    full_name: str = "Font Size Test",
    sidebar_font_size: float | None = None,
    description_font_size: float | None = None,
    date_font_size: float | None = None,
) -> dict[str, Any]:
    """Create resume data with optional font size config overrides."""
    resume_data = create_complete_resume_data(
        template="resume_no_bars",
        full_name=full_name,
    )
    # Add font size config to the config dict
    if sidebar_font_size is not None:
        resume_data["config"]["sidebar_font_size"] = sidebar_font_size
    if description_font_size is not None:
        resume_data["config"]["description_font_size"] = description_font_size
    if date_font_size is not None:
        resume_data["config"]["date_font_size"] = date_font_size
    return resume_data


def _build_paths(base: Path) -> Paths:
    """Construct paths structure for tests using temporary directories."""
    input_dir = base / "input"
    output_dir = base / "output"
    content_dir = base / "content"
    templates_dir = base / "templates"
    static_dir = base / "static"
    for directory in (input_dir, output_dir, content_dir, templates_dir, static_dir):
        directory.mkdir(parents=True, exist_ok=True)
    return Paths(
        data=base,
        input=input_dir,
        output=output_dir,
        content=content_dir,
        templates=templates_dir,
        static=static_dir,
    )


def render_resume_html(name: str, paths: Paths, *, preview: bool = False) -> str:
    """Render HTML by building a plan from hydrated resume data."""
    # Local import to avoid circular dependency (Resume imports many test modules)
    from simple_resume.core.resume import Resume  # noqa: PLC0415

    resume_data = get_content(name, paths=paths)
    resume = Resume.from_data(resume_data, name=name, paths=paths)
    render_plan = resume.prepare_render_plan(preview=preview)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    template_locator = DefaultTemplateLocator()
    factory = create_html_generator_factory(default_template_locator=template_locator)
    prepare_html_func = factory.create_prepare_html_function()
    html, _, _ = prepare_html_func(
        render_plan,
        tmp_path,
        resume_name=name,
        template_locator=template_locator,
    )
    return html


def test_font_size_css_variable_chain_custom_values() -> None:
    """Verify font size config flows through to rendered CSS with custom values."""
    story = scenario("font size CSS variable chain with custom values")
    story.given("a resume config with custom font sizes")

    resume_data = _create_resume_with_font_sizes(
        full_name="Font Size Test User",
        sidebar_font_size=10,
        description_font_size=9,
        date_font_size=8,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)
        paths = _build_paths(temp_dir)
        (paths.input / "font_size_test.yaml").write_text(
            yaml.dump(resume_data), encoding="utf-8"
        )

        story.when("the resume is rendered to HTML")
        html = render_resume_html("font_size_test", paths=paths)
        soup = BeautifulSoup(html, "html.parser")

        story.then(
            "CSS variables are present in the rendered output with custom values"
        )
        # Find the :root style block
        style_blocks = soup.find_all("style")
        root_style = None
        for style in style_blocks:
            if style.string and ":root" in style.string:
                root_style = style.string
                break

        assert root_style is not None, "No :root style block found in HTML"

        # Verify each font size CSS variable
        assert "--sidebar-font-size: 10pt" in root_style, (
            "sidebar_font_size CSS variable not set to 10pt"
        )
        assert "--description-font-size: 9pt" in root_style, (
            "description_font_size CSS variable not set to 9pt"
        )
        assert "--date-font-size: 8pt" in root_style, (
            "date_font_size CSS variable not set to 8pt"
        )


def test_font_size_css_variable_chain_default_fallbacks() -> None:
    """Verify default fallback values when config not specified."""
    story = scenario("font size CSS variable chain with default fallbacks")
    story.given("a resume config without explicit font sizes")

    # Create resume WITHOUT font size config
    resume_data = create_complete_resume_data(
        template="resume_no_bars",
        full_name="Default Font Size User",
    )
    # Ensure font sizes are NOT in the config
    resume_data.pop("sidebar_font_size", None)
    resume_data.pop("description_font_size", None)
    resume_data.pop("date_font_size", None)

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)
        paths = _build_paths(temp_dir)
        (paths.input / "default_font_test.yaml").write_text(
            yaml.dump(resume_data), encoding="utf-8"
        )

        story.when("the resume is rendered to HTML without font size config")
        html = render_resume_html("default_font_test", paths=paths)
        soup = BeautifulSoup(html, "html.parser")

        story.then("CSS variables use default fallback values from Python config")
        style_blocks = soup.find_all("style")
        root_style = None
        for style in style_blocks:
            if style.string and ":root" in style.string:
                root_style = style.string
                break

        assert root_style is not None, "No :root style block found in HTML"

        # Defaults from apply_config_defaults() in config.py:
        # - sidebar_font_size: 8.5
        # - description_font_size: 8.5
        # - date_font_size: 9
        assert "--sidebar-font-size: 8.5pt" in root_style, (
            "sidebar_font_size default not set to 8.5pt"
        )
        assert "--description-font-size: 8.5pt" in root_style, (
            "description_font_size default not set to 8.5pt"
        )
        assert "--date-font-size: 9pt" in root_style, (
            "date_font_size default not set to 9pt"
        )


def test_font_size_css_variables_consumed_by_css() -> None:
    """Verify CSS variables are actually consumed by common.css rules."""
    story = scenario("font size CSS variables are consumed by CSS")
    story.given("a resume with custom font sizes")

    resume_data = _create_resume_with_font_sizes(
        full_name="CSS Consumption Test",
        sidebar_font_size=11,
        description_font_size=10,
        date_font_size=9,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)
        paths = _build_paths(temp_dir)
        (paths.input / "css_consumption_test.yaml").write_text(
            yaml.dump(resume_data), encoding="utf-8"
        )

        story.when("the resume is rendered to HTML")
        html = render_resume_html("css_consumption_test", paths=paths)
        soup = BeautifulSoup(html, "html.parser")

        story.then("common.css rules consume the CSS variables using var()")
        style_blocks = soup.find_all("style")
        common_css = None
        for style in style_blocks:
            if style.string and "font-size: var(--sidebar-font-size" in style.string:
                common_css = style.string
                break

        assert common_css is not None, (
            "common.css not found or doesn't use font size CSS variables"
        )

        # Verify the CSS uses var() with fallback values
        assert "font-size: var(--sidebar-font-size, 8.5pt)" in common_css, (
            "common.css doesn't consume --sidebar-font-size with fallback"
        )
        assert "font-size: var(--description-font-size, 8.5pt)" in common_css, (
            "common.css doesn't consume --description-font-size with fallback"
        )
        assert "font-size: var(--date-font-size, 9pt)" in common_css, (
            "common.css doesn't consume --date-font-size with fallback"
        )
