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
from tests.bdd import Scenario


class TestResolvePaletteConfig:
    """Tests for resolve_palette_config function."""

    def test_invalid_source_raises_palette_error(self, story: Scenario) -> None:
        """Test that invalid source type raises PaletteError."""
        story.given("an invalid palette source type")
        story.when("resolving palette config")
        registry = PaletteRegistry()
        block = {"source": "invalid_source_type"}

        with pytest.raises(PaletteError, match="Unsupported palette source"):
            resolve_palette_config(block, registry=registry)

    def test_registry_without_name_raises_error(self, story: Scenario) -> None:
        """Test that registry source without name raises error."""
        story.given("a registry source block without 'name' field")
        story.when("resolving palette config")
        registry = PaletteRegistry()
        block = {"source": "registry"}  # Missing 'name'

        with pytest.raises(PaletteLookupError, match="requires 'name'"):
            resolve_palette_config(block, registry=registry)

    def test_registry_with_name_returns_colors(self, story: Scenario) -> None:
        """Test registry source with valid name returns colors."""
        story.given("a registered palette in the registry")
        story.when("resolving palette config with registry source")
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

    def test_generator_source_returns_colors(self, story: Scenario) -> None:
        """Test generator source returns generated colors."""
        story.given("a generator source config block")
        story.when("resolving palette config")
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

    def test_remote_source_returns_fetch_request(self, story: Scenario) -> None:
        """Test remote source returns fetch request."""
        story.given("a remote source config block with keywords")
        story.when("resolving palette config")
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

    def test_unsupported_source_value_raises_error(self, story: Scenario) -> None:
        """Test unsupported source value in enum raises error."""
        story.given("a mocked PaletteSource returning unknown value")
        story.when("resolving palette config")
        registry = PaletteRegistry()

        # Mock PaletteSource.normalize to return an unexpected value
        with mock.patch.object(
            PaletteSource, "normalize", return_value=mock.MagicMock(value="unknown")
        ):
            block = {"source": "something"}

            with pytest.raises(PaletteError, match="Unsupported palette source"):
                resolve_palette_config(block, registry=registry)
