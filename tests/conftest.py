"""Pytest configuration and fixtures for Resume project tests."""

from __future__ import annotations

import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
import yaml

from .bdd import Scenario
from .bdd import scenario as make_scenario


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_resume_data() -> dict[str, Any]:
    """Sample Resume data for testing."""
    return {
        "template": "resume_no_bars",
        "full_name": "John Doe",
        "address": ["123 Test St", "Test City, TC 12345"],
        "titles": {
            "contact": "Contact",
            "certification": "Certifications",
            "expertise": "Expertise",
            "keyskills": "Key Skills",
        },
        "phone": "555-123-4567",
        "email": "john.doe@example.com",
        "web": "https://johndoe.dev",
        "linkedin": "in/johndoe",
        "description": "This is a **test** description with *markdown* formatting.",
        "expertise": ["Python", "Testing", "TDD"],
        "certification": ["Test Certification", "Another Certificate"],
        "keyskills": ["Skill 1", "Skill 2", "Skill 3"],
        "body": {
            "Experience": [
                {
                    "start": "01/2020",
                    "end": "Present",
                    "title": "Senior Developer",
                    "company": "Test Company",
                    "description": (
                        "- Developed core features\n"
                        "- Wrote tests\n"
                        "- Followed TDD principles"
                    ),
                }
            ],
            "Education": [
                {
                    "start": "09/2015",
                    "end": "05/2019",
                    "title": "Bachelor of Science",
                    "company": "Test University",
                    "description": "Graduated with honors in Computer Science",
                }
            ],
        },
        "config": {
            "theme_color": "#0395DE",
            "sidebar_color": "#F6F6F6",
            "sidebar_text_color": "#000000",
            "bar_background_color": "#DFDFDF",
            "date2_color": "#616161",
            "frame_color": "#757575",
            "heading_icon_color": "#0395DE",
            "bold_color": "#000000",
            "padding": 12,
            "page_width": 190,
            "page_height": 270,
            "sidebar_width": 60,
            "profile_image_padding_bottom": 6,
            "pitch_padding_top": 4,
            "pitch_padding_bottom": 4,
            "pitch_padding_left": 4,
            "h2_padding_left": 4,
            "date_container_width": 13,
            "date_container_padding_left": 8,
            "description_container_padding_left": 3,
            "frame_padding": 10,
            "cover_padding_top": 10,
            "cover_padding_bottom": 20,
            "cover_padding_h": 25,
            # Sidebar padding defaults (matching _apply_config_defaults)
            "sidebar_padding_left": 10,  # base_padding - 2
            "sidebar_padding_right": 10,  # base_padding - 2
            "sidebar_padding_top": 0,
            "sidebar_padding_bottom": 12,  # base_padding
            # Spacing defaults (matching _apply_config_defaults)
            "skill_container_padding_top": 3,
            "skill_spacer_padding_top": 3,
            "h3_padding_top": 7,
            "h2_padding_top": 8,
            "section_heading_margin_top": 4,
            "section_heading_margin_bottom": 2,
        },
    }


@pytest.fixture
def sample_resume_file(temp_dir: Path, sample_resume_data: dict[str, Any]) -> Path:
    """Create a sample Resume YAML file for testing."""
    resume_file = temp_dir / "test_resume.yaml"
    with open(resume_file, "w", encoding="utf-8") as f:
        yaml.dump(sample_resume_data, f, default_flow_style=False, allow_unicode=True)
    return resume_file


def create_complete_resume_data(
    template: str = "resume_no_bars",
    full_name: str = "Test User",
    experience: list[dict[str, Any]] | None = None,
    expertise: list[str] | dict[str, int] | None = None,
    description: str = "This is a **test** description.",
) -> dict[str, Any]:
    """Create a complete Resume data structure with all required fields."""
    if experience is None:
        experience = [
            {
                "start": "01/2020",
                "end": "Present",
                "title": "Test Developer",
                "company": "Test Company",
                "description": ("- Developed core features\n- Wrote tests"),
            }
        ]

    # Different templates expect different data formats
    certification: list[str] | dict[str, int]

    if template == "resume_with_bars":
        if expertise is None:
            expertise = {"Python": 95, "Testing": 90, "TDD": 85}
        certification = {"Test Certification": 90, "Another Certificate": 85}
    else:
        if expertise is None:
            expertise = ["Python", "Testing", "TDD"]
        certification = ["Test Certification", "Another Certificate"]

    return {
        "template": template,
        "full_name": full_name,
        "address": ["123 Test St", "Test City, TC 12345"],
        "titles": {
            "contact": "Contact",
            "certification": "Certifications",
            "expertise": "Expertise",
            "keyskills": "Key Skills",
        },
        "phone": "555-123-4567",
        "email": f"{full_name.lower().replace(' ', '.')}@example.com",
        "github": full_name.lower().replace(" ", ""),
        "web": "https://example.com",
        "linkedin": "in/testuser",
        "description": description,
        "expertise": expertise,
        "certification": certification,
        "keyskills": ["Skill 1", "Skill 2", "Skill 3"],
        "programming": (
            {"Python": 90, "JavaScript": 80, "React": 75}
            if template == "resume_with_bars"
            else []
        ),
        "body": {
            "Experience": experience,
            "Education": [
                {
                    "start": "09/2015",
                    "end": "05/2019",
                    "title": "Bachelor of Science",
                    "company": "Test University",
                    "description": "Graduated with honors in Computer Science",
                }
            ],
        },
        "config": {
            "theme_color": "#0395DE",
            "sidebar_color": "#F6F6F6",
            "sidebar_text_color": "#000000",
            "bar_background_color": "#DFDFDF",
            "date2_color": "#616161",
            "frame_color": "#757575",
            "heading_icon_color": "#0395DE",
            "bold_color": "#000000",
            "padding": 12,
            "page_width": 190,
            "page_height": 270,
            "sidebar_width": 60,
            "profile_image_padding_bottom": 6,
            "pitch_padding_top": 4,
            "pitch_padding_bottom": 4,
            "pitch_padding_left": 4,
            "h2_padding_left": 4,
            "date_container_width": 13,
            "date_container_padding_left": 8,
            "description_container_padding_left": 3,
            "frame_padding": 10,
            "cover_padding_top": 10,
            "cover_padding_bottom": 20,
            "cover_padding_h": 25,
            # Sidebar padding defaults (matching _apply_config_defaults)
            "sidebar_padding_left": 10,  # base_padding - 2
            "sidebar_padding_right": 10,  # base_padding - 2
            "sidebar_padding_top": 0,
            "sidebar_padding_bottom": 12,  # base_padding
            # Spacing defaults (matching _apply_config_defaults)
            "skill_container_padding_top": 3,
            "skill_spacer_padding_top": 3,
            "h3_padding_top": 7,
            "h2_padding_top": 8,
            "section_heading_margin_top": 4,
            "section_heading_margin_bottom": 2,
        },
    }


def make_resume_missing_contact(
    full_name: str = "User Without Contact",
) -> dict[str, Any]:
    """Return resume data stripped of contact details for negative-path tests."""

    data = create_complete_resume_data(full_name=full_name)
    for key in ("address", "phone", "email", "github", "web", "linkedin"):
        data.pop(key, None)
    return data


def make_resume_with_projects(full_name: str = "Project User") -> dict[str, Any]:
    """Resume data that includes a Projects section for scenario-based tests."""

    data = create_complete_resume_data(full_name=full_name)
    data.setdefault("body", {})["Projects"] = [
        {
            "start": "2023",
            "end": "2024",
            "title": "ML Platform",
            "title_link": "https://example.com/ml",
            "company": "Side Project",
            "company_link": "https://example.com",
            "description": "Built ML platform with reproducible pipelines.",
        }
    ]
    return data


@pytest.fixture
def sample_resume_with_markdown() -> dict[str, Any]:
    """Sample Resume data with markdown content for testing."""
    return {
        "template": "resume_no_bars",
        "full_name": "Jane Smith",
        "description": """
# Professional Summary
This is a detailed description with **bold text**, *italic text*, and [links](https://example.com).

## Key Achievements
- Led a team of 5 developers
- Increased test coverage from 50% to 95%
- Implemented TDD across all projects

### Technical Skills
- **Python**: Expert level
- **Testing**: Pytest, unittest, mocking
- **CI/CD**: GitHub Actions, GitLab CI

Visit my [portfolio](https://janesmith.dev) for more examples.
        """.strip(),
        "body": {
            "Experience": [
                {
                    "start": "01/2021",
                    "end": "Present",
                    "title": "Lead Developer",
                    "company": "Tech Corp",
                    "description": """
## Responsibilities
- Architecture design and implementation
- **Code review** and mentoring
- Establishing **testing best practices**

### Key Projects
1. **E-commerce Platform**: Built using Django with 100% test coverage
2. **API Gateway**: Microservices architecture with integration tests
3. **Testing Framework**: Custom pytest plugins for the organization

*Learn more about our [testing methodology](https://techcorp.dev/testing)*
                    """.strip(),
                }
            ]
        },
    }


@pytest.fixture
def mock_weasyprint() -> dict[str, Mock]:
    """Create mock WeasyPrint objects for testing."""
    mock_css = Mock()
    mock_html = Mock()
    mock_html.write_pdf = Mock()
    return {"CSS": Mock(return_value=mock_css), "HTML": Mock(return_value=mock_html)}


@pytest.fixture(autouse=True)
def mock_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock environment variables and paths for testing."""
    # Mock paths to avoid dependency on actual file structure
    monkeypatch.setenv("TESTING", "true")

    # Mock config paths
    test_paths = {
        "PATH_DATA": "test_data",
        "PATH_INPUT": "test_data/input/",
        "PATH_OUTPUT": "test_data/output/",
        "FILE_DEFAULT": "test_default",
    }

    for key, value in test_paths.items():
        monkeypatch.setattr(f"simple_resume.config.{key}", value)


@pytest.fixture
def story(request: pytest.FixtureRequest) -> Scenario:
    """Provide a Scenario helper tied to the current test node."""
    return make_scenario(request.node.nodeid)
