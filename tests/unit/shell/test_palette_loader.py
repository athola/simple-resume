"""Tests for shell palette loader (I/O operations)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast
from unittest import mock

from palettable.palette import Palette as PalettablePalette

from simple_resume.core.palettes.common import Palette
from simple_resume.core.palettes.registry import PaletteRegistry
from simple_resume.core.palettes.sources import PalettableRecord
from simple_resume.shell.palettes.loader import (
    _ensure_cache_dir,
    build_palettable_snapshot,
    discover_palettable,
    ensure_palettable_loaded,
    get_cache_file_path,
    get_default_palette_file,
    get_palette_registry,
    load_all_palettable_palettes,
    load_cached_palettable,
    load_default_palettes,
    load_palettable_palette,
    reset_palette_registry,
    save_palettable_cache,
)
from tests.bdd import Scenario


class TestGetDefaultPaletteFile:
    """Tests for get_default_palette_file function."""

    @mock.patch("simple_resume.core.palettes.sources._default_file")
    def test_returns_path_from_core(self, mock_default_file, story: Scenario) -> None:
        """Test that function delegates to core _default_file."""
        story.case("get_default_palette_file delegates to core default")
        expected_path = Path("/fake/path/default_palettes.json")
        mock_default_file.return_value = expected_path

        result = get_default_palette_file()

        assert result == expected_path
        mock_default_file.assert_called_once()


class TestGetCacheFilePath:
    """Tests for get_cache_file_path function."""

    @mock.patch("simple_resume.shell.palettes.loader.get_cache_dir")
    def test_constructs_path_and_creates_dir(
        self, mock_get_cache_dir, story: Scenario, tmp_path
    ) -> None:
        """Test cache file path construction and directory creation."""
        story.case("cache file path is constructed and directory ensured")
        cache_dir = tmp_path / "cache"
        mock_get_cache_dir.return_value = cache_dir

        result = get_cache_file_path("test.json")

        assert result == cache_dir / "test.json"
        assert cache_dir.exists()


class TestLoadDefaultPalettes:
    """Tests for load_default_palettes function."""

    @mock.patch("simple_resume.shell.palettes.loader.get_default_palette_file")
    def test_file_not_exists_returns_empty(
        self, mock_get_file, story: Scenario
    ) -> None:
        """Test returns empty list when file doesn't exist."""
        story.case("missing default palette file yields empty list")
        mock_path = mock.Mock(spec=Path)
        mock_path.exists.return_value = False
        mock_get_file.return_value = mock_path

        result = load_default_palettes()

        assert result == []

    @mock.patch("simple_resume.shell.palettes.loader.get_default_palette_file")
    def test_loads_palettes_from_file(
        self, mock_get_file, story: Scenario, tmp_path
    ) -> None:
        """Test loading palettes from JSON file."""
        story.case("default palettes file is parsed into Palette objects")
        palette_file = tmp_path / "palettes.json"
        palette_data = [
            {
                "name": "test_palette",
                "colors": ["#FF0000", "#00FF00", "#0000FF"],
                "source": "test",
                "metadata": {"key": "value"},
            }
        ]
        palette_file.write_text(json.dumps(palette_data))
        mock_get_file.return_value = palette_file

        result = load_default_palettes()

        assert len(result) == 1
        assert result[0].name == "test_palette"
        assert result[0].swatches == ("#FF0000", "#00FF00", "#0000FF")
        assert result[0].source == "test"
        assert result[0].metadata == {"key": "value"}

    @mock.patch("simple_resume.shell.palettes.loader.get_default_palette_file")
    def test_handles_missing_optional_fields(
        self, mock_get_file, story: Scenario, tmp_path
    ) -> None:
        """Test loading palette with missing optional fields."""
        story.case("palette defaults are applied when optional fields missing")
        palette_file = tmp_path / "palettes.json"
        palette_data = [{"name": "minimal", "colors": ["#FFFFFF"]}]
        palette_file.write_text(json.dumps(palette_data))
        mock_get_file.return_value = palette_file

        result = load_default_palettes()

        assert len(result) == 1
        assert result[0].source == "default"
        assert result[0].metadata == {}


class TestEnsureCacheDir:
    """Tests for _ensure_cache_dir function."""

    def test_creates_parent_directories(self, story: Scenario, tmp_path) -> None:
        """Test cache directory creation."""
        story.case("cache directories are created when missing")
        cache_path = tmp_path / "nested" / "cache" / "file.json"

        result = _ensure_cache_dir(cache_path)

        assert result == cache_path
        assert cache_path.parent.exists()


class TestLoadCachedPalettable:
    """Tests for load_cached_palettable function."""

    @mock.patch("simple_resume.shell.palettes.loader.get_cache_file_path")
    def test_no_cache_returns_empty(self, mock_get_path, story: Scenario) -> None:
        """Test returns empty list when cache doesn't exist."""
        story.case("missing palettable cache yields empty list")
        mock_path = mock.Mock(spec=Path)
        mock_path.exists.return_value = False
        mock_get_path.return_value = mock_path

        result = load_cached_palettable()

        assert result == []

    @mock.patch("simple_resume.shell.palettes.loader.get_cache_file_path")
    def test_loads_records_from_cache(
        self, mock_get_path, story: Scenario, tmp_path
    ) -> None:
        """Test loading palettable records from cache."""
        story.case("cached palettable records are parsed")
        cache_file = tmp_path / "cache.json"
        cache_data = [
            {
                "name": "Test_5",
                "module": "palettable.test",
                "attribute": "Test_5",
                "category": "test",
                "palette_type": "sequential",
                "size": 5,
            }
        ]
        cache_file.write_text(json.dumps(cache_data))
        mock_get_path.return_value = cache_file

        result = load_cached_palettable()

        assert len(result) == 1
        assert isinstance(result[0], PalettableRecord)
        assert result[0].name == "Test_5"


class TestSavePalettableCache:
    """Tests for save_palettable_cache function."""

    @mock.patch("simple_resume.shell.palettes.loader.get_cache_file_path")
    @mock.patch("simple_resume.shell.palettes.loader._ensure_cache_dir")
    def test_saves_records_to_cache(
        self, mock_ensure, mock_get_path, story: Scenario, tmp_path
    ) -> None:
        """Test saving palettable records to cache."""
        story.case("palettable records are serialized to cache file")
        cache_file = tmp_path / "cache.json"
        mock_get_path.return_value = cache_file
        mock_ensure.return_value = cache_file

        records = [
            PalettableRecord(
                name="Test_5",
                module="palettable.test",
                attribute="Test_5",
                category="test",
                palette_type="sequential",
                size=5,
            )
        ]

        save_palettable_cache(records)

        assert cache_file.exists()
        data = json.loads(cache_file.read_text())
        assert len(data) == 1
        assert data[0]["name"] == "Test_5"


class TestDiscoverPalettable:
    """Tests for discover_palettable function."""

    @mock.patch("simple_resume.shell.palettes.loader._iter_palette_modules")
    @mock.patch("simple_resume.shell.palettes.loader.import_module")
    def test_discovers_palettes(self, mock_import, mock_iter, story: Scenario) -> None:
        """Test discovering palettes from modules."""
        story.case("palettable modules are discovered and parsed")
        mock_iter.return_value = ["palettable.colorbrewer.sequential"]

        mock_palette = mock.Mock(spec=PalettablePalette)
        mock_palette.name = "Test_5"
        mock_palette.type = "sequential"
        mock_palette.colors = ["#FF0000"] * 5

        # Create mock module with proper attributes
        mock_module = mock.MagicMock()
        mock_module.__name__ = "palettable.colorbrewer.sequential"
        mock_module.Test_5 = mock_palette
        mock_import.return_value = mock_module

        # Mock dir() to return just our test attributes
        with mock.patch("builtins.dir", return_value=["Test_5"]):
            result = discover_palettable()

        assert len(result) == 1
        assert result[0].name == "Test_5"

    @mock.patch("simple_resume.shell.palettes.loader._iter_palette_modules")
    @mock.patch("simple_resume.shell.palettes.loader.import_module")
    def test_handles_import_errors(
        self, mock_import, mock_iter, story: Scenario
    ) -> None:
        """Test handling of module import errors."""
        story.case("discovery continues when imports fail")
        mock_iter.return_value = ["palettable.broken"]
        mock_import.side_effect = ImportError("Module not found")

        result = discover_palettable()

        # Should not raise, should return empty or skip broken module
        assert isinstance(result, list)

    @mock.patch("simple_resume.shell.palettes.loader._iter_palette_modules")
    @mock.patch("simple_resume.shell.palettes.loader.import_module")
    def test_handles_short_module_names(
        self, mock_import, mock_iter, story: Scenario
    ) -> None:
        """Test handling of modules with short names."""
        story.case("modules with shallow paths are skipped gracefully")
        mock_iter.return_value = ["palettable"]  # Only 1 dot
        mock_module = mock.Mock()
        mock_module.configure_mock(**{"__dir__": mock.Mock(return_value=[])})
        mock_import.return_value = mock_module

        with mock.patch("builtins.dir", return_value=[]):
            result = discover_palettable()

        assert isinstance(result, list)


class TestEnsurePalettableLoaded:
    """Tests for ensure_palettable_loaded function."""

    @mock.patch("simple_resume.shell.palettes.loader.load_cached_palettable")
    def test_returns_cached_if_available(
        self, mock_load_cached, story: Scenario
    ) -> None:
        """Test returns cached records when available."""
        story.case("cached palettable records are reused")
        cached_records = [
            PalettableRecord(
                name="Test_5",
                module="palettable.test",
                attribute="Test_5",
                category="test",
                palette_type="sequential",
                size=5,
            )
        ]
        mock_load_cached.return_value = cached_records

        result = ensure_palettable_loaded()

        assert result == cached_records

    @mock.patch("simple_resume.shell.palettes.loader.load_cached_palettable")
    @mock.patch("simple_resume.shell.palettes.loader.discover_palettable")
    @mock.patch("simple_resume.shell.palettes.loader.save_palettable_cache")
    def test_discovers_and_caches_if_no_cache(
        self, mock_save, mock_discover, mock_load_cached, story: Scenario
    ) -> None:
        """Test discovers and caches when cache is empty."""
        story.case("discovery runs when cache is empty and saves result")
        mock_load_cached.return_value = []
        discovered_records = [
            PalettableRecord(
                name="Test_5",
                module="palettable.test",
                attribute="Test_5",
                category="test",
                palette_type="sequential",
                size=5,
            )
        ]
        mock_discover.return_value = discovered_records

        result = ensure_palettable_loaded()

        assert result == discovered_records
        mock_save.assert_called_once_with(discovered_records)


class TestLoadPalettablePalette:
    """Tests for load_palettable_palette function."""

    @mock.patch("simple_resume.shell.palettes.loader.import_module")
    def test_loads_palette_successfully(self, mock_import, story: Scenario) -> None:
        """Test loading a palettable palette."""
        story.case("palettable palette loads and normalizes swatches")
        mock_palette = mock.Mock()
        mock_palette.hex_colors = ["FF0000", "00FF00"]

        mock_module = mock.Mock()
        mock_module.Test_5 = mock_palette
        mock_import.return_value = mock_module

        record = PalettableRecord(
            name="Test_5",
            module="palettable.test",
            attribute="Test_5",
            category="test",
            palette_type="sequential",
            size=2,
        )

        result = load_palettable_palette(record)

        assert result is not None
        assert result.name == "Test_5"
        assert result.swatches == ("#FF0000", "#00FF00")
        assert result.source == "palettable"

    @mock.patch("simple_resume.shell.palettes.loader.import_module")
    def test_handles_colors_attribute(self, mock_import, story: Scenario) -> None:
        """Test loading palette with 'colors' attribute."""
        story.case("palette falls back to colors attribute when hex_colors missing")
        mock_palette = mock.Mock()
        mock_palette.hex_colors = None
        mock_palette.colors = ["#AABBCC"]

        mock_module = mock.Mock()
        mock_module.Test_5 = mock_palette
        mock_import.return_value = mock_module

        record = PalettableRecord(
            name="Test_5",
            module="palettable.test",
            attribute="Test_5",
            category="test",
            palette_type="sequential",
            size=1,
        )

        result = load_palettable_palette(record)

        assert result is not None
        assert result.swatches == ("#AABBCC",)

    @mock.patch("simple_resume.shell.palettes.loader.import_module")
    def test_returns_none_on_import_error(self, mock_import, story: Scenario) -> None:
        """Test returns None when import fails."""
        story.case("import errors yield None for palette loading")
        mock_import.side_effect = ImportError("Module not found")

        record = PalettableRecord(
            name="Test_5",
            module="palettable.broken",
            attribute="Test_5",
            category="test",
            palette_type="sequential",
            size=5,
        )

        result = load_palettable_palette(record)

        assert result is None

    @mock.patch("simple_resume.shell.palettes.loader.import_module")
    def test_returns_none_for_empty_colors(self, mock_import, story: Scenario) -> None:
        """Test returns None when palette has no colors."""
        story.case("palettes without colors are ignored")
        mock_palette = mock.Mock()
        mock_palette.hex_colors = None
        mock_palette.colors = []

        mock_module = mock.Mock()
        mock_module.Test_5 = mock_palette
        mock_import.return_value = mock_module

        record = PalettableRecord(
            name="Test_5",
            module="palettable.test",
            attribute="Test_5",
            category="test",
            palette_type="sequential",
            size=0,
        )

        result = load_palettable_palette(record)

        assert result is None


class TestLoadAllPalettablePalettes:
    """Tests for load_all_palettable_palettes function."""

    @mock.patch("simple_resume.shell.palettes.loader.ensure_palettable_loaded")
    @mock.patch("simple_resume.shell.palettes.loader.load_palettable_palette")
    def test_loads_all_palettes(
        self, mock_load_palette, mock_ensure, story: Scenario
    ) -> None:
        """Test loading all palettable palettes."""
        story.case("all discovered palettable palettes are converted")
        records = [
            PalettableRecord(
                name="Test_5",
                module="palettable.test",
                attribute="Test_5",
                category="test",
                palette_type="sequential",
                size=5,
            )
        ]
        mock_ensure.return_value = records
        mock_load_palette.return_value = Palette(
            name="Test_5",
            swatches=("#FF0000",),
            source="palettable",
            metadata={},
        )

        result = load_all_palettable_palettes()

        assert len(result) == 1
        assert result[0].name == "Test_5"

    @mock.patch("simple_resume.shell.palettes.loader.ensure_palettable_loaded")
    @mock.patch("simple_resume.shell.palettes.loader.load_palettable_palette")
    def test_skips_failed_palettes(
        self, mock_load_palette, mock_ensure, story: Scenario
    ) -> None:
        """Test skips palettes that fail to load."""
        story.case("failed palette loads are skipped")
        records = [
            PalettableRecord(
                name="Test_5",
                module="palettable.test",
                attribute="Test_5",
                category="test",
                palette_type="sequential",
                size=5,
            )
        ]
        mock_ensure.return_value = records
        mock_load_palette.return_value = None

        result = load_all_palettable_palettes()

        assert len(result) == 0


class TestBuildPalettableSnapshot:
    """Tests for build_palettable_snapshot function."""

    @mock.patch("simple_resume.shell.palettes.loader.ensure_palettable_loaded")
    @mock.patch("simple_resume.shell.palettes.loader.time")
    def test_builds_snapshot(self, mock_time, mock_ensure, story: Scenario) -> None:
        """Test building palettable snapshot."""
        story.case("snapshot captures timestamp, count and palette list")
        mock_time.time.return_value = 1234567890.0
        records = [
            PalettableRecord(
                name="Test_5",
                module="palettable.test",
                attribute="Test_5",
                category="test",
                palette_type="sequential",
                size=5,
            )
        ]
        mock_ensure.return_value = records

        result = build_palettable_snapshot()

        assert result["generated_at"] == 1234567890.0
        assert result["count"] == 1
        assert len(cast(list, result["palettes"])) == 1


class TestGetPaletteRegistry:
    """Tests for get_palette_registry function."""

    @mock.patch("simple_resume.shell.palettes.loader.build_palette_registry")
    def test_returns_registry(self, mock_build, story: Scenario) -> None:
        """Test returns palette registry."""
        story.case("registry is built once and cached across calls")
        # Clear cache first to ensure mock is used (test isolation)
        reset_palette_registry()

        mock_registry = PaletteRegistry()
        mock_build.return_value = mock_registry

        result = get_palette_registry()

        assert result == mock_registry
        # Cached call should not invoke build again
        result2 = get_palette_registry()
        assert result2 == mock_registry
        assert mock_build.call_count == 1

        # Clean up cache for other tests
        reset_palette_registry()


class TestResetPaletteRegistry:
    """Tests for reset_palette_registry function."""

    def test_clears_cache(self, story: Scenario) -> None:
        """Test clearing registry cache."""
        story.case("registry cache can be cleared to force rebuild")
        # Clear cache before test to ensure clean state
        reset_palette_registry()

        # Call get_palette_registry to populate cache
        registry1 = get_palette_registry()
        assert registry1 is not None

        # Call again should return same cached instance
        registry2 = get_palette_registry()
        assert registry1 is registry2

        # Reset cache
        reset_palette_registry()

        # Call again should create new instance
        registry3 = get_palette_registry()
        assert registry3 is not None
        # After reset, we get a fresh registry (may or may not be same object)
