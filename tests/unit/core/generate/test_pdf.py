"""Tests for pure PDF generation logic (core layer).

Following TDD principles - these tests are written BEFORE refactoring.
Tests verify PDF generation logic is pure and returns effects instead of performing I/O.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import pytest

from simple_resume.core.constants import RenderMode
from simple_resume.core.effects import MakeDirectory, RenderPdf, WriteFile
from simple_resume.core.exceptions import ConfigurationError
from simple_resume.core.generate.exceptions import TemplateError
from simple_resume.core.generate.pdf import (
    LatexGenerationContext,
    PdfGenerationConfig,
    prepare_pdf_with_latex,
    prepare_pdf_with_weasyprint,
)
from simple_resume.core.models import RenderPlan, ResumeConfig
from simple_resume.core.paths import Paths
from simple_resume.core.protocols import TemplateLocator
from simple_resume.shell.config import TEMPLATE_LOC
from tests.bdd import Scenario


def _make_template_locator() -> TemplateLocator:
    locator = MagicMock(spec=TemplateLocator)
    locator.get_template_location.return_value = TEMPLATE_LOC
    return locator


def _make_latex_renderer(tex_content: str) -> object:
    render_fn = MagicMock(return_value=MagicMock(tex=tex_content))

    class _StubLatexRenderer:
        def get_latex_functions(self) -> tuple[object, object, object]:
            return (RuntimeError, lambda *args, **kwargs: None, render_fn)

    return _StubLatexRenderer()


class TestPreparePdfWithWeasyprint:
    """Tests for prepare_pdf_with_weasyprint - pure logic without I/O."""

    def test_returns_html_content_effects_and_metadata(self, story: Scenario) -> None:
        """prepare_pdf_with_weasyprint returns (html_content, effects, metadata)."""
        story.given("a standard render plan for HTML-based PDF generation")
        story.when("prepare_pdf_with_weasyprint is executed")
        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test_resume",
                mode=RenderMode.HTML,
                template_name="demo.html",
                context={"name": "Test User", "title": "Engineer"},
                config=ResumeConfig(page_width=210, page_height=297),
                base_path="",
            )
            output_path = Path(temp_dir) / "output" / "resume.pdf"
            template_locator = _make_template_locator()

            html_content, effects, metadata = prepare_pdf_with_weasyprint(
                render_plan=render_plan,
                output_path=output_path,
                resume_name="test_resume",
                filename="resume.yaml",
                template_locator=template_locator,
            )

            # Should return HTML content (string)
            assert isinstance(html_content, str)
            assert len(html_content) > 0

            # Should return list of effects
            assert isinstance(effects, list)
            assert len(effects) > 0

            # Should return metadata
            assert metadata is not None
            assert metadata.format_type == "pdf"
            assert metadata.template_name == "demo.html"
            assert metadata.resume_name == "test_resume"

    def test_includes_make_directory_effect(self, story: Scenario) -> None:
        """prepare_pdf_with_weasyprint includes MakeDirectory effect for output dir."""
        story.given("the output path resides in nested directories")
        story.when("building PDF generation effects")
        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.HTML,
                template_name="demo.html",
                context={"name": "Test"},
                config=ResumeConfig(),
                base_path="",
            )
            output_path = Path(temp_dir) / "nested" / "dirs" / "resume.pdf"
            template_locator = _make_template_locator()

            _, effects, _ = prepare_pdf_with_weasyprint(
                render_plan=render_plan,
                output_path=output_path,
                resume_name="test",
                template_locator=template_locator,
            )

            # Should include MakeDirectory effect for parent directory
            make_dir_effects = [e for e in effects if isinstance(e, MakeDirectory)]
            assert len(make_dir_effects) == 1
            assert make_dir_effects[0].path == output_path.parent
            assert make_dir_effects[0].parents is True

    def test_includes_render_pdf_effect(self, story: Scenario) -> None:
        """prepare_pdf_with_weasyprint includes RenderPdf effect for PDF output."""
        story.given("a render plan configured for PDF output")
        story.when("preparing PDF with weasyprint")
        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.HTML,
                template_name="demo.html",
                context={"name": "Test"},
                config=ResumeConfig(),
                base_path="",
            )
            output_path = Path(temp_dir) / "resume.pdf"
            template_locator = _make_template_locator()

            _, effects, _ = prepare_pdf_with_weasyprint(
                render_plan=render_plan,
                output_path=output_path,
                resume_name="test",
                template_locator=template_locator,
            )

            # Should include RenderPdf effect
            render_effects = [e for e in effects if isinstance(e, RenderPdf)]
            assert len(render_effects) == 1
            assert render_effects[0].output_path == output_path

    def test_raises_template_error_for_latex_mode(self, story: Scenario) -> None:
        """prepare_pdf_with_weasyprint raises error when render plan uses LaTeX mode."""
        story.given("a render plan set to LaTeX mode")
        story.when("preparing PDF via weasyprint")
        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.LATEX,
                template_name="resume.tex",
                context={},
                config=ResumeConfig(),
                base_path="",
            )
            output_path = Path(temp_dir) / "resume.pdf"
            template_locator = _make_template_locator()

            with pytest.raises(TemplateError, match="LaTeX mode not supported"):
                prepare_pdf_with_weasyprint(
                    render_plan=render_plan,
                    output_path=output_path,
                    resume_name="test",
                    template_locator=template_locator,
                )

    def test_raises_template_error_when_context_missing(self, story: Scenario) -> None:
        """prepare_pdf_with_weasyprint raises error when context is None."""
        story.given("context is missing from the render plan")
        story.when("preparing PDF output")
        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.HTML,
                template_name="demo.html",
                context=None,  # Missing context
                config=ResumeConfig(),
                base_path="",
            )
            output_path = Path(temp_dir) / "resume.pdf"
            template_locator = _make_template_locator()

            with pytest.raises(TemplateError, match="missing context"):
                prepare_pdf_with_weasyprint(
                    render_plan=render_plan,
                    output_path=output_path,
                    resume_name="test",
                    template_locator=template_locator,
                )

    def test_raises_template_error_when_template_name_missing(
        self, story: Scenario
    ) -> None:
        """prepare_pdf_with_weasyprint raises error when template_name is None."""
        story.given("no template name is supplied")
        story.when("preparing PDF output")
        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.HTML,
                template_name=None,  # Missing template
                context={"name": "Test"},
                config=ResumeConfig(),
                base_path="",
            )
            output_path = Path(temp_dir) / "resume.pdf"
            template_locator = _make_template_locator()

            with pytest.raises(TemplateError, match="missing.*template"):
                prepare_pdf_with_weasyprint(
                    render_plan=render_plan,
                    output_path=output_path,
                    resume_name="test",
                    template_locator=template_locator,
                )

    def test_raises_configuration_error_when_locator_missing(
        self, story: Scenario
    ) -> None:
        """Raises ConfigurationError when the template locator is missing."""
        story.given("a render plan without an injected template locator")
        story.when("preparing PDF without a locator")
        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.HTML,
                template_name="demo.html",
                context={"name": "Test"},
                config=ResumeConfig(),
                base_path="",
            )
            output_path = Path(temp_dir) / "resume.pdf"

            with pytest.raises(ConfigurationError, match="template locator"):
                prepare_pdf_with_weasyprint(
                    render_plan=render_plan,
                    output_path=output_path,
                    resume_name="test",
                )

    def test_uses_default_page_dimensions_when_not_specified(
        self, story: Scenario
    ) -> None:
        """prepare_pdf_with_weasyprint uses defaults when dimensions not in config."""
        story.given("page width and height are unset in the resume config")
        story.when("preparing PDF output")
        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.HTML,
                template_name="demo.html",
                context={"name": "Test"},
                config=ResumeConfig(page_width=None, page_height=None),
                base_path="",
            )
            output_path = Path(temp_dir) / "resume.pdf"
            template_locator = _make_template_locator()

            html_content, _, _ = prepare_pdf_with_weasyprint(
                render_plan=render_plan,
                output_path=output_path,
                resume_name="test",
                template_locator=template_locator,
            )

            # HTML content should include CSS with default dimensions
            # (We can't inspect WeasyPrint's internal CSS, but verify it doesn't crash)
            assert isinstance(html_content, str)

    def test_respects_custom_page_dimensions(self, story: Scenario) -> None:
        """prepare_pdf_with_weasyprint respects custom page dimensions from config."""
        story.given("custom page dimensions are provided")
        story.when("preparing PDF output")
        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.HTML,
                template_name="demo.html",
                context={"name": "Test"},
                config=ResumeConfig(page_width=216, page_height=279),  # US Letter
                base_path="",
            )
            output_path = Path(temp_dir) / "resume.pdf"
            template_locator = _make_template_locator()

            html_content, _, _ = prepare_pdf_with_weasyprint(
                render_plan=render_plan,
                output_path=output_path,
                resume_name="test",
                template_locator=template_locator,
            )

            # Verify it doesn't crash with custom dimensions
            assert isinstance(html_content, str)

    def test_includes_palette_metadata_in_result(self, story: Scenario) -> None:
        """prepare_pdf_with_weasyprint includes palette metadata from render plan."""
        story.given("palette metadata attached to the render plan")
        story.when("preparing PDF with weasyprint")
        palette_meta = {
            "source": "colourlovers",
            "palette_name": "Ocean Breeze",
            "colors": ["#1a2b3c", "#4d5e6f"],
        }
        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.HTML,
                template_name="demo.html",
                context={"name": "Test"},
                config=ResumeConfig(),
                base_path="",
                palette_metadata=palette_meta,
            )
            output_path = Path(temp_dir) / "resume.pdf"
            template_locator = _make_template_locator()

            _, _, metadata = prepare_pdf_with_weasyprint(
                render_plan=render_plan,
                output_path=output_path,
                resume_name="test",
                template_locator=template_locator,
            )

            assert metadata.palette_info == palette_meta

    def test_no_io_operations_performed(self, story: Scenario) -> None:
        """prepare_pdf_with_weasyprint performs NO I/O operations (critical test)."""
        story.given("pdf preparation should emit effects instead of writing files")
        story.when("preparing PDF with mocked filesystem operations")
        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.HTML,
                template_name="demo.html",
                context={"name": "Test"},
                config=ResumeConfig(),
                base_path="",
            )
            output_path = Path(temp_dir) / "nonexistent" / "path" / "resume.pdf"
            template_locator = _make_template_locator()

            # This should NOT create any directories or files
            with patch("pathlib.Path.mkdir") as mock_mkdir:
                with patch("pathlib.Path.write_text") as mock_write_text:
                    with patch("pathlib.Path.write_bytes") as mock_write_bytes:
                        html_content, effects, metadata = prepare_pdf_with_weasyprint(
                            render_plan=render_plan,
                            output_path=output_path,
                            resume_name="test",
                            template_locator=template_locator,
                        )

                        # Verify NO I/O was performed
                        mock_mkdir.assert_not_called()
                        mock_write_text.assert_not_called()
                        mock_write_bytes.assert_not_called()

                        # But effects should be returned
                        assert len(effects) > 0


class TestPreparePdfWithLatex:
    """Tests for prepare_pdf_with_latex - pure logic without I/O."""

    def test_returns_tex_content_effects_and_metadata(self, story: Scenario) -> None:
        """prepare_pdf_with_latex returns (tex_content, effects, metadata)."""
        story.given("a LaTeX render plan and generation config")
        story.when("preparing PDF with the LaTeX helper")

        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.LATEX,
                template_name="resume.tex",
                context={},
                config=ResumeConfig(),
                base_path="",
            )
            output_path = Path(temp_dir) / "resume.pdf"
            paths = Paths(
                data=Path(temp_dir),
                input=Path(temp_dir),
                output=Path(temp_dir),
                content=Path(temp_dir),
                templates=Path(temp_dir) / "templates",
                static=Path(temp_dir) / "static",
            )
            LatexGenerationContext(
                resume_data={"name": "Test User", "title": "Engineer"},
                processed_data={"name": "Test User", "title": "Engineer"},
                output_path=output_path,
                paths=paths,
                filename="resume.yaml",
            )

            latex_renderer = _make_latex_renderer(
                "\\documentclass{article}\\begin{document}Test\\end{document}"
            )
            config = PdfGenerationConfig(
                resume_name="test_resume",
                filename="resume.yaml",
                latex_renderer=latex_renderer,
            )

            tex_content, effects, metadata = prepare_pdf_with_latex(
                render_plan=render_plan,
                output_path=output_path,
                config=config,
            )

            # Should return TeX content
            assert isinstance(tex_content, str)
            assert "documentclass" in tex_content

            # Should return effects
            assert isinstance(effects, list)
            assert len(effects) > 0

            # Should return metadata
            assert metadata is not None
            assert metadata.format_type == "pdf"

    def test_includes_make_directory_effect(self, story: Scenario) -> None:
        """prepare_pdf_with_latex includes MakeDirectory effect."""
        story.given("a nested output path for LaTeX PDF generation")
        story.when("preparing PDF with LaTeX helper")

        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.LATEX,
                template_name="resume.tex",
                context={},
                config=ResumeConfig(),
                base_path="",
            )
            output_path = Path(temp_dir) / "nested" / "resume.pdf"
            paths = Paths(
                data=Path(temp_dir),
                input=Path(temp_dir),
                output=Path(temp_dir),
                content=Path(temp_dir),
                templates=Path(temp_dir),
                static=Path(temp_dir),
            )
            LatexGenerationContext(
                resume_data={},
                processed_data={},
                output_path=output_path,
                paths=paths,
            )
            latex_renderer = _make_latex_renderer("\\documentclass{article}")
            config = PdfGenerationConfig(
                resume_name="test_resume",
                latex_renderer=latex_renderer,
            )

            _, effects, _ = prepare_pdf_with_latex(
                render_plan=render_plan,
                output_path=output_path,
                config=config,
            )

            make_dir_effects = [e for e in effects if isinstance(e, MakeDirectory)]
            assert len(make_dir_effects) >= 1
            assert output_path.parent in [e.path for e in make_dir_effects]

    def test_includes_write_tex_file_effect(self, story: Scenario) -> None:
        """prepare_pdf_with_latex includes WriteFile effect for .tex file."""
        story.given("LaTeX generation produces a .tex artifact")
        story.when("preparing PDF effects")

        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.LATEX,
                template_name="resume.tex",
                context={},
                config=ResumeConfig(),
                base_path="",
            )
            output_path = Path(temp_dir) / "resume.pdf"
            paths = Paths(
                data=Path(temp_dir),
                input=Path(temp_dir),
                output=Path(temp_dir),
                content=Path(temp_dir),
                templates=Path(temp_dir),
                static=Path(temp_dir),
            )
            LatexGenerationContext(
                resume_data={},
                processed_data={},
                output_path=output_path,
                paths=paths,
            )

            latex_renderer = _make_latex_renderer("\\documentclass{article}")
            config = PdfGenerationConfig(
                resume_name="test_resume",
                latex_renderer=latex_renderer,
            )

            _, effects, _ = prepare_pdf_with_latex(
                render_plan=render_plan,
                output_path=output_path,
                config=config,
            )

            write_effects = [e for e in effects if isinstance(e, WriteFile)]
        tex_write = [e for e in write_effects if e.path.suffix == ".tex"]
        assert len(tex_write) >= 1

    def test_raises_configuration_error_when_renderer_missing(
        self, story: Scenario
    ) -> None:
        """prepare_pdf_with_latex raises error when no LaTeX renderer is provided."""
        story.given("a LaTeX render plan without an injected renderer")
        story.when("preparing LaTeX output without a renderer")

        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.LATEX,
                template_name="resume.tex",
                context={},
                config=ResumeConfig(),
                base_path="",
            )
            output_path = Path(temp_dir) / "resume.pdf"
            paths = Paths(
                data=Path(temp_dir),
                input=Path(temp_dir),
                output=Path(temp_dir),
                content=Path(temp_dir),
                templates=Path(temp_dir),
                static=Path(temp_dir),
            )
            LatexGenerationContext(
                resume_data={},
                processed_data={},
                output_path=output_path,
                paths=paths,
            )

            config = PdfGenerationConfig(resume_name="test_resume")

            with patch(
                "simple_resume.shell.render.latex.render_resume_latex_from_data",
                return_value=MagicMock(tex="\\documentclass{article}"),
            ):
                with pytest.raises(ConfigurationError, match="LaTeX renderer"):
                    prepare_pdf_with_latex(
                        render_plan=render_plan,
                        output_path=output_path,
                        config=config,
                    )

    def test_raises_configuration_error_when_paths_none(self, story: Scenario) -> None:
        """prepare_pdf_with_latex raises error when paths is None."""
        story.given("paths are missing from the LaTeX generation context")
        story.when("preparing PDF with LaTeX helper")

        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.LATEX,
                template_name="resume.tex",
                context={},
                config=ResumeConfig(),
                base_path="",
            )
            output_path = Path(temp_dir) / "resume.pdf"
            LatexGenerationContext(
                resume_data={},
                processed_data={},
                output_path=output_path,
                paths=None,  # Missing paths
            )

            with pytest.raises(
                ConfigurationError, match="LaTeX generation requires.*paths"
            ):
                config = PdfGenerationConfig(
                    resume_name="test_resume",
                    latex_renderer=_make_latex_renderer("\\documentclass{article}"),
                )

                prepare_pdf_with_latex(
                    render_plan=render_plan,
                    output_path=output_path,
                    config=config,
                )

    def test_no_io_operations_performed(self, story: Scenario) -> None:
        """prepare_pdf_with_latex performs NO I/O operations (critical test)."""
        story.given("LaTeX preparation should be pure and emit effects only")
        story.when("running prepare_pdf_with_latex with mocked filesystem calls")

        with TemporaryDirectory() as temp_dir:
            render_plan = RenderPlan(
                name="test",
                mode=RenderMode.LATEX,
                template_name="resume.tex",
                context={},
                config=ResumeConfig(),
                base_path="",
            )
            output_path = Path(temp_dir) / "nonexistent" / "resume.pdf"
            paths = Paths(
                data=Path(temp_dir),
                input=Path(temp_dir),
                output=Path(temp_dir),
                content=Path(temp_dir),
                templates=Path(temp_dir),
                static=Path(temp_dir),
            )
            LatexGenerationContext(
                resume_data={},
                processed_data={},
                output_path=output_path,
                paths=paths,
            )
            latex_renderer = _make_latex_renderer("\\documentclass{article}")

            with patch("pathlib.Path.mkdir") as mock_mkdir:
                with patch("pathlib.Path.write_text") as mock_write_text:
                    config = PdfGenerationConfig(
                        resume_name="test_resume",
                        latex_renderer=latex_renderer,
                    )

                    _, effects, _ = prepare_pdf_with_latex(
                        render_plan=render_plan,
                        output_path=output_path,
                        config=config,
                    )

                    # Verify NO I/O was performed
                    mock_mkdir.assert_not_called()
                    mock_write_text.assert_not_called()

                    # But effects should be returned
                    assert len(effects) > 0
