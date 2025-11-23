"""Tests for LaTeX section preparation functions."""

from __future__ import annotations

import pytest

from simple_resume.core.latex.sections import (
    build_contact_lines,
    prepare_sections,
    prepare_skill_sections,
)


class TestBuildContactLines:
    """Tests for build_contact_lines function."""

    def test_empty_data(self) -> None:
        """Test with empty data dictionary."""
        lines = build_contact_lines({})
        assert lines == []

    def test_address_string(self) -> None:
        """Test with address as string."""
        data = {"address": "123 Main St, City, State"}
        lines = build_contact_lines(data)
        assert len(lines) == 1
        assert r"\faLocation" in lines[0]
        assert "123 Main St" in lines[0]

    def test_address_list(self) -> None:
        """Test with address as list."""
        data = {"address": ["123 Main St", "City", "State", "12345"]}
        lines = build_contact_lines(data)
        assert len(lines) == 1
        assert r"\faLocation" in lines[0]
        assert "123 Main St, City, State, 12345" in lines[0]

    def test_address_with_none_values(self) -> None:
        """Test address list with None values (should be filtered)."""
        data = {"address": ["123 Main St", None, "City", ""]}
        lines = build_contact_lines(data)
        assert len(lines) == 1
        # None and empty strings should be filtered out
        assert "123 Main St, City" in lines[0]

    def test_phone_number(self) -> None:
        """Test with phone number."""
        data = {"phone": "+1-555-1234"}
        lines = build_contact_lines(data)
        assert len(lines) == 1
        assert r"\faPhone" in lines[0]
        assert "+1-555-1234" in lines[0]

    def test_email(self) -> None:
        """Test with email address."""
        data = {"email": "user@example.com"}
        lines = build_contact_lines(data)
        assert len(lines) == 1
        assert r"\faEnvelope" in lines[0]
        assert r"\href{mailto:" in lines[0]
        assert "user@example.com" in lines[0]

    def test_email_with_special_chars(self) -> None:
        """Test email with special characters."""
        data = {"email": "user+tag@example.com"}
        lines = build_contact_lines(data)
        assert len(lines) == 1
        assert "user+tag@example.com" in lines[0]

    def test_github_username(self) -> None:
        """Test with GitHub username."""
        data = {"github": "username"}
        lines = build_contact_lines(data)
        assert len(lines) == 1
        assert r"\faGithub" in lines[0]
        assert "https://github.com/username" in lines[0]

    def test_github_full_url(self) -> None:
        """Test with full GitHub URL."""
        data = {"github": "https://github.com/username"}
        lines = build_contact_lines(data)
        assert len(lines) == 1
        assert "https://github.com/username" in lines[0]

    def test_github_with_leading_slash(self) -> None:
        """Test GitHub username with leading slash."""
        data = {"github": "/username"}
        lines = build_contact_lines(data)
        assert "https://github.com/username" in lines[0]

    def test_web_url(self) -> None:
        """Test with web URL."""
        data = {"web": "https://example.com"}
        lines = build_contact_lines(data)
        assert len(lines) == 1
        assert r"\faGlobe" in lines[0]
        assert "https://example.com" in lines[0]

    def test_web_with_github_domain(self) -> None:
        """Test web URL with github.com domain."""
        data = {"web": "https://github.com/username"}
        lines = build_contact_lines(data)
        assert len(lines) == 1
        assert r"\faGithub" in lines[0]

    def test_both_github_and_web_github(self) -> None:
        """Test with both github field and web field pointing to github."""
        data = {
            "github": "username",
            "web": "https://github.com/username",
        }
        lines = build_contact_lines(data)
        # Should only show github once
        github_lines = [line for line in lines if r"\faGithub" in line]
        assert len(github_lines) == 1

    def test_linkedin(self) -> None:
        """Test with LinkedIn profile."""
        data = {"linkedin": "in/username"}
        lines = build_contact_lines(data)
        assert len(lines) == 1
        assert r"\faLinkedin" in lines[0]
        assert "https://www.linkedin.com/in/username" in lines[0]

    def test_linkedin_full_url(self) -> None:
        """Test with full LinkedIn URL."""
        data = {"linkedin": "https://www.linkedin.com/in/username"}
        lines = build_contact_lines(data)
        assert len(lines) == 1
        assert "https://www.linkedin.com/in/username" in lines[0]

    def test_all_contact_info(self) -> None:
        """Test with all contact information."""
        data = {
            "address": "123 Main St, City",
            "phone": "555-1234",
            "email": "user@example.com",
            "github": "username",
            "web": "https://example.com",
            "linkedin": "in/username",
        }
        lines = build_contact_lines(data)
        # Should have all 6 lines
        assert len(lines) == 6

    def test_latex_escaping_in_phone(self) -> None:
        """Test that special chars in phone are escaped."""
        data = {"phone": "555-1234 ext#5"}
        lines = build_contact_lines(data)
        assert r"\#5" in lines[0]

    def test_url_escaping_in_links(self) -> None:
        """Test that URLs are properly escaped."""
        data = {"web": "https://example.com?param=value&other=test#anchor"}
        lines = build_contact_lines(data)
        assert r"\&" in lines[0]
        assert r"\#" in lines[0]

    def test_nolinkurl_in_email(self) -> None:
        """Test that email uses nolinkurl."""
        data = {"email": "user@example.com"}
        lines = build_contact_lines(data)
        assert r"\nolinkurl{" in lines[0]

    def test_nolinkurl_in_github(self) -> None:
        """Test that GitHub URL uses nolinkurl."""
        data = {"github": "username"}
        lines = build_contact_lines(data)
        assert r"\nolinkurl{" in lines[0]

    @pytest.mark.parametrize(
        "field,value,expected_icon",
        [
            ("address", "123 Main St", r"\faLocation"),
            ("phone", "555-1234", r"\faPhone"),
            ("email", "user@example.com", r"\faEnvelope"),
            ("github", "username", r"\faGithub"),
            ("web", "https://example.com", r"\faGlobe"),
            ("linkedin", "in/username", r"\faLinkedin"),
        ],
    )
    def test_correct_icons(self, field: str, value: str, expected_icon: str) -> None:
        """Test that correct icons are used for each field."""
        data = {field: value}
        lines = build_contact_lines(data)
        assert any(expected_icon in line for line in lines)


class TestPrepareSections:
    """Tests for prepare_sections function."""

    def test_empty_data(self) -> None:
        """Test with empty data."""
        sections = prepare_sections({})
        assert sections == []

    def test_no_body_section(self) -> None:
        """Test when data has no 'body' key."""
        data = {"full_name": "John Doe"}
        sections = prepare_sections(data)
        assert sections == []

    def test_body_not_dict(self) -> None:
        """Test when body is not a dictionary."""
        data = {"body": "not a dict"}
        sections = prepare_sections(data)
        assert sections == []

    def test_single_section_single_entry(self) -> None:
        """Test single section with single entry."""
        data = {
            "body": {
                "Experience": [
                    {
                        "title": "Software Engineer",
                        "company": "Tech Corp",
                        "start": "2020",
                        "end": "2023",
                        "description": "Developed software.",
                    }
                ]
            }
        }
        sections = prepare_sections(data)
        assert len(sections) == 1
        assert sections[0].title == "Experience"
        assert len(sections[0].entries) == 1
        assert sections[0].entries[0].title == "Software Engineer"

    def test_section_with_non_list_entries(self) -> None:
        """Test section where entries is not a list (should be skipped)."""
        data = {
            "body": {
                "Experience": "not a list",
            }
        }
        sections = prepare_sections(data)
        assert sections == []

    def test_entry_not_dict(self) -> None:
        """Test when entry is not a dictionary (should be skipped)."""
        data = {"body": {"Experience": ["not a dict", {"title": "Valid Entry"}]}}
        sections = prepare_sections(data)
        assert len(sections) == 1
        # Only the valid entry should be included
        assert len(sections[0].entries) == 1

    def test_entry_with_title_link(self) -> None:
        """Test entry with title_link."""
        data = {
            "body": {
                "Projects": [
                    {
                        "title": "My Project",
                        "title_link": "https://example.com",
                    }
                ]
            }
        }
        sections = prepare_sections(data)
        assert r"\href{https://example.com}" in sections[0].entries[0].title

    def test_entry_with_company_link(self) -> None:
        """Test entry with company_link."""
        data = {
            "body": {
                "Experience": [
                    {
                        "title": "Engineer",
                        "company": "Tech Corp",
                        "company_link": "https://techcorp.com",
                    }
                ]
            }
        }
        sections = prepare_sections(data)
        subtitle = sections[0].entries[0].subtitle
        assert subtitle is not None
        assert r"\href{https://techcorp.com}" in subtitle

    def test_entry_with_dates(self) -> None:
        """Test entry with start and end dates."""
        data = {
            "body": {
                "Experience": [
                    {
                        "title": "Engineer",
                        "start": "2020",
                        "end": "2023",
                    }
                ]
            }
        }
        sections = prepare_sections(data)
        assert sections[0].entries[0].date_range == "2020 -- 2023"

    def test_entry_with_description(self) -> None:
        """Test entry with description (converted to blocks)."""
        data = {
            "body": {
                "Experience": [
                    {
                        "title": "Engineer",
                        "description": "Led development team.\n\n- Task 1\n- Task 2",
                    }
                ]
            }
        }
        sections = prepare_sections(data)
        blocks = sections[0].entries[0].blocks
        assert len(blocks) == 2
        assert blocks[0]["kind"] == "paragraph"
        assert blocks[1]["kind"] == "itemize"

    def test_multiple_sections(self) -> None:
        """Test with multiple sections."""
        data = {
            "body": {
                "Experience": [{"title": "Job"}],
                "Education": [{"title": "Degree"}],
                "Projects": [{"title": "Project"}],
            }
        }
        sections = prepare_sections(data)
        assert len(sections) == 3
        section_titles = [s.title for s in sections]
        assert "Experience" in section_titles
        assert "Education" in section_titles
        assert "Projects" in section_titles

    def test_section_with_multiple_entries(self) -> None:
        """Test section with multiple entries."""
        data = {
            "body": {
                "Experience": [
                    {"title": "Job 1"},
                    {"title": "Job 2"},
                    {"title": "Job 3"},
                ]
            }
        }
        sections = prepare_sections(data)
        assert len(sections[0].entries) == 3

    def test_markdown_in_section_title(self) -> None:
        """Test markdown conversion in section title."""
        data = {"body": {"**Experience**": [{"title": "Job"}]}}
        sections = prepare_sections(data)
        assert r"\textbf{Experience}" in sections[0].title

    def test_markdown_in_entry_fields(self) -> None:
        """Test markdown conversion in entry fields."""
        data = {
            "body": {
                "Experience": [
                    {
                        "title": "**Senior** Engineer",
                        "company": "*Tech Corp*",
                    }
                ]
            }
        }
        sections = prepare_sections(data)
        title = sections[0].entries[0].title
        subtitle = sections[0].entries[0].subtitle
        assert title is not None
        assert subtitle is not None
        assert r"\textbf{Senior}" in title
        assert r"\textit{Tech Corp}" in subtitle

    def test_empty_section_not_included(self) -> None:
        """Test that sections with no valid entries are not included."""
        data = {
            "body": {
                "Empty": [],
                "Valid": [{"title": "Entry"}],
            }
        }
        sections = prepare_sections(data)
        # Only the valid section should be included
        assert len(sections) == 1
        assert sections[0].title == "Valid"


class TestPrepareSkillSections:
    """Tests for prepare_skill_sections function."""

    def test_empty_data(self) -> None:
        """Test with empty data."""
        sections = prepare_skill_sections({})
        assert sections == []

    def test_expertise_list(self) -> None:
        """Test with expertise as list."""
        data = {"expertise": ["Python", "JavaScript", "Go"]}
        sections = prepare_skill_sections(data)
        assert len(sections) == 1
        assert sections[0]["title"] == "Expertise"
        assert len(sections[0]["items"]) == 3

    def test_expertise_grouped(self) -> None:
        """Test with grouped expertise."""
        data = {
            "expertise": [
                {"Languages": ["Python", "Go"]},
                {"Frameworks": ["Django", "Flask"]},
            ]
        }
        sections = prepare_skill_sections(data)
        assert len(sections) == 2
        assert sections[0]["title"] == "Languages"
        assert sections[1]["title"] == "Frameworks"

    def test_programming_skills(self) -> None:
        """Test with programming skills."""
        data = {"programming": ["Python", "JavaScript"]}
        sections = prepare_skill_sections(data)
        assert len(sections) == 1
        assert sections[0]["title"] == "Programming"

    def test_keyskills(self) -> None:
        """Test with key skills."""
        data = {"keyskills": ["Leadership", "Communication"]}
        sections = prepare_skill_sections(data)
        assert len(sections) == 1
        assert sections[0]["title"] == "Key Skills"

    def test_certification(self) -> None:
        """Test with certifications."""
        data = {"certification": ["AWS Certified", "PMP"]}
        sections = prepare_skill_sections(data)
        assert len(sections) == 1
        assert sections[0]["title"] == "Certifications"

    def test_custom_titles(self) -> None:
        """Test with custom titles."""
        data = {
            "expertise": ["Python"],
            "titles": {
                "expertise": "Technical Expertise",
                "programming": "Programming Languages",
            },
        }
        sections = prepare_skill_sections(data)
        assert sections[0]["title"] == "Technical Expertise"

    def test_all_skill_types(self) -> None:
        """Test with all skill types."""
        data = {
            "expertise": ["Python"],
            "programming": ["JavaScript"],
            "keyskills": ["Leadership"],
            "certification": ["AWS"],
        }
        sections = prepare_skill_sections(data)
        assert len(sections) == 4

    def test_markdown_in_skills(self) -> None:
        """Test markdown conversion in skills."""
        data = {"expertise": ["**Python**", "*JavaScript*"]}
        sections = prepare_skill_sections(data)
        assert r"\textbf{Python}" in sections[0]["items"][0]
        assert r"\textit{JavaScript}" in sections[0]["items"][1]

    def test_markdown_in_group_title(self) -> None:
        """Test markdown in group title."""
        data = {
            "expertise": [
                {"**Languages**": ["Python"]},
            ]
        }
        sections = prepare_skill_sections(data)
        assert r"\textbf{Languages}" in sections[0]["title"]

    def test_none_values_filtered(self) -> None:
        """Test that empty string values in items are filtered."""
        data = {"expertise": ["Python", "", "JavaScript", "  "]}
        sections = prepare_skill_sections(data)
        # Only non-empty items should be included (empty strings and whitespace
        # filtered)
        assert len(sections[0]["items"]) == 2

    def test_empty_list_skipped(self) -> None:
        """Test that groups with empty list items are skipped."""
        data = {
            "expertise": [
                {"Valid": ["Python"]},
                {"Invalid": []},
            ]
        }
        sections = prepare_skill_sections(data)
        # Only the valid group should be included
        assert len(sections) == 1
        assert sections[0]["title"] == "Valid"

    def test_empty_items_skipped(self) -> None:
        """Test that groups with empty items lists are skipped."""
        data = {
            "expertise": [
                {"Empty": []},
                {"Valid": ["Python"]},
            ]
        }
        sections = prepare_skill_sections(data)
        assert len(sections) == 1
        assert sections[0]["title"] == "Valid"

    def test_group_without_title(self) -> None:
        """Test group without explicit title uses default."""
        # When expertise is a simple list, not grouped, it uses default title
        data = {
            "expertise": ["Python", "JavaScript"],
        }
        sections = prepare_skill_sections(data)
        assert len(sections) == 1
        assert sections[0]["title"] == "Expertise"
