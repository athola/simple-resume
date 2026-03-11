"""Tests for PDF and HTML text extraction in ATS screening (#104)."""

from __future__ import annotations

from pathlib import Path

import pytest

from simple_resume.core.exceptions import ValidationError
from simple_resume.shell.cli import main as cli
from simple_resume.shell.cli._screen import _collect_resume_files
from tests.bdd import Scenario


class TestPdfExtraction:
    """PDF text extraction via pdfplumber."""

    def test_extract_pdf_text(self, tmp_path: Path, story: Scenario) -> None:
        fpdf2 = pytest.importorskip("fpdf")
        story.given("a PDF file with text content")
        pdf_file = tmp_path / "resume.pdf"
        pdf = fpdf2.FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.cell(text="Python developer with Django experience")
        pdf.output(str(pdf_file))

        story.when("reading the PDF file")
        content = cli._read_file_text(pdf_file)

        story.then("text is extracted from the PDF")
        assert "Python" in content

    def test_corrupt_pdf_raises_validation_error(
        self, tmp_path: Path, story: Scenario
    ) -> None:
        story.given("a corrupt PDF file")
        bad_pdf = tmp_path / "corrupt.pdf"
        bad_pdf.write_bytes(b"not a real pdf")

        story.when("reading the corrupt PDF")
        with pytest.raises(ValidationError, match="extract text"):
            cli._read_file_text(bad_pdf)

        story.then("a ValidationError is raised")


class TestHtmlExtraction:
    """HTML text extraction via BeautifulSoup."""

    def test_extract_html_text(self, tmp_path: Path, story: Scenario) -> None:
        story.given("an HTML file with resume content")
        html_file = tmp_path / "resume.html"
        html_file.write_text(
            "<html><body><h1>Jane Doe</h1>"
            "<p>Python developer with 5 years of experience.</p>"
            "</body></html>"
        )

        story.when("reading the HTML file")
        content = cli._read_file_text(html_file)

        story.then("text is extracted without HTML tags")
        assert "Jane Doe" in content
        assert "Python developer" in content
        assert "<html>" not in content

    def test_extract_htm_text(self, tmp_path: Path, story: Scenario) -> None:
        story.given("an .htm file")
        htm_file = tmp_path / "resume.htm"
        htm_file.write_text("<html><body><p>Go engineer</p></body></html>")

        story.when("reading the .htm file")
        content = cli._read_file_text(htm_file)

        story.then("text is extracted")
        assert "Go engineer" in content


class TestCollectResumeFilesWithNewFormats:
    """_collect_resume_files now includes PDF and HTML."""

    def test_collects_pdf_and_html(self, tmp_path: Path, story: Scenario) -> None:
        story.given("a directory with pdf, html, htm, and txt files")
        (tmp_path / "a.pdf").write_bytes(b"pdf")
        (tmp_path / "b.html").write_text("html")
        (tmp_path / "c.htm").write_text("htm")
        (tmp_path / "d.txt").write_text("txt")
        (tmp_path / "e.py").write_text("py")

        story.when("collecting resume files")
        files = _collect_resume_files(tmp_path)

        story.then("pdf, html, htm, and txt are included; py is excluded")
        names = [f.name for f in files]
        assert "a.pdf" in names
        assert "b.html" in names
        assert "c.htm" in names
        assert "d.txt" in names
        assert "e.py" not in names
