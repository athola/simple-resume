"""Test cases for result objects functionality."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from simple_resume.exceptions import FileSystemError
from simple_resume.result import (
    BatchGenerationResult,
    GenerationMetadata,
    GenerationResult,
)
from tests.bdd import Scenario


class TestGenerationMetadata:
    """Test GenerationMetadata dataclass."""

    def test_metadata_creation(self, story: Scenario) -> None:
        story.given("all metadata fields are supplied")
        metadata = GenerationMetadata(
            format_type="pdf",
            template_name="modern",
            generation_time=1.5,
            file_size=1024,
            resume_name="test_resume",
            palette_info={"name": "ocean"},
            page_count=2,
        )

        story.then("each attribute is stored as provided")
        assert metadata.format_type == "pdf"
        assert metadata.template_name == "modern"
        assert metadata.generation_time == 1.5
        assert metadata.file_size == 1024
        assert metadata.resume_name == "test_resume"
        assert metadata.palette_info == {"name": "ocean"}
        assert metadata.page_count == 2

    def test_metadata_with_defaults(self, story: Scenario) -> None:
        story.given("optional metadata fields are omitted")
        metadata = GenerationMetadata(
            format_type="html",
            template_name="basic",
            generation_time=0.5,
            file_size=512,
            resume_name="resume",
        )

        story.then("optional attributes default to None")
        assert metadata.palette_info is None
        assert metadata.page_count is None


class TestGenerationResultInit:
    """Test GenerationResult initialization."""

    def test_result_creation_with_metadata(
        self,
        story: Scenario,
        tmp_path: Path,
    ) -> None:
        output_file = tmp_path / "test.pdf"
        output_file.write_text("test content")

        metadata = GenerationMetadata(
            format_type="pdf",
            template_name="modern",
            generation_time=1.0,
            file_size=1024,
            resume_name="test",
        )

        result = GenerationResult(output_file, "pdf", metadata)

        story.then("output path, format type, and metadata are set")
        assert result.output_path == output_file
        assert result.format_type == "pdf"
        assert result.metadata == metadata

    def test_result_creation_without_metadata(
        self,
        story: Scenario,
        tmp_path: Path,
    ) -> None:
        output_file = tmp_path / "test.html"
        result = GenerationResult(output_file, "html")

        story.then("default metadata is synthesized when none is provided")
        assert result.output_path == output_file
        assert result.format_type == "html"
        assert result.metadata.format_type == "html"
        assert result.metadata.template_name == "unknown"
        assert result.metadata.resume_name == "unknown"

    def test_result_normalizes_format_type(
        self,
        story: Scenario,
        tmp_path: Path,
    ) -> None:
        output_file = tmp_path / "test.PDF"
        result = GenerationResult(output_file, "PDF")

        story.then("format type is normalized to lowercase")
        assert result.format_type == "pdf"


class TestGenerationResultProperties:
    """Test GenerationResult properties."""

    def test_size_property(self, story: Scenario, tmp_path: Path) -> None:
        output_file = tmp_path / "test.pdf"
        content = "x" * 1000
        output_file.write_text(content)

        result = GenerationResult(output_file, "pdf")

        story.then("size reports the file size in bytes")
        assert result.size == len(content.encode())

    def test_size_property_for_nonexistent_file(
        self,
        story: Scenario,
        tmp_path: Path,
    ) -> None:
        output_file = tmp_path / "nonexistent.pdf"
        result = GenerationResult(output_file, "pdf")

        story.then("size is zero when the file is missing")
        assert result.size == 0

    def test_size_human_bytes(self, story: Scenario, tmp_path: Path) -> None:
        output_file = tmp_path / "test.pdf"
        output_file.write_bytes(b"x" * 500)

        result = GenerationResult(output_file, "pdf")

        story.then("size_human chooses byte units for small files")
        assert result.size_human.endswith("B")

    def test_size_human_kilobytes(self, story: Scenario, tmp_path: Path) -> None:
        output_file = tmp_path / "test.pdf"
        output_file.write_bytes(b"x" * (10 * 1024))  # 10 KB

        result = GenerationResult(output_file, "pdf")

        story.then("size_human uses KB for kilobyte-scale files")
        assert result.size_human.endswith("KB")

    def test_size_human_megabytes(self, story: Scenario, tmp_path: Path) -> None:
        output_file = tmp_path / "test.pdf"
        output_file.write_bytes(b"x" * (5 * 1024 * 1024))  # 5 MB

        result = GenerationResult(output_file, "pdf")

        story.then("size_human scales to MB for megabyte files")
        assert result.size_human.endswith("MB")

    def test_size_human_terabytes(self, story: Scenario, tmp_path: Path) -> None:
        output_file = tmp_path / "test.pdf"
        output_file.write_bytes(b"x")  # Create the file
        result = GenerationResult(output_file, "pdf")

        # Mock stat to return a very large file size
        mock_stat = Mock()
        mock_stat.st_size = 5 * 1024**4  # 5 TB
        with patch.object(Path, "stat", return_value=mock_stat):
            size_str = result.size_human
            story.then("size_human labels very large files in TB")
            assert size_str.endswith("TB")

    def test_exists_property_true(self, story: Scenario, tmp_path: Path) -> None:
        output_file = tmp_path / "test.pdf"
        output_file.write_text("test")

        result = GenerationResult(output_file, "pdf")

        story.then("exists returns True when the file is present")
        assert result.exists is True

    def test_exists_property_false(self, story: Scenario, tmp_path: Path) -> None:
        output_file = tmp_path / "nonexistent.pdf"
        result = GenerationResult(output_file, "pdf")

        story.then("exists returns False for missing files")
        assert result.exists is False

    def test_exists_property_false_for_directory(
        self,
        story: Scenario,
        tmp_path: Path,
    ) -> None:
        output_dir = tmp_path / "test_dir"
        output_dir.mkdir()

        result = GenerationResult(output_dir, "pdf")

        story.then("directories are not treated as existing output files")
        assert result.exists is False

    def test_name_property(self, story: Scenario, tmp_path: Path) -> None:
        output_file = tmp_path / "test_resume.pdf"
        result = GenerationResult(output_file, "pdf")

        story.then("name returns the file basename")
        assert result.name == "test_resume.pdf"

    def test_stem_property(self, story: Scenario, tmp_path: Path) -> None:
        output_file = tmp_path / "test_resume.pdf"
        result = GenerationResult(output_file, "pdf")

        story.then("stem strips the extension from the filename")
        assert result.stem == "test_resume"

    def test_suffix_property(self, story: Scenario, tmp_path: Path) -> None:
        output_file = tmp_path / "test_resume.pdf"
        result = GenerationResult(output_file, "pdf")

        story.then("suffix exposes the file extension")
        assert result.suffix == ".pdf"


class TestGenerationResultOpen:
    """Test GenerationResult.open() method."""

    def test_open_raises_error_for_nonexistent_file(
        self, story: Scenario, tmp_path: Path
    ) -> None:
        output_file = tmp_path / "nonexistent.pdf"
        result = GenerationResult(output_file, "pdf")

        story.then("open raises FileSystemError when the file is missing")
        with pytest.raises(FileSystemError, match="doesn't exist"):
            result.open()

    @patch("simple_resume.result.GenerationResult._open_pdf")
    def test_open_calls_open_pdf_for_pdf_format(
        self, mock_open_pdf: Mock, story: Scenario, tmp_path: Path
    ) -> None:
        output_file = tmp_path / "test.pdf"
        output_file.write_text("test")
        mock_open_pdf.return_value = True

        result = GenerationResult(output_file, "pdf")
        story.when("open is called for a PDF")
        result.open()

        story.then("the PDF-specific helper is used")
        mock_open_pdf.assert_called_once()

    @patch("simple_resume.result.GenerationResult._open_html")
    def test_open_calls_open_html_for_html_format(
        self, mock_open_html: Mock, story: Scenario, tmp_path: Path
    ) -> None:
        output_file = tmp_path / "test.html"
        output_file.write_text("test")
        mock_open_html.return_value = True

        result = GenerationResult(output_file, "html")
        story.when("open is called for HTML")
        result.open()

        story.then("the HTML helper handles the request")
        mock_open_html.assert_called_once()

    @patch("simple_resume.result.GenerationResult._open_generic")
    def test_open_calls_open_generic_for_other_formats(
        self, mock_open_generic: Mock, story: Scenario, tmp_path: Path
    ) -> None:
        output_file = tmp_path / "test.txt"
        output_file.write_text("test")
        mock_open_generic.return_value = True

        result = GenerationResult(output_file, "txt")
        story.when("open is called for an unknown format")
        result.open()

        story.then("the generic helper is invoked once")
        mock_open_generic.assert_called_once()

    @patch("simple_resume.result.GenerationResult._open_pdf")
    def test_open_wraps_exceptions(
        self,
        mock_open_pdf: Mock,
        story: Scenario,
        tmp_path: Path,
    ) -> None:
        output_file = tmp_path / "test.pdf"
        output_file.write_text("test")
        mock_open_pdf.side_effect = Exception("Permission denied")

        result = GenerationResult(output_file, "pdf")

        story.then("exceptions from helpers are wrapped as FileSystemError")
        with pytest.raises(FileSystemError, match="Failed to open"):
            result.open()


class TestGenerationResultOpenPlatformSpecific:
    """Test platform-specific open methods."""

    @patch("sys.platform", "darwin")
    @patch("shutil.which")
    @patch("subprocess.Popen")
    def test_open_pdf_macos(
        self, mock_popen: Mock, mock_which: Mock, tmp_path: Path
    ) -> None:
        """_open_pdf() works on macOS."""
        output_file = tmp_path / "test.pdf"
        output_file.write_text("test")
        mock_which.return_value = "/usr/bin/open"

        result = GenerationResult(output_file, "pdf")
        success = result._open_pdf()

        assert success is True
        mock_popen.assert_called_once()

    @patch("sys.platform", "linux")
    @patch("shutil.which")
    @patch("subprocess.Popen")
    def test_open_pdf_linux_with_xdg_open(
        self, mock_popen: Mock, mock_which: Mock, tmp_path: Path
    ) -> None:
        """_open_pdf() works on Linux with xdg-open."""
        output_file = tmp_path / "test.pdf"
        output_file.write_text("test")
        mock_which.return_value = "/usr/bin/xdg-open"

        result = GenerationResult(output_file, "pdf")
        success = result._open_pdf()

        assert success is True
        mock_popen.assert_called_once()

    @patch("sys.platform", "linux")
    @patch("shutil.which")
    @patch("builtins.print")
    def test_open_pdf_linux_without_xdg_open(
        self, mock_print: Mock, mock_which: Mock, tmp_path: Path
    ) -> None:
        """_open_pdf() returns False on Linux without xdg-open."""
        output_file = tmp_path / "test.pdf"
        output_file.write_text("test")
        mock_which.return_value = None

        result = GenerationResult(output_file, "pdf")
        success = result._open_pdf()

        assert success is False
        mock_print.assert_called()  # Should print tip message

    @patch("sys.platform", "darwin")
    @patch("shutil.which")
    @patch("subprocess.Popen")
    def test_open_pdf_handles_exceptions(
        self, mock_popen: Mock, mock_which: Mock, tmp_path: Path
    ) -> None:
        """_open_pdf() returns False on exceptions."""
        output_file = tmp_path / "test.pdf"
        output_file.write_text("test")
        mock_which.return_value = "/usr/bin/open"
        mock_popen.side_effect = Exception("Failed to open")

        result = GenerationResult(output_file, "pdf")
        success = result._open_pdf()

        assert success is False

    @patch("shutil.which")
    @patch("subprocess.Popen")
    def test_open_html_finds_browser(
        self, mock_popen: Mock, mock_which: Mock, tmp_path: Path
    ) -> None:
        """_open_html() opens HTML with available browser."""
        output_file = tmp_path / "test.html"
        output_file.write_text("<html></html>")
        mock_which.side_effect = (
            lambda x: "/usr/bin/firefox" if x == "firefox" else None
        )

        result = GenerationResult(output_file, "html")
        success = result._open_html()

        assert success is True
        mock_popen.assert_called_once()

    @patch("shutil.which")
    def test_open_html_no_browser_found(self, mock_which: Mock, tmp_path: Path) -> None:
        """_open_html() returns False when no browser found."""
        output_file = tmp_path / "test.html"
        output_file.write_text("<html></html>")
        mock_which.return_value = None

        result = GenerationResult(output_file, "html")
        success = result._open_html()

        assert success is False

    @patch("shutil.which")
    @patch("subprocess.Popen")
    def test_open_html_handles_browser_exception(
        self, mock_popen: Mock, mock_which: Mock, tmp_path: Path
    ) -> None:
        """_open_html() continues to next browser on exception."""
        output_file = tmp_path / "test.html"
        output_file.write_text("<html></html>")

        # First browser fails, second succeeds
        mock_which.side_effect = (
            lambda x: f"/usr/bin/{x}" if x in ["firefox", "chromium"] else None
        )
        mock_popen.side_effect = [Exception("Failed"), None]

        result = GenerationResult(output_file, "html")
        success = result._open_html()

        # Should try firefox (fail), then chromium (succeed)
        assert mock_popen.call_count == 2
        assert success is True

    @patch("sys.platform", "darwin")
    @patch("subprocess.run")
    def test_open_generic_macos(self, mock_run: Mock, tmp_path: Path) -> None:
        """_open_generic() works on macOS."""
        output_file = tmp_path / "test.txt"
        output_file.write_text("test")

        result = GenerationResult(output_file, "txt")
        success = result._open_generic()

        assert success is True
        mock_run.assert_called_once()

    @patch("sys.platform", "linux")
    @patch("shutil.which")
    @patch("subprocess.run")
    def test_open_generic_linux_with_xdg_open(
        self, mock_run: Mock, mock_which: Mock, tmp_path: Path
    ) -> None:
        """_open_generic() works on Linux with xdg-open."""
        output_file = tmp_path / "test.txt"
        output_file.write_text("test")
        mock_which.return_value = "/usr/bin/xdg-open"

        result = GenerationResult(output_file, "txt")
        success = result._open_generic()

        assert success is True
        mock_run.assert_called_once()

    @patch("sys.platform", "linux")
    @patch("shutil.which")
    def test_open_generic_linux_without_xdg_open(
        self, mock_which: Mock, tmp_path: Path
    ) -> None:
        """_open_generic() returns False on Linux without xdg-open."""
        output_file = tmp_path / "test.txt"
        output_file.write_text("test")
        mock_which.return_value = None

        result = GenerationResult(output_file, "txt")
        success = result._open_generic()

        assert success is False

    @patch("sys.platform", "darwin")
    @patch("subprocess.run")
    def test_open_generic_handles_exceptions(
        self, mock_run: Mock, tmp_path: Path
    ) -> None:
        """_open_generic() returns False on exceptions."""
        output_file = tmp_path / "test.txt"
        output_file.write_text("test")
        mock_run.side_effect = Exception("Failed")

        result = GenerationResult(output_file, "txt")
        success = result._open_generic()

        assert success is False


class TestGenerationResultFileOperations:
    """Test GenerationResult file operations."""

    def test_delete_existing_file(self, tmp_path: Path) -> None:
        """delete() removes existing file and returns True."""
        output_file = tmp_path / "test.pdf"
        output_file.write_text("test")

        result = GenerationResult(output_file, "pdf")
        success = result.delete()

        assert success is True
        assert not output_file.exists()

    def test_delete_nonexistent_file(self, tmp_path: Path) -> None:
        """delete() returns False for nonexistent file."""
        output_file = tmp_path / "nonexistent.pdf"
        result = GenerationResult(output_file, "pdf")

        success = result.delete()

        assert success is False

    def test_delete_handles_os_error(self, tmp_path: Path) -> None:
        """delete() returns False on OSError."""
        output_file = tmp_path / "test.pdf"
        output_file.write_text("test")

        result = GenerationResult(output_file, "pdf")

        with patch.object(Path, "unlink") as mock_unlink:
            mock_unlink.side_effect = OSError("Permission denied")
            success = result.delete()

            assert success is False

    def test_copy_to_file_path(self, tmp_path: Path) -> None:
        """copy_to() copies file to specified path."""
        output_file = tmp_path / "test.pdf"
        output_file.write_text("test content")
        dest_file = tmp_path / "copy.pdf"

        result = GenerationResult(output_file, "pdf")
        copied_path = result.copy_to(dest_file)

        assert copied_path == dest_file
        assert dest_file.exists()
        assert dest_file.read_text() == "test content"

    def test_copy_to_directory(self, tmp_path: Path) -> None:
        """copy_to() copies file to directory with original name."""
        output_file = tmp_path / "test.pdf"
        output_file.write_text("test content")
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()

        result = GenerationResult(output_file, "pdf")
        copied_path = result.copy_to(dest_dir)

        assert copied_path == dest_dir / "test.pdf"
        assert (dest_dir / "test.pdf").exists()

    def test_copy_to_raises_error_on_failure(self, tmp_path: Path) -> None:
        """copy_to() raises FileSystemError on copy failure."""
        output_file = tmp_path / "test.pdf"
        output_file.write_text("test")
        dest_file = tmp_path / "copy.pdf"

        result = GenerationResult(output_file, "pdf")

        with patch("shutil.copy2") as mock_copy:
            mock_copy.side_effect = OSError("Permission denied")

            with pytest.raises(FileSystemError, match="Failed to copy"):
                result.copy_to(dest_file)

    def test_move_to_file_path(self, tmp_path: Path) -> None:
        """move_to() moves file to specified path."""
        output_file = tmp_path / "test.pdf"
        output_file.write_text("test content")
        dest_file = tmp_path / "moved.pdf"

        result = GenerationResult(output_file, "pdf")
        moved_path = result.move_to(dest_file)

        assert moved_path == dest_file
        assert dest_file.exists()
        assert not output_file.exists()

    def test_move_to_directory(self, tmp_path: Path) -> None:
        """move_to() moves file to directory with original name."""
        output_file = tmp_path / "test.pdf"
        output_file.write_text("test content")
        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()

        result = GenerationResult(output_file, "pdf")
        moved_path = result.move_to(dest_dir)

        assert moved_path == dest_dir / "test.pdf"
        assert (dest_dir / "test.pdf").exists()
        assert not output_file.exists()

    def test_move_to_raises_error_on_failure(self, tmp_path: Path) -> None:
        """move_to() raises FileSystemError on move failure."""
        output_file = tmp_path / "test.pdf"
        output_file.write_text("test")
        dest_file = tmp_path / "moved.pdf"

        result = GenerationResult(output_file, "pdf")

        with patch("shutil.move") as mock_move:
            mock_move.side_effect = OSError("Permission denied")

            with pytest.raises(FileSystemError, match="Failed to move"):
                result.move_to(dest_file)

    def test_read_text_success(self, tmp_path: Path) -> None:
        """read_text() reads file content as text."""
        output_file = tmp_path / "test.html"
        output_file.write_text("<!DOCTYPE html><html></html>", encoding="utf-8")

        result = GenerationResult(output_file, "html")
        content = result.read_text()

        assert content == "<!DOCTYPE html><html></html>"

    def test_read_text_with_encoding(self, tmp_path: Path) -> None:
        """read_text() uses specified encoding."""
        output_file = tmp_path / "test.txt"
        output_file.write_text("Test content", encoding="latin-1")

        result = GenerationResult(output_file, "txt")
        content = result.read_text(encoding="latin-1")

        assert content == "Test content"

    def test_read_text_raises_error_on_failure(self, tmp_path: Path) -> None:
        """read_text() raises FileSystemError on read failure."""
        output_file = tmp_path / "nonexistent.txt"
        result = GenerationResult(output_file, "txt")

        with pytest.raises(FileSystemError, match="Failed to read"):
            result.read_text()

    def test_read_bytes_success(self, tmp_path: Path) -> None:
        """read_bytes() reads file content as bytes."""
        output_file = tmp_path / "test.pdf"
        test_bytes = b"PDF binary content"
        output_file.write_bytes(test_bytes)

        result = GenerationResult(output_file, "pdf")
        content = result.read_bytes()

        assert content == test_bytes

    def test_read_bytes_raises_error_on_failure(self, tmp_path: Path) -> None:
        """read_bytes() raises FileSystemError on read failure."""
        output_file = tmp_path / "nonexistent.pdf"
        result = GenerationResult(output_file, "pdf")

        with pytest.raises(FileSystemError, match="Failed to read"):
            result.read_bytes()


class TestGenerationResultStringRepresentation:
    """Test GenerationResult string representations."""

    def test_str_representation(self, tmp_path: Path) -> None:
        """__str__() returns simple string representation."""
        output_file = tmp_path / "test.pdf"
        result = GenerationResult(output_file, "pdf")

        str_repr = str(result)

        assert "GenerationResult" in str_repr
        assert "test.pdf" in str_repr
        assert "format=pdf" in str_repr

    def test_repr_representation(self, tmp_path: Path) -> None:
        """__repr__() returns detailed representation."""
        output_file = tmp_path / "test.pdf"
        output_file.write_text("test")
        result = GenerationResult(output_file, "pdf")

        repr_str = repr(result)

        assert "GenerationResult" in repr_str
        assert "output_path=" in repr_str
        assert "format_type=" in repr_str
        assert "size=" in repr_str

    def test_bool_true_for_existing_file(self, tmp_path: Path) -> None:
        """__bool__() returns True for existing file."""
        output_file = tmp_path / "test.pdf"
        output_file.write_text("test")
        result = GenerationResult(output_file, "pdf")

        assert bool(result) is True
        assert result  # Truthy check

    def test_bool_false_for_nonexistent_file(self, tmp_path: Path) -> None:
        """__bool__() returns False for nonexistent file."""
        output_file = tmp_path / "nonexistent.pdf"
        result = GenerationResult(output_file, "pdf")

        assert bool(result) is False
        assert not result  # Falsy check


class TestBatchGenerationResult:
    """Test BatchGenerationResult functionality."""

    def test_batch_result_creation(self) -> None:
        """BatchGenerationResult can be created with all fields."""
        results: dict[str, GenerationResult] = {}
        errors: dict[str, Exception] = {}

        batch = BatchGenerationResult(
            results=results, total_time=10.5, successful=5, failed=2, errors=errors
        )

        assert batch.results == results
        assert batch.total_time == 10.5
        assert batch.successful == 5
        assert batch.failed == 2
        assert batch.errors == errors

    def test_batch_result_defaults(self) -> None:
        """BatchGenerationResult has correct defaults."""
        batch = BatchGenerationResult()

        assert batch.results == {}
        assert batch.total_time == 0.0
        assert batch.successful == 0
        assert batch.failed == 0
        assert batch.errors == {}

    def test_total_property(self) -> None:
        """Total property returns sum of successful and failed."""
        batch = BatchGenerationResult(successful=5, failed=2)

        assert batch.total == 7

    def test_success_rate_property(self) -> None:
        """success_rate property returns percentage."""
        batch = BatchGenerationResult(successful=7, failed=3)

        assert batch.success_rate == 70.0

    def test_success_rate_with_zero_total(self) -> None:
        """success_rate returns 0.0 when total is 0."""
        batch = BatchGenerationResult(successful=0, failed=0)

        assert batch.success_rate == 0.0

    def test_get_successful(self, tmp_path: Path) -> None:
        """get_successful() returns only existing results."""
        file1 = tmp_path / "test1.pdf"
        file1.write_text("test")
        file2 = tmp_path / "test2.pdf"  # Doesn't exist

        result1 = GenerationResult(file1, "pdf")
        result2 = GenerationResult(file2, "pdf")

        batch = BatchGenerationResult(results={"resume1": result1, "resume2": result2})

        successful = batch.get_successful()

        assert len(successful) == 1
        assert "resume1" in successful

    def test_get_failed(self) -> None:
        """get_failed() returns copy of errors."""
        error1 = Exception("Error 1")
        error2 = Exception("Error 2")
        errors = {"resume1": error1, "resume2": error2}

        batch = BatchGenerationResult(errors=errors)

        failed = batch.get_failed()

        assert failed == errors
        assert failed is not errors  # Should be a copy

    def test_open_all(self, tmp_path: Path) -> None:
        """open_all() opens all successful results."""
        file1 = tmp_path / "test1.pdf"
        file1.write_text("test")
        file2 = tmp_path / "test2.pdf"
        file2.write_text("test")

        result1 = GenerationResult(file1, "pdf")
        result2 = GenerationResult(file2, "pdf")

        batch = BatchGenerationResult(results={"resume1": result1, "resume2": result2})

        with (
            patch.object(result1, "open") as mock_open1,
            patch.object(result2, "open") as mock_open2,
        ):
            batch.open_all()

            mock_open1.assert_called_once()
            mock_open2.assert_called_once()

    def test_open_all_continues_on_exception(self, tmp_path: Path) -> None:
        """open_all() continues opening even if one fails."""
        file1 = tmp_path / "test1.pdf"
        file1.write_text("test")
        file2 = tmp_path / "test2.pdf"
        file2.write_text("test")

        result1 = GenerationResult(file1, "pdf")
        result2 = GenerationResult(file2, "pdf")

        batch = BatchGenerationResult(results={"resume1": result1, "resume2": result2})

        with (
            patch.object(result1, "open") as mock_open1,
            patch.object(result2, "open") as mock_open2,
        ):
            mock_open1.side_effect = Exception("Failed to open")

            # Should not raise exception
            batch.open_all()

            # Both should be called
            mock_open1.assert_called_once()
            mock_open2.assert_called_once()

    def test_delete_all(self, tmp_path: Path) -> None:
        """delete_all() deletes all successful results."""
        file1 = tmp_path / "test1.pdf"
        file1.write_text("test")
        file2 = tmp_path / "test2.pdf"
        file2.write_text("test")

        result1 = GenerationResult(file1, "pdf")
        result2 = GenerationResult(file2, "pdf")

        batch = BatchGenerationResult(results={"resume1": result1, "resume2": result2})

        deleted = batch.delete_all()

        assert deleted == 2
        assert not file1.exists()
        assert not file2.exists()

    def test_delete_all_counts_only_deleted(self, tmp_path: Path) -> None:
        """delete_all() counts only successfully deleted files."""
        file1 = tmp_path / "test1.pdf"
        file1.write_text("test")
        file2 = tmp_path / "test2.pdf"  # Doesn't exist

        result1 = GenerationResult(file1, "pdf")
        result2 = GenerationResult(file2, "pdf")

        batch = BatchGenerationResult(results={"resume1": result1, "resume2": result2})

        deleted = batch.delete_all()

        # Only file1 was deleted (file2 didn't exist)
        assert deleted == 1

    def test_str_representation(self) -> None:
        """__str__() returns string representation."""
        batch = BatchGenerationResult(successful=5, failed=2, total_time=10.5)

        str_repr = str(batch)

        assert "BatchGenerationResult" in str_repr
        assert "successful=5" in str_repr
        assert "failed=2" in str_repr
