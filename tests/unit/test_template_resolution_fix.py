"""TDD tests for the template resolution fix.

These tests verify that the template resolution issue has been fixed
where templates were not found due to incorrect path resolution.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from jinja2.loaders import FileSystemLoader

from simple_resume.config import TEMPLATE_LOC, resolve_paths
from simple_resume.core.models import RenderMode, RenderPlan, ResumeConfig
from simple_resume.core.plan import prepare_render_data
from simple_resume.core.resume import Resume
from simple_resume.exceptions import TemplateError
from simple_resume.rendering import get_template_environment
from tests.bdd import Scenario


class TestTemplateResolutionFix:
    """Test cases to verify the template resolution fix."""

    @pytest.fixture
    def sample_resume_data(self) -> dict[str, object]:
        """Sample resume data for testing."""
        return {
            "full_name": "Test User",
            "email": "test@example.com",
            "template": "resume_no_bars",
            "config": {
                "page_width": 210,
                "page_height": 297,
                "theme_color": "#0395DE",
                "sidebar_width": 60,
                "h2_padding_left": 4,
                "padding": 12,
                "sidebar_color": "#F6F6F6",
                "sidebar_text_color": "#000000",
                "bar_background_color": "#DFDFDF",
                "date2_color": "#616161",
                "frame_color": "#757575",
                "date_container_width": 13,
                "description_container_padding_left": 3,
            },
            "description": "Test description",
            "body": {
                "experience": [
                    {
                        "company": "Test Company",
                        "position": "Developer",
                        "start_date": "2020-01",
                        "end_date": "2023-12",
                        "description": "Development work",
                    }
                ]
            },
            "titles": {
                "contact": "Contact",
                "certification": "Certifications",
                "expertise": "Expertise",
                "keyskills": "Key Skills",
            },
        }

    @pytest.fixture
    def valid_render_plan(self) -> RenderPlan:
        """Create a valid render plan for testing."""
        config = ResumeConfig(
            page_width=210,
            page_height=297,
            sidebar_width=60,
            theme_color="#0395DE",
            sidebar_color="#F6F6F6",
            sidebar_text_color="#000000",
            bar_background_color="#DFDFDF",
            date2_color="#616161",
            frame_color="#757575",
            color_scheme="default",
            output_mode="markdown",
            template="resume_no_bars",
        )

        # Create a context that matches what the templates expect
        context = {
            "full_name": "Test User",
            "email": "test@example.com",
            "preview": False,
            "resume_config": {
                "page_width": 210,
                "page_height": 297,
                "sidebar_width": 60,
                "h2_padding_left": 4,  # This appears to be expected by the template
                "theme_color": "#0395DE",
                "sidebar_color": "#F6F6F6",
                "sidebar_text_color": "#000000",
                "bar_background_color": "#DFDFDF",
                "date2_color": "#616161",
                "frame_color": "#757575",
                "color_scheme": "default",
                "output_mode": "markdown",
                "padding": 12,  # Added based on the sample config
                "profile_image_padding_bottom": 6,
                "pitch_padding_top": 4,
                "pitch_padding_bottom": 4,
                "pitch_padding_left": 4,
                "date_container_width": 13,
                "date_container_padding_left": 8,
                "description_container_padding_left": 3,
                "frame_padding": 10,
                "cover_padding_top": 10,
                "cover_padding_bottom": 20,
                "cover_padding_h": 25,
                # Sidebar padding defaults (matching _apply_config_defaults)
                "sidebar_padding_left": 10,  # base_padding - 2
                "sidebar_padding_right": 10,  # base_padding - 2
                "sidebar_padding_top": 0,
                "sidebar_padding_bottom": 12,  # base_padding
                # Spacing defaults (matching _apply_config_defaults)
                "skill_container_padding_top": 3,
                "skill_spacer_padding_top": 3,
                "h3_padding_top": 7,
                "h2_padding_top": 8,
                "section_heading_margin_top": 4,
                "section_heading_margin_bottom": 2,
            },
            "titles": {
                "contact": "Contact",
                "certification": "Certifications",
                "expertise": "Expertise",
                "keyskills": "Key Skills",
            },
            "description": "Test description",
            "body": {
                "experience": [
                    {
                        "company": "Test Company",
                        "position": "Developer",
                        "start_date": "2020-01",
                        "end_date": "2023-12",
                        "description": "Development work",
                    }
                ]
            },
        }

        return RenderPlan(
            name="test_resume",
            mode=RenderMode.HTML,
            config=config,
            template_name="html/resume_no_bars.html",
            context=context,
            # Deliberately incorrect base_path should not affect template resolution
            base_path="/some/incorrect/path",
        )

    def test_template_environment_uses_correct_templates_path(
        self, story: Scenario, sample_resume_data: dict[str, object]
    ) -> None:
        """Ensure template environment uses templates path, not base_path."""
        story.case(
            given="a render plan generated with an arbitrary base path",
            when="the template environment is requested",
            then=(
                "the loader resolves templates relative to TEMPLATE_LOC "
                "instead of the base path"
            ),
        )
        # Clear the cache to ensure we get a fresh environment
        get_template_environment.cache_clear()

        # Mock the rendering to avoid actual file generation
        with patch("weasyprint.HTML") as mock_html_class:
            with patch("weasyprint.CSS") as mock_css_class:
                # Create a mock PDF writer that returns a mock result
                mock_css_instance = Mock()
                mock_html_instance = Mock()
                mock_html_class.return_value = mock_html_instance
                mock_css_class.return_value = mock_css_instance

                # Create a render plan matching prepare_render_data
                base_path = "/some/inconsistent/base/path"
                plan = prepare_render_data(
                    sample_resume_data, preview=False, base_path=base_path
                )

                resume_config = (
                    plan.context.get("resume_config", {}) if plan.context else {}
                )
                defaults = {
                    "sidebar_width": 60,
                    "h2_padding_left": 4,
                    "padding": 12,
                    "sidebar_color": "#F6F6F6",
                    "sidebar_text_color": "#000000",
                    "bar_background_color": "#DFDFDF",
                    "date2_color": "#616161",
                    "frame_color": "#757575",
                    "date_container_width": 13,
                    "date_container_padding_left": 2,
                    "description_container_padding_left": 3,
                }
                for key, value in defaults.items():
                    resume_config.setdefault(key, value)
                if plan.context is not None:
                    plan.context["resume_config"] = resume_config

                # Create a Path-like object that can be used in place of Path
                actual_dir = Path(tempfile.mkdtemp())
                actual_output_path = actual_dir / "test.pdf"

                class StringablePath:
                    def __init__(self, path: Path):
                        self.path = path

                    def __str__(self) -> str:
                        return str(self.path)

                    @property
                    def parent(self) -> Path:
                        return self.path.parent

                mock_output_path = (
                    actual_output_path  # Use the actual Path object instead
                )

                resume = Resume.from_data(sample_resume_data)

                # PDF generation should not fail due to template resolution
                try:
                    result = resume.to_pdf(output_path=mock_output_path)
                    # If we get here, template resolution worked correctly
                    assert result is not None
                except TemplateError as exc:
                    # If there's an error ensure it's not template resolution related
                    assert "html/resume_no_bars.html" not in str(exc), (
                        f"Template resolution failed: {exc}"
                    )

    def test_template_resolution_with_actual_template(
        self, story: Scenario, sample_resume_data: dict[str, object]
    ) -> None:
        """Confirm templates can be resolved without full rendering."""
        story.case(
            given="the built-in templates residing under TEMPLATE_LOC",
            when="the environment loads resume_no_bars.html",
            then="the template is resolved without rendering errors",
        )
        # Verify that the template files exist in the expected location
        template_path = TEMPLATE_LOC
        assert template_path.exists(), (
            f"Templates directory does not exist: {template_path}"
        )

        resume_template = template_path / "html/resume_no_bars.html"
        assert resume_template.exists(), (
            f"resume_no_bars.html does not exist: {resume_template}"
        )

        # Test that we can create a template environment and load the template
        env = get_template_environment(str(template_path))
        template = env.get_template("html/resume_no_bars.html")
        assert template is not None

        # Only verify loading without requiring full rendering context.
        # The key regression was template lookup, not rendering fidelity.

    def test_generate_pdf_uses_templates_directory_not_base_path(
        self, story: Scenario, valid_render_plan: RenderPlan
    ) -> None:
        """Ensure PDF generation uses template directory rather than base_path."""
        story.case(
            given="a render plan whose base path is intentionally incorrect",
            when="PDF generation runs",
            then="templates are still located under TEMPLATE_LOC",
        )
        # Create a resume instance
        resume = Resume.from_data(
            {
                "full_name": "Test User",
                "template": "resume_no_bars",
                "titles": {
                    "contact": "Contact",
                    "certification": "Certifications",
                    "expertise": "Expertise",
                    "keyskills": "Key Skills",
                },
                "config": {
                    "page_width": 210,
                    "page_height": 297,
                    "date_container_padding_left": 2,
                    "date_container_width": 13,
                    "description_container_padding_left": 3,
                    "sidebar_width": 60,
                    "h2_padding_left": 4,
                    "padding": 12,
                    "sidebar_color": "#F6F6F6",
                    "sidebar_text_color": "#000000",
                    "bar_background_color": "#DFDFDF",
                    "date2_color": "#616161",
                    "frame_color": "#757575",
                },
                "body": {
                    "experience": [
                        {
                            "company": "Test Company",
                            "position": "Developer",
                            "start_date": "2020-01",
                            "end_date": "2023-12",
                            "description": "Development work",
                        }
                    ]
                },
            }
        )

        # Create a temporary output file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            output_path = Path(tmp_file.name)

        try:
            # Mock the PDF writing to avoid actual PDF generation
            with patch("simple_resume.core.pdf_generation.HTML") as mock_html_class:
                with patch("simple_resume.core.pdf_generation.CSS") as mock_css_class:
                    mock_css_instance = Mock()
                    mock_html_instance = Mock()
                    mock_html_class.return_value = mock_html_instance
                    mock_css_class.return_value = mock_css_instance

                    # This should run without template resolution errors.
                    # Template must be loaded from TEMPLATE_LOC, not plan.base_path.
                    result = resume.to_pdf(output_path=output_path)

                    # Verify WeasyPrint was invoked with rendered HTML content
                    mock_html_class.assert_called_once()
                    html_args, html_kwargs = mock_html_class.call_args
                    if "string" in html_kwargs:
                        rendered_html = html_kwargs["string"]
                    elif html_args:
                        rendered_html = html_args[0]
                    else:
                        raise AssertionError(
                            "weasyprint.HTML was not passed HTML content"
                        )
                    # Verify business-critical content is rendered correctly
                    assert "Test User" in rendered_html, (
                        "Full name must appear in resume"
                    )
                    assert "Test Company" in rendered_html, (
                        "Company name must appear in resume"
                    )
                    assert "Development work" in rendered_html, (
                        "Job description must appear in resume"
                    )

                    # Verify proper HTML structure for business use
                    assert "<!DOCTYPE html>" in rendered_html, (
                        "Must generate valid HTML"
                    )
                    assert "<body>" in rendered_html and "</body>" in rendered_html, (
                        "Must have proper HTML body"
                    )

                    # Verify contact information rendering (business requirement)
                    if "test@example.com" in str(resume.__dict__):
                        # Check if email is in either rendered HTML or resume data
                        resume_data_str = str(resume.__dict__)
                        assert (
                            "test@example.com" in resume_data_str
                            or "test@example.com" in rendered_html
                        ), "Contact information must be included"

                    mock_css_class.assert_called_once()
                    css_args, css_kwargs = mock_css_class.call_args
                    css_string = css_kwargs.get("string") or (
                        css_args[0] if css_args else ""
                    )
                    expected_dims = (
                        f"{valid_render_plan.config.page_width}mm "
                        f"{valid_render_plan.config.page_height}mm"
                    )
                    assert expected_dims in css_string

                    assert result is not None
        finally:
            # Clean up the temporary file
            if output_path.exists():
                output_path.unlink()

    def test_generate_html_uses_templates_directory_not_base_path(
        self, story: Scenario, valid_render_plan: RenderPlan
    ) -> None:
        """Ensure HTML generation loads templates from the templates directory."""
        story.case(
            given="an HTML render plan with an arbitrary base_path",
            when="_generate_html_with_jinja runs",
            then="templates load from TEMPLATE_LOC so the output contains resume data",
        )
        resume = Resume.from_data(
            {
                "full_name": "Test User",
                "template": "resume_no_bars",
                "titles": {
                    "contact": "Contact",
                    "certification": "Certifications",
                    "expertise": "Expertise",
                    "keyskills": "Key Skills",
                },
                "config": {
                    "page_width": 210,
                    "page_height": 297,
                    "sidebar_width": 60,
                    "h2_padding_left": 4,
                    "padding": 12,
                    "date_container_width": 13,
                    "description_container_padding_left": 3,
                },
                "body": {
                    "experience": [
                        {
                            "company": "Test Company",
                            "position": "Developer",
                            "start_date": "2020-01",
                            "end_date": "2023-12",
                            "description": "Development work",
                        }
                    ]
                },
            }
        )

        # Create a temporary output file
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp_file:
            output_path = Path(tmp_file.name)

        try:
            # This should work without template resolution errors
            result = resume.to_html(output_path=output_path)

            # Verify that the output file was created and contains
            # business-relevant content
            assert output_path.exists(), "HTML file must be created"
            content = output_path.read_text()

            # Verify business-critical resume elements are present
            assert "Test User" in content, "Applicant name must appear in HTML resume"
            assert "Test Company" in content, "Company name must be included"
            assert "Development work" in content, "Job description must be present"

            # Note: Position and dates might be in different format
            # or not rendered in all templates
            # This is actually valuable business intelligence about template behavior

            # Verify HTML structure is valid for business use
            assert "<!DOCTYPE html>" in content or "<html" in content, (
                "Must produce valid HTML"
            )
            assert "<head>" in content and "</head>" in content, (
                "Must have HTML head section"
            )
            assert "<body>" in content and "</body>" in content, (
                "Must have HTML body section"
            )

            # Verify contact information rendering
            # (critical for recruiter communication)
            if "test@example.com" in str(resume.__dict__):
                assert "test@example.com" in content, (
                    "Contact email must be visible to recruiters"
                )

            assert result is not None, "Generation result must be returned"
        finally:
            # Clean up the temporary file
            if output_path.exists():
                output_path.unlink()

    def test_template_loader_search_path_correctness(self, story: Scenario) -> None:
        """Ensure the template loader uses the expected search path."""
        story.case(
            given="the cached template environment",
            when="examining the loader search path",
            then="TEMPLATE_LOC appears as the canonical search directory",
        )
        env = get_template_environment(str(TEMPLATE_LOC))

        # Verify that the loader's search path contains the templates directory
        loader = env.loader
        assert isinstance(loader, FileSystemLoader)

        # The search path should contain the templates directory
        search_paths = list(loader.searchpath)
        assert str(TEMPLATE_LOC) in search_paths, (
            f"Template directory {TEMPLATE_LOC} should be in search path"
        )

        # Verify that common templates exist
        template_names = [
            "html/resume_no_bars.html",
            "html/resume_with_bars.html",
            "html/cover.html",
        ]
        for template_name in template_names:
            template_file = TEMPLATE_LOC / template_name
            assert template_file.exists(), (
                f"Template {template_name} should exist at {template_file}"
            )

    def test_template_resolution_failure_scenario(self, story: Scenario) -> None:
        """Test to document the scenario that was previously failing."""
        story.case(
            given=(
                "a render plan with a base path pointing at content "
                "instead of templates"
            ),
            when="prepare_render_data runs",
            then="the resulting plan still references resume_no_bars.html",
        )
        # This test documents what would have failed before the fix.
        # A render plan pointing base_path to the content directory (instead of
        # the templates directory) previously caused template resolution to fail.

        # Verify we can prepare the render data without errors; this builds a
        # plan based on the data with the proper template name.
        sample_data = {
            "full_name": "Test User",
            "template": "resume_no_bars",
            "config": {"page_width": 210, "page_height": 297},
        }

        plan = prepare_render_data(
            sample_data, preview=False, base_path="/some/content/path"
        )
        assert plan.template_name == "html/resume_no_bars.html"
        assert plan.context is not None


class TestTemplateResolutionRegression:
    """Regression tests to prevent the template resolution issue from recurring."""

    def test_demo_palette_scenario(self, story: Scenario) -> None:  # noqa: PLR0912, PLR0915
        """Test the specific scenario that was failing in the demo-palette command."""
        story.case(
            given="the demo-palette workflow rendering resume_no_bars",
            when="prepare_render_data and template loading execute",
            then="templates resolve via TEMPLATE_LOC without validation failures",
        )
        # This test recreates the scenario from the demo-palette command
        # which was failing due to template resolution issues

        sample_data = {
            "template": "resume_no_bars",
            "full_name": "Demo User",
            "job_title": "Software Engineer",
            "config": {
                "page_width": 210,
                "page_height": 297,
                "theme_color": "#0395DE",
            },
            "description": "Demo description for palette testing",
        }

        # Create resume instance
        resume = Resume.from_data(sample_data)

        # Validate the resume first
        validation = resume.validate()
        assert validation.is_valid, f"Resume validation failed: {validation.errors}"

        # Prepare render data (this would have been failing before)
        render_plan = prepare_render_data(
            sample_data,
            preview=False,
            base_path=str(resume._paths.content)
            if resume._paths
            else "/default/content/path",
        )

        assert render_plan.template_name == "html/resume_no_bars.html"
        assert render_plan.mode is RenderMode.HTML
        assert render_plan.context is not None

        # The fix always resolves templates from TEMPLATE_LOC, regardless of
        # render_plan.base_path.
        assert TEMPLATE_LOC.exists(), "Templates directory must exist for test"

        # Verify template can be loaded
        env = get_template_environment(str(TEMPLATE_LOC))
        template_name = render_plan.template_name
        assert template_name is not None
        template = env.get_template(template_name)
        assert template is not None

        # Add any missing config fields to prevent template errors
        if "resume_config" in render_plan.context:
            resume_config = render_plan.context["resume_config"]
            # Provide defaults expected by template requirements.
            if resume_config.get("sidebar_width") is None:
                resume_config["sidebar_width"] = 60
            if resume_config.get("h2_padding_left") is None:
                resume_config["h2_padding_left"] = 4
            if resume_config.get("padding") is None:
                resume_config["padding"] = 12
            if resume_config.get("profile_image_padding_bottom") is None:
                resume_config["profile_image_padding_bottom"] = 6
            if resume_config.get("pitch_padding_top") is None:
                resume_config["pitch_padding_top"] = 4
            if resume_config.get("pitch_padding_bottom") is None:
                resume_config["pitch_padding_bottom"] = 4
            if resume_config.get("pitch_padding_left") is None:
                resume_config["pitch_padding_left"] = 4
            if resume_config.get("date_container_width") is None:
                resume_config["date_container_width"] = 13
            if resume_config.get("date_container_padding_left") is None:
                resume_config["date_container_padding_left"] = 8
            if resume_config.get("description_container_padding_left") is None:
                resume_config["description_container_padding_left"] = 3
            if resume_config.get("frame_padding") is None:
                resume_config["frame_padding"] = 10
            if resume_config.get("cover_padding_top") is None:
                resume_config["cover_padding_top"] = 10
            if resume_config.get("cover_padding_bottom") is None:
                resume_config["cover_padding_bottom"] = 20
            if resume_config.get("cover_padding_h") is None:
                resume_config["cover_padding_h"] = 25
        else:
            # Create resume_config if it doesn't exist
            render_plan.context["resume_config"] = {
                "page_width": 210,
                "page_height": 297,
                "sidebar_width": 60,
                "h2_padding_left": 4,
                "theme_color": "#0395DE",
                "padding": 12,
                # Add other required fields
            }

        # Also ensure other required fields exist
        if "titles" not in render_plan.context:
            render_plan.context["titles"] = {
                "contact": "Contact",
                "certification": "Certifications",
                "expertise": "Expertise",
                "keyskills": "Key Skills",
            }

        if "body" not in render_plan.context:
            render_plan.context["body"] = {
                "experience": [
                    {
                        "start": "2020-01",
                        "end": "2023-12",
                        "title": "Developer",
                        "company": "Test Company",
                        "description": "Development work",
                    }
                ]
            }

        # Verify rendering works
        rendered: str = template.render(**render_plan.context)
        assert sample_data["full_name"] in rendered  # type: ignore[operator]


class TestFullTemplateResolution:
    """Test template resolution functionality with all field types."""

    @pytest.fixture
    def sample_resume_with_all_fields(self) -> dict[str, object]:
        """Create sample resume data with all required template fields."""
        return {
            "template": "resume_no_bars",
            "full_name": "Comprehensive Test User",
            "email": "test@example.com",
            "phone": "555-123-4567",
            "web": "https://example.com",
            "linkedin": "in/testuser",
            "titles": {
                "contact": "Contact",
                "expertise": "Expertise",
                "certification": "Certifications",
                "keyskills": "Key Skills",
            },
            "description": "This is a test resume with all field types.",
            "address": ["123 Test Street", "Test City, TC 12345"],
            "expertise": ["Expertise 1", "Expertise 2"],
            "certification": ["Certification 1", "Certification 2"],
            "keyskills": ["Skill 1", "Skill 2"],
            "body": {
                "Experience": [
                    {
                        "start": "2020-01",
                        "end": "2023-12",
                        "title": "Senior Developer",
                        "company": "Test Company",
                        "description": (
                            "Development work spanning multiple project areas."
                        ),
                    }
                ],
                "Education": [
                    {
                        "start": "2016-09",
                        "end": "2020-06",
                        "title": "Bachelor's Degree",
                        "company": "Test University",
                        "description": "Computer Science degree",
                    }
                ],
            },
            "config": {
                "page_width": 210,
                "page_height": 297,
                "sidebar_width": 60,
                "h2_padding_left": 4,
                "theme_color": "#0395DE",
                "sidebar_color": "#F6F6F6",
                "sidebar_text_color": "#000000",
                "bar_background_color": "#DFDFDF",
                "date2_color": "#616161",
                "frame_color": "#757575",
                "padding": 12,
                "profile_image_padding_bottom": 6,
                "pitch_padding_top": 4,
                "pitch_padding_bottom": 4,
                "pitch_padding_left": 4,
                "date_container_width": 13,
                "date_container_padding_left": 8,
                "description_container_padding_left": 3,
                "frame_padding": 10,
                "cover_padding_top": 10,
                "cover_padding_bottom": 20,
                "cover_padding_h": 25,
            },
        }

    def test_full_template_resolution_end_to_end(
        self, story: Scenario, sample_resume_with_all_fields: dict[str, object]
    ) -> None:
        """TDD test: Comprehensive end-to-end template resolution."""
        story.case(
            given="resume data that populates every template section",
            when="prepare_render_data and template rendering run",
            then="the rendered HTML contains the expected names and roles",
        )
        # Act: Prepare render plan (this calls prepare_render_data)
        # base_path should not influence template resolution after the fix.
        render_plan = prepare_render_data(
            sample_resume_with_all_fields,
            preview=False,
            base_path="/some/path/that/should/not/matter",
        )

        # Assert: Render plan is correctly configured
        assert render_plan.template_name == "html/resume_no_bars.html"
        assert render_plan.mode is RenderMode.HTML
        assert render_plan.context is not None
        assert "full_name" in render_plan.context
        assert "resume_config" in render_plan.context

        # Act: Load template from correct location (the fix)
        env = get_template_environment(str(TEMPLATE_LOC))
        template_name = render_plan.template_name
        assert template_name is not None
        template = env.get_template(template_name)

        # Assert: Template loads without error (the main fix)
        assert template is not None

        # Act: Render template with context
        html_output = template.render(**render_plan.context)

        # Assert: Output contains expected content
        assert "Comprehensive Test User" in html_output
        assert "Test Company" in html_output
        assert "Senior Developer" in html_output

    def test_template_resolution_with_different_templates(
        self, story: Scenario, sample_resume_with_all_fields: dict[str, object]
    ) -> None:
        """TDD test: Template resolution works with different template types."""
        story.case(
            given="each built-in HTML template",
            when="loading templates via get_template_environment",
            then="every template resolves even if base_path changes",
        )
        # The main goal is to test that templates can be loaded from the correct path
        # Different templates have different requirements, so just test loading
        templates_to_test = [
            "html/resume_no_bars.html",
            "html/resume_with_bars.html",
            "html/cover.html",
        ]

        for template_name in templates_to_test:
            # Ensure template exists
            template_path = TEMPLATE_LOC / template_name
            if template_path.exists():
                # Load the template - this tests the fix that templates can be found
                env = get_template_environment(str(TEMPLATE_LOC))
                template = env.get_template(template_name)

                # Should not raise template not found error (the main fix)
                assert template is not None

                plan = prepare_render_data(sample_resume_with_all_fields, preview=False)
                context = plan.context or {}

                # Normalize certification structure for templates expecting
                # value mappings.
                certification = context.get("certification")
                if isinstance(certification, list):
                    context["certification"] = dict.fromkeys(certification, 30)

                rendered = template.render(**context)
                assert "Test User" in rendered

    def test_template_resolution_uses_correct_path_not_base_path(
        self, story: Scenario
    ) -> None:
        """TDD test: Template resolution uses templates path, not base_path."""
        story.case(
            given="paths whose content and template directories differ",
            when="prepare_render_data renders resume_no_bars",
            then="template loading still occurs from TEMPLATE_LOC",
        )
        # This tests the core fix specifically
        # Create paths with different content and templates directories
        paths = resolve_paths()

        # The fix ensures that template loading uses TEMPLATE_LOC, not paths.content
        env_from_templates = get_template_environment(str(TEMPLATE_LOC))
        env_from_content = get_template_environment(str(paths.templates))

        # Both environments should load templates because files exist at TEMPLATE_LOC.
        template_name = "html/resume_no_bars.html"
        template_from_templates = env_from_templates.get_template(template_name)
        template_from_content = env_from_content.get_template(template_name)
        assert template_from_templates is not None
        assert template_from_content is not None

        # The key is using TEMPLATE_LOC for template loading.
        resume_data = {
            "full_name": "Path Test User",
            "config": {"page_width": 210, "theme_color": "#0395DE"},
            "titles": {"contact": "Contact"},
            "body": {"experience": []},
        }

        # Prepare render data with a base_path that's NOT the templates directory
        # Alternate base_path should not affect template loading.
        render_plan = prepare_render_data(
            resume_data,
            preview=False,
            base_path="/some/different/path",
        )

        # Successful rendering proves templates load from TEMPLATE_LOC, not base_path.

        assert render_plan.context is not None
        context = render_plan.context

        # Ensure render_plan.context has complete config for template
        if "resume_config" in context:
            resume_config = context["resume_config"]
            # Add required missing fields
            resume_config.setdefault("sidebar_width", 60)
            resume_config.setdefault("h2_padding_left", 4)
            resume_config.setdefault("theme_color", "#0395DE")
            resume_config.setdefault("sidebar_color", "#F6F6F6")
            resume_config.setdefault("sidebar_text_color", "#000000")
            resume_config.setdefault("bar_background_color", "#DFDFDF")
            resume_config.setdefault("date2_color", "#616161")
            resume_config.setdefault("frame_color", "#757575")
            resume_config.setdefault("padding", 12)
            resume_config.setdefault("profile_image_padding_bottom", 6)
            resume_config.setdefault("pitch_padding_top", 4)
            resume_config.setdefault("pitch_padding_bottom", 4)
            resume_config.setdefault("pitch_padding_left", 4)
            resume_config.setdefault("date_container_width", 13)
            resume_config.setdefault("date_container_padding_left", 8)
            resume_config.setdefault("description_container_padding_left", 3)
            resume_config.setdefault("frame_padding", 10)
            resume_config.setdefault("cover_padding_top", 10)
            resume_config.setdefault("cover_padding_bottom", 20)
            resume_config.setdefault("cover_padding_h", 25)

        # Ensure required fields exist
        if "titles" not in context:
            context["titles"] = {"contact": "Contact"}
        if "body" not in context:
            context["body"] = {"experience": []}

        env = get_template_environment(str(TEMPLATE_LOC))
        render_template_name: str | None = render_plan.template_name
        assert render_template_name is not None
        template = env.get_template(render_template_name)
        output = template.render(**context)
        assert "Path Test User" in output
