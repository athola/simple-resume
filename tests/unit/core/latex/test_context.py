"""Tests for LaTeX context building (pure version without I/O)."""

from __future__ import annotations

from typing import Any

from simple_resume.core.latex.context import build_latex_context_pure


class TestBuildLatexContextPure:
    """Tests for build_latex_context_pure function."""

    def test_minimal_data(self) -> None:
        """Test with minimal data."""
        data: dict[str, Any] = {}
        context = build_latex_context_pure(data)

        assert "full_name" in context
        assert "headline" in context
        assert "contact_lines" in context
        assert "summary_blocks" in context
        assert "skill_sections" in context
        assert "sections" in context
        assert context["full_name"] == ""

    def test_full_name(self) -> None:
        """Test full_name conversion."""
        data = {"full_name": "John Doe"}
        context = build_latex_context_pure(data)
        assert context["full_name"] == "John Doe"

    def test_full_name_with_markdown(self) -> None:
        """Test full_name with markdown."""
        data = {"full_name": "**John** Doe"}
        context = build_latex_context_pure(data)
        assert r"\textbf{John}" in context["full_name"]

    def test_job_title(self) -> None:
        """Test job_title conversion (headline)."""
        data = {"job_title": "Software Engineer"}
        context = build_latex_context_pure(data)
        assert context["headline"] == "Software Engineer"

    def test_no_job_title(self) -> None:
        """Test when job_title is missing."""
        data: dict[str, Any] = {}
        context = build_latex_context_pure(data)
        assert context["headline"] is None

    def test_job_title_with_markdown(self) -> None:
        """Test job_title with markdown."""
        data = {"job_title": "*Senior* Engineer"}
        context = build_latex_context_pure(data)
        assert r"\textit{Senior}" in context["headline"]

    def test_description_as_summary(self) -> None:
        """Test description converted to summary_blocks."""
        data = {"description": "Experienced engineer.\n\n- Skill 1\n- Skill 2"}
        context = build_latex_context_pure(data)
        assert len(context["summary_blocks"]) == 2
        assert context["summary_blocks"][0]["kind"] == "paragraph"
        assert context["summary_blocks"][1]["kind"] == "itemize"

    def test_contact_info(self) -> None:
        """Test contact information."""
        data = {
            "email": "user@example.com",
            "phone": "555-1234",
            "github": "username",
        }
        context = build_latex_context_pure(data)
        assert len(context["contact_lines"]) == 3

    def test_skill_sections(self) -> None:
        """Test skill sections."""
        data = {
            "expertise": ["Python", "JavaScript"],
            "programming": ["C++", "Go"],
        }
        context = build_latex_context_pure(data)
        assert len(context["skill_sections"]) == 2

    def test_body_sections(self) -> None:
        """Test body sections."""
        data = {
            "body": {
                "Experience": [{"title": "Job"}],
                "Education": [{"title": "Degree"}],
            }
        }
        context = build_latex_context_pure(data)
        assert len(context["sections"]) == 2

    def test_complete_resume_data(self) -> None:
        """Test with complete resume data."""
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

    def test_latex_escaping_throughout(self) -> None:
        """Test that LaTeX chars are escaped throughout."""
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

    def test_empty_data_returns_valid_context(self) -> None:
        """Test that empty data still returns a valid context."""
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

    def test_none_values_handled(self) -> None:
        """Test that None values are handled gracefully."""
        data = {
            "full_name": None,
            "job_title": None,
            "description": None,
        }
        context = build_latex_context_pure(data)

        assert context["full_name"] == "None"  # Converted to string
        assert context["headline"] is None
        assert context["summary_blocks"] == []

    def test_no_fontawesome_block_in_pure_function(self) -> None:
        """Test that pure function does not include fontawesome_block."""
        # The pure function should NOT try to check filesystem for fonts
        # That's an I/O operation that belongs in the shell
        data = {"full_name": "John Doe"}
        context = build_latex_context_pure(data)

        # fontawesome_block should not be included in pure context
        # It will be added by shell layer when it has file system access
        assert (
            "fontawesome_block" not in context or context["fontawesome_block"] is None
        )
