"""Tests for LaTeX context building (pure version without I/O)."""

from __future__ import annotations

from typing import Any

from simple_resume.core.latex.context import build_latex_context_pure
from tests.bdd import Scenario


class TestBuildLatexContextPure:
    """Tests for build_latex_context_pure function."""

    def test_minimal_data(self, story: Scenario) -> None:
        """Test with minimal data."""
        story.given("an empty data dictionary")
        story.when("building LaTeX context")
        data: dict[str, Any] = {}
        context = build_latex_context_pure(data)

        assert "full_name" in context
        assert "headline" in context
        assert "contact_lines" in context
        assert "summary_blocks" in context
        assert "skill_sections" in context
        assert "sections" in context
        assert context["full_name"] == ""

    def test_full_name(self, story: Scenario) -> None:
        """Test full_name conversion."""
        story.given("data with a full_name field")
        story.when("building LaTeX context")
        data = {"full_name": "John Doe"}
        context = build_latex_context_pure(data)
        assert context["full_name"] == "John Doe"

    def test_full_name_with_markdown(self, story: Scenario) -> None:
        """Test full_name with markdown."""
        story.given("a full_name containing markdown bold syntax")
        story.when("building LaTeX context")
        data = {"full_name": "**John** Doe"}
        context = build_latex_context_pure(data)
        assert r"\textbf{John}" in context["full_name"]

    def test_job_title(self, story: Scenario) -> None:
        """Test job_title conversion (headline)."""
        story.given("data with a job_title field")
        story.when("building LaTeX context")
        data = {"job_title": "Software Engineer"}
        context = build_latex_context_pure(data)
        assert context["headline"] == "Software Engineer"

    def test_no_job_title(self, story: Scenario) -> None:
        """Test when job_title is missing."""
        story.given("data without a job_title field")
        story.when("building LaTeX context")
        data: dict[str, Any] = {}
        context = build_latex_context_pure(data)
        assert context["headline"] is None

    def test_job_title_with_markdown(self, story: Scenario) -> None:
        """Test job_title with markdown."""
        story.given("a job_title containing markdown italic syntax")
        story.when("building LaTeX context")
        data = {"job_title": "*Senior* Engineer"}
        context = build_latex_context_pure(data)
        assert r"\textit{Senior}" in context["headline"]

    def test_description_as_summary(self, story: Scenario) -> None:
        """Test description converted to summary_blocks."""
        story.given("data with a multi-block description field")
        story.when("building LaTeX context")
        data = {"description": "Experienced engineer.\n\n- Skill 1\n- Skill 2"}
        context = build_latex_context_pure(data)
        assert len(context["summary_blocks"]) == 2
        assert context["summary_blocks"][0]["kind"] == "paragraph"
        assert context["summary_blocks"][1]["kind"] == "itemize"

    def test_contact_info(self, story: Scenario) -> None:
        """Test contact information."""
        story.given("data with email, phone, and github fields")
        story.when("building LaTeX context")
        data = {
            "email": "user@example.com",
            "phone": "555-1234",
            "github": "username",
        }
        context = build_latex_context_pure(data)
        assert len(context["contact_lines"]) == 3

    def test_skill_sections(self, story: Scenario) -> None:
        """Test skill sections."""
        story.given("data with expertise and programming skill lists")
        story.when("building LaTeX context")
        data = {
            "expertise": ["Python", "JavaScript"],
            "programming": ["C++", "Go"],
        }
        context = build_latex_context_pure(data)
        assert len(context["skill_sections"]) == 2

    def test_body_sections(self, story: Scenario) -> None:
        """Test body sections."""
        story.given("data with body sections for Experience and Education")
        story.when("building LaTeX context")
        data = {
            "body": {
                "Experience": [{"title": "Job"}],
                "Education": [{"title": "Degree"}],
            }
        }
        context = build_latex_context_pure(data)
        assert len(context["sections"]) == 2

    def test_complete_resume_data(self, story: Scenario) -> None:
        """Test with complete resume data."""
        story.given("a complete resume with all fields populated")
        story.when("building LaTeX context")
        data = {
            "full_name": "Jane Smith",
            "job_title": "Senior Software Engineer",
            "description": "Experienced professional with 10+ years.",
            "email": "jane@example.com",
            "phone": "555-1234",
            "expertise": ["Python", "JavaScript"],
            "body": {
                "Experience": [
                    {
                        "title": "Senior Engineer",
                        "company": "Tech Corp",
                        "start": "2020",
                        "end": "Present",
                        "description": "Led development team.",
                    }
                ],
                "Education": [
                    {
                        "title": "BS Computer Science",
                        "company": "University",
                        "start": "2010",
                        "end": "2014",
                    }
                ],
            },
        }
        context = build_latex_context_pure(data)

        assert context["full_name"] == "Jane Smith"
        assert context["headline"] == "Senior Software Engineer"
        assert len(context["contact_lines"]) == 2
        assert len(context["summary_blocks"]) == 1
        assert len(context["skill_sections"]) == 1
        assert len(context["sections"]) == 2

    def test_latex_escaping_throughout(self, story: Scenario) -> None:
        """Test that LaTeX chars are escaped throughout."""
        story.given("data with LaTeX special characters in various fields")
        story.when("building LaTeX context")
        data = {
            "full_name": "John & Jane",
            "job_title": "C++ Developer",
            "description": "Expert in $variable handling.",
            "email": "user+tag@example.com",
        }
        context = build_latex_context_pure(data)

        assert r"\&" in context["full_name"]
        assert "C++" in context["headline"]
        assert r"\$variable" in context["summary_blocks"][0]["text"]

    def test_empty_data_returns_valid_context(self, story: Scenario) -> None:
        """Test that empty data still returns a valid context."""
        story.given("an empty data dictionary")
        story.when("building LaTeX context")
        context = build_latex_context_pure({})

        # All expected keys should be present
        assert "full_name" in context
        assert "headline" in context
        assert "contact_lines" in context
        assert "summary_blocks" in context
        assert "skill_sections" in context
        assert "sections" in context

        # Lists should be empty, not None
        assert context["contact_lines"] == []
        assert context["summary_blocks"] == []
        assert context["skill_sections"] == []
        assert context["sections"] == []

    def test_none_values_handled(self, story: Scenario) -> None:
        """Test that None values are handled gracefully."""
        story.given("data with None values for several fields")
        story.when("building LaTeX context")
        data = {
            "full_name": None,
            "job_title": None,
            "description": None,
        }
        context = build_latex_context_pure(data)

        assert context["full_name"] == "None"  # Converted to string
        assert context["headline"] is None
        assert context["summary_blocks"] == []

    def test_no_fontawesome_block_in_pure_function(self, story: Scenario) -> None:
        """Test that pure function does not include fontawesome_block."""
        story.given("any resume data")
        story.when("building LaTeX context with the pure function")
        # The pure function should NOT try to check filesystem for fonts
        # That's an I/O operation that belongs in the shell
        data = {"full_name": "John Doe"}
        context = build_latex_context_pure(data)

        # fontawesome_block should not be included in pure context
        # It will be added by shell layer when it has file system access
        assert (
            "fontawesome_block" not in context or context["fontawesome_block"] is None
        )
