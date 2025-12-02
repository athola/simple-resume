"""Tests for core/palettes/resolution.py - pure palette resolution logic."""

from __future__ import annotations

from unittest import mock

import pytest

from simple_resume.core.palettes.common import Palette, PaletteSource
from simple_resume.core.palettes.exceptions import (
    PaletteError,
    PaletteLookupError,
)
from simple_resume.core.palettes.registry import PaletteRegistry
from simple_resume.core.palettes.resolution import resolve_palette_config


class TestResolvePaletteConfig:
    """Tests for resolve_palette_config function."""

    def test_invalid_source_raises_palette_error(self) -> None:
        """Test that invalid source type raises PaletteError."""
        registry = PaletteRegistry()
        block = {"source": "invalid_source_type"}

        with pytest.raises(PaletteError, match="Unsupported palette source"):
            resolve_palette_config(block, registry=registry)

    def test_registry_without_name_raises_error(self) -> None:
        """Test that registry source without name raises error."""
        registry = PaletteRegistry()
        block = {"source": "registry"}  # Missing 'name'

        with pytest.raises(PaletteLookupError, match="requires 'name'"):
            resolve_palette_config(block, registry=registry)

    def test_registry_with_name_returns_colors(self) -> None:
        """Test registry source with valid name returns colors."""
        registry = PaletteRegistry()
        # Register a test palette
        test_palette = Palette(
            name="test_palette",
            swatches=("#FF0000", "#00FF00", "#0000FF"),
            source="test",
            metadata={},
        )
        registry.register(test_palette)

        block = {"source": "registry", "name": "test_palette"}
        result = resolve_palette_config(block, registry=registry)

        assert result.colors is not None
        assert len(result.colors) == 3
        assert result.colors[0] == "#FF0000"

    def test_generator_source_returns_colors(self) -> None:
        """Test generator source returns generated colors."""
        registry = PaletteRegistry()
        block = {
            "source": "generator",
            "size": 3,
            "seed": 42,
        }

        result = resolve_palette_config(block, registry=registry)

        assert result.colors is not None
        assert len(result.colors) == 3
        assert result.fetch_request is None

    def test_remote_source_returns_fetch_request(self) -> None:
        """Test remote source returns fetch request."""
        registry = PaletteRegistry()
        block = {
            "source": "remote",
            "keywords": "ocean blue",
            "num_results": 3,
        }

        result = resolve_palette_config(block, registry=registry)

        assert result.fetch_request is not None
        assert result.fetch_request.keywords == "ocean blue"
        assert result.fetch_request.num_results == 3
        assert result.colors is None

    def test_unsupported_source_value_raises_error(self) -> None:
        """Test unsupported source value in enum raises error."""
        registry = PaletteRegistry()

        # Mock PaletteSource.normalize to return an unexpected value
        with mock.patch.object(
            PaletteSource, "normalize", return_value=mock.MagicMock(value="unknown")
        ):
            block = {"source": "something"}

            with pytest.raises(PaletteError, match="Unsupported palette source"):
                resolve_palette_config(block, registry=registry)
