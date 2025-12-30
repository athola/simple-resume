"""Tests for LaTeX section preparation functions."""

from __future__ import annotations

import pytest

from simple_resume.core.latex.sections import (
    build_contact_lines,
    prepare_sections,
    prepare_skill_sections,
)
from tests.bdd import Scenario


class TestBuildContactLines:
    """Tests for build_contact_lines function."""

    def test_empty_data(self, story: Scenario) -> None:
        """Test with empty data dictionary."""
        story.given("an empty data dictionary")
        story.when("building contact lines")
        lines = build_contact_lines({})
        assert lines == []

    def test_address_string(self, story: Scenario) -> None:
        """Test with address as string."""
        story.given("data with address as a string")
        story.when("building contact lines")
        data = {"address": "123 Main St, City, State"}
        lines = build_contact_lines(data)
        assert len(lines) == 1
        assert r"\faLocation" in lines[0]
        assert "123 Main St" in lines[0]

    def test_address_list(self, story: Scenario) -> None:
        """Test with address as list."""
        story.given("data with address as a list")
        story.when("building contact lines")
        data = {"address": ["123 Main St", "City", "State", "12345"]}
        lines = build_contact_lines(data)
        assert len(lines) == 1
        assert r"\faLocation" in lines[0]
        assert "123 Main St, City, State, 12345" in lines[0]

    def test_address_with_none_values(self, story: Scenario) -> None:
        """Test address list with None values (should be filtered)."""
        story.given("address list containing None and empty values")
        story.when("building contact lines")
        data = {"address": ["123 Main St", None, "City", ""]}
        lines = build_contact_lines(data)
        assert len(lines) == 1
        # None and empty strings should be filtered out
        assert "123 Main St, City" in lines[0]

    def test_phone_number(self, story: Scenario) -> None:
        """Test with phone number."""
        story.given("data with a phone number")
        story.when("building contact lines")
        data = {"phone": "+1-555-1234"}
        lines = build_contact_lines(data)
        assert len(lines) == 1
        assert r"\faPhone" in lines[0]
        assert "+1-555-1234" in lines[0]

    def test_email(self, story: Scenario) -> None:
        """Test with email address."""
        story.given("data with an email address")
        story.when("building contact lines")
        data = {"email": "user@example.com"}
        lines = build_contact_lines(data)
        assert len(lines) == 1
        assert r"\faEnvelope" in lines[0]
        assert r"\href{mailto:" in lines[0]
        assert "user@example.com" in lines[0]

    def test_email_with_special_chars(self, story: Scenario) -> None:
        """Test email with special characters."""
        story.given("an email address containing special characters")
        story.when("building contact lines")
        data = {"email": "user+tag@example.com"}
        lines = build_contact_lines(data)
        assert len(lines) == 1
        assert "user+tag@example.com" in lines[0]

    def test_github_username(self, story: Scenario) -> None:
        """Test with GitHub username."""
        story.given("data with a GitHub username")
        story.when("building contact lines")
        data = {"github": "username"}
        lines = build_contact_lines(data)
        assert len(lines) == 1
        assert r"\faGithub" in lines[0]
        assert "https://github.com/username" in lines[0]

    def test_github_full_url(self, story: Scenario) -> None:
        """Test with full GitHub URL."""
        story.given("data with a full GitHub URL")
        story.when("building contact lines")
        data = {"github": "https://github.com/username"}
        lines = build_contact_lines(data)
        assert len(lines) == 1
        assert "https://github.com/username" in lines[0]

    def test_github_with_leading_slash(self, story: Scenario) -> None:
        """Test GitHub username with leading slash."""
        story.given("GitHub username with leading slash")
        story.when("building contact lines")
        data = {"github": "/username"}
        lines = build_contact_lines(data)
        assert "https://github.com/username" in lines[0]

    def test_web_url(self, story: Scenario) -> None:
        """Test with web URL."""
        story.given("data with a web URL")
        story.when("building contact lines")
        data = {"web": "https://example.com"}
        lines = build_contact_lines(data)
        assert len(lines) == 1
        assert r"\faGlobe" in lines[0]
        assert "https://example.com" in lines[0]

    def test_web_with_github_domain(self, story: Scenario) -> None:
        """Test web URL with github.com domain."""
        story.given("web URL pointing to github.com")
        story.when("building contact lines")
        data = {"web": "https://github.com/username"}
        lines = build_contact_lines(data)
        assert len(lines) == 1
        assert r"\faGithub" in lines[0]

    def test_both_github_and_web_github(self, story: Scenario) -> None:
        """Test with both github field and web field pointing to github."""
        story.given("both github and web fields pointing to same GitHub profile")
        story.when("building contact lines")
        data = {
            "github": "username",
            "web": "https://github.com/username",
        }
        lines = build_contact_lines(data)
        # Should only show github once
        github_lines = [line for line in lines if r"\faGithub" in line]
        assert len(github_lines) == 1

    def test_linkedin(self, story: Scenario) -> None:
        """Test with LinkedIn profile."""
        story.given("data with a LinkedIn profile path")
        story.when("building contact lines")
        data = {"linkedin": "in/username"}
        lines = build_contact_lines(data)
        assert len(lines) == 1
        assert r"\faLinkedin" in lines[0]
        assert "https://www.linkedin.com/in/username" in lines[0]

    def test_linkedin_full_url(self, story: Scenario) -> None:
        """Test with full LinkedIn URL."""
        story.given("data with a full LinkedIn URL")
        story.when("building contact lines")
        data = {"linkedin": "https://www.linkedin.com/in/username"}
        lines = build_contact_lines(data)
        assert len(lines) == 1
        assert "https://www.linkedin.com/in/username" in lines[0]

    def test_all_contact_info(self, story: Scenario) -> None:
        """Test with all contact information."""
        story.given("data with all contact fields populated")
        story.when("building contact lines")
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

    def test_latex_escaping_in_phone(self, story: Scenario) -> None:
        """Test that special chars in phone are escaped."""
        story.given("phone number with LaTeX special character '#'")
        story.when("building contact lines")
        data = {"phone": "555-1234 ext#5"}
        lines = build_contact_lines(data)
        assert r"\#5" in lines[0]

    def test_url_escaping_in_links(self, story: Scenario) -> None:
        """Test that URLs are properly escaped."""
        story.given("web URL with query params, ampersand, and anchor")
        story.when("building contact lines")
        data = {"web": "https://example.com?param=value&other=test#anchor"}
        lines = build_contact_lines(data)
        assert r"\&" in lines[0]
        assert r"\#" in lines[0]

    def test_nolinkurl_in_email(self, story: Scenario) -> None:
        """Test that email uses nolinkurl."""
        story.given("data with an email address")
        story.when("building contact lines")
        data = {"email": "user@example.com"}
        lines = build_contact_lines(data)
        assert r"\nolinkurl{" in lines[0]

    def test_nolinkurl_in_github(self, story: Scenario) -> None:
        """Test that GitHub URL uses nolinkurl."""
        story.given("data with a GitHub username")
        story.when("building contact lines")
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
    def test_correct_icons(
        self, field: str, value: str, expected_icon: str, story: Scenario
    ) -> None:
        """Test that correct icons are used for each field."""
        story.given(f"contact field '{field}' with value '{value}'")
        story.when("building contact lines")
        data = {field: value}
        lines = build_contact_lines(data)
        assert any(expected_icon in line for line in lines)


class TestPrepareSections:
    """Tests for prepare_sections function."""

    def test_empty_data(self, story: Scenario) -> None:
        """Test with empty data."""
        story.given("an empty data dictionary")
        story.when("preparing sections")
        sections = prepare_sections({})
        assert sections == []

    def test_no_body_section(self, story: Scenario) -> None:
        """Test when data has no 'body' key."""
        story.given("data with full_name but no body key")
        story.when("preparing sections")
        data = {"full_name": "John Doe"}
        sections = prepare_sections(data)
        assert sections == []

    def test_body_not_dict(self, story: Scenario) -> None:
        """Test when body is not a dictionary."""
        story.given("body field as a string instead of dict")
        story.when("preparing sections")
        data = {"body": "not a dict"}
        sections = prepare_sections(data)
        assert sections == []

    def test_single_section_single_entry(self, story: Scenario) -> None:
        """Test single section with single entry."""
        story.given("body with one Experience section containing one entry")
        story.when("preparing sections")
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

    def test_section_with_non_list_entries(self, story: Scenario) -> None:
        """Test section where entries is not a list (should be skipped)."""
        story.given("section entries as a string instead of list")
        story.when("preparing sections")
        data = {
            "body": {
                "Experience": "not a list",
            }
        }
        sections = prepare_sections(data)
        assert sections == []

    def test_entry_not_dict(self, story: Scenario) -> None:
        """Test when entry is not a dictionary (should be skipped)."""
        story.given("entry list with a string and a valid dict entry")
        story.when("preparing sections")
        data = {"body": {"Experience": ["not a dict", {"title": "Valid Entry"}]}}
        sections = prepare_sections(data)
        assert len(sections) == 1
        # Only the valid entry should be included
        assert len(sections[0].entries) == 1

    def test_entry_with_title_link(self, story: Scenario) -> None:
        """Test entry with title_link."""
        story.given("entry with title and title_link")
        story.when("preparing sections")
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

    def test_entry_with_company_link(self, story: Scenario) -> None:
        """Test entry with company_link."""
        story.given("entry with company and company_link")
        story.when("preparing sections")
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

    def test_entry_with_dates(self, story: Scenario) -> None:
        """Test entry with start and end dates."""
        story.given("entry with start and end dates")
        story.when("preparing sections")
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

    def test_entry_with_description(self, story: Scenario) -> None:
        """Test entry with description (converted to blocks)."""
        story.given("entry with multi-block description (paragraph + list)")
        story.when("preparing sections")
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

    def test_multiple_sections(self, story: Scenario) -> None:
        """Test with multiple sections."""
        story.given("body with Experience, Education, and Projects sections")
        story.when("preparing sections")
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

    def test_section_with_multiple_entries(self, story: Scenario) -> None:
        """Test section with multiple entries."""
        story.given("Experience section with three job entries")
        story.when("preparing sections")
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

    def test_markdown_in_section_title(self, story: Scenario) -> None:
        """Test markdown conversion in section title."""
        story.given("section title with markdown bold syntax")
        story.when("preparing sections")
        data = {"body": {"**Experience**": [{"title": "Job"}]}}
        sections = prepare_sections(data)
        assert r"\textbf{Experience}" in sections[0].title

    def test_markdown_in_entry_fields(self, story: Scenario) -> None:
        """Test markdown conversion in entry fields."""
        story.given("entry with markdown in title and company fields")
        story.when("preparing sections")
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

    def test_empty_section_not_included(self, story: Scenario) -> None:
        """Test that sections with no valid entries are not included."""
        story.given("body with an empty section and a valid section")
        story.when("preparing sections")
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

    def test_empty_data(self, story: Scenario) -> None:
        """Test with empty data."""
        story.given("an empty data dictionary")
        story.when("preparing skill sections")
        sections = prepare_skill_sections({})
        assert sections == []

    def test_expertise_list(self, story: Scenario) -> None:
        """Test with expertise as list."""
        story.given("expertise field with three skills in a list")
        story.when("preparing skill sections")
        data = {"expertise": ["Python", "JavaScript", "Go"]}
        sections = prepare_skill_sections(data)
        assert len(sections) == 1
        assert sections[0]["title"] == "Expertise"
        assert len(sections[0]["items"]) == 3

    def test_expertise_grouped(self, story: Scenario) -> None:
        """Test with grouped expertise."""
        story.given("expertise as grouped dict items (Languages, Frameworks)")
        story.when("preparing skill sections")
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

    def test_programming_skills(self, story: Scenario) -> None:
        """Test with programming skills."""
        story.given("programming field with two languages")
        story.when("preparing skill sections")
        data = {"programming": ["Python", "JavaScript"]}
        sections = prepare_skill_sections(data)
        assert len(sections) == 1
        assert sections[0]["title"] == "Programming"

    def test_keyskills(self, story: Scenario) -> None:
        """Test with key skills."""
        story.given("keyskills field with soft skills")
        story.when("preparing skill sections")
        data = {"keyskills": ["Leadership", "Communication"]}
        sections = prepare_skill_sections(data)
        assert len(sections) == 1
        assert sections[0]["title"] == "Key Skills"

    def test_certification(self, story: Scenario) -> None:
        """Test with certifications."""
        story.given("certification field with two certifications")
        story.when("preparing skill sections")
        data = {"certification": ["AWS Certified", "PMP"]}
        sections = prepare_skill_sections(data)
        assert len(sections) == 1
        assert sections[0]["title"] == "Certifications"

    def test_custom_titles(self, story: Scenario) -> None:
        """Test with custom titles."""
        story.given("expertise field with custom titles mapping")
        story.when("preparing skill sections")
        data = {
            "expertise": ["Python"],
            "titles": {
                "expertise": "Technical Expertise",
                "programming": "Programming Languages",
            },
        }
        sections = prepare_skill_sections(data)
        assert sections[0]["title"] == "Technical Expertise"

    def test_all_skill_types(self, story: Scenario) -> None:
        """Test with all skill types."""
        story.given(
            "all four skill types (expertise, programming, keyskills, certification)"
        )
        story.when("preparing skill sections")
        data = {
            "expertise": ["Python"],
            "programming": ["JavaScript"],
            "keyskills": ["Leadership"],
            "certification": ["AWS"],
        }
        sections = prepare_skill_sections(data)
        assert len(sections) == 4

    def test_markdown_in_skills(self, story: Scenario) -> None:
        """Test markdown conversion in skills."""
        story.given("expertise skills with markdown bold and italic")
        story.when("preparing skill sections")
        data = {"expertise": ["**Python**", "*JavaScript*"]}
        sections = prepare_skill_sections(data)
        assert r"\textbf{Python}" in sections[0]["items"][0]
        assert r"\textit{JavaScript}" in sections[0]["items"][1]

    def test_markdown_in_group_title(self, story: Scenario) -> None:
        """Test markdown in group title."""
        story.given("grouped expertise with markdown bold in group title")
        story.when("preparing skill sections")
        data = {
            "expertise": [
                {"**Languages**": ["Python"]},
            ]
        }
        sections = prepare_skill_sections(data)
        assert r"\textbf{Languages}" in sections[0]["title"]

    def test_none_values_filtered(self, story: Scenario) -> None:
        """Test that empty string values in items are filtered."""
        story.given("expertise list with empty strings and whitespace")
        story.when("preparing skill sections")
        data = {"expertise": ["Python", "", "JavaScript", "  "]}
        sections = prepare_skill_sections(data)
        # Only non-empty items should be included (empty strings and whitespace
        # filtered)
        assert len(sections[0]["items"]) == 2

    def test_empty_list_skipped(self, story: Scenario) -> None:
        """Test that groups with empty list items are skipped."""
        story.given("grouped expertise with one valid group and one empty group")
        story.when("preparing skill sections")
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

    def test_empty_items_skipped(self, story: Scenario) -> None:
        """Test that groups with empty items lists are skipped."""
        story.given("grouped expertise with empty group first, valid group second")
        story.when("preparing skill sections")
        data = {
            "expertise": [
                {"Empty": []},
                {"Valid": ["Python"]},
            ]
        }
        sections = prepare_skill_sections(data)
        assert len(sections) == 1
        assert sections[0]["title"] == "Valid"

    def test_group_without_title(self, story: Scenario) -> None:
        """Test group without explicit title uses default."""
        story.given("expertise as simple list (no grouping)")
        story.when("preparing skill sections")
        # When expertise is a simple list, not grouped, it uses default title
        data = {
            "expertise": ["Python", "JavaScript"],
        }
        sections = prepare_skill_sections(data)
        assert len(sections) == 1
        assert sections[0]["title"] == "Expertise"
