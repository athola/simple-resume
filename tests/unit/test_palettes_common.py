"""Tests for palettes common module."""

from __future__ import annotations

from pathlib import Path

import pytest

from simple_resume.palettes.common import Palette, PaletteSource, get_cache_dir


class TestPalette:
    """Test Palette dataclass."""

    def test_palette_creation(self) -> None:
        """Test creating a Palette instance."""
        palette = Palette(
            name="test",
            swatches=("#FF0000", "#00FF00"),
            source="registry",
        )

        assert palette.name == "test"
        assert palette.swatches == ("#FF0000", "#00FF00")
        assert palette.source == "registry"
        assert palette.metadata == {}

    def test_palette_with_metadata(self) -> None:
        """Test Palette with metadata."""
        metadata: dict[str, object] = {
            "author": "test",
            "description": "A test palette",
        }
        palette = Palette(
            name="test",
            swatches=("#FF0000",),
            source="registry",
            metadata=metadata,
        )

        assert palette.metadata == metadata

    def test_palette_to_dict(self) -> None:
        """Test Palette.to_dict() serialization."""
        palette = Palette(
            name="test",
            swatches=("#FF0000", "#00FF00", "#0000FF"),
            source="registry",
            metadata={"author": "tester"},
        )

        result = palette.to_dict()

        assert result == {
            "name": "test",
            "swatches": ["#FF0000", "#00FF00", "#0000FF"],
            "source": "registry",
            "metadata": {"author": "tester"},
        }

    def test_palette_immutability(self) -> None:
        """Test that Palette is immutable."""
        palette = Palette(
            name="test",
            swatches=("#FF0000",),
            source="registry",
        )

        with pytest.raises(AttributeError):
            palette.name = "new_name"  # type: ignore[misc]


class TestPaletteSource:
    """Test PaletteSource enum."""

    def test_palette_source_values(self) -> None:
        """Test PaletteSource enum values."""
        assert PaletteSource.REGISTRY.value == "registry"
        assert PaletteSource.GENERATOR.value == "generator"
        assert PaletteSource.REMOTE.value == "remote"

    def test_normalize_with_none(self) -> None:
        """Test normalize() with None returns REGISTRY."""
        result = PaletteSource.normalize(None)
        assert result == PaletteSource.REGISTRY

    def test_normalize_with_enum(self) -> None:
        """Test normalize() with existing enum member."""
        result = PaletteSource.normalize(PaletteSource.GENERATOR)
        assert result == PaletteSource.GENERATOR

    def test_normalize_with_string(self) -> None:
        """Test normalize() with string value."""
        result = PaletteSource.normalize("registry")
        assert result == PaletteSource.REGISTRY

        result = PaletteSource.normalize("GENERATOR")
        assert result == PaletteSource.GENERATOR

        result = PaletteSource.normalize("  remote  ")
        assert result == PaletteSource.REMOTE

    def test_normalize_with_invalid_type(self) -> None:
        """Test normalize() raises TypeError for invalid types."""
        with pytest.raises(TypeError, match="must be string or PaletteSource"):
            PaletteSource.normalize(123)  # type: ignore[arg-type]

    def test_normalize_with_invalid_string(self) -> None:
        """Test normalize() raises ValueError for invalid string."""
        with pytest.raises(ValueError, match="Unsupported.*source"):
            PaletteSource.normalize("invalid")

    def test_normalize_with_param_name(self) -> None:
        """Test normalize() error message includes param_name."""
        with pytest.raises(ValueError, match="Unsupported palette_param source"):
            PaletteSource.normalize("invalid", param_name="palette_param")


class TestGetCacheDir:
    """Test get_cache_dir function."""

    def test_get_cache_dir_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test get_cache_dir() returns default path."""
        monkeypatch.delenv("SIMPLE_RESUME_PALETTE_CACHE_DIR", raising=False)

        result = get_cache_dir()

        assert str(result).endswith(".cache/simple-resume/palettes")

    def test_get_cache_dir_custom(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test get_cache_dir() respects environment variable."""
        custom_path = str(tmp_path / "custom" / "palettes")
        monkeypatch.setenv("SIMPLE_RESUME_PALETTE_CACHE_DIR", custom_path)

        result = get_cache_dir()

        assert str(result) == custom_path

    def test_get_cache_dir_expands_home(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test get_cache_dir() expands ~ in custom path."""
        monkeypatch.setenv("SIMPLE_RESUME_PALETTE_CACHE_DIR", "~/my_palettes")

        result = get_cache_dir()

        assert "~" not in str(result)
        assert str(result).endswith("my_palettes")
