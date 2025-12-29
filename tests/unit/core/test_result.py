"""Tests for core/result.py - GenerationResult and BatchGenerationResult.

Following the FCIS architecture, GenerationResult is now a pure data class.
I/O operations are handled by module-level helper functions.
Platform-specific file opening tests are in tests/unit/shell/test_file_opener.py.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import PropertyMock, patch

import pytest

from simple_resume.core.result import (
    BatchGenerationResult,
    GenerationMetadata,
    GenerationResult,
)


class TestGenerationMetadata:
    """Tests for GenerationMetadata."""

    def test_metadata_creation(self) -> None:
        """Test basic metadata creation."""
        metadata = GenerationMetadata(
            format_type="pdf",
            template_name="basic",
            generation_time=1.5,
            file_size=1024,
            resume_name="john_doe",
            palette_info={"primary": "#000000"},
            page_count=2,
        )
        assert metadata.format_type == "pdf"
        assert metadata.template_name == "basic"
        assert metadata.generation_time == 1.5
        assert metadata.file_size == 1024
        assert metadata.resume_name == "john_doe"
        assert metadata.palette_info == {"primary": "#000000"}
        assert metadata.page_count == 2


class TestGenerationResult:
    """Tests for GenerationResult (pure data class)."""

    def test_post_init_normalizes_format(self, tmp_path) -> None:
        """Test that format_type is normalized to lowercase."""
        result = GenerationResult(output_path=tmp_path / "test.pdf", format_type="PDF")
        assert result.format_type == "pdf"

    def test_post_init_converts_path_to_pathlib(self) -> None:
        """Test that output_path is converted to Path object."""
        result = GenerationResult(output_path=Path("/tmp/test.pdf"), format_type="pdf")  # noqa: S108
        assert isinstance(result.output_path, Path)

    def test_post_init_creates_default_metadata(self, tmp_path) -> None:
        """Test that default metadata is created when not provided."""
        result = GenerationResult(output_path=tmp_path / "test.pdf", format_type="pdf")
        assert result.metadata is not None
        assert result.metadata.format_type == "pdf"
        assert result.metadata.template_name == "unknown"
        assert result.metadata.resume_name == "unknown"

    def test_str_representation(self, tmp_path) -> None:
        """Test __str__ representation."""
        file_path = tmp_path / "test.pdf"
        file_path.write_text("test content")
        result = GenerationResult(output_path=file_path, format_type="pdf")
        str_repr = str(result)
        assert "GenerationResult" in str_repr
        assert "format=pdf" in str_repr
        assert "path=" in str_repr

    def test_name_property(self, tmp_path) -> None:
        """Test name property returns filename."""
        result = GenerationResult(
            output_path=tmp_path / "resume.pdf", format_type="pdf"
        )
        assert result.name == "resume.pdf"

    def test_stem_property(self, tmp_path) -> None:
        """Test stem property returns filename without extension."""
        result = GenerationResult(
            output_path=tmp_path / "resume.pdf", format_type="pdf"
        )
        assert result.stem == "resume"

    def test_suffix_property(self, tmp_path) -> None:
        """Test suffix property returns file extension."""
        result = GenerationResult(
            output_path=tmp_path / "resume.pdf", format_type="pdf"
        )
        assert result.suffix == ".pdf"

    def test_size_property_existing_file(self, tmp_path) -> None:
        """Test size property for existing file."""
        file_path = tmp_path / "test.pdf"
        content = "x" * 100
        file_path.write_text(content)
        result = GenerationResult(output_path=file_path, format_type="pdf")
        assert result.size == len(content)

    def test_size_property_nonexistent_file(self, tmp_path) -> None:
        """Test size property for nonexistent file."""
        result = GenerationResult(
            output_path=tmp_path / "nonexistent.pdf", format_type="pdf"
        )
        assert result.size == 0

    def test_size_human_bytes(self, tmp_path) -> None:
        """Test size_human property for small files."""
        file_path = tmp_path / "test.pdf"
        file_path.write_text("x" * 100)
        result = GenerationResult(output_path=file_path, format_type="pdf")
        assert "B" in result.size_human

    def test_size_human_kilobytes(self, tmp_path) -> None:
        """Test size_human property for KB files."""
        file_path = tmp_path / "test.pdf"
        file_path.write_text("x" * 2048)
        result = GenerationResult(output_path=file_path, format_type="pdf")
        assert "KB" in result.size_human

    def test_size_human_megabytes(self, tmp_path) -> None:
        """Test size_human property for MB files."""
        file_path = tmp_path / "test.pdf"
        # Write ~1.5 MB
        file_path.write_bytes(b"x" * (1024 * 1024 + 512 * 1024))
        result = GenerationResult(output_path=file_path, format_type="pdf")
        assert "MB" in result.size_human

    def test_size_human_gigabytes(self, tmp_path) -> None:
        """Test size_human property for GB+ files."""
        # Patch the size property to return a large GB-sized value
        file_path = tmp_path / "test.pdf"
        file_path.write_text("test")
        result = GenerationResult(output_path=file_path, format_type="pdf")

        # Test with a multi-gigabyte file size
        with patch.object(type(result), "size", new_callable=PropertyMock) as mock_size:
            mock_size.return_value = 2 * 1024 * 1024 * 1024  # 2 GB
            assert "GB" in result.size_human

    def test_exists_property_true(self, tmp_path) -> None:
        """Test exists property for existing file."""
        file_path = tmp_path / "test.pdf"
        file_path.write_text("content")
        result = GenerationResult(output_path=file_path, format_type="pdf")
        assert result.exists is True

    def test_exists_property_false(self, tmp_path) -> None:
        """Test exists property for nonexistent file."""
        result = GenerationResult(
            output_path=tmp_path / "nonexistent.pdf", format_type="pdf"
        )
        assert result.exists is False

    def test_bool_true_when_exists(self, tmp_path) -> None:
        """Test __bool__ returns True when file exists."""
        file_path = tmp_path / "test.pdf"
        file_path.write_text("content")
        result = GenerationResult(output_path=file_path, format_type="pdf")
        assert bool(result) is True

    def test_bool_false_when_not_exists(self, tmp_path) -> None:
        """Test __bool__ returns False when file doesn't exist."""
        result = GenerationResult(
            output_path=tmp_path / "nonexistent.pdf", format_type="pdf"
        )
        assert bool(result) is False


class TestBatchGenerationResult:
    """Tests for BatchGenerationResult."""

    def test_total_property(self) -> None:
        """Test total property returns sum of successful and failed."""
        batch = BatchGenerationResult(successful=5, failed=3)
        assert batch.total == 8

    def test_success_rate_property(self) -> None:
        """Test success_rate property returns percentage."""
        batch = BatchGenerationResult(successful=7, failed=3)
        assert batch.success_rate == 70.0

    def test_success_rate_zero_division(self) -> None:
        """Test success_rate property returns 0 when total is 0."""
        batch = BatchGenerationResult(successful=0, failed=0)
        assert batch.success_rate == 0.0

    def test_iteration(self, tmp_path) -> None:
        """Test iteration over results."""
        result1 = GenerationResult(output_path=tmp_path / "a.pdf", format_type="pdf")
        result2 = GenerationResult(output_path=tmp_path / "b.html", format_type="html")
        batch = BatchGenerationResult(results={"pdf": result1, "html": result2})

        items = list(batch)

        assert len(items) == 2
        assert result1 in items
        assert result2 in items

    def test_iteration_empty_results(self) -> None:
        """Test iteration over empty results (results=None)."""
        batch = BatchGenerationResult(results=None)  # type: ignore[arg-type]
        items = list(batch)
        assert items == []

    def test_len_empty_results(self) -> None:
        """Test __len__ with empty results (results=None)."""
        batch = BatchGenerationResult(results=None)  # type: ignore[arg-type]
        assert len(batch) == 0

    def test_getitem_none_results_raises(self) -> None:
        """Test __getitem__ raises KeyError when results is None."""
        batch = BatchGenerationResult(results=None)  # type: ignore[arg-type]
        with pytest.raises(KeyError, match="No results available"):
            _ = batch["missing"]

    def test_get_none_results_returns_default(self) -> None:
        """Test get returns default when results is None."""
        batch = BatchGenerationResult(results=None)  # type: ignore[arg-type]
        assert batch.get("missing") is None
        assert batch.get("missing", "default") == "default"  # type: ignore[arg-type]

    def test_len(self, tmp_path) -> None:
        """Test __len__ returns number of results."""
        result1 = GenerationResult(output_path=tmp_path / "a.pdf", format_type="pdf")
        batch = BatchGenerationResult(results={"pdf": result1})
        assert len(batch) == 1

    def test_getitem(self, tmp_path) -> None:
        """Test __getitem__ returns result by key."""
        result1 = GenerationResult(output_path=tmp_path / "a.pdf", format_type="pdf")
        batch = BatchGenerationResult(results={"pdf": result1})
        assert batch["pdf"] == result1

    def test_getitem_missing_raises_keyerror(self) -> None:
        """Test __getitem__ raises KeyError for missing key."""
        batch = BatchGenerationResult()
        with pytest.raises(KeyError):
            batch["missing"]

    def test_contains(self, tmp_path) -> None:
        """Test __contains__ checks for key presence."""
        result1 = GenerationResult(output_path=tmp_path / "a.pdf", format_type="pdf")
        batch = BatchGenerationResult(results={"pdf": result1})
        assert "pdf" in batch
        assert "html" not in batch

    def test_get_existing_key(self, tmp_path) -> None:
        """Test get method returns result for existing key."""
        result1 = GenerationResult(output_path=tmp_path / "a.pdf", format_type="pdf")
        batch = BatchGenerationResult(results={"pdf": result1})
        assert batch.get("pdf") == result1

    def test_get_missing_key_returns_default(self, tmp_path) -> None:
        """Test get method returns default for missing key."""
        batch = BatchGenerationResult()
        assert batch.get("missing") is None
        assert batch.get("missing") is None

    def test_get_successful(self, tmp_path) -> None:
        """Test get_successful returns list of successful results."""
        result1 = GenerationResult(output_path=tmp_path / "a.pdf", format_type="pdf")
        result2 = GenerationResult(output_path=tmp_path / "b.html", format_type="html")
        batch = BatchGenerationResult(results={"pdf": result1, "html": result2})

        successful = batch.get_successful()

        assert len(successful) == 2
        assert result1 in successful
        assert result2 in successful

    def test_get_failed(self) -> None:
        """Test get_failed returns dictionary of errors."""
        error1 = ValueError("Error 1")
        error2 = RuntimeError("Error 2")
        batch = BatchGenerationResult(errors={"pdf": error1, "html": error2})

        failed = batch.get_failed()

        assert len(failed) == 2
        assert failed["pdf"] == error1
        assert failed["html"] == error2
