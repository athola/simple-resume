"""Tests for pure HTML generation logic (core layer).

Following TDD principles - these tests are written BEFORE implementation.
Tests verify that HTML generation logic is pure and returns effects instead
of performing I/O.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import pytest

from simple_resume.core.constants import RenderMode
from simple_resume.core.effects import MakeDirectory, WriteFile
from simple_resume.core.generate.exceptions import TemplateError
from simple_resume.core.generate.html import (
    create_html_generator_factory,
)
from simple_resume.core.models import RenderPlan, ResumeConfig
from simple_resume.core.protocols import TemplateLocator
from simple_resume.shell.config import TEMPLATE_LOC
from tests.bdd import Scenario


class TestPrepareHtmlWithJinja:
    """Tests for prepare_html_with_jinja - pure logic without I/O."""

    def test_returns_html_content_effects_and_metadata(self, story: Scenario) -> None:
        """prepare_html_with_jinja returns (html_content, effects, metadata)."""
        story.given("a render plan targeting HTML output")
        story.when("preparing HTML using the generator factory")
        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test_resume",
                mode=RenderMode.HTML,
                template_name="demo.html",
                context={"name": "Test User", "title": "Engineer"},
                config=ResumeConfig(),
                base_path=temp_dir,
            )
            output_path = Path(temp_dir) / "output" / "resume.html"

            # Create a mock template locator for testing
            mock_locator = MagicMock(spec=TemplateLocator)
            mock_locator.get_template_location.return_value = Path(temp_dir)

            with patch(
                "simple_resume.core.generate.html.get_template_environment"
            ) as mock_env:
                # Setup mock template environment and template
                mock_template_env = MagicMock()
                mock_template = MagicMock()
                mock_template.render.return_value = (
                    "<html><body>Test rendered content</body></html>"
                )
                mock_template_env.get_template.return_value = mock_template
                mock_env.return_value = mock_template_env

                factory = create_html_generator_factory(
                    default_template_locator=mock_locator
                )
                prepare_html_func = factory.create_prepare_html_function()
                html_content, effects, metadata = prepare_html_func(
                    render_plan=render_plan,
                    output_path=output_path,
                    resume_name="test_resume",
                    filename="resume.yaml",
                    template_locator=mock_locator,
                )

            # Should return HTML content (string)
            assert isinstance(html_content, str)
            assert len(html_content) > 0
            assert "<html" in html_content or "<HTML" in html_content

            # Should return list of effects
            assert isinstance(effects, list)
            assert len(effects) > 0

            # Should return metadata
            assert metadata is not None
            assert metadata.format_type == "html"
            assert metadata.template_name == "demo.html"

    def test_includes_make_directory_effect(self, story: Scenario) -> None:
        """prepare_html_with_jinja includes MakeDirectory effect for output dir."""
        story.given("an output path nested within directories")
        story.when("preparing HTML generation effects")
        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.HTML,
                template_name="demo.html",
                context={"name": "Test"},
                config=ResumeConfig(),
                base_path=temp_dir,
            )
            output_path = Path(temp_dir) / "nested/dirs/resume.html"

            # Create a mock template locator for testing
            mock_locator = MagicMock(spec=TemplateLocator)
            mock_locator.get_template_location.return_value = Path(temp_dir)

            with patch(
                "simple_resume.core.generate.html.get_template_environment"
            ) as mock_env:
                # Setup mock template environment and template
                mock_template_env = MagicMock()
                mock_template = MagicMock()
                mock_template.render.return_value = (
                    "<html><body>Test content</body></html>"
                )
                mock_template_env.get_template.return_value = mock_template
                mock_env.return_value = mock_template_env

                factory = create_html_generator_factory(
                    default_template_locator=mock_locator
                )
                prepare_html_func = factory.create_prepare_html_function()
                _, effects, _ = prepare_html_func(
                    render_plan=render_plan,
                    output_path=output_path,
                    resume_name="test_resume",
                    template_locator=mock_locator,
                )

            # Should include MakeDirectory effect for parent directory
            make_dir_effects = [e for e in effects if isinstance(e, MakeDirectory)]
            assert len(make_dir_effects) == 1
            assert make_dir_effects[0].path == output_path.parent
            assert make_dir_effects[0].parents is True

    def test_includes_write_file_effect_for_html(self, story: Scenario) -> None:
        """prepare_html_with_jinja includes WriteFile effect for HTML output."""
        story.given("a render plan for HTML output")
        story.when("building effects for HTML generation")
        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.HTML,
                template_name="demo.html",
                context={"name": "Test"},
                config=ResumeConfig(),
                base_path=temp_dir,
            )
            output_path = Path(temp_dir) / "resume.html"

            # Create a mock template locator for testing
            mock_locator = MagicMock(spec=TemplateLocator)
            mock_locator.get_template_location.return_value = Path(temp_dir)

            with patch(
                "simple_resume.core.generate.html.get_template_environment"
            ) as mock_env:
                # Setup mock template environment and template
                mock_template_env = MagicMock()
                mock_template = MagicMock()
                mock_template.render.return_value = (
                    "<html><body>Test content</body></html>"
                )
                mock_template_env.get_template.return_value = mock_template
                mock_env.return_value = mock_template_env

                factory = create_html_generator_factory(
                    default_template_locator=mock_locator
                )
                prepare_html_func = factory.create_prepare_html_function()
                _, effects, _ = prepare_html_func(
                    render_plan=render_plan,
                    output_path=output_path,
                    resume_name="test_resume",
                    template_locator=mock_locator,
                )

            # Should include WriteFile effect for HTML
            write_effects = [e for e in effects if isinstance(e, WriteFile)]
            html_write_effects = [e for e in write_effects if e.path == output_path]
            assert len(html_write_effects) == 1
            assert isinstance(
                html_write_effects[0].content, str
            )  # HTML content is string

    def test_html_does_not_include_base_tag(self, story: Scenario) -> None:
        """prepare_html_with_jinja does NOT include base tag - assets copied instead."""
        story.given("a base path is specified in the render plan")
        story.when("rendering HTML content")
        with TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "base"
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.HTML,
                template_name="demo.html",
                context={"name": "Test"},
                config=ResumeConfig(),
                base_path=str(base_path),
            )
            output_path = Path(temp_dir) / "resume.html"

            # Create a mock template locator for testing
            mock_locator = MagicMock(spec=TemplateLocator)
            mock_locator.get_template_location.return_value = Path(temp_dir)

            with patch(
                "simple_resume.core.generate.html.get_template_environment"
            ) as mock_env:
                # Setup mock template environment and template
                mock_template_env = MagicMock()
                mock_template = MagicMock()
                mock_template.render.return_value = (
                    "<html><head></head><body>Test content</body></html>"
                )
                mock_template_env.get_template.return_value = mock_template
                mock_env.return_value = mock_template_env

                factory = create_html_generator_factory(
                    default_template_locator=mock_locator
                )
                prepare_html_func = factory.create_prepare_html_function()
                html_content, _, _ = prepare_html_func(
                    render_plan=render_plan,
                    output_path=output_path,
                    resume_name="test_resume",
                    template_locator=mock_locator,
                )

            # Should NOT include base tag - shell layer copies assets to output dir
            assert "<base href=" not in html_content
            # Should return rendered HTML as-is
            assert "Test content" in html_content

    def test_html_without_head_preserved_as_is(self, story: Scenario) -> None:
        """prepare_html_with_jinja preserves HTML without modifications."""
        story.given("a template without a head element")
        story.when("rendering HTML")
        with TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "base"
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.HTML,
                template_name="demo.html",
                context={"name": "Test"},
                config=ResumeConfig(),
                base_path=str(base_path),
            )
            output_path = Path(temp_dir) / "resume.html"

            # Create a mock template locator for testing
            mock_locator = MagicMock(spec=TemplateLocator)
            mock_locator.get_template_location.return_value = Path(temp_dir)

            with patch(
                "simple_resume.core.generate.html.get_template_environment"
            ) as mock_env:
                # Setup mock template environment and template
                mock_template_env = MagicMock()
                mock_template = MagicMock()
                mock_template.render.return_value = (
                    "<html><body>No head tag</body></html>"
                )
                mock_template_env.get_template.return_value = mock_template
                mock_env.return_value = mock_template_env

                factory = create_html_generator_factory(
                    default_template_locator=mock_locator
                )
                prepare_html_func = factory.create_prepare_html_function()
                html_content, _, _ = prepare_html_func(
                    render_plan=render_plan,
                    output_path=output_path,
                    resume_name="test_resume",
                    template_locator=mock_locator,
                )

            # HTML should be preserved as-is (no base tag injection)
            assert "<base href=" not in html_content
            assert "No head tag" in html_content
            assert html_content.startswith("<html>")

    def test_raises_template_error_for_latex_mode(self, story: Scenario) -> None:
        """prepare_html_with_jinja raises error when render plan uses LaTeX mode."""
        story.given("a render plan configured for LaTeX mode")
        story.when("attempting to prepare HTML")
        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.LATEX,
                template_name="resume.tex",
                context={},
                config=ResumeConfig(),
                base_path=temp_dir,
            )
            output_path = Path(temp_dir) / "resume.html"

            factory = create_html_generator_factory()
            prepare_html_func = factory.create_prepare_html_function()
            with pytest.raises(TemplateError, match="LaTeX mode not supported"):
                prepare_html_func(
                    render_plan=render_plan,
                    output_path=output_path,
                    resume_name="test_resume",
                )

    def test_raises_template_error_when_context_missing(self, story: Scenario) -> None:
        """prepare_html_with_jinja raises error when context is None."""
        story.given("a render plan missing context data")
        story.when("preparing HTML output")
        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.HTML,
                template_name="demo.html",
                context=None,  # Missing context
                config=ResumeConfig(),
                base_path=temp_dir,
            )
            output_path = Path(temp_dir) / "resume.html"

            factory = create_html_generator_factory()
            prepare_html_func = factory.create_prepare_html_function()
            with pytest.raises(TemplateError, match="missing context"):
                prepare_html_func(
                    render_plan=render_plan,
                    output_path=output_path,
                    resume_name="test_resume",
                )

    def test_raises_template_error_when_template_name_missing(
        self, story: Scenario
    ) -> None:
        """prepare_html_with_jinja raises error when template_name is None."""
        story.given("a render plan with no template name provided")
        story.when("preparing HTML output")
        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.HTML,
                template_name=None,  # Missing template
                context={"name": "Test"},
                config=ResumeConfig(),
                base_path=temp_dir,
            )
            output_path = Path(temp_dir) / "resume.html"

        factory = create_html_generator_factory()
        prepare_html_func = factory.create_prepare_html_function()
        with pytest.raises(TemplateError, match="missing.*template"):
            prepare_html_func(
                render_plan=render_plan,
                output_path=output_path,
                resume_name="test_resume",
            )

    def test_no_io_operations_performed(self, story: Scenario) -> None:
        """prepare_html_with_jinja performs NO I/O operations (critical test)."""
        story.given("HTML preparation is pure and should emit effects only")
        story.when("running prepare_html")
        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.HTML,
                template_name="demo.html",
                context={"name": "Test"},
                config=ResumeConfig(),
                base_path=temp_dir,
            )
            output_path = Path(temp_dir) / "nonexistent/path/resume.html"

            # This should NOT create any directories or files
            with patch("pathlib.Path.mkdir") as mock_mkdir:
                with patch("pathlib.Path.write_text") as mock_write_text:
                    with patch("pathlib.Path.write_bytes") as mock_write_bytes:
                        # Create a mock template locator for testing
                        mock_locator = MagicMock(spec=TemplateLocator)
                        mock_locator.get_template_location.return_value = Path(temp_dir)

                        with patch(
                            "simple_resume.core.generate.html.get_template_environment"
                        ) as template_env_patch:
                            # Setup mock template environment and template
                            mock_template_env = MagicMock()
                            mock_template = MagicMock()
                            mock_template.render.return_value = (
                                "<html><body>Test content</body></html>"
                            )
                            mock_template_env.get_template.return_value = mock_template
                            template_env_patch.return_value = mock_template_env

                            factory = create_html_generator_factory(
                                default_template_locator=mock_locator
                            )
                            prepare_html_func = factory.create_prepare_html_function()
                            html_content, effects, metadata = prepare_html_func(
                                render_plan=render_plan,
                                output_path=output_path,
                                resume_name="test_resume",
                                template_locator=mock_locator,
                            )

                        # Verify NO I/O was performed
                        mock_mkdir.assert_not_called()
                        mock_write_text.assert_not_called()
                        mock_write_bytes.assert_not_called()

                        # But effects should be returned
                        assert len(effects) > 0
                        assert isinstance(html_content, str)

    def test_uses_explicit_template_loc(self, story: Scenario) -> None:
        """prepare_html_with_jinja uses template_loc when provided."""
        story.given("an explicit template locator is supplied")
        story.when("preparing HTML with that locator")
        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.HTML,
                template_name="demo.html",
                context={"name": "Test"},
                config=ResumeConfig(),
                base_path=temp_dir,
            )
            output_path = Path(temp_dir) / "resume.html"

            # Provide explicit template location
            # Create a mock template locator for testing
            mock_locator = MagicMock(spec=TemplateLocator)
            mock_locator.get_template_location.return_value = Path(temp_dir)

            with patch(
                "simple_resume.core.generate.html.get_template_environment"
            ) as mock_env:
                # Setup mock template environment and template
                mock_template_env = MagicMock()
                mock_template = MagicMock()
                mock_template.render.return_value = (
                    "<html><body>Test content</body></html>"
                )
                mock_template_env.get_template.return_value = mock_template
                mock_env.return_value = mock_template_env

                factory = create_html_generator_factory(
                    default_template_locator=mock_locator
                )
                prepare_html_func = factory.create_prepare_html_function()
                html_content, effects, metadata = prepare_html_func(
                    render_plan=render_plan,
                    output_path=output_path,
                    resume_name="test_resume",
                    template_locator=mock_locator,
                    filename="resume.yaml",
                )

            # Should successfully generate HTML
            assert isinstance(html_content, str)
            assert len(html_content) > 0

    def test_uses_injected_template_locator(self, story: Scenario) -> None:
        """prepare_html_with_jinja uses injected template_locator when provided."""
        story.given("a template locator is injected at call time")
        story.when("preparing HTML generation")
        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.HTML,
                template_name="demo.html",
                context={"name": "Test"},
                config=ResumeConfig(),
                base_path=temp_dir,
            )
            output_path = Path(temp_dir) / "resume.html"

            # Create mock template locator
            mock_locator = MagicMock()
            mock_locator.get_template_location.return_value = TEMPLATE_LOC

            # Call with injected locator
            factory = create_html_generator_factory()
            prepare_html_func = factory.create_prepare_html_function()
            html_content, effects, metadata = prepare_html_func(
                render_plan=render_plan,
                output_path=output_path,
                resume_name="test_resume",
                template_locator=mock_locator,  # Injected locator
                filename="resume.yaml",
            )

            # Should have used the injected locator
            mock_locator.get_template_location.assert_called_once()
            assert isinstance(html_content, str)
