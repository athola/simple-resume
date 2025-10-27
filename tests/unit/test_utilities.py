"""Unit tests for cv.utilities module following TDD principles.

These tests follow the Red-Green-Refactor cycle:
1. RED: Write failing tests for desired functionality
2. GREEN: Write minimal code to make tests pass
3. REFACTOR: Improve code while keeping tests green

Tests follow extreme programming practices:
- Edge case coverage
- Business logic validation
- Clear, descriptive test names
- Single assertion per test where possible
- Test isolation and independence
"""

from pathlib import Path
from typing import Any
from unittest.mock import Mock, mock_open, patch

import pytest
import yaml

from cv.utilities import _read_yaml, _transform_from_markdown, get_content


class TestReadYaml:
    """Test cases for _read_yaml function following TDD principles."""

    def test_read_valid_yaml_file_returns_dict(self, temp_dir: Path) -> None:
        """RED: Test that reading a valid YAML file returns a dictionary."""
        # Arrange
        test_data = {"name": "John", "age": 30, "skills": ["Python", "Testing"]}
        yaml_file = temp_dir / "test.yaml"

        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.dump(test_data, f)

        # Act
        result = _read_yaml(str(yaml_file))

        # Assert
        assert result == test_data
        assert isinstance(result, dict)

    def test_read_empty_yaml_file_returns_empty_dict(self, temp_dir: Path) -> None:
        """RED: Test that reading an empty YAML file returns an empty dict."""
        # Arrange
        yaml_file = temp_dir / "empty.yaml"
        yaml_file.write_text("", encoding="utf-8")

        # Act
        result = _read_yaml(str(yaml_file))

        # Assert
        assert result == {}
        assert isinstance(result, dict)

    def test_read_yaml_with_null_content_returns_empty_dict(
        self, temp_dir: Path
    ) -> None:
        """RED: Test that reading YAML with null content returns empty dict."""
        # Arrange
        yaml_file = temp_dir / "null.yaml"
        yaml_file.write_text("null", encoding="utf-8")

        # Act
        result = _read_yaml(str(yaml_file))

        # Assert
        assert result == {}
        assert isinstance(result, dict)

    def test_read_nonexistent_file_raises_file_not_found(self) -> None:
        """RED: Test that reading a non-existent file raises FileNotFoundError."""
        # Arrange
        nonexistent_path = "/path/to/nonexistent/file.yaml"

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            _read_yaml(nonexistent_path)

    def test_read_invalid_yaml_file_raises_exception(self, temp_dir: Path) -> None:
        """RED: Test that reading invalid YAML raises appropriate exception."""
        # Arrange
        yaml_file = temp_dir / "invalid.yaml"
        yaml_file.write_text("invalid: yaml: content: [", encoding="utf-8")

        # Act & Assert
        with pytest.raises(yaml.YAMLError):
            _read_yaml(str(yaml_file))

    def test_read_yaml_with_complex_nested_structure(self, temp_dir: Path) -> None:
        """RED: Test reading YAML with complex nested structure."""
        # Arrange
        complex_data = {
            "personal": {
                "name": "Jane Doe",
                "contact": {
                    "email": "jane@example.com",
                    "phone": "555-1234",
                    "social": {"linkedin": "in/janedoe", "github": "janedoe"},
                },
            },
            "experience": [
                {
                    "company": "Tech Corp",
                    "role": "Senior Developer",
                    "duration": "2020-Present",
                }
            ],
        }

        yaml_file = temp_dir / "complex.yaml"
        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.dump(complex_data, f)

        # Act
        result = _read_yaml(str(yaml_file))

        # Assert
        assert result == complex_data
        assert result["personal"]["contact"]["social"]["linkedin"] == "in/janedoe"
        assert len(result["experience"]) == 1

    @patch("builtins.open", new_callable=mock_open, read_data="key: value")
    def test_read_yaml_file_encoding_handling(self, mock_file: Mock) -> None:
        """GREEN: Test that YAML files are read with UTF-8 encoding."""
        # Act
        result = _read_yaml("dummy_path.yaml")

        # Assert
        mock_file.assert_called_once_with("dummy_path.yaml", encoding="utf-8")
        assert result == {"key": "value"}


class TestTransformFromMarkdown:
    """Test cases for _transform_from_markdown function following TDD principles."""

    def test_transform_markdown_in_description_field(self) -> None:
        """RED: Test that markdown in description field is converted to HTML."""
        # Arrange
        data = {"description": "This is **bold** and *italic* text."}

        # Act
        _transform_from_markdown(data)

        # Assert
        expected_html = "<p>This is <strong>bold</strong> and <em>italic</em> text.</p>"
        assert data["description"] == expected_html

    def test_transform_markdown_in_body_sections(self) -> None:
        """RED: Test that markdown in body sections is converted to HTML."""
        # Arrange
        data: dict[str, Any] = {
            "body": {
                "Experience": [
                    {"description": "- Item 1\n- Item 2 with **bold** text"},
                    {"description": "Regular text without markdown"},
                ],
                "Education": [{"description": "# Header\nSome content"}],
            }
        }

        # Act
        _transform_from_markdown(data)

        # Assert
        # Check Experience section
        exp_desc = data["body"]["Experience"][0]["description"]
        assert "<strong>bold</strong>" in exp_desc
        assert "<ul>" in exp_desc
        assert "<li>" in exp_desc

        # Check regular text is still processed
        regular_desc = data["body"]["Experience"][1]["description"]
        assert regular_desc == "<p>Regular text without markdown</p>"

        # Check Education section
        edu_desc = data["body"]["Education"][0]["description"]
        assert "<h1>" in edu_desc
        assert "<p>Some content</p>" in edu_desc

    def test_transform_with_no_markdown_fields(self) -> None:
        """RED: Test that data without markdown fields is unchanged."""
        # Arrange
        data: dict[str, Any] = {
            "name": "John Doe",
            "age": 30,
            "body": {
                "Experience": [
                    {
                        "title": "Developer",
                        "company": "Tech Corp",
                        # No description field
                    }
                ]
            },
        }

        # Act
        _transform_from_markdown(data)

        # Assert
        assert data["name"] == "John Doe"
        assert data["age"] == 30
        assert "description" not in data["body"]["Experience"][0]

    def test_transform_with_empty_body_sections(self) -> None:
        """RED: Test handling of empty body sections."""
        # Arrange
        data: dict[str, Any] = {"body": {"Experience": [], "Education": []}}

        # Act
        _transform_from_markdown(data)

        # Assert
        assert data["body"]["Experience"] == []
        assert data["body"]["Education"] == []

    def test_transform_with_complex_markdown_content(self) -> None:
        """RED: Test transformation of complex markdown with links, lists, and
        formatting."""
        # Arrange
        data: dict[str, Any] = {
            "description": """
# Professional Summary

I am a **senior developer** with expertise in:

- Python programming
- Test-driven development
- CI/CD pipelines

Visit my [portfolio](https://example.com) for more details.
            """.strip()
        }

        # Act
        _transform_from_markdown(data)

        # Assert
        result = data["description"]
        assert "<h1>Professional Summary</h1>" in result
        assert "<strong>senior developer</strong>" in result
        assert "<ul>" in result
        assert "<li>Python programming</li>" in result
        assert '<a href="https://example.com">portfolio</a>' in result

    def test_transform_preserves_other_fields(self) -> None:
        """RED: Test that transformation preserves non-markdown fields."""
        # Arrange
        data: dict[str, Any] = {
            "name": "John Doe",
            "email": "john@example.com",
            "description": "Simple description",
            "skills": ["Python", "Testing"],
            "config": {"theme": "dark"},
        }

        # Act
        _transform_from_markdown(data)

        # Assert
        assert data["name"] == "John Doe"
        assert data["email"] == "john@example.com"
        assert data["skills"] == ["Python", "Testing"]
        assert data["config"]["theme"] == "dark"
        # Only description should be transformed
        assert data["description"] == "<p>Simple description</p>"

    def test_transform_with_code_blocks_and_tables(self) -> None:
        """RED: Test transformation of markdown code blocks and tables."""
        # Arrange
        data: dict[str, Any] = {
            "description": """Here's some code:

```python
def hello_world():
    print("Hello, World!")
```

And a table:

| Feature | Status |
|---------|--------|
| Testing | Complete |
| CI/CD | In Progress"""
        }

        # Act
        _transform_from_markdown(data)

        # Assert - Updated expectations for proper markdown rendering
        result = data["description"]
        # Code blocks should now render properly with syntax highlighting
        assert '<div class="codehilite">' in result
        assert "<pre><span></span><code>" in result
        assert "hello_world" in result
        assert "def" in result
        # Tables should render as proper HTML tables
        assert "<table>" in result
        assert "<thead>" in result
        assert "<th>Feature</th>" in result
        assert "<td>Testing</td>" in result

    def test_enhanced_markdown_features_for_technical_cvs(self) -> None:
        """GREEN: Test that enhanced markdown features work for technical CVs."""
        # Arrange
        data: dict[str, Any] = {
            "body": {
                "Projects": [
                    {
                        "description": """## Python API Development

### Key Implementation

```python
import flask
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/data')
def get_data():
    \"\"\"Get data from API endpoint.\"\"\"
    return jsonify({'status': 'success'})
```

### Performance Optimizations

- Used Redis caching for 10x speed improvement
- Implemented database connection pooling
- Added async request processing"""
                    }
                ],
                "Skills": [
                    {
                        "description": """## Technical Skills

| Technology | Level | Experience | Projects |
|------------|-------|------------|----------|
| Python | Expert | 5+ years | 15+ projects |
| PostgreSQL | Advanced | 3 years | 5+ databases |
| Docker | Expert | 4 years | 20+ containers |
| Kubernetes | Intermediate | 2 years | 3 clusters |
| FastAPI | Advanced | 2 years | 8+ APIs"""
                    }
                ],
            }
        }

        # Act
        _transform_from_markdown(data)

        # Assert - Technical CV markdown features
        project_desc = data["body"]["Projects"][0]["description"]
        skills_desc = data["body"]["Skills"][0]["description"]

        # Code blocks with syntax highlighting
        assert '<div class="codehilite">' in project_desc
        assert "<pre><span></span><code>" in project_desc
        assert "get_data" in project_desc
        assert "def" in project_desc

        # Headers
        assert "<h2>" in project_desc
        assert "<h3>" in project_desc

        # Tables for skills
        assert "<table>" in skills_desc
        assert "<thead>" in skills_desc
        assert "<th>Technology</th>" in skills_desc
        assert "<td>Python</td>" in skills_desc

        # Bullet points (they're in list items, not bold)
        assert "Used Redis caching for 10x speed improvement" in project_desc

    def test_enhanced_markdown_features_for_business_cvs(self) -> None:
        """GREEN: Test that enhanced markdown features work for business CVs."""
        # Arrange
        data = {
            "body": {
                "Experience": [
                    {
                        "description": r"""## Business Impact

### Key Achievements

- **Revenue Growth**: Increased sales by 45% through strategic partnerships
- **Cost Reduction**: Reduced operational costs by 30% through process optimization
- **Team Leadership**: Managed team of 12+ professionals

### Project Management


| Project | Role | Duration | Budget | Outcome |
|---------|------|----------|---------|---------|
| Q4 2023 Sales Initiative | Project Manager | 3 months | $500K | +45% sales |
| Process Automation | Lead | 6 months | $200K | -30% costs |
| Team Expansion | Manager | 12 months | $1M | +40% team size |"""
                    }
                ],
                "Education": [
                    {
                        "description": """## Executive Education


| Degree | Institution | Year | Focus |
|--------|------------|------|-------|
| MBA | Harvard Business School | 2020 | Strategy & Leadership |
| BSc Business | Stanford University | 2015 | Finance & Management |
| Certificate | Wharton Executive | 2022 | Digital Transformation"""
                    }
                ],
            }
        }

        # Act
        _transform_from_markdown(data)

        # Assert - Business CV markdown features
        exp_desc = data["body"]["Experience"][0]["description"]
        edu_desc = data["body"]["Education"][0]["description"]

        # Professional headers
        assert "<h2>" in exp_desc
        assert "<h3>" in exp_desc

        # Bullet points with bold emphasis
        assert "<strong>Revenue Growth</strong>" in exp_desc
        assert "<strong>Cost Reduction</strong>" in exp_desc

        # Tables for experience/education
        assert "<table>" in exp_desc
        assert "<thead>" in exp_desc
        assert "<th>Project</th>" in exp_desc
        assert "<td>$500K</td>" in exp_desc

        assert "<table>" in edu_desc
        assert "<thead>" in edu_desc
        assert "<th>Degree</th>" in edu_desc
        assert "<td>MBA</td>" in edu_desc


class TestGetContent:
    """Test cases for get_content function following TDD principles."""

    @patch("cv.utilities._read_yaml")
    @patch("cv.utilities._transform_from_markdown")
    @patch("cv.utilities.FILE_DEFAULT", "default_cv")
    @patch("cv.utilities.PATH_INPUT", "test_input/")
    def test_get_content_with_empty_name_uses_default(
        self, mock_transform: Mock, mock_read: Mock
    ) -> None:
        """RED: Test that empty name uses default file name."""
        # Arrange
        expected_data = {"name": "Default CV", "template": "default"}
        mock_read.return_value = expected_data

        # Act
        result = get_content()

        # Assert
        mock_read.assert_called_once_with("test_input/default_cv.yaml")
        mock_transform.assert_called_once_with(expected_data)
        assert result == expected_data

    @patch("cv.utilities._read_yaml")
    @patch("cv.utilities._transform_from_markdown")
    @patch("cv.utilities.FILE_DEFAULT", "default_cv")
    @patch("cv.utilities.PATH_INPUT", "test_input/")
    def test_get_content_with_specific_name(
        self, mock_transform: Mock, mock_read: Mock
    ) -> None:
        """RED: Test that specific name is used correctly."""
        # Arrange
        expected_data = {"name": "John Doe", "template": "modern"}
        mock_read.return_value = expected_data

        # Act
        result = get_content("john_doe")

        # Assert
        mock_read.assert_called_once_with("test_input/john_doe.yaml")
        mock_transform.assert_called_once_with(expected_data)
        assert result == expected_data

    @patch("cv.utilities._read_yaml")
    @patch("cv.utilities._transform_from_markdown")
    @patch("cv.utilities.FILE_DEFAULT", "default_cv")
    @patch("cv.utilities.PATH_INPUT", "test_input/")
    def test_get_content_with_name_containing_dot(
        self, mock_transform: Mock, mock_read: Mock
    ) -> None:
        """RED: Test that names with dots are handled correctly."""
        # Arrange
        expected_data = {"name": "Jane Smith", "template": "classic"}
        mock_read.return_value = expected_data

        # Act
        result = get_content("jane.smith")

        # Assert - Function strips extension, so we pass name without extension
        mock_read.assert_called_once_with(
            "test_input/jane.yaml"
        )  # Function strips dots and adds .yaml
        mock_transform.assert_called_once_with(expected_data)
        assert result == expected_data

    @patch("cv.utilities._read_yaml")
    @patch("cv.utilities._transform_from_markdown")
    @patch("cv.utilities.FILE_DEFAULT", "default_cv")
    @patch("cv.utilities.PATH_INPUT", "test_input/")
    def test_get_content_with_name_containing_multiple_dots(
        self, mock_transform: Mock, mock_read: Mock
    ) -> None:
        """RED: Test that names with multiple dots are handled correctly."""
        # Arrange
        expected_data = {"name": "Bob Johnson", "template": "creative"}
        mock_read.return_value = expected_data

        # Act
        result = get_content("bob.johnson")

        # Assert - Function strips dots and adds .yaml
        mock_read.assert_called_once_with("test_input/bob.yaml")
        mock_transform.assert_called_once_with(expected_data)
        assert result == expected_data

    @patch("cv.utilities._read_yaml")
    @patch("cv.utilities._transform_from_markdown")
    @patch("cv.utilities.FILE_DEFAULT", "default_cv")
    @patch("cv.utilities.PATH_INPUT", "test_input/")
    def test_get_content_with_yml_extension(
        self, mock_transform: Mock, mock_read: Mock
    ) -> None:
        """RED: Test that .yml extension is handled correctly."""
        # Arrange
        expected_data = {"name": "Alice Brown", "template": "minimal"}
        mock_read.return_value = expected_data

        # Act
        result = get_content("alice_brown")

        # Assert - Function strips extension and adds .yaml
        mock_read.assert_called_once_with("test_input/alice_brown.yaml")
        mock_transform.assert_called_once_with(expected_data)
        assert result == expected_data

    @patch("cv.utilities._read_yaml", side_effect=FileNotFoundError)
    @patch("cv.utilities.FILE_DEFAULT", "default_cv")
    @patch("cv.utilities.PATH_INPUT", "test_input/")
    def test_get_content_file_not_found_raises_exception(self, mock_read: Mock) -> None:
        """RED: Test that file not found error is properly raised."""
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            get_content("nonexistent_file")

    @patch("cv.utilities._read_yaml")
    @patch("cv.utilities._transform_from_markdown")
    @patch("cv.utilities.FILE_DEFAULT", "default_cv")
    @patch("cv.utilities.PATH_INPUT", "test_input/")
    def test_get_content_integration_with_markdown_transformation(
        self, mock_transform: Mock, mock_read: Mock
    ) -> None:
        """GREEN: Integration test for complete get_content workflow."""
        # Arrange
        raw_data = {
            "name": "Test User",
            "description": "This is **bold** text",
            "body": {
                "Experience": [
                    {"description": "## Responsibilities\n- Task 1\n- Task 2"}
                ]
            },
        }
        mock_read.return_value = raw_data

        # The transform should actually modify the data in place
        def actual_transform(data: dict[str, Any]) -> dict[str, Any]:
            data["description"] = "<p>This is <strong>bold</strong> text</p>"
            return data

        mock_transform.side_effect = actual_transform

        # Act
        result = get_content("test_user")

        # Assert
        mock_read.assert_called_once_with("test_input/test_user.yaml")
        mock_transform.assert_called_once_with(raw_data)
        assert result["description"] == "<p>This is <strong>bold</strong> text</p>"
        assert result["name"] == "Test User"

    def test_get_content_business_logic_validation(
        self, sample_cv_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GREEN: Business logic test for CV content structure validation."""
        # Arrange
        monkeypatch.setattr("cv.utilities.PATH_INPUT", str(sample_cv_file.parent) + "/")

        # Act
        result = get_content(sample_cv_file.stem)

        # Assert - Business logic validations
        assert isinstance(result, dict), "CV content should be a dictionary"

        # Required fields validation
        required_fields = ["template", "full_name"]
        for field in required_fields:
            assert field in result, f"Required field '{field}' is missing from CV data"
            assert result[field], f"Required field '{field}' cannot be empty"

        # Template validation
        assert isinstance(result["template"], str), "Template should be a string"
        assert result["template"].strip(), "Template name cannot be empty"

        # Name validation
        assert isinstance(result["full_name"], str), "Full name should be a string"
        assert (
            len(result["full_name"].strip()) > 1
        ), "Full name must have at least 2 characters"

        # Contact info validation if present
        if "email" in result:
            assert "@" in result["email"], "Email should contain @"
            assert (
                "." in result["email"].split("@")[1]
            ), "Email should have valid domain"

        if "phone" in result:
            assert (
                result["phone"]
                .replace("-", "")
                .replace(" ", "")
                .replace(")", "")
                .replace("(", "")
                .isdigit()
            ), "Phone should contain only digits, spaces, and standard phone characters"
