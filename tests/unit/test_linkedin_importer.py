"""Tests for LinkedIn profile to simple-resume conversion.

Feature: LinkedIn Import
    As a job seeker
    I want to import my LinkedIn profile data
    So that I can quickly create a simple-resume YAML file
"""

from __future__ import annotations

from simple_resume.core.importers.linkedin import linkedin_to_simple_resume


def _make_profile(**overrides: object) -> dict:
    """Build a minimal LinkedIn profile dict with optional overrides."""
    base = {
        "full_name": "Jane Doe",
        "headline": "Senior Software Engineer",
        "email": "jane@example.com",
        "location": "San Francisco, CA",
        "summary": "Experienced engineer with 10 years in backend systems.",
    }
    base.update(overrides)
    return base


class TestLinkedInToSimpleResume:
    """Scenario group: converting a LinkedIn profile dict to simple-resume format."""

    def test_minimal_profile_returns_valid_structure(self):
        """Given a minimal profile, the result has template and full_name."""
        result = linkedin_to_simple_resume({"full_name": "Test User"})
        assert result["template"] == "resume_no_bars"
        assert result["full_name"] == "Test User"

    def test_header_fields_mapped(self):
        """Given a profile with header fields, they map to simple-resume keys."""
        result = linkedin_to_simple_resume(_make_profile())
        assert result["full_name"] == "Jane Doe"
        assert result["job_title"] == "Senior Software Engineer"
        assert result["email"] == "jane@example.com"
        assert result["address"] == ["San Francisco, CA"]
        expected_desc = "Experienced engineer with 10 years in backend systems."
        assert result["description"] == expected_desc

    def test_linkedin_url_mapped(self):
        """Given a profile with linkedin_url, it maps to linkedin field."""
        result = linkedin_to_simple_resume(_make_profile(linkedin_url="in/jane-doe"))
        assert result["linkedin"] == "in/jane-doe"

    def test_experience_converted_to_body(self):
        """Given experience entries, they become body['Experience'] entries."""
        profile = _make_profile(
            experience=[
                {
                    "title": "Senior Engineer",
                    "company": "Acme Corp",
                    "start_date": "2020-01",
                    "end_date": "2023-06",
                    "description": "Built APIs.",
                },
                {
                    "title": "Junior Engineer",
                    "company": "Startup Inc",
                    "start_date": "2017-03",
                    "end_date": "2020-01",
                    "description": "Frontend work.",
                },
            ]
        )
        result = linkedin_to_simple_resume(profile)
        exp = result["body"]["Experience"]
        assert len(exp) == 2
        assert exp[0]["title"] == "Senior Engineer"
        assert exp[0]["company"] == "Acme Corp"
        assert exp[0]["start"] == "2020-01"
        assert exp[0]["end"] == "2023-06"
        assert exp[0]["description"] == "Built APIs."

    def test_education_converted_to_body(self):
        """Given education entries, they become body['Education'] entries."""
        profile = _make_profile(
            education=[
                {
                    "degree": "B.S.",
                    "field_of_study": "Computer Science",
                    "school": "MIT",
                    "start_date": "2013",
                    "end_date": "2017",
                }
            ]
        )
        result = linkedin_to_simple_resume(profile)
        edu = result["body"]["Education"]
        assert len(edu) == 1
        assert edu[0]["title"] == "B.S. Computer Science"
        assert edu[0]["company"] == "MIT"

    def test_skills_converted_to_keyskills(self):
        """Given a skills list, they become sorted keyskills."""
        profile = _make_profile(skills=["Python", "Go", "Python", "AWS"])
        result = linkedin_to_simple_resume(profile)
        assert result["keyskills"] == ["AWS", "Go", "Python"]

    def test_skills_from_dicts(self):
        """Given skills as list of dicts with 'name' key, they are extracted."""
        profile = _make_profile(skills=[{"name": "Docker"}, {"name": "Kubernetes"}])
        result = linkedin_to_simple_resume(profile)
        assert result["keyskills"] == ["Docker", "Kubernetes"]

    def test_empty_experience_omitted(self):
        """Given an empty experience list, body has no Experience key."""
        profile = _make_profile(experience=[])
        result = linkedin_to_simple_resume(profile)
        assert "body" not in result or "Experience" not in result.get("body", {})

    def test_empty_skills_omitted(self):
        """Given an empty skills list, keyskills is absent."""
        profile = _make_profile(skills=[])
        result = linkedin_to_simple_resume(profile)
        assert "keyskills" not in result

    def test_empty_profile_returns_template_only(self):
        """Given an empty profile dict, only template is set."""
        result = linkedin_to_simple_resume({})
        assert result == {"template": "resume_no_bars"}

    def test_alternative_key_names(self):
        """Given alternative key names (name, about), they still map correctly."""
        profile = {
            "name": "Alt Name",
            "about": "Alt description.",
        }
        result = linkedin_to_simple_resume(profile)
        assert result["full_name"] == "Alt Name"
        assert result["description"] == "Alt description."

    def test_current_position_gets_present_end_date(self):
        """Given is_current flag on experience, end date becomes 'Present'."""
        profile = _make_profile(
            experience=[
                {
                    "title": "Lead Engineer",
                    "company": "Current Co",
                    "start_date": "2023-01",
                    "is_current": "true",
                }
            ]
        )
        result = linkedin_to_simple_resume(profile)
        assert result["body"]["Experience"][0]["end"] == "Present"

    def test_whitespace_stripped_from_values(self):
        """Given values with whitespace, they are stripped."""
        profile = {"full_name": "  Jane Doe  ", "headline": " Engineer "}
        result = linkedin_to_simple_resume(profile)
        assert result["full_name"] == "Jane Doe"
        assert result["job_title"] == "Engineer"
