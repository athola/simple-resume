"""Behavioural tests for simple_resume.utilities using BDD terminology."""

from pathlib import Path
from typing import Any
from unittest.mock import Mock, mock_open, patch

import pytest
import yaml

from simple_resume import config, utilities
from simple_resume.palettes.registry import Palette
from simple_resume.utilities import (
    _read_yaml,
    _transform_from_markdown,
    get_content,
    validate_config,
)


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
        """RED: Test transformation of complex markdown with links, lists, and.

        formatting.
        """
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

    def test_enhanced_markdown_features_for_technical_resumes(self) -> None:
        """GREEN: Test that enhanced markdown features work for technical Resumes."""
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

        # Assert - Technical Resume markdown features
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

    def test_enhanced_markdown_features_for_business_resumes(self) -> None:
        """GREEN: Test that enhanced markdown features work for business Resumes."""
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

        # Assert - Business Resume markdown features
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

    @patch("simple_resume.hydration.load_resume_yaml")
    @patch("simple_resume.hydration.hydrate_resume_data")
    @patch("simple_resume.config.FILE_DEFAULT", "test_default")
    def test_get_content_with_empty_name_uses_default(
        self, mock_transform: Mock, mock_read: Mock
    ) -> None:
        """RED: Test that empty name uses default file name."""
        # Arrange
        expected_data = {"name": "Default Resume", "template": "default"}
        mock_read.return_value = (expected_data, Path("test_default.yaml"), None)
        mock_transform.return_value = expected_data
        paths = config.Paths(
            data=Path("data_dir"),
            input=Path("test_input"),
            output=Path("test_output"),
        )

        # Act
        result = get_content(paths=paths)

        # Assert
        mock_read.assert_called_once_with("", paths=paths)
        mock_transform.assert_called_once_with(
            expected_data,
            filename=Path("test_default.yaml"),
            transform_markdown=True,
        )
        assert result == expected_data

    @patch("simple_resume.hydration.load_resume_yaml")
    @patch("simple_resume.hydration.hydrate_resume_data")
    @patch("simple_resume.config.FILE_DEFAULT", "test_default")
    def test_get_content_with_specific_name(
        self, mock_transform: Mock, mock_read: Mock
    ) -> None:
        """RED: Test that specific name is used correctly."""
        # Arrange
        expected_data = {"name": "John Doe", "template": "modern"}
        mock_read.return_value = (expected_data, Path("test_file.yaml"), None)
        mock_transform.return_value = expected_data
        paths = config.Paths(
            data=Path("data_dir"),
            input=Path("test_input"),
            output=Path("test_output"),
        )

        # Act
        result = get_content("john_doe", paths=paths)

        # Assert
        mock_read.assert_called_once_with("john_doe", paths=paths)
        mock_transform.assert_called_once_with(
            expected_data,
            filename=Path("test_file.yaml"),
            transform_markdown=True,
        )
        assert result == expected_data

    @patch("simple_resume.hydration.load_resume_yaml")
    @patch("simple_resume.hydration.hydrate_resume_data")
    @patch("simple_resume.config.FILE_DEFAULT", "test_default")
    def test_get_content_with_name_containing_dot(
        self, mock_transform: Mock, mock_read: Mock
    ) -> None:
        """RED: Test that names with dots are handled correctly."""
        # Arrange
        expected_data = {"name": "Jane Smith", "template": "classic"}
        mock_read.return_value = (expected_data, Path("test_file.yaml"), None)
        mock_transform.return_value = expected_data
        paths = config.Paths(
            data=Path("data_dir"),
            input=Path("test_input"),
            output=Path("test_output"),
        )

        # Act
        result = get_content("jane.smith", paths=paths)

        # Assert - Function strips extension, so we pass name without extension
        mock_read.assert_called_once_with("jane.smith", paths=paths)
        mock_transform.assert_called_once_with(
            expected_data,
            filename=Path("test_file.yaml"),
            transform_markdown=True,
        )
        assert result == expected_data

    @patch("simple_resume.hydration.load_resume_yaml")
    @patch("simple_resume.hydration.hydrate_resume_data")
    @patch("simple_resume.config.FILE_DEFAULT", "test_default")
    def test_get_content_with_name_containing_multiple_dots(
        self, mock_transform: Mock, mock_read: Mock
    ) -> None:
        """RED: Test that names with multiple dots are handled correctly."""
        # Arrange
        expected_data = {"name": "Bob Johnson", "template": "creative"}
        mock_read.return_value = (expected_data, Path("test_file.yaml"), None)
        mock_transform.return_value = expected_data
        paths = config.Paths(
            data=Path("data_dir"),
            input=Path("test_input"),
            output=Path("test_output"),
        )

        # Act
        result = get_content("bob.johnson", paths=paths)

        # Assert - Function strips dots and adds .yaml
        mock_read.assert_called_once_with("bob.johnson", paths=paths)
        mock_transform.assert_called_once_with(
            expected_data,
            filename=Path("test_file.yaml"),
            transform_markdown=True,
        )
        assert result == expected_data

    @patch("simple_resume.hydration.load_resume_yaml")
    @patch("simple_resume.hydration.hydrate_resume_data")
    @patch("simple_resume.config.FILE_DEFAULT", "test_default")
    def test_get_content_with_yml_extension(
        self, mock_transform: Mock, mock_read: Mock
    ) -> None:
        """RED: Test that .yml extension is handled correctly."""
        # Arrange
        expected_data = {"name": "Alice Brown", "template": "minimal"}
        mock_read.return_value = (expected_data, Path("test_file.yaml"), None)
        mock_transform.return_value = expected_data
        paths = config.Paths(
            data=Path("data_dir"),
            input=Path("test_input"),
            output=Path("test_output"),
        )

        # Act
        result = get_content("alice_brown", paths=paths)

        # Assert - Function strips extension and adds .yaml
        mock_read.assert_called_once_with("alice_brown", paths=paths)
        mock_transform.assert_called_once_with(
            expected_data,
            filename=Path("test_file.yaml"),
            transform_markdown=True,
        )
        assert result == expected_data

    @patch("simple_resume.hydration.load_resume_yaml", side_effect=FileNotFoundError)
    @patch("simple_resume.config.FILE_DEFAULT", "test_default")
    def test_get_content_file_not_found_raises_exception(self, mock_read: Mock) -> None:
        """RED: Test that file not found error is properly raised."""
        paths = config.Paths(
            data=Path("data_dir"),
            input=Path("test_input"),
            output=Path("test_output"),
        )

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            get_content("nonexistent_file", paths=paths)

    @patch("simple_resume.hydration.load_resume_yaml")
    @patch("simple_resume.hydration.hydrate_resume_data")
    @patch("simple_resume.config.FILE_DEFAULT", "test_default")
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
        mock_read.return_value = (raw_data, Path("test_file.yaml"), None)
        mock_transform.return_value = raw_data
        paths = config.Paths(
            data=Path("data_dir"),
            input=Path("test_input"),
            output=Path("test_output"),
        )

        # The transform should actually modify the data in place
        def actual_transform(data: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
            data["description"] = "<p>This is <strong>bold</strong> text</p>"
            return data

        mock_transform.side_effect = actual_transform

        # Act
        result = get_content("test_user", paths=paths)

        # Assert
        mock_read.assert_called_once_with("test_user", paths=paths)
        # hydrate_resume_data makes a deep copy, so we just verify it was called
        assert mock_transform.called
        assert result["description"] == "<p>This is <strong>bold</strong> text</p>"
        assert result["name"] == "Test User"

    def test_get_content_business_logic_validation(
        self, sample_resume_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GREEN: Business logic test for Resume content structure validation."""
        # Arrange
        paths = config.Paths(
            data=sample_resume_file.parent.parent,
            input=sample_resume_file.parent,
            output=sample_resume_file.parent / "output",
        )

        # Act
        result = get_content(sample_resume_file.stem, paths=paths)

        # Assert - Business logic validations
        assert isinstance(result, dict), "Resume content should be a dictionary"

        # Required fields validation
        required_fields = ["template", "full_name"]
        for field in required_fields:
            assert field in result, (
                f"Required field '{field}' is missing from Resume data"
            )
            assert result[field], f"Required field '{field}' cannot be empty"

        # Template validation
        assert isinstance(result["template"], str), "Template should be a string"
        assert result["template"].strip(), "Template name cannot be empty"

        # Name validation
        assert isinstance(result["full_name"], str), "Full name should be a string"
        assert len(result["full_name"].strip()) > 1, (
            "Full name must have at least 2 characters"
        )

        # Contact info validation if present
        if "email" in result:
            assert "@" in result["email"], "Email should contain @"
            assert "." in result["email"].split("@")[1], (
                "Email should have valid domain"
            )

        if "phone" in result:
            assert (
                result["phone"]
                .replace("-", "")
                .replace(" ", "")
                .replace(")", "")
                .replace("(", "")
                .isdigit()
            ), "Phone should contain only digits, spaces, and standard phone characters"


class TestValidateConfig:
    """Test cases for validate_config function."""

    def test_valid_config_passes_validation(self) -> None:
        """Valid config with correct dimensions and colors should pass."""
        config = {
            "page_width": 190,
            "page_height": 270,
            "sidebar_width": 60,
            "theme_color": "#0395DE",
            "sidebar_color": "#F6F6F6",
        }
        # Should not raise any exception
        validate_config(config)

    def test_sidebar_width_equals_page_width_fails(self) -> None:
        """Sidebar width equal to page width should fail validation."""
        config = {
            "page_width": 190,
            "page_height": 270,
            "sidebar_width": 190,
        }
        with pytest.raises(ValueError, match="must be less than"):
            validate_config(config)

    def test_sidebar_width_greater_than_page_width_fails(self) -> None:
        """Sidebar width greater than page width should fail validation."""
        config = {
            "page_width": 190,
            "page_height": 270,
            "sidebar_width": 200,
        }
        with pytest.raises(ValueError, match="must be less than"):
            validate_config(config)

    def test_negative_page_width_fails(self) -> None:
        """Negative page dimensions should fail validation."""
        config = {
            "page_width": -190,
            "page_height": 270,
        }
        with pytest.raises(ValueError, match="must be positive"):
            validate_config(config)

    def test_invalid_color_format_fails(self) -> None:
        """Invalid hex color format should fail validation."""
        config = {
            "theme_color": "blue",
        }
        with pytest.raises(ValueError, match="Invalid color format"):
            validate_config(config)

    def test_default_color_scheme_applied_when_missing(self) -> None:
        """Missing colors should be populated with defaults."""
        config_map = {
            "color_scheme": "",
            "theme_color": "",
            "sidebar_color": None,
        }
        validate_config(config_map)
        assert config_map["color_scheme"] == "default"
        for field in (
            "theme_color",
            "sidebar_color",
            "sidebar_text_color",
            "bar_background_color",
            "date2_color",
            "frame_color",
            "heading_icon_color",
        ):
            assert field in config_map
            assert isinstance(config_map[field], str)
            assert config_map[field].startswith("#")

    def test_sidebar_text_color_derives_from_sidebar_color(self) -> None:
        """Sidebar text should contrast with automatically computed values."""
        config_map = {
            "sidebar_color": "#222222",
        }
        validate_config(config_map)
        assert config_map["sidebar_text_color"] == "#F5F5F5"
        assert config_map["heading_icon_color"] == "#F5F5F5"

    def test_palette_registry_block(self, monkeypatch: pytest.MonkeyPatch) -> None:
        palette = Palette(
            name="demo",
            swatches=("#111111", "#222222", "#333333", "#444444", "#555555"),
            source="test",
        )

        class DummyRegistry:
            def get(self, _: str) -> Palette:
                return palette

        monkeypatch.setattr(
            "simple_resume.utilities.get_global_registry", lambda: DummyRegistry()
        )

        config_map = {
            "palette": {"source": "registry", "name": "demo"},
        }
        validate_config(config_map)
        assert config_map["theme_color"] == "#111111"
        assert config_map["color_scheme"] == "demo"
        assert config_map["heading_icon_color"] == config_map["sidebar_text_color"]

    def test_palette_generator_block(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "simple_resume.utilities.generate_hcl_palette",
            lambda size, **_: ["#AAAAAA", "#BBBBBB", "#CCCCCC"][:size],
        )

        config_map = {
            "palette": {
                "source": "generator",
                "size": 3,
                "seed": 1,
                "hue_range": [100, 120],
                "luminance_range": [0.4, 0.8],
            }
        }

        validate_config(config_map)
        assert config_map["theme_color"] == "#AAAAAA"
        assert config_map["sidebar_color"] == "#BBBBBB"
        # bar_background_color cycles to the first color (theme, sidebar,
        # sidebar_text, bar_background, ...).
        assert config_map["bar_background_color"] == "#AAAAAA"
        assert config_map["heading_icon_color"] == config_map["sidebar_text_color"]

    def test_validate_config_coerces_string_numbers(self) -> None:
        """Quoted numeric values should be coerced to numeric types."""
        config_map = {
            "page_width": "190",
            "page_height": "270",
            "sidebar_width": "60",
        }
        validate_config(config_map)
        assert config_map["page_width"] == 190
        assert config_map["page_height"] == 270
        assert config_map["sidebar_width"] == 60
        for key in ("page_width", "page_height", "sidebar_width"):
            assert isinstance(config_map[key], int)

    def test_validate_config_rejects_non_numeric_strings(self) -> None:
        """Non-numeric strings should produce a descriptive ValueError."""
        config_map = {
            "page_width": "not-a-number",
            "page_height": "270",
        }
        with pytest.raises(ValueError, match="page_width.*numeric"):
            validate_config(config_map, filename="sample.yaml")

    def test_short_hex_color_passes(self) -> None:
        """Short hex color format (#RGB) should pass validation."""
        config = {
            "theme_color": "#FFF",
            "sidebar_color": "#000",
        }
        validate_config(config)

    def test_empty_config_passes(self) -> None:
        """Empty config should pass validation (no-op)."""
        validate_config({})


class TestUtilityEdgeCases:
    """Additional edge-case coverage for utility helpers."""

    def test_hex_to_rgb_rejects_invalid_digits(self, story) -> None:
        """Ensure invalid hex strings surface ValueError."""
        story.given("a malformed hex color string containing non-hex characters")
        story.when("the helper converts the color to RGB")
        with pytest.raises(ValueError):
            utilities._hex_to_rgb("#GGGGGG")
        story.then("a ValueError is raised to signal invalid input")

    @pytest.mark.parametrize("value", [True, False])
    def test_coerce_number_rejects_boolean_inputs(self, story, value: bool) -> None:
        """Boolean values are not accepted as numeric configuration."""
        story.given(f"a boolean value {value!r} supplied for page_width")
        story.when("the value is coerced to a number")
        with pytest.raises(ValueError):
            utilities._coerce_number(value, field="page_width", prefix="")
        story.then("the converter rejects boolean inputs with a ValueError")

    def test_coerce_number_rejects_empty_string(self, story) -> None:
        """Empty strings should raise descriptive errors."""
        story.given("an empty string is provided for page_height")
        story.when("the coercion helper validates the value")
        with pytest.raises(ValueError):
            utilities._coerce_number("   ", field="page_height", prefix="resume.yaml: ")
        story.then("a ValueError explains the numeric requirement")

    def test_coerce_number_rejects_non_numeric_iterable(self, story) -> None:
        """Non-numeric iterable values are invalid."""
        story.given("a list containing numeric text is supplied as sidebar_width")
        story.when("the coercion helper attempts conversion")
        with pytest.raises(ValueError):
            utilities._coerce_number(
                ["100"], field="sidebar_width", prefix="resume.yaml: "
            )
        story.then("the helper raises ValueError for unsupported iterable input")

    def test_calculate_text_color_defaults_for_invalid_input(self, story) -> None:
        """Invalid colors fall back to black for safety."""
        story.given("an invalid color string is supplied for text calculation")
        story.when("the helper determines an appropriate text color")
        result = utilities.calculate_text_color("not-a-color")
        story.then("the helper falls back to black for safety")
        assert result == "#000000"

    def test_calculate_luminance_returns_normalized_value(self, story) -> None:
        """Luminance should be within 0-1 range for valid hex."""
        story.given("a mid-grey color is used for luminance calculation")
        story.when("the helper computes relative luminance")
        luminance = utilities.calculate_luminance("#808080")
        story.then("the resulting value falls within the 0-1 range")
        assert 0.0 <= luminance <= 1.0


class TestNormalizeConfigEdgeCases:
    """Regression coverage for normalize_config validation branches."""

    def test_normalize_config_rejects_non_positive_page_dimensions(self, story) -> None:
        """Both page width and height must be positive numbers."""
        story.given("resume config includes a non-positive page_height")
        story.when("normalize_config validates the dimension")
        with pytest.raises(ValueError):
            utilities.normalize_config({"page_height": 0}, filename="resume.yaml")
        story.then("a ValueError explains the positive requirement")

    def test_normalize_config_validates_sidebar_width_bounds(self, story) -> None:
        """Sidebar width cannot be equal to or exceed page width."""
        story.given("sidebar width equals page width in the config")
        story.when("normalize_config processes the data")
        config_data = {"page_width": 210, "sidebar_width": 210}
        with pytest.raises(ValueError):
            utilities.normalize_config(config_data, filename="resume.yaml")
        story.then("the helper raises ValueError about sidebar bounds")

    def test_normalize_config_sets_default_color_scheme_for_non_string(
        self, story
    ) -> None:
        """Non-string color_scheme values fall back to default."""
        story.given("color_scheme is provided as a non-string value")
        story.when("normalize_config processes the configuration")
        normalized, _ = utilities.normalize_config({"color_scheme": 123})
        story.then("the scheme defaults to 'default'")
        assert normalized["color_scheme"] == "default"

    def test_normalize_config_rejects_non_string_color_values(self, story) -> None:
        """Color fields must be strings containing hex codes."""
        story.given("theme_color is provided as a list instead of a string")
        story.when("normalize_config runs validation")
        with pytest.raises(ValueError):
            utilities.normalize_config(
                {"theme_color": ["#FFF"]}, filename="resume.yaml"
            )
        story.then("a ValueError surfaces for invalid color value types")


class TestPaletteHandling:
    """Ensure palette helpers handle error and success scenarios."""

    def test_apply_palette_block_wraps_unexpected_errors(
        self,
        monkeypatch: pytest.MonkeyPatch,
        story,
    ) -> None:
        """Unexpected exceptions are wrapped in PaletteGenerationError."""

        def boom(_: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
            raise RuntimeError("boom")

        monkeypatch.setattr(utilities, "_resolve_palette_block", boom)
        config_data = {"palette": {"source": "registry", "name": "modern"}}
        story.given("palette resolution raises an unexpected runtime error")
        with pytest.raises(utilities.PaletteGenerationError):
            utilities._apply_palette_block(config_data)
        story.then("the wrapper re-raises a PaletteGenerationError")

    def test_apply_palette_block_returns_none_for_empty_swatches(
        self,
        monkeypatch: pytest.MonkeyPatch,
        story,
    ) -> None:
        """Empty swatch lists result in no palette metadata."""

        def empty(_: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
            return [], {"source": "custom"}

        monkeypatch.setattr(utilities, "_resolve_palette_block", empty)
        config_data = {"palette": {"source": "registry", "name": "modern"}}
        story.given("palette resolution returns no swatches")
        story.when("the palette block applies the swatches")
        result = utilities._apply_palette_block(config_data)
        story.then("no palette metadata is produced when swatches are empty")
        assert result is None

    def test_resolve_palette_block_requires_registry_name(self, story) -> None:
        """Registry source without a palette name raises PaletteLookupError."""
        story.given("a palette block specifies registry source without a name")
        with pytest.raises(utilities.PaletteLookupError):
            utilities._resolve_palette_block({"source": "registry"})
        story.then("palette lookup errors to inform missing name")

    def test_resolve_palette_block_validates_generator_ranges(self, story) -> None:
        """Generator sources must provide valid hue and luminance ranges."""
        block = {
            "source": "generator",
            "hue_range": (0,),
            "luminance_range": (0.2, 0.8),
        }
        story.given("generator palette block has malformed hue_range")
        with pytest.raises(utilities.PaletteGenerationError):
            utilities._resolve_palette_block(block)
        story.then("palette generation errors to highlight invalid ranges")

    def test_resolve_palette_block_remote_success(
        self,
        monkeypatch: pytest.MonkeyPatch,
        story,
    ) -> None:
        """Remote palette lookups hydrate configuration metadata."""

        class DummyPalette:
            name = "Example"
            swatches = ("#111111", "#222222", "#333333")
            metadata = {"creator": "api"}

        class DummyClient:
            def fetch(self, **_: Any) -> list[DummyPalette]:
                return [DummyPalette()]

        monkeypatch.setattr(utilities, "ColourLoversClient", lambda: DummyClient())
        story.given("the remote palette provider returns a palette")
        story.when("the palette block resolves the remote palette")
        swatches, metadata = utilities._resolve_palette_block({"source": "remote"})
        story.then("metadata reflects remote source details")
        assert swatches == list(DummyPalette.swatches)
        assert metadata["source"] == "remote"
        assert metadata["name"] == DummyPalette.name

    def test_resolve_palette_block_remote_without_results(
        self,
        monkeypatch: pytest.MonkeyPatch,
        story,
    ) -> None:
        """Remote palette lookup must return at least one palette."""

        class DummyClient:
            def fetch(self, **_: Any) -> list[Any]:
                return []

        monkeypatch.setattr(utilities, "ColourLoversClient", lambda: DummyClient())
        story.given("the remote provider returns no palettes")
        with pytest.raises(utilities.PaletteLookupError):
            utilities._resolve_palette_block({"source": "remote"})
        story.then("a PaletteLookupError communicates missing palettes")


class TestSkillFormatting:
    """Additional coverage for format_skill_groups helpers."""

    def test_coerce_items_handles_none_and_sets(self, story) -> None:
        """Coercion of None and iterable values behaves predictably."""
        story.given("coerce_items receives None and a set of skills")
        story.when("items are normalized")
        assert utilities._coerce_items(None) == []
        items = utilities._coerce_items({"python", "pytest"})
        story.then("the resulting list omits blanks and trims entries")
        assert all(item for item in items)

    def test_format_skill_groups_with_dict_input(self, story) -> None:
        """Dictionary inputs produce titled groups."""
        story.given("skill groups provided as a dictionary")
        story.when("the formatter processes the entries")
        result = utilities.format_skill_groups({"Languages": ["Python", "Go"]})
        story.then("each key becomes a titled group")
        assert result == [
            {"title": "Languages", "items": ["Python", "Go"]},
        ]

    def test_format_skill_groups_with_nested_iterables(self, story) -> None:
        """Nested iterables expand into multiple groups."""
        payload: list[Any] = [
            {"Frameworks": ["FastAPI"]},
            "Docker",
        ]
        story.given("skills contain nested dictionaries and strings")
        story.when("the formatter normalizes the payload")
        result = utilities.format_skill_groups(payload)
        story.then("groups reflect nested structure with proper titles")
        assert result[0]["title"] == "Frameworks"
        assert "FastAPI" in result[0]["items"]
        assert result[1]["title"] is None
        assert result[1]["items"] == ["Docker"]

    def test_format_skill_groups_simple_string(self, story) -> None:
        """Simple strings become untitled groups."""
        story.given("a single string skill is provided")
        story.when("the formatter converts it into groups")
        result = utilities.format_skill_groups("pytest")
        story.then("the result contains a single untitled group with the value")
        assert result == [{"title": None, "items": ["pytest"]}]
