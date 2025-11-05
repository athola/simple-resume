"""Tests for the new enhanced API features.

This module tests the new pandas/requests-style API features including:
- Symmetric I/O patterns
- Method chaining
- Session management
- Rich result objects
- Exception hierarchy
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from simple_resume import (
    BatchGenerationResult,
    ConfigurationError,
    GenerationConfig,
    GenerationError,
    GenerationResult,
    Resume,
    ResumeSession,
    SessionConfig,
    ValidationError,
    generate_all,
    generate_html,
    generate_pdf,
    generate_resume,
)
from simple_resume.config import Paths
from simple_resume.exceptions import (
    SimpleResumeError,
    raise_configuration_error,
    raise_generation_error,
    raise_validation_error,
)


class TestResumeSymmetricIO:
    """Test symmetric I/O patterns (pandas-style)."""

    @pytest.fixture
    def sample_resume_data(self):
        """Sample resume data for testing."""
        return {
            "full_name": "John Doe",
            "email": "john@example.com",
            "phone": "+1-555-0123",
            "description": "Software engineer with 5 years experience",
            "config": {
                "page_width": 210,
                "page_height": 297,
                "theme_color": "#0395DE",
            },
            "body": {
                "experience": [
                    {
                        "company": "Tech Corp",
                        "position": "Senior Developer",
                        "start_date": "2020-01",
                        "end_date": "2023-12",
                        "description": "Led development of cloud services",
                    }
                ]
            },
        }

    @pytest.fixture
    def temp_paths(self):
        """Create temporary paths for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            input_dir = base_path / "input"
            output_dir = base_path / "output"
            templates_dir = base_path / "templates"
            static_dir = base_path / "static"

            input_dir.mkdir(parents=True)
            output_dir.mkdir(parents=True)
            templates_dir.mkdir(parents=True)
            static_dir.mkdir(parents=True)

            # Create a minimal template
            template_file = templates_dir / "test_template.html"
            template_file.write_text("<html><body>{{ full_name }}</body></html>")

            paths = Paths(
                data=base_path,
                content=input_dir,
                input=input_dir,
                output=output_dir,
                templates=templates_dir,
                static=static_dir,
            )

            yield paths, base_path

    def test_resume_from_data(self, sample_resume_data):
        """Test creating Resume from data dictionary."""
        resume = Resume.from_data(sample_resume_data, name="test_resume")

        assert resume._name == "test_resume"
        assert resume._data["full_name"] == "John Doe"
        assert resume.validate().is_valid

    def test_resume_with_template_chaining(self, sample_resume_data):
        """Test method chaining for template changes."""
        resume = Resume.from_data(sample_resume_data)

        # Test method chaining
        new_resume = (
            resume.with_template("modern_template")
            .with_palette("professional")
            .with_config(page_width=220)
            .preview()
        )

        assert new_resume._data["template"] == "modern_template"
        assert new_resume._data["config"]["color_scheme"] == "professional"
        assert new_resume._data["config"]["page_width"] == 220
        assert new_resume._is_preview

    def test_resume_validate_method(self, sample_resume_data):
        """Test Resume validation method."""
        resume = Resume.from_data(sample_resume_data)

        validation = resume.validate()
        assert validation.is_valid
        assert not validation.errors

        # Test that validation is cached
        validation2 = resume.validate()
        assert validation is validation2

    def test_resume_generate_method(self, sample_resume_data, temp_paths):
        """Test unified generate method."""
        paths, _ = temp_paths
        resume = Resume.from_data(sample_resume_data, paths=paths)

        # Mock the generation methods to avoid actual file creation
        with patch.object(resume, "_generate_pdf_with_weasyprint") as mock_pdf:
            with patch.object(resume, "_generate_html_with_jinja") as mock_html:
                mock_result = Mock(spec=GenerationResult)
                mock_pdf.return_value = mock_result
                mock_html.return_value = mock_result

                # Test PDF generation
                resume.generate(format="pdf")
                mock_pdf.assert_called_once()

                # Test HTML generation
                resume.generate(format="html")
                mock_html.assert_called_once()

                # Test invalid format
                with pytest.raises(ValueError, match="Unsupported format"):
                    resume.generate(format="invalid")

    def test_resume_read_yaml_classmethod(self, temp_paths):
        """Test pandas-style read_yaml class method."""
        paths, base_path = temp_paths

        # Create a test YAML file
        yaml_file = paths.input / "test_resume.yaml"
        yaml_content = """
full_name: "Jane Smith"
email: "jane@example.com"
config:
  page_width: 210
  theme_color: "#FF5733"
"""
        yaml_file.write_text(yaml_content)

        # Test reading with path overrides
        resume = Resume.read_yaml(
            "test_resume",
            data_dir=str(base_path),
            content_dir=str(paths.content),
            templates_dir=str(paths.templates),
            static_dir=str(paths.static),
        )

        assert resume._name == "test_resume"
        assert resume._data["full_name"] == "Jane Smith"
        assert resume._data["config"]["theme_color"] == "#FF5733"

    def test_resume_with_palette_variations(self, sample_resume_data):
        """Test different palette application methods."""
        resume = Resume.from_data(sample_resume_data)

        # Test palette by name
        resume1 = resume.with_palette("professional")
        assert resume1._data["config"]["color_scheme"] == "professional"

        # Test palette configuration dict
        palette_config = {"source": "generator", "seed": 42, "size": 6}
        resume2 = resume.with_palette(palette_config)
        assert resume2._data["config"]["palette"] == palette_config


class TestResumeSession:
    """Test ResumeSession functionality."""

    @pytest.fixture
    def temp_session_paths(self):
        """Create temporary paths for session testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            input_dir = base_path / "input"
            output_dir = base_path / "output"
            templates_dir = base_path / "templates"
            static_dir = base_path / "static"

            input_dir.mkdir(parents=True)
            output_dir.mkdir(parents=True)
            templates_dir.mkdir(parents=True)
            static_dir.mkdir(parents=True)

            # Create test YAML files
            yaml1 = input_dir / "resume1.yaml"
            yaml2 = input_dir / "resume2.yaml"

            yaml1.write_text("""
full_name: "Alice Johnson"
email: "alice@example.com"
config:
  template: "modern"
""")

            yaml2.write_text("""
full_name: "Bob Wilson"
email: "bob@example.com"
config:
  template: "classic"
""")

            yield input_dir, output_dir, templates_dir, static_dir

    def test_session_initialization(self, temp_session_paths):
        """Test ResumeSession initialization."""
        input_dir, output_dir, templates_dir, static_dir = temp_session_paths

        session = ResumeSession(
            data_dir=input_dir.parent,
            content_dir=input_dir,
            templates_dir=templates_dir,
            static_dir=static_dir,
        )

        assert session.is_active
        assert session.operation_count == 0
        assert session.session_id is not None
        assert session.paths.input == input_dir

    def test_session_context_manager(self, temp_session_paths):
        """Test ResumeSession as context manager."""
        input_dir, output_dir, templates_dir, static_dir = temp_session_paths

        with ResumeSession(
            data_dir=input_dir.parent,
            content_dir=input_dir,
            templates_dir=templates_dir,
            static_dir=static_dir,
        ) as session:
            assert session.is_active
            session_id = session.session_id

        # Session should be closed after context
        assert not session.is_active
        assert session_id == session.session_id  # ID remains the same

    def test_session_resume_loading_with_cache(self, temp_session_paths):
        """Test resume loading with caching."""
        input_dir, output_dir, templates_dir, static_dir = temp_session_paths

        with ResumeSession(
            data_dir=input_dir.parent,
            content_dir=input_dir,
            templates_dir=templates_dir,
            static_dir=static_dir,
        ) as session:
            # Load resume first time
            resume1 = session.resume("resume1")
            assert resume1._data["full_name"] == "Alice Johnson"

            # Load same resume again (should use cache)
            resume2 = session.resume("resume1")
            assert resume1 is resume2  # Should be same object due to caching

            # Load with cache disabled
            resume3 = session.resume("resume1", use_cache=False)
            assert resume3 is not resume1  # Should be different object

    def test_session_configuration_defaults(self, temp_session_paths):
        """Test session configuration defaults."""
        input_dir, output_dir, templates_dir, static_dir = temp_session_paths

        config = SessionConfig(
            default_template="professional", default_palette="modern", preview_mode=True
        )

        with ResumeSession(
            data_dir=input_dir.parent,
            content_dir=input_dir,
            templates_dir=templates_dir,
            static_dir=static_dir,
            config=config,
        ) as session:
            resume = session.resume("resume1")
            assert resume._data["template"] == "professional"
            assert resume._data["config"]["color_scheme"] == "modern"
            assert resume._is_preview

    def test_session_cache_management(self, temp_session_paths):
        """Test session cache management."""
        input_dir, output_dir, templates_dir, static_dir = temp_session_paths

        with ResumeSession(
            data_dir=input_dir.parent,
            content_dir=input_dir,
            templates_dir=templates_dir,
            static_dir=static_dir,
        ) as session:
            # Load some resumes
            session.resume("resume1")
            session.resume("resume2")

            # Check cache info
            cache_info = session.get_cache_info()
            assert cache_info["cache_size"] == 2
            assert "resume1" in cache_info["cached_resumes"]
            assert "resume2" in cache_info["cached_resumes"]

            # Invalidate specific cache
            session.invalidate_cache("resume1")
            cache_info = session.get_cache_info()
            assert cache_info["cache_size"] == 1
            assert "resume1" not in cache_info["cached_resumes"]

            # Invalidate all cache
            session.invalidate_cache()
            cache_info = session.get_cache_info()
            assert cache_info["cache_size"] == 0


class TestGenerationResult:
    """Test GenerationResult functionality."""

    @pytest.fixture
    def temp_result_file(self):
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".pdf", delete=False) as f:
            f.write("dummy pdf content")
            return Path(f.name)

    def test_generation_result_properties(self, temp_result_file):
        """Test GenerationResult properties."""
        result = GenerationResult(temp_result_file, "pdf")

        assert result.exists
        assert result.format_type == "pdf"
        assert result.name == temp_result_file.name
        assert result.stem == temp_result_file.stem
        assert result.suffix == temp_result_file.suffix
        assert result.size > 0
        assert isinstance(result.size_human, str)

    def test_generation_result_file_operations(self, temp_result_file):
        """Test GenerationResult file operations."""
        result = GenerationResult(temp_result_file, "pdf")

        # Test reading content
        content = result.read_text()
        assert content == "dummy pdf content"

        bytes_content = result.read_bytes()
        assert b"dummy pdf content" in bytes_content

        # Test copy operation
        copy_dir = temp_result_file.parent / "copies"
        copy_dir.mkdir(exist_ok=True)
        copied_path = result.copy_to(copy_dir)
        assert copied_path.exists()
        assert copied_path.read_text() == "dummy pdf content"

        # Test move operation
        move_path = copied_path.with_name("moved_test.pdf")
        moved_path = result.copy_to(move_path)
        assert moved_path.exists()

        # Test delete operation - use unlink() for Path objects
        moved_path.unlink()
        assert not moved_path.exists()

    def test_generation_result_bool_conversion(self, temp_result_file):
        """Test GenerationResult boolean conversion."""
        result = GenerationResult(temp_result_file, "pdf")
        assert bool(result) is True

        # Delete file and test
        temp_result_file.unlink()
        assert bool(result) is False

    def test_batch_generation_result(self):
        """Test BatchGenerationResult functionality."""
        results = {}
        errors = {}

        # Create some mock results
        for i in range(3):
            mock_result = Mock(spec=GenerationResult)
            mock_result.exists = True
            results[f"resume{i}"] = mock_result

        # Create some mock errors
        errors["failed_resume"] = Exception("Test error")

        batch_result = BatchGenerationResult(
            results=results, total_time=5.5, successful=3, failed=1, errors=errors
        )

        assert batch_result.total == 4
        assert batch_result.success_rate == 75.0
        assert len(batch_result.get_successful()) == 3
        assert len(batch_result.get_failed()) == 1

        # Test iteration
        successful_items = list(batch_result)
        assert len(successful_items) == 3


class TestExceptionHierarchy:
    """Test the new exception hierarchy."""

    def test_base_exception(self):
        """Test base SimpleResumeError."""
        exc = SimpleResumeError("Test message")
        assert str(exc) == "Test message"
        assert isinstance(exc, Exception)

    def test_validation_error_with_context(self):
        """Test ValidationError with context."""
        errors = ["Missing field", "Invalid format"]
        warnings = ["Deprecated setting"]

        exc = ValidationError(
            "Validation failed", errors=errors, warnings=warnings, filename="test.yaml"
        )

        assert "test.yaml" in str(exc)
        assert exc.errors == errors
        assert exc.warnings == warnings

    def test_configuration_error_with_details(self):
        """Test ConfigurationError with specific details."""
        exc = ConfigurationError(
            "Invalid configuration",
            config_key="page_width",
            config_value="-10",
            filename="test.yaml",
        )

        assert "page_width" in str(exc)
        assert exc.config_key == "page_width"
        assert exc.config_value == "-10"

    def test_generation_error_with_metadata(self):
        """Test GenerationError with generation metadata."""
        exc = GenerationError(
            "PDF generation failed",
            format_type="pdf",
            output_path="/path/to/output.pdf",
        )

        assert "pdf" in str(exc)
        assert exc.format_type == "pdf"
        assert exc.output_path == "/path/to/output.pdf"

    def test_convenience_functions(self):
        """Test convenience exception raising functions."""
        # Test validation error
        with pytest.raises(ValidationError) as exc_info:
            raise_validation_error("Invalid data", errors=["Field missing"])
        assert "Invalid data" in str(exc_info.value)

        # Test configuration error
        with pytest.raises(ConfigurationError) as exc_info:
            raise_configuration_error(
                "Bad config",
                config_key="theme",
                config_value="invalid",
                filename="test.yaml",
            )
        assert exc_info.value.config_key == "theme"

        # Test generation error
        with pytest.raises(GenerationError) as exc_info:
            raise_generation_error("Generation failed", format_type="pdf")
        assert exc_info.value.format_type == "pdf"


class TestUnifiedGenerationFunctions:
    """Test the new unified generation functions."""

    @pytest.fixture
    def temp_generation_paths(self):
        """Create temporary paths for generation testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            input_dir = base_path / "input"
            output_dir = base_path / "output"
            templates_dir = base_path / "templates"
            static_dir = base_path / "static"

            input_dir.mkdir(parents=True)
            output_dir.mkdir(parents=True)
            templates_dir.mkdir(parents=True)
            static_dir.mkdir(parents=True)

            # Create test YAML file
            yaml_file = input_dir / "test_resume.yaml"
            yaml_file.write_text("""
full_name: "Test User"
email: "test@example.com"
config:
  page_width: 210
  theme_color: "#0395DE"
""")

            # Create minimal template
            template_file = templates_dir / "test_template.html"
            template_file.write_text("<html><body>{{ full_name }}</body></html>")

            yield input_dir, output_dir, templates_dir, static_dir

    @patch("simple_resume.generation.ResumeSession")
    def test_generate_pdf_function(self, mock_session_class, temp_generation_paths):
        """Test unified generate_pdf function."""
        input_dir, output_dir, templates_dir, static_dir = temp_generation_paths

        # Mock session and result
        mock_session = Mock()
        mock_result = Mock(spec=GenerationResult)
        mock_resume = Mock()
        mock_resume.with_config.return_value.to_pdf.return_value = mock_result
        mock_session.resume.return_value = mock_resume
        mock_session_class.return_value.__enter__.return_value = mock_session

        config = GenerationConfig(
            data_dir=input_dir.parent,
            name="test_resume",
            template="test_template",
        )
        result = generate_pdf(config, theme_color="#FF0000")

        assert result is mock_result
        mock_session_class.assert_called_once()
        mock_session.resume.assert_called_once_with("test_resume")
        mock_resume.with_config.assert_called_once_with(theme_color="#FF0000")
        mock_resume.with_config.return_value.to_pdf.assert_called_once()

    @patch("simple_resume.generation.ResumeSession")
    def test_generate_html_function(self, mock_session_class, temp_generation_paths):
        """Test unified generate_html function."""
        input_dir, output_dir, templates_dir, static_dir = temp_generation_paths

        # Mock session and result
        mock_session = Mock()
        mock_result = Mock(spec=GenerationResult)
        mock_session.resume.return_value.to_html.return_value = mock_result
        mock_session_class.return_value.__enter__.return_value = mock_session

        config = GenerationConfig(
            data_dir=input_dir.parent,
            name="test_resume",
            template="test_template",
            browser="firefox",
        )
        result = generate_html(config)

        assert result is mock_result
        # browser is an explicit parameter, not config_override,
        # so no with_config() call
        mock_session.resume.return_value.to_html.assert_called_once_with(
            open_after=False, browser="firefox"
        )

    @patch("simple_resume.generation.ResumeSession")
    def test_generate_all_function(self, mock_session_class, temp_generation_paths):
        """Test unified generate_all function."""
        input_dir, output_dir, templates_dir, static_dir = temp_generation_paths

        # Mock session and results
        mock_session = Mock()
        mock_pdf_result = Mock(spec=BatchGenerationResult)
        mock_html_result = Mock(spec=BatchGenerationResult)
        mock_session.generate_all.side_effect = [mock_pdf_result, mock_html_result]
        mock_session_class.return_value.__enter__.return_value = mock_session

        config = GenerationConfig(
            data_dir=input_dir.parent, formats=["pdf", "html"], template="test_template"
        )
        results = generate_all(config)

        assert "pdf" in results
        assert "html" in results
        assert results["pdf"] is mock_pdf_result
        assert results["html"] is mock_html_result

    @patch("simple_resume.generation.ResumeSession")
    def test_generate_resume_function(self, mock_session_class, temp_generation_paths):
        """Test unified generate_resume function."""
        input_dir, output_dir, templates_dir, static_dir = temp_generation_paths

        # Mock session and result
        mock_session = Mock()
        mock_result = Mock(spec=GenerationResult)
        mock_session.resume.return_value.to_pdf.return_value = mock_result
        mock_session_class.return_value.__enter__.return_value = mock_session

        config = GenerationConfig(
            name="test_resume",
            data_dir=input_dir.parent,
            format="pdf",
            template="test_template",
        )
        result = generate_resume(config)

        assert result is mock_result

    def test_generate_all_invalid_format(self):
        """Test generate_all with invalid format."""
        config = GenerationConfig(formats=["invalid_format"])
        with pytest.raises(ValueError, match="Unsupported format"):
            generate_all(config)


class TestAPIIntegration:
    """Test integration between different API components."""

    @pytest.fixture
    def integration_data(self):
        """Sample data for integration testing."""
        return {
            "full_name": "Integration Test",
            "email": "test@integration.com",
            "config": {
                "page_width": 210,
                "page_height": 297,
                "theme_color": "#2E86AB",
            },
        }

    def test_chaining_with_session(self, integration_data):
        """Test method chaining with session management."""
        resume = Resume.from_data(integration_data)

        # Test that chaining creates new instances
        modified_resume = (
            resume.with_template("modern").with_palette("professional").preview()
        )

        assert resume is not modified_resume
        assert modified_resume._is_preview
        assert modified_resume._data["template"] == "modern"

    def test_error_propagation_through_api(self, integration_data):
        """Test that errors properly propagate through API layers."""
        resume = Resume.from_data(integration_data)

        # Test validation returns result with errors for invalid data
        # Note: validate() returns a result object, it doesn't raise exceptions
        # This follows the pandas-style API pattern of returning result objects
        valid_result = resume.validate()
        assert valid_result.is_valid
        assert not valid_result.errors

        # Test that invalid data is detected by validation
        invalid_data = {"config": {"theme_color": "not-a-color"}}
        invalid_resume = Resume.from_data(invalid_data)
        invalid_result = invalid_resume.validate()
        assert not invalid_result.is_valid
        assert len(invalid_result.errors) > 0
        assert "theme_color" in invalid_result.errors[0]

    def test_api_compatibility_patterns(self, integration_data):
        """Test that API follows pandas/requests compatibility patterns."""
        # Test symmetric I/O pattern
        assert hasattr(Resume, "read_yaml")
        assert hasattr(Resume, "to_pdf")
        assert hasattr(Resume, "to_html")

        # Test method chaining pattern
        resume = Resume.from_data(integration_data)
        assert hasattr(resume, "with_template")
        assert hasattr(resume, "with_palette")
        assert hasattr(resume, "with_config")

        # Test fluent interface
        chained = resume.with_template("test").preview()
        assert chained._data["template"] == "test"
        assert chained._is_preview
