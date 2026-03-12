"""Tests for PDF and HTML text extraction in ATS screening (#104)."""

from __future__ import annotations

from pathlib import Path

import pytest

from simple_resume.core.exceptions import ValidationError
from simple_resume.shell.cli import main as cli
from simple_resume.shell.cli._screen import _collect_resume_files, _extract_pdf_text
from tests.bdd import Scenario

# Minimal valid PDF with one page containing "Hello World" text.
# Hand-crafted to avoid needing fpdf2 as a test dependency.
_MINIMAL_PDF = (
    b"%PDF-1.0\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
    b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
    b"4 0 obj<</Length 44>>stream\n"
    b"BT /F1 12 Tf 100 700 Td (Hello World) Tj ET\n"
    b"endstream\nendobj\n"
    b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"xref\n0 6\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000058 00000 n \n"
    b"0000000115 00000 n \n"
    b"0000000266 00000 n \n"
    b"0000000360 00000 n \n"
    b"trailer<</Size 6/Root 1 0 R>>\n"
    b"startxref\n435\n%%EOF"
)


class TestPdfExtraction:
    """PDF text extraction via pdfplumber."""

    def test_extract_pdf_text(self, tmp_path: Path, story: Scenario) -> None:
        story.given("a minimal PDF file with text content")
        pdf_file = tmp_path / "resume.pdf"
        pdf_file.write_bytes(_MINIMAL_PDF)

        story.when("reading the PDF file")
        content = cli._read_file_text(pdf_file)

        story.then("text is extracted from the PDF")
        assert "Hello World" in content

    def test_extract_pdf_text_directly(self, tmp_path: Path, story: Scenario) -> None:
        story.given("a minimal PDF file")
        pdf_file = tmp_path / "doc.pdf"
        pdf_file.write_bytes(_MINIMAL_PDF)

        story.when("extracting text directly via _extract_pdf_text")
        content = _extract_pdf_text(pdf_file)

        story.then("page text is extracted correctly")
        assert "Hello World" in content

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
