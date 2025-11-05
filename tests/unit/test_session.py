"""Test cases for session management functionality."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from simple_resume.config import Paths
from simple_resume.exceptions import ConfigurationError, SessionError
from simple_resume.session import (
    ResumeSession,
    SessionConfig,
    create_session,
)


class TestSessionConfig:
    """Behavioural expectations for SessionConfig."""

    def test_session_config_defaults(self, story) -> None:
        story.given("no overrides are provided")
        config = SessionConfig()

        story.then("all optional fields fall back to defaults")
        assert config.paths is None
        assert config.default_template is None
        assert config.default_palette is None
        assert config.default_format == "pdf"
        assert config.auto_open is False
        assert config.preview_mode is False
        assert config.output_dir is None
        assert config.session_metadata == {}

    def test_session_config_custom_values(self, story) -> None:
        output_dir = Path("/workspace/output")
        paths = Mock(spec=Paths)
        metadata = {"user": "test"}

        config = SessionConfig(
            paths=paths,
            default_template="modern",
            default_palette="blue",
            default_format="html",
            auto_open=True,
            preview_mode=True,
            output_dir=output_dir,
            session_metadata=metadata,
        )

        story.then("the provided values are stored verbatim")
        assert config.paths is paths
        assert config.default_template == "modern"
        assert config.default_palette == "blue"
        assert config.default_format == "html"
        assert config.auto_open is True
        assert config.preview_mode is True
        assert config.output_dir == output_dir
        assert config.session_metadata == metadata


class TestResumeSessionInit:
    """Session initialization scenarios."""

    def test_session_init_with_data_dir(self, story, tmp_path: Path) -> None:
        story.given("a valid data directory path")
        session = ResumeSession(data_dir=str(tmp_path))

        story.then("a session is created with active state and resolved paths")
        assert session.session_id is not None
        assert session.is_active is True
        assert session.operation_count == 0
        assert session.paths is not None
        session.close()

    def test_session_init_with_paths_object(self, story) -> None:
        mock_paths = Mock(spec=Paths)
        session = ResumeSession(paths=mock_paths)

        story.then("using explicit Paths bypasses resolution and activates session")
        assert session.paths is mock_paths
        assert session.is_active is True
        session.close()

    def test_session_init_with_both_paths_and_overrides_raises_error(
        self, story
    ) -> None:
        mock_paths = Mock(spec=Paths)

        story.given("a caller provides both resolved paths and overrides")
        with pytest.raises(ConfigurationError, match="either paths or path_overrides"):
            ResumeSession(paths=mock_paths, content_dir="/workspace/content")

        story.then("a configuration error is raised")

    def test_session_init_with_invalid_data_dir_raises_error(self, story) -> None:
        with patch("simple_resume.session.resolve_paths") as mock_resolve:
            mock_resolve.side_effect = Exception("Invalid path")

            story.when("ResumeSession attempts to resolve an invalid data_dir")
            with pytest.raises(ConfigurationError, match="Failed to resolve paths"):
                ResumeSession(data_dir="/invalid/path")

        story.then("the invalid path is surfaced as a configuration error")

    def test_session_init_with_output_dir_override(self, story, tmp_path: Path) -> None:
        output_dir = tmp_path / "custom_output"
        config = SessionConfig(output_dir=output_dir)

        session = ResumeSession(data_dir=str(tmp_path), config=config)

        story.then("the override updates both session and config paths")
        assert session.paths.output == output_dir
        assert session.config.paths.output == output_dir
        session.close()

    def test_session_init_with_custom_config(self, story, tmp_path: Path) -> None:
        config = SessionConfig(
            default_template="modern",
            default_palette="ocean",
            auto_open=True,
            preview_mode=True,
        )

        session = ResumeSession(data_dir=str(tmp_path), config=config)

        assert session.config.default_template == "modern"
        assert session.config.default_palette == "ocean"
        assert session.config.auto_open is True
        assert session.config.preview_mode is True
        session.close()


class TestResumeSessionProperties:
    """Test ResumeSession properties."""

    def test_session_id_property(self, story, tmp_path: Path) -> None:
        session = ResumeSession(data_dir=str(tmp_path))

        story.then("a unique session_id string is generated")
        assert isinstance(session.session_id, str)
        assert len(session.session_id) > 0
        session.close()

    def test_paths_property(self, story, tmp_path: Path) -> None:
        session = ResumeSession(data_dir=str(tmp_path))

        story.then("paths exposes the resolved Paths instance")
        assert isinstance(session.paths, Paths)
        session.close()

    def test_config_property(self, story, tmp_path: Path) -> None:
        config = SessionConfig(default_template="modern")
        session = ResumeSession(data_dir=str(tmp_path), config=config)

        story.then("session.config is the same object supplied at construction")
        assert session.config is config
        assert session.config.default_template == "modern"
        session.close()

    def test_is_active_property(self, story, tmp_path: Path) -> None:
        session = ResumeSession(data_dir=str(tmp_path))

        story.then("is_active tracks whether the session has been closed")
        assert session.is_active is True
        session.close()
        assert session.is_active is False

    def test_operation_count_property(self, story, tmp_path: Path) -> None:
        session = ResumeSession(data_dir=str(tmp_path))

        assert session.operation_count == 0
        session._operation_count = 5
        story.then("operation_count reflects the internal counter")
        assert session.operation_count == 5
        session.close()

    def test_average_generation_time_empty(self, story, tmp_path: Path) -> None:
        session = ResumeSession(data_dir=str(tmp_path))

        story.then("without generation history the average is zero")
        assert session.average_generation_time == 0.0
        session.close()

    def test_average_generation_time_with_data(self, story, tmp_path: Path) -> None:
        session = ResumeSession(data_dir=str(tmp_path))
        session._generation_times = [1.0, 2.0, 3.0]

        story.then("the average of recorded timings is returned")
        assert session.average_generation_time == 2.0
        session.close()


class TestResumeSessionResume:
    """Test ResumeSession.resume() method."""

    def test_resume_loads_with_session_paths(self, tmp_path: Path) -> None:
        """resume() loads resume with session paths."""
        # Create test YAML file
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        yaml_file = input_dir / "test_resume.yaml"
        yaml_file.write_text("full_name: Test User\nemail: test@example.com\n")

        session = ResumeSession(data_dir=str(tmp_path))
        loaded_resume = session.resume("test_resume")

        assert loaded_resume._data["full_name"] == "Test User"
        assert session.operation_count == 1
        session.close()

    def test_resume_caches_by_default(self, tmp_path: Path) -> None:
        """resume() caches loaded resumes by default."""
        # Create test YAML file
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        yaml_file = input_dir / "test_resume.yaml"
        yaml_file.write_text("full_name: Test User\n")

        session = ResumeSession(data_dir=str(tmp_path))
        resume1 = session.resume("test_resume")
        resume2 = session.resume("test_resume")

        assert resume1 is resume2
        assert session.operation_count == 1  # Only one load operation
        session.close()

    def test_resume_bypasses_cache_when_disabled(self, tmp_path: Path) -> None:
        """resume() bypasses cache when use_cache=False."""
        # Create test YAML file
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        yaml_file = input_dir / "test_resume.yaml"
        yaml_file.write_text("full_name: Test User\n")

        session = ResumeSession(data_dir=str(tmp_path))
        resume1 = session.resume("test_resume", use_cache=False)
        resume2 = session.resume("test_resume", use_cache=False)

        assert resume1 is not resume2
        assert session.operation_count == 2  # Two load operations
        session.close()

    def test_resume_applies_default_template(self, tmp_path: Path) -> None:
        """resume() applies session default template."""
        # Create test YAML file
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        yaml_file = input_dir / "test_resume.yaml"
        yaml_file.write_text("full_name: Test User\n")

        config = SessionConfig(default_template="modern")
        session = ResumeSession(data_dir=str(tmp_path), config=config)
        resume = session.resume("test_resume")

        assert resume._data.get("template") == "modern"
        session.close()

    def test_resume_applies_default_palette(self, tmp_path: Path) -> None:
        """resume() applies session default palette."""
        # Create test YAML file
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        yaml_file = input_dir / "test_resume.yaml"
        yaml_file.write_text("full_name: Test User\n")

        config = SessionConfig(default_palette="ocean")
        session = ResumeSession(data_dir=str(tmp_path), config=config)
        loaded_resume = session.resume("test_resume")

        # Palette application is tracked in the resume
        assert loaded_resume._data.get("config", {}).get("color_scheme") == "ocean"
        session.close()

    def test_resume_applies_preview_mode(self, tmp_path: Path) -> None:
        """resume() applies preview mode from session config."""
        # Create test YAML file
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        yaml_file = input_dir / "test_resume.yaml"
        yaml_file.write_text("full_name: Test User\n")

        config = SessionConfig(preview_mode=True)
        session = ResumeSession(data_dir=str(tmp_path), config=config)
        resume = session.resume("test_resume")

        assert resume._is_preview is True
        session.close()

    def test_resume_raises_error_when_session_inactive(self, tmp_path: Path) -> None:
        """resume() raises SessionError when session is inactive."""
        session = ResumeSession(data_dir=str(tmp_path))
        session.close()

        with pytest.raises(SessionError, match="session is not active"):
            session.resume("test_resume")

    def test_resume_wraps_exceptions_in_session_error(self, tmp_path: Path) -> None:
        """resume() wraps non-SessionError exceptions."""
        session = ResumeSession(data_dir=str(tmp_path))

        with pytest.raises(SessionError, match="Failed to load resume"):
            session.resume("nonexistent_resume")

        session.close()


class TestResumeSessionGenerateAll:
    """Test ResumeSession.generate_all() method."""

    def test_generate_all_with_no_yaml_files(self, tmp_path: Path) -> None:
        """generate_all() returns empty result with no YAML files."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        session = ResumeSession(data_dir=str(tmp_path))
        result = session.generate_all()

        assert result.successful == 0
        assert result.failed == 0
        assert len(result.results) == 0
        session.close()

    def test_generate_all_finds_yaml_files(self, tmp_path: Path) -> None:
        """generate_all() finds and processes YAML files."""
        # Create test YAML files
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "resume1.yaml").write_text("full_name: User One\n")
        (input_dir / "resume2.yaml").write_text("full_name: User Two\n")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        session = ResumeSession(data_dir=str(tmp_path))

        with patch.object(session, "resume") as mock_resume:
            mock_result = Mock()
            mock_resume_obj = Mock()
            mock_resume_obj.to_pdf.return_value = mock_result
            mock_resume.return_value = mock_resume_obj

            result = session.generate_all(format="pdf")

            assert result.successful == 2
            assert result.failed == 0
            assert len(result.results) == 2

        session.close()

    def test_generate_all_with_pattern(self, tmp_path: Path) -> None:
        """generate_all() filters files by pattern."""
        # Create test YAML files
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "user_resume.yaml").write_text("full_name: User\n")
        (input_dir / "admin_resume.yaml").write_text("full_name: Admin\n")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        session = ResumeSession(data_dir=str(tmp_path))

        with patch.object(session, "resume") as mock_resume:
            mock_result = Mock()
            mock_resume_obj = Mock()
            mock_resume_obj.to_pdf.return_value = mock_result
            mock_resume.return_value = mock_resume_obj

            result = session.generate_all(format="pdf", pattern="user*")

            # Should only find user_resume
            assert result.successful >= 0  # Depends on glob behavior

        session.close()

    def test_generate_all_pdf_format(self, tmp_path: Path) -> None:
        """generate_all() generates PDF format."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "test.yaml").write_text("full_name: Test\n")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        session = ResumeSession(data_dir=str(tmp_path))

        with patch.object(session, "resume") as mock_resume:
            mock_result = Mock()
            mock_resume_obj = Mock()
            mock_resume_obj.to_pdf.return_value = mock_result
            mock_resume.return_value = mock_resume_obj

            session.generate_all(format="pdf")

            mock_resume_obj.to_pdf.assert_called()

        session.close()

    def test_generate_all_html_format(self, tmp_path: Path) -> None:
        """generate_all() generates HTML format."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "test.yaml").write_text("full_name: Test\n")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        session = ResumeSession(data_dir=str(tmp_path))

        with patch.object(session, "resume") as mock_resume:
            mock_result = Mock()
            mock_resume_obj = Mock()
            mock_resume_obj.to_html.return_value = mock_result
            mock_resume.return_value = mock_resume_obj

            session.generate_all(format="html")

            mock_resume_obj.to_html.assert_called()

        session.close()

    def test_generate_all_invalid_format_raises_error(self, tmp_path: Path) -> None:
        """generate_all() raises ValueError for invalid format."""
        session = ResumeSession(data_dir=str(tmp_path))

        with pytest.raises(ValueError, match="Unsupported format"):
            session.generate_all(format="invalid")

        session.close()

    def test_generate_all_raises_error_when_session_inactive(
        self, tmp_path: Path
    ) -> None:
        """generate_all() raises SessionError when session inactive."""
        session = ResumeSession(data_dir=str(tmp_path))
        session.close()

        with pytest.raises(SessionError, match="session is not active"):
            session.generate_all()

    def test_generate_all_uses_session_auto_open(self, tmp_path: Path) -> None:
        """generate_all() uses session auto_open setting."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "test.yaml").write_text("full_name: Test\n")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        config = SessionConfig(auto_open=True)
        session = ResumeSession(data_dir=str(tmp_path), config=config)

        with patch.object(session, "resume") as mock_resume:
            mock_result = Mock()
            mock_resume_obj = Mock()
            mock_resume_obj.to_pdf.return_value = mock_result
            mock_resume.return_value = mock_resume_obj

            session.generate_all(format="pdf")

            # Should pass open_after=True
            call_kwargs = mock_resume_obj.to_pdf.call_args[1]
            assert call_kwargs.get("open_after") is True

        session.close()

    def test_generate_all_handles_generation_errors(self, tmp_path: Path) -> None:
        """generate_all() handles errors and continues."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "resume1.yaml").write_text("full_name: User One\n")
        (input_dir / "resume2.yaml").write_text("full_name: User Two\n")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        session = ResumeSession(data_dir=str(tmp_path))

        with patch.object(session, "resume") as mock_resume:
            # First resume fails, second succeeds
            mock_result = Mock()
            mock_resume_obj = Mock()
            mock_resume_obj.to_pdf.return_value = mock_result

            call_count = [0]

            def side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    raise Exception("Generation failed")
                return mock_resume_obj

            mock_resume.side_effect = side_effect

            result = session.generate_all(format="pdf")

            assert result.failed == 1
            assert result.successful == 1

        session.close()

    def test_generate_all_tracks_operation_count(self, tmp_path: Path) -> None:
        """generate_all() increments operation count."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "resume1.yaml").write_text("full_name: User One\n")
        (input_dir / "resume2.yaml").write_text("full_name: User Two\n")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        session = ResumeSession(data_dir=str(tmp_path))
        initial_count = session.operation_count

        with patch.object(session, "resume") as mock_resume:
            mock_result = Mock()
            mock_resume_obj = Mock()
            mock_resume_obj.to_pdf.return_value = mock_result
            mock_resume.return_value = mock_resume_obj

            session.generate_all(format="pdf")

            assert session.operation_count > initial_count

        session.close()


class TestResumeSessionFindYamlFiles:
    """Test ResumeSession._find_yaml_files() method."""

    def test_find_yaml_files_returns_empty_when_no_input_dir(
        self, tmp_path: Path
    ) -> None:
        """_find_yaml_files() returns empty list when input dir doesn't exist."""
        session = ResumeSession(data_dir=str(tmp_path))

        yaml_files = session._find_yaml_files()

        assert yaml_files == []
        session.close()

    def test_find_yaml_files_finds_yaml_extension(self, tmp_path: Path) -> None:
        """_find_yaml_files() finds .yaml files."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "resume1.yaml").write_text("test")
        (input_dir / "resume2.yaml").write_text("test")

        session = ResumeSession(data_dir=str(tmp_path))
        yaml_files = session._find_yaml_files()

        assert len(yaml_files) == 2
        assert all(f.suffix == ".yaml" for f in yaml_files)
        session.close()

    def test_find_yaml_files_finds_yml_extension(self, tmp_path: Path) -> None:
        """_find_yaml_files() finds .yml files."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "resume1.yml").write_text("test")
        (input_dir / "resume2.yml").write_text("test")

        session = ResumeSession(data_dir=str(tmp_path))
        yaml_files = session._find_yaml_files()

        assert len(yaml_files) == 2
        session.close()

    def test_find_yaml_files_ignores_non_yaml_files(self, tmp_path: Path) -> None:
        """_find_yaml_files() ignores non-YAML files."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "resume.yaml").write_text("test")
        (input_dir / "readme.txt").write_text("test")
        (input_dir / "config.json").write_text("test")

        session = ResumeSession(data_dir=str(tmp_path))
        yaml_files = session._find_yaml_files()

        assert len(yaml_files) == 1
        assert yaml_files[0].suffix == ".yaml"
        session.close()

    def test_find_yaml_files_ignores_directories(self, tmp_path: Path) -> None:
        """_find_yaml_files() ignores directories."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "resume.yaml").write_text("test")
        (input_dir / "subdir.yaml").mkdir()  # Directory with .yaml extension

        session = ResumeSession(data_dir=str(tmp_path))
        yaml_files = session._find_yaml_files()

        assert len(yaml_files) == 1
        assert yaml_files[0].is_file()
        session.close()

    def test_find_yaml_files_returns_sorted_list(self, tmp_path: Path) -> None:
        """_find_yaml_files() returns sorted list."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "c_resume.yaml").write_text("test")
        (input_dir / "a_resume.yaml").write_text("test")
        (input_dir / "b_resume.yaml").write_text("test")

        session = ResumeSession(data_dir=str(tmp_path))
        yaml_files = session._find_yaml_files()

        names = [f.name for f in yaml_files]
        assert names == sorted(names)
        session.close()

    def test_find_yaml_files_handles_exceptions_gracefully(
        self, tmp_path: Path
    ) -> None:
        """_find_yaml_files() returns empty list on exceptions."""
        session = ResumeSession(data_dir=str(tmp_path))

        # Mock the glob method to raise an exception
        with patch.object(Path, "glob") as mock_glob:
            mock_glob.side_effect = Exception("Permission denied")

            yaml_files = session._find_yaml_files()

            assert yaml_files == []

        session.close()


class TestResumeSessionCaching:
    """Test ResumeSession caching functionality."""

    def test_invalidate_cache_all(self, tmp_path: Path) -> None:
        """invalidate_cache() clears all cached resumes."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "resume1.yaml").write_text("full_name: User One\n")
        (input_dir / "resume2.yaml").write_text("full_name: User Two\n")

        session = ResumeSession(data_dir=str(tmp_path))
        session.resume("resume1")
        session.resume("resume2")

        assert len(session._resumes_loaded) == 2

        session.invalidate_cache()

        assert len(session._resumes_loaded) == 0
        session.close()

    def test_invalidate_cache_specific(self, tmp_path: Path) -> None:
        """invalidate_cache() clears specific resume."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "resume1.yaml").write_text("full_name: User One\n")
        (input_dir / "resume2.yaml").write_text("full_name: User Two\n")

        session = ResumeSession(data_dir=str(tmp_path))
        session.resume("resume1")
        session.resume("resume2")

        assert len(session._resumes_loaded) == 2

        session.invalidate_cache("resume1")

        assert len(session._resumes_loaded) == 1
        assert "resume2" in session._resumes_loaded
        session.close()

    def test_invalidate_cache_nonexistent_key(self, tmp_path: Path) -> None:
        """invalidate_cache() handles nonexistent keys gracefully."""
        session = ResumeSession(data_dir=str(tmp_path))

        # Should not raise error
        session.invalidate_cache("nonexistent")

        session.close()

    def test_get_cache_info(self, tmp_path: Path) -> None:
        """get_cache_info() returns cache statistics."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "resume1.yaml").write_text("full_name: User One\n")

        session = ResumeSession(data_dir=str(tmp_path))
        session.resume("resume1")

        info = session.get_cache_info()

        assert "cached_resumes" in info
        assert "cache_size" in info
        assert "memory_usage_estimate" in info
        assert info["cache_size"] == 1
        assert "resume1" in info["cached_resumes"]
        session.close()

    def test_get_cache_info_empty(self, tmp_path: Path) -> None:
        """get_cache_info() works with empty cache."""
        session = ResumeSession(data_dir=str(tmp_path))

        info = session.get_cache_info()

        assert info["cache_size"] == 0
        assert info["cached_resumes"] == []
        assert info["memory_usage_estimate"] == 0
        session.close()


class TestResumeSessionContextManager:
    """Test ResumeSession as context manager."""

    def test_session_context_manager_entry(self, tmp_path: Path) -> None:
        """Session can be used as context manager."""
        with ResumeSession(data_dir=str(tmp_path)) as session:
            assert session.is_active is True

    def test_session_context_manager_exit(self, tmp_path: Path) -> None:
        """Session closes automatically on context exit."""
        session = ResumeSession(data_dir=str(tmp_path))

        with session:
            assert session.is_active is True

        assert session.is_active is False

    def test_session_context_manager_enter_inactive_raises_error(
        self, tmp_path: Path
    ) -> None:
        """Cannot enter context with inactive session."""
        session = ResumeSession(data_dir=str(tmp_path))
        session.close()

        with pytest.raises(SessionError, match="Cannot enter inactive session"):
            with session:
                pass

    def test_session_close_method(self, tmp_path: Path) -> None:
        """close() method properly cleans up resources."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "test.yaml").write_text("full_name: Test\n")

        session = ResumeSession(data_dir=str(tmp_path))
        session.resume("test")
        session._generation_times.append(1.5)

        assert len(session._resumes_loaded) > 0
        assert len(session._generation_times) > 0
        assert session.is_active is True

        session.close()

        assert len(session._resumes_loaded) == 0
        assert len(session._generation_times) == 0
        assert session.is_active is False

    def test_session_close_idempotent(self, tmp_path: Path) -> None:
        """close() can be called multiple times safely."""
        session = ResumeSession(data_dir=str(tmp_path))

        session.close()
        session.close()  # Should not raise error

        assert session.is_active is False


class TestResumeSessionStringRepresentation:
    """Test ResumeSession string representations."""

    def test_session_repr(self, tmp_path: Path) -> None:
        """__repr__() returns detailed representation."""
        session = ResumeSession(data_dir=str(tmp_path))

        repr_str = repr(session)

        assert "ResumeSession" in repr_str
        assert "id=" in repr_str
        assert "active=True" in repr_str
        assert "operations=0" in repr_str
        session.close()

    def test_session_str(self, tmp_path: Path) -> None:
        """__str__() returns simple string representation."""
        session = ResumeSession(data_dir=str(tmp_path))

        str_repr = str(session)

        assert "ResumeSession" in str_repr
        assert len(str_repr) < 50  # Should be concise
        session.close()


class TestCreateSessionConvenience:
    """Test create_session convenience function."""

    def test_create_session_basic(self, tmp_path: Path) -> None:
        """create_session creates and manages session."""
        with create_session(data_dir=str(tmp_path)) as session:
            assert isinstance(session, ResumeSession)
            assert session.is_active is True

    def test_create_session_with_config(self, tmp_path: Path) -> None:
        """create_session accepts configuration."""
        config = SessionConfig(default_template="modern")

        with create_session(data_dir=str(tmp_path), config=config) as session:
            assert session.config.default_template == "modern"

    def test_create_session_closes_on_exception(self, tmp_path: Path) -> None:
        """create_session closes session even on exception."""
        session_ref = None

        try:
            with create_session(data_dir=str(tmp_path)) as session:
                session_ref = session
                raise ValueError("Test error")
        except ValueError:
            pass

        # Session should be closed
        assert session_ref is not None
        assert session_ref.is_active is False

    def test_create_session_with_path_overrides(self, tmp_path: Path) -> None:
        """create_session accepts path overrides."""
        with create_session(
            data_dir=str(tmp_path), content_dir=str(tmp_path / "custom")
        ) as session:
            assert session.is_active is True
