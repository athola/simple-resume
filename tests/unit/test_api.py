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
from typing import cast
from unittest.mock import Mock, patch

import pytest

import simple_resume.generation as generation_module
from simple_resume import (
    BatchGenerationResult,
    ConfigurationError,
    GenerationError,
    GenerationResult,
    Resume,
    ValidationError,
    generate,
    preview,
)
from simple_resume.config import Paths
from simple_resume.exceptions import SimpleResumeError
from simple_resume.generation import (
    GenerationConfig,
    generate_all,
    generate_html,
    generate_pdf,
    generate_resume,
)
from simple_resume.session import ResumeSession, SessionConfig


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

    def test_resume_from_data(self, story, sample_resume_data):
        story.given("a complete resume payload provided as a dictionary")
        story.when("Resume.from_data is invoked with an explicit name")
        resume = Resume.from_data(sample_resume_data, name="test_resume")

        story.then("the resulting Resume stores the name and validates successfully")
        assert resume._name == "test_resume"
        assert resume._data["full_name"] == "John Doe"
        assert resume.validate().is_valid

    def test_resume_with_template_chaining(self, story, sample_resume_data):
        story.given("an existing Resume constructed from data")
        resume = Resume.from_data(sample_resume_data)

        story.when("chaining template, palette, config, and preview modifications")
        new_resume = (
            resume.with_template("modern_template")
            .with_palette("professional")
            .with_config(page_width=220)
            .preview()
        )

        story.then("each chained call mutates the derived resume as expected")
        assert new_resume._data["template"] == "modern_template"
        assert new_resume._data["config"]["color_scheme"] == "professional"
        assert new_resume._data["config"]["page_width"] == 220
        assert new_resume._is_preview

    def test_resume_validate_method(self, story, sample_resume_data):
        story.given("a Resume instance with valid configuration")
        resume = Resume.from_data(sample_resume_data)

        story.when("validate is invoked twice")
        validation = resume.validate()
        validation2 = resume.validate()

        story.then("validation passes with caching of the result")
        assert validation.is_valid
        assert not validation.errors
        assert validation is validation2

    def test_resume_generate_method(self, story, sample_resume_data, temp_paths):
        story.given("a Resume bound to resolved paths and mocked generators")
        paths, _ = temp_paths
        resume = Resume.from_data(sample_resume_data, paths=paths)

        with (
            patch.object(resume, "_generate_pdf") as mock_pdf,
            patch.object(resume, "_generate_html") as mock_html,
        ):
            mock_result = Mock(spec=GenerationResult)
            mock_pdf.return_value = mock_result
            mock_html.return_value = mock_result

            story.when("calling generate for PDF, HTML, then an unsupported format")
            resume.generate(format="pdf")
            resume.generate(format="html")

            story.then("the appropriate generator is invoked and invalid formats fail")
            mock_pdf.assert_called_once()
            mock_html.assert_called_once()
            with pytest.raises(ValueError, match="Unsupported format"):
                resume.generate(format="invalid")

    def test_resume_read_yaml_classmethod(self, story, temp_paths):
        story.given("a YAML resume file stored within the input directory")
        paths, _ = temp_paths
        yaml_file = paths.input / "test_resume.yaml"
        yaml_content = """
full_name: "Jane Smith"
email: "jane@example.com"
config:
  page_width: 210
  theme_color: "#FF5733"
"""
        yaml_file.write_text(yaml_content)

        story.when("Resume.read_yaml loads the file")
        resume = Resume.read_yaml(yaml_file)

        story.then("the returned Resume reflects the file contents")
        assert resume._name == "test_resume"
        assert resume._data["full_name"] == "Jane Smith"
        assert resume._data["config"]["theme_color"] == "#FF5733"

    def test_resume_with_palette_variations(self, story, sample_resume_data):
        story.given("a Resume that supports palette overrides by name or config")
        resume = Resume.from_data(sample_resume_data)
        palette_config = {"source": "generator", "seed": 42, "size": 6}

        story.when("applying a palette by name and again via configuration dict")
        resume1 = resume.with_palette("professional")
        resume2 = resume.with_palette(palette_config)

        story.then("the config color_scheme or palette data is updated accordingly")
        assert resume1._data["config"]["color_scheme"] == "professional"
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

    def test_session_initialization(self, story, temp_session_paths):
        story.given(
            "resolved directories for data, content, templates, and static assets"
        )
        input_dir, _, templates_dir, static_dir = temp_session_paths

        story.when("a ResumeSession is instantiated with those paths")
        session = ResumeSession(
            data_dir=input_dir.parent,
            content_dir=input_dir,
            templates_dir=templates_dir,
            static_dir=static_dir,
        )

        story.then(
            "the session starts active with zero operations and registered paths"
        )
        assert session.is_active
        assert session.operation_count == 0
        assert session.session_id is not None
        assert session.paths.input == input_dir

    def test_session_context_manager(self, story, temp_session_paths):
        story.given("a session created via context manager")
        input_dir, _, templates_dir, static_dir = temp_session_paths

        with ResumeSession(
            data_dir=input_dir.parent,
            content_dir=input_dir,
            templates_dir=templates_dir,
            static_dir=static_dir,
        ) as session:
            story.when("the context is entered")
            assert session.is_active
            session_id = session.session_id

        story.then("exiting the context closes the session but preserves the ID")
        assert not session.is_active
        assert session_id == session.session_id

    def test_session_resume_loading_with_cache(self, story, temp_session_paths):
        story.given("pre-populated resume YAML files accessible to the session")
        input_dir, _, templates_dir, static_dir = temp_session_paths

        with ResumeSession(
            data_dir=input_dir.parent,
            content_dir=input_dir,
            templates_dir=templates_dir,
            static_dir=static_dir,
        ) as session:
            story.when("the same resume is requested with and without cache usage")
            resume1 = session.resume("resume1")
            resume2 = session.resume("resume1")
            resume3 = session.resume("resume1", use_cache=False)

        story.then(
            "cached calls reuse the object while disabled cache reloads fresh data"
        )
        assert resume1._data["full_name"] == "Alice Johnson"
        assert resume1 is resume2
        assert resume3 is not resume1

    def test_session_configuration_defaults(self, story, temp_session_paths):
        story.given(
            "session configuration overrides template, palette, and preview mode"
        )
        input_dir, _, templates_dir, static_dir = temp_session_paths
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
            story.when("a resume is loaded through the session")
            resume = session.resume("resume1")

        story.then("the resume inherits the configured defaults and preview state")
        assert resume._data["template"] == "professional"
        assert resume._data["config"]["color_scheme"] == "modern"
        assert resume._is_preview

    def test_session_cache_management(self, story, temp_session_paths):
        story.given("two resumes are loaded through a long-lived session")
        input_dir, _, templates_dir, static_dir = temp_session_paths

        with ResumeSession(
            data_dir=input_dir.parent,
            content_dir=input_dir,
            templates_dir=templates_dir,
            static_dir=static_dir,
        ) as session:
            session.resume("resume1")
            session.resume("resume2")

            story.when("cache is inspected, partially cleared, then fully cleared")
            cache_info = session.get_cache_info()
            session.invalidate_cache("resume1")
            partial_cache = session.get_cache_info()
            session.invalidate_cache()
            empty_cache = session.get_cache_info()

        story.then("cache metrics reflect the current entries after each operation")
        assert cache_info["cache_size"] == 2
        assert set(cache_info["cached_resumes"]) == {"resume1", "resume2"}
        assert partial_cache["cache_size"] == 1
        assert set(partial_cache["cached_resumes"]) == {"resume2"}
        assert empty_cache["cache_size"] == 0


class TestGenerationResult:
    """Test GenerationResult functionality."""

    @pytest.fixture
    def temp_result_file(self):
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".pdf", delete=False) as f:
            f.write("dummy pdf content")
            return Path(f.name)

    def test_generation_result_properties(self, story, temp_result_file):
        story.given("a generated PDF represented by a real temporary file")
        result = GenerationResult(temp_result_file, "pdf")

        story.when("introspecting metadata on the GenerationResult")
        story.then("file existence, naming, and sizing details are exposed")
        assert result.exists
        assert result.format_type == "pdf"
        assert result.name == temp_result_file.name
        assert result.stem == temp_result_file.stem
        assert result.suffix == temp_result_file.suffix
        assert result.size > 0
        assert isinstance(result.size_human, str)

    def test_generation_result_file_operations(self, story, temp_result_file):
        story.given("a GenerationResult wrapping a PDF on disk")
        result = GenerationResult(temp_result_file, "pdf")

        story.when("reading, copying, moving, and deleting the artifact")
        content = result.read_text()
        bytes_content = result.read_bytes()
        copy_dir = temp_result_file.parent / "copies"
        copy_dir.mkdir(exist_ok=True)
        copied_path = result.copy_to(copy_dir)
        move_path = copied_path.with_name("moved_test.pdf")
        moved_path = result.copy_to(move_path)

        story.then("each filesystem operation reflects the underlying file state")
        assert content == "dummy pdf content"
        assert b"dummy pdf content" in bytes_content
        assert copied_path.exists()
        assert copied_path.read_text() == "dummy pdf content"
        assert move_path.exists()
        moved_path.unlink()
        assert not moved_path.exists()

    def test_generation_result_bool_conversion(self, story, temp_result_file):
        story.given("a GenerationResult pointing to an existing file")
        result = GenerationResult(temp_result_file, "pdf")

        story.when("the file remains on disk and later is removed")
        exists_before = bool(result)
        temp_result_file.unlink()
        exists_after = bool(result)

        story.then("truthiness mirrors the presence of the generated artifact")
        assert exists_before is True
        assert exists_after is False

    def test_batch_generation_result(self, story):
        story.given("three successful results and one recorded failure")
        results = {}
        errors = {"failed_resume": Exception("Test error")}
        for i in range(3):
            mock_result = Mock(spec=GenerationResult)
            mock_result.exists = True
            results[f"resume{i}"] = mock_result

        story.when("assembling a BatchGenerationResult")
        batch_result = BatchGenerationResult(
            results=results, total_time=5.5, successful=3, failed=1, errors=errors
        )

        story.then("aggregate metrics, listings, and iteration reflect the inputs")
        assert batch_result.total == 4
        assert batch_result.success_rate == 75.0
        assert len(batch_result.get_successful()) == 3
        assert len(batch_result.get_failed()) == 1
        assert len(list(batch_result)) == 3


class TestExceptionHierarchy:
    """Test the new exception hierarchy."""

    def test_base_exception(self, story):
        story.given("the base SimpleResumeError is instantiated")
        exc = SimpleResumeError("Test message")

        story.then("it behaves like a normal Exception and preserves the message")
        assert str(exc) == "Test message"
        assert isinstance(exc, Exception)

    def test_validation_error_with_context(self, story):
        story.given("structured validation errors and warnings for a YAML file")
        errors = ["Missing field", "Invalid format"]
        warnings = ["Deprecated setting"]

        story.when("ValidationError is raised with those details")
        exc = ValidationError(
            "Validation failed", errors=errors, warnings=warnings, filename="test.yaml"
        )

        story.then("the exception message and attributes expose the context")
        assert "test.yaml" in str(exc)
        assert exc.errors == errors
        assert exc.warnings == warnings

    def test_configuration_error_with_details(self, story):
        story.given("a configuration value violates constraints")
        story.when("ConfigurationError is instantiated with context fields")
        exc = ConfigurationError(
            "Invalid configuration",
            config_key="page_width",
            config_value="-10",
            filename="test.yaml",
        )

        story.then("the key and value are reflected in both message and attributes")
        assert "page_width" in str(exc)
        assert exc.config_key == "page_width"
        assert exc.config_value == "-10"

    def test_generation_error_with_metadata(self, story):
        story.given("a generation failure for a PDF output path")
        story.when("GenerationError is raised with format and path metadata")
        exc = GenerationError(
            "PDF generation failed",
            format_type="pdf",
            output_path="/path/to/output.pdf",
        )

        story.then("message and attributes expose the failing format and target path")
        assert "pdf" in str(exc)
        assert exc.format_type == "pdf"
        assert exc.output_path == "/path/to/output.pdf"

    def test_exception_hierarchy(self, story):
        story.given(
            "the ValidationError, ConfigurationError, and GenerationError classes"
        )

        story.when("inspecting inheritance and raising each exception")
        story.then("all derive from SimpleResumeError and behave polymorphically")
        assert issubclass(ValidationError, SimpleResumeError)
        assert issubclass(ConfigurationError, SimpleResumeError)
        assert issubclass(GenerationError, SimpleResumeError)
        assert issubclass(ValidationError, ValueError)

        with pytest.raises(SimpleResumeError):
            raise ValidationError("Invalid data", errors=["Field missing"])

        with pytest.raises(SimpleResumeError):
            raise ConfigurationError(
                "Bad config",
                config_key="theme",
                config_value="invalid",
                filename="test.yaml",
            )

        with pytest.raises(SimpleResumeError):
            raise GenerationError("Generation failed", format_type="pdf")


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
    def test_generate_pdf_function(
        self,
        mock_session_class,
        story,
        temp_generation_paths,
    ):
        story.given("GenerationConfig inputs and a mocked ResumeSession pipeline")
        input_dir, _, _, _ = temp_generation_paths
        mock_session = Mock()
        mock_result = Mock(spec=GenerationResult)
        mock_resume = Mock()
        mock_resume.with_config.return_value.to_pdf.return_value = mock_result
        mock_session.resume.return_value = mock_resume
        mock_session_class.return_value.__enter__.return_value = mock_session

        story.when("generate_pdf executes with override parameters")
        config = GenerationConfig(
            data_dir=input_dir.parent,
            name="test_resume",
            template="test_template",
        )
        result = generate_pdf(config, theme_color="#FF0000")

        story.then("the resume is fetched once and render pipeline receives overrides")
        assert result is mock_result
        mock_session_class.assert_called_once()
        mock_session.resume.assert_called_once_with("test_resume")
        mock_resume.with_config.assert_called_once_with(theme_color="#FF0000")
        mock_resume.with_config.return_value.to_pdf.assert_called_once()

    @patch("simple_resume.generation.ResumeSession")
    def test_generate_html_function(
        self,
        mock_session_class,
        story,
        temp_generation_paths,
    ):
        story.given("GenerationConfig requests HTML output via a browser-aware call")
        input_dir, _, _, _ = temp_generation_paths
        mock_session = Mock()
        mock_result = Mock(spec=GenerationResult)
        mock_session.resume.return_value.to_html.return_value = mock_result
        mock_session_class.return_value.__enter__.return_value = mock_session

        story.when("generate_html executes without config overrides")
        config = GenerationConfig(
            data_dir=input_dir.parent,
            name="test_resume",
            template="test_template",
            browser="firefox",
        )
        result = generate_html(config)

        story.then("the ResumeSession renders HTML exactly once with browser options")
        assert result is mock_result
        mock_session.resume.return_value.to_html.assert_called_once_with(
            open_after=False, browser="firefox"
        )

    @patch("simple_resume.generation.ResumeSession")
    def test_generate_all_function(
        self,
        mock_session_class,
        story,
        temp_generation_paths,
    ):
        story.given("formats include pdf and html with mocked session responses")
        input_dir, _, _, _ = temp_generation_paths
        mock_session = Mock()
        mock_pdf_result = Mock(spec=BatchGenerationResult)
        mock_html_result = Mock(spec=BatchGenerationResult)
        mock_session.generate_all.side_effect = [mock_pdf_result, mock_html_result]
        mock_session_class.return_value.__enter__.return_value = mock_session

        story.when("generate_all iterates over requested formats")
        config = GenerationConfig(
            data_dir=input_dir.parent, formats=["pdf", "html"], template="test_template"
        )
        results = generate_all(config)

        story.then("a mapping of formats to results is returned")
        assert results == {"pdf": mock_pdf_result, "html": mock_html_result}

    @patch("simple_resume.generation.ResumeSession")
    def test_generate_resume_function(
        self,
        mock_session_class,
        story,
        temp_generation_paths,
    ):
        story.given("a single-format GenerationConfig and mocked ResumeSession")
        input_dir, _, _, _ = temp_generation_paths
        mock_session = Mock()
        mock_result = Mock(spec=GenerationResult)
        mock_session.resume.return_value.to_pdf.return_value = mock_result
        mock_session_class.return_value.__enter__.return_value = mock_session

        story.when("generate_resume executes")
        config = GenerationConfig(
            name="test_resume",
            data_dir=input_dir.parent,
            format="pdf",
            template="test_template",
        )
        result = generate_resume(config)

        story.then("the helper delegates to ResumeSession and returns the result")
        assert result is mock_result

    def test_generate_all_invalid_format(self, story):
        story.given("GenerationConfig specifies an unsupported format")
        config = GenerationConfig(formats=["invalid_format"])

        story.then("generate_all raises a ValueError before invoking any session")
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

    def test_chaining_with_session(self, story, integration_data):
        story.given("a resume instance supporting fluent mutation")
        resume = Resume.from_data(integration_data)

        story.when("template, palette, and preview are chained")
        modified_resume = (
            resume.with_template("modern").with_palette("professional").preview()
        )

        story.then("each operation returns a new preview-ready resume")
        assert resume is not modified_resume
        assert modified_resume._is_preview
        assert modified_resume._data["template"] == "modern"

    def test_error_propagation_through_api(self, story, integration_data):
        story.given("valid and invalid resume payloads")
        resume = Resume.from_data(integration_data)
        invalid_data = {"config": {"theme_color": "not-a-color"}}
        invalid_resume = Resume.from_data(invalid_data)

        story.when("validate is called on both payloads")
        valid_result = resume.validate()
        invalid_result = invalid_resume.validate()

        story.then("valid data passes while invalid config yields descriptive errors")
        assert valid_result.is_valid
        assert not valid_result.errors
        assert not invalid_result.is_valid
        assert any("theme_color" in err for err in invalid_result.errors)

    def test_api_compatibility_patterns(self, story, integration_data):
        story.given("the API promises pandas/requests style affordances")

        story.when("checking for symmetric I/O and fluent interfaces")
        resume = Resume.from_data(integration_data)

        story.then("core entry points and method chaining helpers exist")
        for attr in ("read_yaml", "to_pdf", "to_html"):
            assert hasattr(Resume, attr)
        for attr in ("with_template", "with_palette", "with_config"):
            assert hasattr(resume, attr)
        chained = resume.with_template("test").preview()
        assert chained._data["template"] == "test"
        assert chained._is_preview


class TestConvenienceHelpers:
    """Behavioural coverage for the high-level generate/preview helpers."""

    def test_generate_deduces_yaml_path_defaults(self, story, tmp_path, monkeypatch):
        story.given("a YAML resume path on disk")
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        resume_path = input_dir / "casey.yaml"
        resume_path.write_text("full_name: Casey")

        captured_config: GenerationConfig | None = None

        def fake_generate_pdf(config: GenerationConfig, **overrides):
            nonlocal captured_config
            captured_config = config
            return "PDF"

        monkeypatch.setattr(generation_module, "generate_pdf", fake_generate_pdf)

        story.when("generate() runs with default parameters")
        results = generate(resume_path)

        story.then("the helper returns a mapping and passes a GenerationConfig")
        assert results == {"pdf": "PDF"}
        assert captured_config is not None
        assert captured_config.data_dir == input_dir
        assert captured_config.name == "casey"
        assert captured_config.preview is False

    def test_generate_multiple_formats_uses_generate_all(
        self, story, tmp_path, monkeypatch
    ) -> None:
        story.given("a directory of resumes and multiple requested formats")

        captured_config: GenerationConfig | None = None

        def fake_generate_all(config: GenerationConfig, **overrides):
            nonlocal captured_config
            captured_config = config
            return {fmt: f"result-{fmt}" for fmt in config.formats or []}

        monkeypatch.setattr(generation_module, "generate_all", fake_generate_all)

        story.when("generate() is called with pdf and html formats")
        results = generate(tmp_path, formats=("pdf", "html"), preview=True)

        story.then("generate_all receives normalized formats and preview flag")
        assert cast(dict[str, str], results) == {
            "pdf": "result-pdf",
            "html": "result-html",
        }
        assert captured_config is not None
        assert captured_config.formats == ["pdf", "html"]
        assert captured_config.preview is True

    def test_preview_calls_generate_html_with_preview_mode(
        self, story, tmp_path, monkeypatch
    ) -> None:
        story.given("a YAML file for a specific resume")
        resume_path = tmp_path / "casey.yaml"
        resume_path.write_text("full_name: Casey")

        captured_config: GenerationConfig | None = None

        def fake_generate_html(config: GenerationConfig, **overrides):
            nonlocal captured_config
            captured_config = config
            return "HTML"

        monkeypatch.setattr(generation_module, "generate_html", fake_generate_html)

        story.when("preview() is invoked")
        result = preview(resume_path)

        story.then("generate_html receives preview-mode configuration")
        assert cast(str, result) == "HTML"
        assert captured_config is not None
        assert captured_config.preview is True
        assert captured_config.name == "casey"

    def test_preview_requires_specific_resume(self, story, tmp_path) -> None:
        story.given("only a directory was provided")

        story.then("preview raises a ValueError explaining the requirement")
        with pytest.raises(ValueError, match="requires a specific resume"):
            preview(tmp_path)
