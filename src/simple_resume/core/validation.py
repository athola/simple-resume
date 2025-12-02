"""Provide validation functions for resume inputs and files."""

import re
from pathlib import Path
from typing import Any

from simple_resume.core.constants import (
    MAX_FILE_SIZE_MB,
    SUPPORTED_FORMATS,
    OutputFormat,
)
from simple_resume.core.constants.files import SUPPORTED_YAML_EXTENSIONS
from simple_resume.core.exceptions import (
    ConfigurationError,
    FileSystemError,
    ValidationError,
)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DATE_REGEX = re.compile(r"^\d{4}(-\d{2})?$")


def validate_format(
    format_str: str | OutputFormat, param_name: str = "format"
) -> OutputFormat:
    """Validate and normalize a format string.

    Args:
        format_str: The format string or enum to validate.
        param_name: The parameter name for error messages.

    Returns:
        An `OutputFormat` enum value.

    Raises:
        ValidationError: If the format is not supported.

    """
    if not format_str:
        raise ValidationError(f"{param_name} cannot be empty")

    normalized = (
        format_str.value
        if isinstance(format_str, OutputFormat)
        else format_str.lower().strip()
    )

    if not OutputFormat.is_valid(normalized):
        raise ValidationError(
            f"Unsupported {param_name}: '{format_str}'. "
            f"Supported formats: {', '.join(SUPPORTED_FORMATS)}"
        )

    return OutputFormat(normalized)


def validate_file_path(
    file_path: str | Path,
    *,
    must_exist: bool = True,
    must_be_file: bool = True,
    allowed_extensions: tuple[str, ...] | None = None,
) -> Path:
    """Validate a file path.

    Args:
        file_path: The path to validate.
        must_exist: If `True`, the path must exist.
        must_be_file: If `True`, the path must be a file.
        allowed_extensions: If provided, the file must have one of these extensions.

    Returns:
        A validated `Path` object.

    Raises:
        FileSystemError: If path validation fails.

    """
    if not file_path:
        raise FileSystemError("File path cannot be empty")

    path = Path(file_path) if isinstance(file_path, str) else file_path

    # Resolve to absolute path if not already absolute.
    if not path.is_absolute():
        path = path.resolve()

    if must_exist and not path.exists():
        raise FileSystemError(f"Path does not exist: {path}")

    if must_be_file and must_exist and not path.is_file():
        raise FileSystemError(f"Path is not a file: {path}")

    if allowed_extensions and path.suffix.lower() not in allowed_extensions:
        raise FileSystemError(
            f"Invalid file extension '{path.suffix}'. "
            f"Allowed: {', '.join(allowed_extensions)}"
        )

    # Check file size if file exists.
    if must_exist and path.is_file():
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise FileSystemError(
                f"File too large: {size_mb:.1f}MB (max: {MAX_FILE_SIZE_MB}MB)"
            )

    return path


def validate_directory_path(
    dir_path: str | Path, *, must_exist: bool = False, create_if_missing: bool = False
) -> Path:
    """Validate a directory path.

    Args:
        dir_path: The directory path to validate.
        must_exist: If `True`, the directory must exist.
        create_if_missing: If `True`, create the directory if it doesn't exist.

    Returns:
        A validated `Path` object.

    Raises:
        FileSystemError: If path validation fails.

    """
    if not dir_path:
        raise FileSystemError("Directory path cannot be empty")

    path = Path(dir_path) if isinstance(dir_path, str) else dir_path

    if not path.is_absolute():
        path = path.resolve()

    if must_exist and not path.exists():
        raise FileSystemError(f"Directory does not exist: {path}")

    if path.exists() and not path.is_dir():
        raise FileSystemError(f"Path is not a directory: {path}")

    if create_if_missing and not path.exists():
        # NOTE: Directory creation has been moved to shell layer.
        # Core validation should not perform I/O operations.
        # Callers should create directories in the shell layer if needed.
        raise FileSystemError(
            f"Directory does not exist and create_if_missing is not supported "
            f"in core validation: {path}. Create the directory in the shell layer."
        )

    return path


def validate_template_name(template: str) -> str:
    """Validate a template name.

    Args:
        template: The template name to validate.

    Returns:
        The validated template name.

    Raises:
        ConfigurationError: If the template name is invalid.

    """
    if not template:
        raise ConfigurationError("Template name cannot be empty")

    template = template.strip()

    # Allow custom templates; ensure reasonable string format.
    if not template.replace("_", "").replace("-", "").isalnum():
        message = (
            f"Invalid template name: '{template}'. "
            "Template names should contain only alphanumeric characters, "
            "hyphens, and underscores."
        )
        raise ConfigurationError(message)

    return template


def validate_yaml_file(file_path: str | Path) -> Path:
    """Validate a YAML resume file.

    Args:
        file_path: The path to the YAML file.

    Returns:
        A validated `Path` object.

    Raises:
        FileSystemError: If file validation fails.

    """
    return validate_file_path(
        file_path,
        must_exist=True,
        must_be_file=True,
        allowed_extensions=tuple(SUPPORTED_YAML_EXTENSIONS),
    )


def validate_resume_data(data: dict[str, Any]) -> None:
    """Validate the basic structure of the resume data.

    Args:
        data: A resume data dictionary.

    Raises:
        ValidationError: If the data structure is invalid.

    """
    if not isinstance(data, dict):
        raise ValidationError("Resume data must be a dictionary")

    if not data:
        raise ValidationError("Resume data cannot be empty")

    # Check required fields.
    if "full_name" not in data:
        raise ValidationError("Resume data must include 'full_name'")

    if not data.get("full_name"):
        raise ValidationError("'full_name' cannot be empty")

    _validate_required_email(data)

    # Check config if present.
    if "config" in data:
        if not isinstance(data["config"], dict):
            raise ValidationError("'config' must be a dictionary")

    _validate_date_fields(data)


def validate_output_path(output_path: str | Path, format_type: str) -> Path:
    """Validate the output file path for a generated resume.

    Args:
        output_path: The output file path.
        format_type: The output format (e.g., "pdf", "html").

    Returns:
        A validated `Path` object.

    Raises:
        FileSystemError: If path validation fails.

    """
    path = Path(output_path) if isinstance(output_path, str) else output_path

    # Validate parent directory.
    if path.parent and path.parent != Path("."):
        validate_directory_path(path.parent, must_exist=False, create_if_missing=False)

    # Check file extension matches format.
    expected_ext = f".{format_type.lower()}"
    if path.suffix.lower() != expected_ext:
        message = (
            f"Output path extension '{path.suffix}' doesn't match format "
            f"'{format_type}'. Expected: {expected_ext}"
        )
        raise FileSystemError(message)

    return path


def _validate_required_email(data: dict[str, Any]) -> None:
    """Validate the required email field."""
    email = data.get("email")
    if email is None:
        raise ValidationError("Resume data must include 'email'")

    if not isinstance(email, str) or not EMAIL_REGEX.match(email.strip()):
        raise ValidationError(
            "Invalid email format. Expected something like user@example.com"
        )


def _is_date_key(key: str) -> bool:
    """Check if a key is a date field."""
    key_lower = key.lower()
    return key_lower == "date" or key_lower.endswith("_date")


def _validate_date_value(field: str, value: Any) -> None:
    """Validate a date field's value.

    Args:
        field: The name of the field being validated.
        value: The value of the date field.

    Raises:
        ValidationError: If the date format is invalid.

    """
    if value is None or value == "":
        return
    if not isinstance(value, str) or not DATE_REGEX.match(value.strip()):
        raise ValidationError(
            f"Invalid date format for '{field}'. Use 'YYYY' or 'YYYY-MM'."
        )


def _validate_date_fields(node: Any) -> None:
    """Recursively validate date fields within a dictionary or list.

    Args:
        node: The dictionary or list node to traverse and validate.

    """
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(key, str) and _is_date_key(key):
                _validate_date_value(key, value)
            _validate_date_fields(value)
    elif isinstance(node, list):
        for item in node:
            _validate_date_fields(item)
