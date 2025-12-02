"""Tests for shell/cli/main.py utility functions."""

from __future__ import annotations

from unittest import mock

from simple_resume.shell.cli.main import _handle_unexpected_error


class TestHandleUnexpectedError:
    """Tests for _handle_unexpected_error function."""

    @mock.patch("builtins.print")
    @mock.patch("logging.getLogger")
    def test_permission_error(self, mock_logger, mock_print) -> None:
        """Test handling of PermissionError."""
        exc = PermissionError("Permission denied")
        result = _handle_unexpected_error(exc, "test context")

        assert result == 2
        mock_logger.return_value.error.assert_called_once()
        assert mock_print.call_count >= 1

    @mock.patch("builtins.print")
    @mock.patch("logging.getLogger")
    def test_os_error(self, mock_logger, mock_print) -> None:
        """Test handling of OSError."""
        exc = OSError("File not found")
        result = _handle_unexpected_error(exc, "generation")

        assert result == 2
        assert any(
            "File System Error" in str(call) for call in mock_print.call_args_list
        )

    @mock.patch("builtins.print")
    @mock.patch("logging.getLogger")
    def test_key_error(self, mock_logger, mock_print) -> None:
        """Test handling of KeyError."""
        exc = KeyError("missing_key")
        result = _handle_unexpected_error(exc, "validation")

        assert result == 3
        assert any("Internal Error" in str(call) for call in mock_print.call_args_list)

    @mock.patch("builtins.print")
    @mock.patch("logging.getLogger")
    def test_attribute_error(self, mock_logger, mock_print) -> None:
        """Test handling of AttributeError."""
        exc = AttributeError("'obj' has no attribute 'foo'")
        result = _handle_unexpected_error(exc, "processing")

        assert result == 3

    @mock.patch("builtins.print")
    @mock.patch("logging.getLogger")
    def test_type_error(self, mock_logger, mock_print) -> None:
        """Test handling of TypeError."""
        exc = TypeError("Expected int, got str")
        result = _handle_unexpected_error(exc, "conversion")

        assert result == 3

    @mock.patch("builtins.print")
    @mock.patch("logging.getLogger")
    def test_memory_error(self, mock_logger, mock_print) -> None:
        """Test handling of MemoryError."""
        exc = MemoryError("Out of memory")
        result = _handle_unexpected_error(exc, "processing")

        assert result == 4
        assert any("Resource Error" in str(call) for call in mock_print.call_args_list)

    @mock.patch("builtins.print")
    @mock.patch("logging.getLogger")
    def test_value_error(self, mock_logger, mock_print) -> None:
        """Test handling of ValueError."""
        exc = ValueError("Invalid value")
        result = _handle_unexpected_error(exc, "input")

        assert result == 5
        assert any("Input Error" in str(call) for call in mock_print.call_args_list)

    @mock.patch("builtins.print")
    @mock.patch("logging.getLogger")
    def test_index_error(self, mock_logger, mock_print) -> None:
        """Test handling of IndexError."""
        exc = IndexError("list index out of range")
        result = _handle_unexpected_error(exc, "parsing")

        assert result == 5

    @mock.patch("builtins.print")
    @mock.patch("logging.getLogger")
    def test_generic_exception(self, mock_logger, mock_print) -> None:
        """Test handling of generic exception."""
        exc = RuntimeError("Something went wrong")
        result = _handle_unexpected_error(exc, "operation")

        assert result == 1
        assert any(
            "Unexpected Error" in str(call) for call in mock_print.call_args_list
        )

    @mock.patch("builtins.print")
    @mock.patch("logging.getLogger")
    def test_logging_called_with_exc_info(self, mock_logger, mock_print) -> None:
        """Test that logger.error is called with exc_info=True."""
        exc = ValueError("Test error")
        _handle_unexpected_error(exc, "test")

        logger_instance = mock_logger.return_value
        logger_instance.error.assert_called_once()
        call_kwargs = logger_instance.error.call_args[1]
        assert call_kwargs["exc_info"] is True
        assert "error_type" in call_kwargs["extra"]
        assert "context" in call_kwargs["extra"]
