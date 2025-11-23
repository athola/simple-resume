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
    HtmlGenerationConfig,
    prepare_html_with_jinja,
)
from simple_resume.core.models import RenderPlan, ResumeConfig
from simple_resume.shell.config import TEMPLATE_LOC


class TestPrepareHtmlWithJinja:
    """Tests for prepare_html_with_jinja - pure logic without I/O."""

    def test_returns_html_content_effects_and_metadata(self) -> None:
        """prepare_html_with_jinja returns (html_content, effects, metadata)."""
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

            config = HtmlGenerationConfig(
                template_loc=None,
                template_locator=None,
                filename="resume.yaml",
            )
            html_content, effects, metadata = prepare_html_with_jinja(
                render_plan=render_plan,
                output_path=output_path,
                config=config,
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

    def test_includes_make_directory_effect(self) -> None:
        """prepare_html_with_jinja includes MakeDirectory effect for output dir."""
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

            _, effects, _ = prepare_html_with_jinja(
                render_plan=render_plan,
                output_path=output_path,
            )

            # Should include MakeDirectory effect for parent directory
            make_dir_effects = [e for e in effects if isinstance(e, MakeDirectory)]
            assert len(make_dir_effects) == 1
            assert make_dir_effects[0].path == output_path.parent
            assert make_dir_effects[0].parents is True

    def test_includes_write_file_effect_for_html(self) -> None:
        """prepare_html_with_jinja includes WriteFile effect for HTML output."""
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

            _, effects, _ = prepare_html_with_jinja(
                render_plan=render_plan,
                output_path=output_path,
            )

            # Should include WriteFile effect for HTML
            write_effects = [e for e in effects if isinstance(e, WriteFile)]
            html_write_effects = [e for e in write_effects if e.path == output_path]
            assert len(html_write_effects) == 1
            assert isinstance(
                html_write_effects[0].content, str
            )  # HTML content is string

    def test_html_includes_base_tag(self) -> None:
        """prepare_html_with_jinja includes base tag for asset resolution."""
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

            html_content, _, _ = prepare_html_with_jinja(
                render_plan=render_plan,
                output_path=output_path,
            )

            # Should include base tag
            assert "<base href=" in html_content

    def test_html_base_tag_without_head(self) -> None:
        """prepare_html_with_jinja handles HTML without <head> tag."""
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

            # Mock template that returns HTML without <head> tag
            with patch(
                "simple_resume.core.generate.html.get_template_environment"
            ) as mock_env:
                mock_template = mock_env.return_value.get_template.return_value
                mock_template.render.return_value = (
                    "<html><body>No head tag</body></html>"
                )

                html_content, _, _ = prepare_html_with_jinja(
                    render_plan=render_plan,
                    output_path=output_path,
                )

                # Should prepend base tag when no <head> present
                assert html_content.startswith("<base href=")
                assert "No head tag" in html_content

    def test_raises_template_error_for_latex_mode(self) -> None:
        """prepare_html_with_jinja raises error when render plan uses LaTeX mode."""
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

            with pytest.raises(TemplateError, match="LaTeX mode not supported"):
                prepare_html_with_jinja(
                    render_plan=render_plan,
                    output_path=output_path,
                )

    def test_raises_template_error_when_context_missing(self) -> None:
        """prepare_html_with_jinja raises error when context is None."""
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

            with pytest.raises(TemplateError, match="missing context"):
                prepare_html_with_jinja(
                    render_plan=render_plan,
                    output_path=output_path,
                )

    def test_raises_template_error_when_template_name_missing(self) -> None:
        """prepare_html_with_jinja raises error when template_name is None."""
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

        with pytest.raises(TemplateError, match="missing.*template"):
            prepare_html_with_jinja(
                render_plan=render_plan,
                output_path=output_path,
            )

    def test_no_io_operations_performed(self) -> None:
        """prepare_html_with_jinja performs NO I/O operations (critical test)."""
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
                        html_content, effects, metadata = prepare_html_with_jinja(
                            render_plan=render_plan,
                            output_path=output_path,
                        )

                        # Verify NO I/O was performed
                        mock_mkdir.assert_not_called()
                        mock_write_text.assert_not_called()
                        mock_write_bytes.assert_not_called()

                        # But effects should be returned
                        assert len(effects) > 0
                        assert isinstance(html_content, str)

    def test_uses_explicit_template_loc(self) -> None:
        """prepare_html_with_jinja uses template_loc when provided."""
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
            config = HtmlGenerationConfig(
                template_loc=TEMPLATE_LOC,  # Explicit template location
                template_locator=None,
                filename="resume.yaml",
            )
            html_content, effects, metadata = prepare_html_with_jinja(
                render_plan=render_plan,
                output_path=output_path,
                config=config,
            )

            # Should successfully generate HTML
            assert isinstance(html_content, str)
            assert len(html_content) > 0

    def test_uses_injected_template_locator(self) -> None:
        """prepare_html_with_jinja uses injected template_locator when provided."""
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

            # Provide via config
            config = HtmlGenerationConfig(
                template_loc=None,
                template_locator=mock_locator,  # Injected locator
                filename="resume.yaml",
            )
            html_content, effects, metadata = prepare_html_with_jinja(
                render_plan=render_plan,
                output_path=output_path,
                config=config,
            )

            # Should have used the injected locator
            mock_locator.get_template_location.assert_called_once()
            assert isinstance(html_content, str)
