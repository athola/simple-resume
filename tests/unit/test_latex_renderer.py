"""Unit tests for the LaTeX rendering pipeline (BDD-flavoured)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from simple_resume import config
from simple_resume.latex_renderer import (
    LatexCompilationError,
    build_latex_context,
    compile_tex_to_html,
    compile_tex_to_pdf,
    render_resume_latex_from_data,
)
from tests.bdd import scenario
from tests.conftest import (
    create_complete_resume_data,
    make_resume_missing_contact,
)


def test_latex_contact_lines_include_icons() -> None:
    """Given/When/Then structure ensures contact lines include semantic icons."""

    story = scenario("build latex context from complete resume")
    story.given("a complete resume payload with phone, email, github, and location")
    data = create_complete_resume_data(full_name="Jane Doe")

    story.when("the latex context is constructed")
    context = build_latex_context(data)

    story.then("the full name is preserved")
    assert context["full_name"] == "Jane Doe"

    story.then("contact lines are prefixed with icons for each detail")
    assert context["contact_lines"], "contact_lines should not be empty"
    assert context["contact_lines"][0].startswith(r"\faLocation\enspace ")
    assert any(
        line.startswith(r"\faEnvelope\enspace ") for line in context["contact_lines"]
    )
    assert any(
        line.startswith(r"\faGithub\enspace ") for line in context["contact_lines"]
    )

    story.then("sections contain at least one entry for resume body content")
    assert context["sections"], "Expected rendered sections in context"


def test_latex_context_omits_missing_contact() -> None:
    """Ensure the context gracefully skips missing contact information."""

    story = scenario("build latex context without contact details")
    story.given("a resume missing address, phone, email, github, and web")
    data = make_resume_missing_contact(full_name="No Contact")

    story.when("_build_contact_lines is executed via context builder")
    context = build_latex_context(data)

    story.then("contact_lines is empty because nothing is available")
    assert context["contact_lines"] == []


def test_given_resume_when_rendering_to_latex_then_tex_header_is_present() -> None:
    """Render to LaTeX and confirm the boilerplate instead of HTML output."""

    story = scenario("render resume to latex")
    story.given("a complete resume payload and resolved package paths")
    data = create_complete_resume_data(full_name="Render Tester")
    paths = config.resolve_paths()

    story.when("render_resume_latex_from_data is invoked")
    result = render_resume_latex_from_data(data, paths=paths)

    story.then("LaTeX boilerplate is present and HTML artifacts are absent")
    assert "\\documentclass" in result.tex
    assert "Render Tester" in result.tex
    assert "<html" not in result.tex


def test_given_detected_latex_engine_when_compiling_tex_then_pdf_is_generated(
    tmp_path: Path,
) -> None:
    """Simulate available LaTeX engine and ensure subprocess is invoked once."""

    story = scenario("compile tex with available engine")
    story.given("a tex file and environment reporting pdflatex availability")
    tex_file = tmp_path / "resume.tex"
    tex_file.write_text(
        r"\documentclass{article}\begin{document}Test\end{document}", encoding="utf-8"
    )

    pdf_path = tex_file.with_suffix(".pdf")
    pdf_path.write_text("", encoding="utf-8")

    with (
        patch("simple_resume.latex_renderer.shutil.which") as mock_which,
        patch("simple_resume.latex_renderer.subprocess.run") as mock_run,
    ):
        mock_which.side_effect = (
            lambda engine: "/usr/bin/pdflatex" if engine == "pdflatex" else None
        )
        mock_run.return_value = Mock(returncode=0, stdout=b"", stderr=b"")

        story.when("compile_tex_to_pdf is executed")
        result_path = compile_tex_to_pdf(tex_file, engines=("pdflatex",))

    story.then("the detected engine is used once and the pdf path is returned")
    assert result_path == pdf_path
    mock_run.assert_called_once()


def test_given_missing_latex_engine_when_compiling_tex_then_error_is_raised(
    tmp_path: Path,
) -> None:
    """Raise a helpful error when LaTeX tooling is unavailable."""

    story = scenario("compile tex without available engines")
    story.given("no LaTeX engine is discoverable on PATH")
    tex_file = tmp_path / "resume.tex"
    tex_file.write_text("Test", encoding="utf-8")

    with patch("simple_resume.latex_renderer.shutil.which", return_value=None):
        story.when("compile_tex_to_pdf is executed")
        with pytest.raises(LatexCompilationError):
            compile_tex_to_pdf(tex_file, engines=("pdflatex",))


def test_given_pandoc_available_when_converting_tex_to_html_then_output_is_generated(
    tmp_path: Path,
) -> None:
    """Use pandoc when available to create HTML output."""

    story = scenario("convert tex to html with pandoc")
    story.given("pandoc is available and tex file exists")
    tex_file = tmp_path / "resume.tex"
    tex_file.write_text(r"\section{Test}", encoding="utf-8")
    html_file = tex_file.with_suffix(".html")
    html_file.write_text("<html></html>", encoding="utf-8")

    with (
        patch("simple_resume.latex_renderer.shutil.which") as mock_which,
        patch("simple_resume.latex_renderer.subprocess.run") as mock_run,
    ):
        mock_which.side_effect = (
            lambda tool: "/usr/bin/pandoc" if tool == "pandoc" else None
        )
        mock_run.return_value = Mock(returncode=0, stdout=b"", stderr=b"")

        story.when("compile_tex_to_html is executed")
        result_path = compile_tex_to_html(tex_file, tools=("pandoc",))

    story.then("pandoc is invoked once and returns the generated html path")
    assert result_path == html_file
    mock_run.assert_called_once()


def test_given_no_tools_when_converting_tex_to_html_then_error_is_raised(
    tmp_path: Path,
) -> None:
    """Raise LatexCompilationError when no HTML conversion tools exist."""

    story = scenario("attempt html conversion without tools")
    story.given("none of the configured tools are available")
    tex_file = tmp_path / "resume.tex"
    tex_file.write_text("content", encoding="utf-8")

    with patch("simple_resume.latex_renderer.shutil.which", return_value=None):
        story.when("compile_tex_to_html is invoked")
        with pytest.raises(LatexCompilationError):
            compile_tex_to_html(tex_file, tools=("pandoc",))
