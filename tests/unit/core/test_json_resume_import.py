from __future__ import annotations

from simple_resume.core.importers.json_resume import json_resume_to_simple_resume


def test_json_resume_conversion_produces_minimal_simple_resume() -> None:
    """Given a complete JSON Resume payload.

    When converting to simple resume format, then all basic fields are
    correctly mapped and structured.
    """
    payload = {
        "basics": {
            "name": "Jane Doe",
            "label": "Software Engineer",
            "email": "jane@example.com",
            "phone": "+1 555 555 5555",
            "url": "https://example.com",
            "summary": "Builder of reliable systems.",
            "profiles": [
                {
                    "network": "LinkedIn",
                    "username": "in/jane",
                    "url": "https://www.linkedin.com/in/jane",
                },
                {
                    "network": "GitHub",
                    "username": "janedoe",
                    "url": "https://github.com/janedoe",
                },
            ],
        },
        "work": [
            {
                "name": "TechCorp",
                "position": "Senior Engineer",
                "url": "https://techcorp.example",
                "startDate": "2022-01",
                "endDate": "Present",
                "summary": "Platform work",
                "highlights": ["Cut latency 40%", "Led migration"],
            }
        ],
        "skills": [{"name": "Backend", "keywords": ["Python", "PostgreSQL"]}],
    }

    converted = json_resume_to_simple_resume(payload)

    assert converted["full_name"] == "Jane Doe"
    assert converted["email"] == "jane@example.com"
    assert converted["headline"] == "Software Engineer"
    assert converted["config"] == {"template": "resume_no_bars"}
    assert converted["template"] == "resume_no_bars"

    assert "body" in converted
    assert "Experience" in converted["body"]
    assert converted["body"]["Experience"][0]["company"] == "TechCorp"
    assert "- Cut latency 40%" in converted["body"]["Experience"][0]["description"]

    assert "expertise" in converted
    assert "Backend" in converted["expertise"]
    assert "keyskills" in converted
    assert "Python" in converted["keyskills"]


def test_json_resume_with_full_location_builds_complete_address() -> None:
    """Given a JSON Resume with complete location details.

    When converting, then address is constructed from all components.
    """
    payload = {
        "basics": {
            "name": "John Smith",
            "email": "john@example.com",
            "location": {
                "address": "123 Main Street",
                "city": "San Francisco",
                "region": "CA",
                "postalCode": "94102",
                "countryCode": "US",
            },
        }
    }

    converted = json_resume_to_simple_resume(payload)

    assert "address" in converted
    assert converted["address"] == [
        "123 Main Street",
        "San Francisco CA 94102",
        "US",
    ]


def test_json_resume_with_partial_location_builds_partial_address() -> None:
    """Given a JSON Resume with partial location details.

    When converting, then only available components are used.
    """
    payload = {
        "basics": {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "location": {
                "city": "New York",
                "countryCode": "USA",
            },
        }
    }

    converted = json_resume_to_simple_resume(payload)

    assert "address" in converted
    assert converted["address"] == ["New York", "USA"]


def test_json_resume_with_empty_location_skips_address() -> None:
    """Given a JSON Resume with empty location object.

    When converting, then address field is not added.
    """
    payload = {
        "basics": {
            "name": "Bob Jones",
            "email": "bob@example.com",
            "location": {},
        }
    }

    converted = json_resume_to_simple_resume(payload)

    assert "address" not in converted


def test_json_resume_with_education_includes_gpa_and_courses() -> None:
    """Given a JSON Resume with education including GPA and courses.

    When converting, then these details are included in description.
    """
    payload = {
        "basics": {
            "name": "Alice Student",
            "email": "alice@example.com",
        },
        "education": [
            {
                "institution": "University of Tech",
                "studyType": "Bachelor of Science",
                "area": "Computer Science",
                "startDate": "2018-09",
                "endDate": "2022-05",
                "gpa": "3.8",
                "courses": ["Data Structures", "Algorithms", "Databases"],
            }
        ],
    }

    converted = json_resume_to_simple_resume(payload)

    assert "Education" in converted["body"]
    edu_entry = converted["body"]["Education"][0]
    assert edu_entry["company"] == "University of Tech"
    assert edu_entry["title"] == "Bachelor of Science Computer Science"
    assert "GPA: 3.8" in edu_entry["description"]
    assert "Courses:" in edu_entry["description"]
    assert "- Data Structures" in edu_entry["description"]


def test_json_resume_with_projects_converts_highlights_to_markdown() -> None:
    """Given a JSON Resume with projects containing highlights.

    When converting, then highlights are formatted as markdown bullets.
    """
    payload = {
        "basics": {
            "name": "Dev Creator",
            "email": "dev@example.com",
        },
        "projects": [
            {
                "name": "Awesome Project",
                "entity": "Tech Startup",
                "description": "A cool application",
                "highlights": [
                    "Built REST API",
                    "Integrated payment gateway",
                    "Deployed to cloud",
                ],
                "startDate": "2023-01",
                "endDate": "2023-06",
            }
        ],
    }

    converted = json_resume_to_simple_resume(payload)

    assert "Projects" in converted["body"]
    project = converted["body"]["Projects"][0]
    assert project["title"] == "Awesome Project"
    assert project["company"] == "Tech Startup"
    assert "- Built REST API" in project["description"]
    assert "- Integrated payment gateway" in project["description"]


def test_json_resume_with_invalid_profile_entries_skips_gracefully() -> None:
    """Given a JSON Resume with mixed valid and invalid profile entries.

    When converting, then only valid profiles are processed.
    """
    payload = {
        "basics": {
            "name": "Mixed Profiles",
            "email": "mixed@example.com",
            "profiles": [
                {
                    "network": "GitHub",
                    "username": "validuser",
                    "url": "https://github.com/validuser",
                },
                "invalid_string_profile",
                None,
                {
                    "network": "LinkedIn",
                    "url": "https://linkedin.com/in/test",
                },
            ],
        }
    }

    converted = json_resume_to_simple_resume(payload)

    # Should have github from valid profile
    assert "github" in converted
    assert converted["github"] == "validuser"
    # Should have linkedin from valid profile
    assert "linkedin" in converted


def test_json_resume_with_minimal_data_produces_valid_resume() -> None:
    """Given a JSON Resume with only required fields.

    When converting, then produces a valid minimal resume without body field.
    """
    payload = {
        "basics": {
            "name": "Minimal User",
            "email": "minimal@example.com",
        }
    }

    converted = json_resume_to_simple_resume(payload)

    assert converted["full_name"] == "Minimal User"
    assert converted["email"] == "minimal@example.com"
    assert converted["template"] == "resume_no_bars"
    assert converted["config"] == {"template": "resume_no_bars"}
    # Body is only added when there are actual sections
    assert "body" not in converted
