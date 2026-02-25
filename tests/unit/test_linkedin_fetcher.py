"""Tests for LinkedIn profile fetcher (shell layer).

Feature: LinkedIn Fetcher
    As a job seeker
    I want to extract profile data from LinkedIn HTML or text files
    So that I can import my LinkedIn profile into simple-resume
"""

from __future__ import annotations

import pytest

from simple_resume.shell.importers.linkedin_fetcher import (
    extract_profile_from_html,
    extract_profile_from_text,
    read_linkedin_file,
)

SAMPLE_HTML = """\
<html>
<body>
<div class="pv-top-card">
  <h1>Jane Doe</h1>
  <div class="text-body-medium">Senior Software Engineer at Acme</div>
  <span class="text-body-small">San Francisco, CA</span>
</div>
<section id="about">
  <div class="pv-shared-text-with-see-more">
    <span>Experienced engineer building scalable systems.</span>
  </div>
</section>
<section id="experience">
  <ul>
    <li>
      <span class="title">Senior Engineer</span>
      <span class="company">Acme Corp</span>
      <span class="date-range">Jan 2020 - Present</span>
      <span class="description">Built REST APIs.</span>
    </li>
  </ul>
</section>
</body>
</html>
"""

SAMPLE_TEXT = """\
Jane Doe
Senior Software Engineer
San Francisco, CA

About
Experienced engineer building scalable systems.

Experience
Senior Engineer at Acme Corp
Jan 2020 - Present
Built REST APIs.

Education
B.S. Computer Science at MIT
2013 - 2017

Skills
Python, Go, AWS, Docker
"""


class TestExtractProfileFromHtml:
    """Scenario group: parsing LinkedIn HTML into a profile dict."""

    def test_extracts_name_from_html(self):
        """Given LinkedIn HTML, the name is extracted from h1."""
        profile = extract_profile_from_html(SAMPLE_HTML)
        assert profile["full_name"] == "Jane Doe"

    def test_extracts_headline_from_html(self):
        """Given LinkedIn HTML, the headline is extracted."""
        profile = extract_profile_from_html(SAMPLE_HTML)
        assert "Senior Software Engineer" in profile.get("headline", "")

    def test_extracts_location_from_html(self):
        """Given LinkedIn HTML, the location is extracted."""
        profile = extract_profile_from_html(SAMPLE_HTML)
        assert profile.get("location") == "San Francisco, CA"

    def test_returns_dict_on_empty_html(self):
        """Given empty HTML, return an empty dict without crashing."""
        profile = extract_profile_from_html("<html><body></body></html>")
        assert isinstance(profile, dict)


class TestExtractProfileFromText:
    """Scenario group: parsing plain text LinkedIn export into a profile dict."""

    def test_extracts_name_from_text(self):
        """Given plain text profile, first line becomes the name."""
        profile = extract_profile_from_text(SAMPLE_TEXT)
        assert profile["full_name"] == "Jane Doe"

    def test_extracts_headline_from_text(self):
        """Given plain text profile, second line becomes headline."""
        profile = extract_profile_from_text(SAMPLE_TEXT)
        assert profile["headline"] == "Senior Software Engineer"

    def test_extracts_skills_from_text(self):
        """Given text with Skills section, skills are parsed."""
        profile = extract_profile_from_text(SAMPLE_TEXT)
        assert "Python" in profile.get("skills", [])
        assert "Docker" in profile.get("skills", [])

    def test_extracts_experience_from_text(self):
        """Given text with Experience section, entries are parsed."""
        profile = extract_profile_from_text(SAMPLE_TEXT)
        exp = profile.get("experience", [])
        assert len(exp) >= 1
        assert exp[0]["title"] == "Senior Engineer"
        assert exp[0]["company"] == "Acme Corp"

    def test_extracts_education_from_text(self):
        """Given text with Education section, entries are parsed."""
        profile = extract_profile_from_text(SAMPLE_TEXT)
        edu = profile.get("education", [])
        assert len(edu) >= 1
        assert "Computer Science" in edu[0].get("field_of_study", "")

    def test_empty_text_returns_empty_dict(self):
        """Given empty text, return an empty dict."""
        profile = extract_profile_from_text("")
        assert isinstance(profile, dict)


class TestReadLinkedInFile:
    """Scenario group: reading a LinkedIn file from disk."""

    def test_reads_html_file(self, tmp_path):
        """Given an HTML file, it is parsed as HTML."""
        html_file = tmp_path / "profile.html"
        html_file.write_text(SAMPLE_HTML)
        profile = read_linkedin_file(str(html_file))
        assert profile["full_name"] == "Jane Doe"

    def test_reads_text_file(self, tmp_path):
        """Given a .txt file, it is parsed as plain text."""
        txt_file = tmp_path / "profile.txt"
        txt_file.write_text(SAMPLE_TEXT)
        profile = read_linkedin_file(str(txt_file))
        assert profile["full_name"] == "Jane Doe"

    def test_raises_on_missing_file(self):
        """Given a non-existent file, raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            read_linkedin_file("/nonexistent/profile.html")

    def test_raises_on_unsupported_format(self, tmp_path):
        """Given an unsupported file extension, raise ValueError."""
        pdf_file = tmp_path / "profile.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")
        with pytest.raises(ValueError, match="Unsupported"):
            read_linkedin_file(str(pdf_file))
