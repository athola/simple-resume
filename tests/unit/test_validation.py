from __future__ import annotations

import os
from pathlib import Path

import pytest

from simple_resume.core import validation
from simple_resume.core.constants import OutputFormat
from simple_resume.core.exceptions import (
    ConfigurationError,
    FileSystemError,
    ValidationError,
)
from simple_resume.core.validation import (
    validate_directory_path,
    validate_file_path,
    validate_format,
    validate_output_path,
    validate_resume_data,
    validate_template_name,
    validate_yaml_file,
)
from tests.bdd import Scenario


def test_validate_format_accepts_supported(story: Scenario) -> None:
    story.given("a supported format string with extra whitespace")
    normalized = validate_format("  PDF ")

    story.then("the value is normalized to the OutputFormat enum")
    assert normalized is OutputFormat.PDF


def test_validate_format_rejects_unknown(story: Scenario) -> None:
    story.given("an unsupported format string")
    with pytest.raises(ValidationError, match="Unsupported"):
        validate_format("docx")


def test_validate_format_empty_input(story: Scenario) -> None:
    story.given("an empty format string")
    with pytest.raises(ValidationError, match="cannot be empty"):
        validate_format("")


def test_validate_file_path_with_existing_file(story: Scenario, tmp_path: Path) -> None:
    story.given("a file that exists on disk")
    file_path = tmp_path / "resume.txt"
    file_path.write_text("example")

    validated = validate_file_path(file_path, must_exist=True)

    story.then("the validated path matches the real file")
    assert validated == file_path.resolve()


def test_validate_file_path_rejects_missing_file(
    story: Scenario,
    tmp_path: Path,
) -> None:
    story.given("a path to a non-existent file")
    missing = tmp_path / "missing.yaml"

    with pytest.raises(FileSystemError, match="not found"):
        validate_file_path(missing)


def test_validate_file_path_empty_string(story: Scenario) -> None:
    story.given("an empty string path")
    with pytest.raises(FileSystemError, match="cannot be empty"):
        validate_file_path("")


def test_validate_file_path_resolves_relative_path(
    story: Scenario,
    tmp_path: Path,
) -> None:
    story.given("a relative path provided as a string")
    cwd = tmp_path / "work"
    cwd.mkdir()
    file_path = cwd / "resume.txt"
    file_path.write_text("content")

    old_cwd = os.getcwd()
    os.chdir(cwd)
    try:
        validated = validate_file_path("resume.txt")
    finally:
        os.chdir(old_cwd)

    story.then("the path is resolved to an absolute location")
    assert validated == file_path.resolve()


def test_validate_file_path_enforces_extension(story: Scenario, tmp_path: Path) -> None:
    story.given("a temporary file that does not use YAML extension")
    file_path = tmp_path / "data.txt"
    file_path.write_text("content")

    with pytest.raises(FileSystemError, match="Invalid file extension"):
        validate_file_path(file_path, allowed_extensions=(".yaml", ".yml"))


def test_validate_file_path_rejects_large_files(
    story: Scenario,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    story.given("a file that exceeds the configured size limit")
    file_path = tmp_path / "large.dat"
    file_path.write_bytes(b"x" * 2048)  # 2KB

    monkeypatch.setattr(validation, "MAX_FILE_SIZE_MB", 0.001)

    with pytest.raises(FileSystemError, match="File too large"):
        validate_file_path(file_path)


def test_validate_directory_path_rejects_file(story: Scenario, tmp_path: Path) -> None:
    story.given("a path that points to an existing file")
    file_path = tmp_path / "file.txt"
    file_path.write_text("content")

    with pytest.raises(FileSystemError, match="not a directory"):
        validate_directory_path(file_path)


def test_validate_directory_path_requires_existing_when_flagged(
    story: Scenario, tmp_path: Path
) -> None:
    story.given("a missing directory with must_exist enabled")
    missing_dir = tmp_path / "missing"

    with pytest.raises(FileSystemError, match="not found|does not exist"):
        validate_directory_path(missing_dir, must_exist=True)


def test_validate_template_name_accepts_simple_patterns(story: Scenario) -> None:
    story.given("a template name containing hyphens and underscores")
    name = validate_template_name(" business-template_2025 ")

    story.then("the cleaned template name is returned")
    assert name == "business-template_2025"


def test_validate_template_name_rejects_illegal_characters(story: Scenario) -> None:
    story.given("a template name with disallowed punctuation")
    with pytest.raises(ConfigurationError, match="Invalid template name"):
        validate_template_name("bad/template")


def test_validate_template_name_empty(story: Scenario) -> None:
    story.given("an empty template name")
    with pytest.raises(ConfigurationError, match="cannot be empty"):
        validate_template_name("")


def test_validate_yaml_file_requires_yaml_extension(
    story: Scenario,
    tmp_path: Path,
) -> None:
    story.given("a YAML file stored under the data directory")
    yaml_path = tmp_path / "resume.yaml"
    yaml_path.write_text("full_name: Example")

    validated = validate_yaml_file(yaml_path)

    story.then("the YAML path is accepted")
    assert validated == yaml_path.resolve()


def test_validate_yaml_file_rejects_wrong_extension(
    story: Scenario,
    tmp_path: Path,
) -> None:
    story.given("a JSON file where YAML is expected")
    json_path = tmp_path / "resume.json"
    json_path.write_text("{}")

    with pytest.raises(FileSystemError, match="Invalid file extension"):
        validate_yaml_file(json_path)


def test_validate_resume_data_checks_full_name(story: Scenario) -> None:
    story.given("resume data without a full name")
    with pytest.raises(ValidationError, match="must include 'full_name'"):
        validate_resume_data({"config": {}})


def test_validate_resume_data_requires_dictionary(story: Scenario) -> None:
    story.given("resume data that is not a dictionary")
    with pytest.raises(ValidationError, match="must be a dictionary"):
        validate_resume_data(["not-a-dict"])  # type: ignore[arg-type]


def test_validate_resume_data_empty_dictionary(story: Scenario) -> None:
    story.given("resume data that is an empty dictionary")
    with pytest.raises(ValidationError, match="cannot be empty"):
        validate_resume_data({})


def test_validate_resume_data_requires_non_empty_full_name(story: Scenario) -> None:
    story.given("resume data with an empty full_name string")
    with pytest.raises(ValidationError, match="cannot be empty"):
        validate_resume_data({"full_name": ""})


def test_validate_resume_data_config_must_be_dict(story: Scenario) -> None:
    story.given("resume data whose config entry is not a dictionary")
    with pytest.raises(ValidationError, match="must be a dictionary"):
        validate_resume_data(
            {
                "full_name": "User",
                "email": "user@example.com",
                "config": "not-a-dict",
            }
        )


def test_validate_resume_data_requires_email(story: Scenario) -> None:
    story.given("resume data missing an email")
    with pytest.raises(ValidationError, match="include 'email'"):
        validate_resume_data({"full_name": "User"})


def test_validate_resume_data_rejects_invalid_email(story: Scenario) -> None:
    story.given("resume data with an invalid email format")
    with pytest.raises(ValidationError, match="Invalid email format"):
        validate_resume_data({"full_name": "User", "email": "not-an-email"})


def test_validate_resume_data_rejects_invalid_dates(story: Scenario) -> None:
    story.given("experience data with a non-ISO date string")
    data = {
        "full_name": "User",
        "email": "user@example.com",
        "body": {"experience": [{"start_date": "Jan 2020", "end_date": "2021-05"}]},
    }

    with pytest.raises(ValidationError, match="Invalid date format"):
        validate_resume_data(data)


def test_validate_resume_data_accepts_valid_dates(story: Scenario) -> None:
    story.given("experience data with ISO-formatted dates")
    data = {
        "full_name": "User",
        "email": "user@example.com",
        "body": {
            "experience": [
                {"start_date": "2020-01", "end_date": "2021-05"},
                {"date": "2022"},
            ]
        },
    }

    validate_resume_data(data)

    story.then("validation completes without raising")


def test_validate_output_path_accepts_matching_extension(
    story: Scenario,
    tmp_path: Path,
) -> None:
    story.given("an output path with the correct extension")
    output_path = tmp_path / "result.pdf"

    validated = validate_output_path(output_path, "pdf")

    story.then("the path is returned without modification")
    assert validated == output_path


def test_validate_output_path_rejects_mismatch(story: Scenario, tmp_path: Path) -> None:
    story.given("an output path whose suffix does not match the requested format")
    output_path = tmp_path / "result.html"

    with pytest.raises(FileSystemError, match="doesn't match format"):
        validate_output_path(output_path, "pdf")


def test_validate_file_path_rejects_directory(story: Scenario, tmp_path: Path) -> None:
    """Test validate_file_path rejects directory when must_be_file=True."""
    story.given("a directory path when must_be_file=True")
    dir_path = tmp_path / "testdir"
    dir_path.mkdir()

    with pytest.raises(FileSystemError, match="not a file"):
        validate_file_path(dir_path, must_exist=True, must_be_file=True)


def test_validate_directory_path_rejects_empty_string(story: Scenario) -> None:
    """Test validate_directory_path rejects empty string."""
    story.given("an empty directory path")

    with pytest.raises(FileSystemError, match="cannot be empty"):
        validate_directory_path("")


def test_validate_directory_path_resolves_relative_path(
    story: Scenario, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test validate_directory_path resolves relative paths."""
    story.given("a relative directory path")
    dir_path = tmp_path / "testdir"
    dir_path.mkdir()

    # Change to parent directory to test relative path
    monkeypatch.chdir(tmp_path)
    relative_path = Path("testdir")

    result = validate_directory_path(relative_path, must_exist=True)

    story.then("path is resolved to absolute path")
    assert result.is_absolute()
    assert result.exists()


def test_validate_directory_path_with_create_if_missing_raises(
    story: Scenario, tmp_path: Path
) -> None:
    """Test validate_directory_path raises error for create_if_missing."""
    story.given("a non-existent directory with create_if_missing=True")
    dir_path = tmp_path / "nonexistent"

    with pytest.raises(FileSystemError, match="create_if_missing is not supported"):
        validate_directory_path(dir_path, create_if_missing=True)


def test_validate_date_field_accepts_none(story: Scenario) -> None:
    """Test date validation accepts None value."""
    story.given("experience data with None date values")
    data = {
        "full_name": "User",
        "email": "user@example.com",
        "body": {
            "experience": [
                {"start_date": None, "end_date": "2021-05"},
                {"date": ""},  # Empty string should also be accepted
            ]
        },
    }

    # Should not raise
    validate_resume_data(data)

    story.then("validation completes without error")
