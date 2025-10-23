"""Pytest configuration and fixtures for CV project tests."""
import os
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock

import pytest
import yaml


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_cv_data() -> Dict[str, Any]:
    """Sample CV data for testing."""
    return {
        "template": "cv_no_bars",
        "full_name": "John Doe",
        "address": ["123 Test St", "Test City, TC 12345"],
        "titles": {
            "contact": "Contact",
            "certification": "Certifications",
            "expertise": "Expertise",
            "keyskills": "Key Skills"
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
                    "description": "- Developed **amazing** features\n- Wrote comprehensive tests\n- Followed TDD principles"
                }
            ],
            "Education": [
                {
                    "start": "09/2015",
                    "end": "05/2019",
                    "title": "Bachelor of Science",
                    "company": "Test University",
                    "description": "Graduated with honors in Computer Science"
                }
            ]
        },
        "config": {
            "theme_color": "#0395DE",
            "sidebar_color": "#F6F6F6",
            "bar_background_color": "#DFDFDF",
            "date2_color": "#616161",
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
            "frame_color": "#757575",
            "cover_padding_top": 10,
            "cover_padding_bottom": 20,
            "cover_padding_h": 25
        }
    }


@pytest.fixture
def sample_cv_file(temp_dir: Path, sample_cv_data: Dict[str, Any]) -> Path:
    """Create a sample CV YAML file for testing."""
    cv_file = temp_dir / "test_cv.yaml"
    with open(cv_file, "w", encoding="utf-8") as f:
        yaml.dump(sample_cv_data, f, default_flow_style=False, allow_unicode=True)
    return cv_file


def create_complete_cv_data(template: str = "cv_no_bars", full_name: str = "Test User",
                           experience: list = None, expertise: list = None,
                           description: str = "This is a **test** description.") -> Dict[str, Any]:
    """Create a complete CV data structure with all required fields."""
    if experience is None:
        experience = [{
            "start": "01/2020",
            "end": "Present",
            "title": "Test Developer",
            "company": "Test Company",
            "description": "- Developed **amazing** features\n- Wrote comprehensive tests"
        }]

    # Different templates expect different data formats
    if template == "cv_with_bars":
        if expertise is None:
            expertise = {"Python": 95, "Testing": 90, "TDD": 85}
        certification = {
            "Test Certification": 90,
            "Another Certificate": 85
        }
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
            "keyskills": "Key Skills"
        },
        "phone": "555-123-4567",
        "email": f"{full_name.lower().replace(' ', '.')}@example.com",
        "web": "https://example.com",
        "linkedin": "in/testuser",
        "description": description,
        "expertise": expertise,
        "certification": certification,
        "keyskills": ["Skill 1", "Skill 2", "Skill 3"],
        "programming": {"Python": 90, "JavaScript": 80, "React": 75} if template == "cv_with_bars" else [],
        "body": {
            "Experience": experience,
            "Education": [
                {
                    "start": "09/2015",
                    "end": "05/2019",
                    "title": "Bachelor of Science",
                    "company": "Test University",
                    "description": "Graduated with honors in Computer Science"
                }
            ]
        },
        "config": {
            "theme_color": "#0395DE",
            "sidebar_color": "#F6F6F6",
            "bar_background_color": "#DFDFDF",
            "date2_color": "#616161",
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
            "frame_color": "#757575",
            "cover_padding_top": 10,
            "cover_padding_bottom": 20,
            "cover_padding_h": 25
        }
    }


@pytest.fixture
def sample_cv_with_markdown() -> Dict[str, Any]:
    """Sample CV data with markdown content for testing."""
    return {
        "template": "cv_no_bars",
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
2. **API Gateway**: Microservices architecture with comprehensive integration tests
3. **Testing Framework**: Custom pytest plugins for the organization

*Learn more about our [testing methodology](https://techcorp.dev/testing)*
                    """.strip()
                }
            ]
        }
    }


@pytest.fixture
def mock_flask_app():
    """Create a mock Flask app for testing."""
    app = Mock()
    app.config = {"TESTING": True}
    return app


@pytest.fixture
def mock_weasyprint():
    """Create mock WeasyPrint objects for testing."""
    mock_css = Mock()
    mock_html = Mock()
    mock_html.write_pdf = Mock()
    return {"CSS": Mock(return_value=mock_css), "HTML": Mock(return_value=mock_html)}


@pytest.fixture(autouse=True)
def mock_environment(monkeypatch):
    """Mock environment variables and paths for testing."""
    # Mock paths to avoid dependency on actual file structure
    monkeypatch.setenv("TESTING", "true")

    # Mock config paths
    test_paths = {
        "PATH_DATA": "test_data",
        "PATH_INPUT": "test_data/input/",
        "PATH_OUTPUT": "test_data/output/",
        "FILE_DEFAULT": "test_default",
        "URL_PRINT": "localhost:5000/print/",
        "URL_VIEW": "localhost:5000/v/"
    }

    for key, value in test_paths.items():
        monkeypatch.setattr(f"cv.config.{key}", value)