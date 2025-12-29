from __future__ import annotations

import hashlib
import sys
from email.message import Message
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock, patch
from urllib.error import HTTPError
from urllib.parse import urlencode

import pytest

from simple_resume.core.palettes.common import Palette
from simple_resume.core.palettes.exceptions import PaletteRemoteError
from simple_resume.core.palettes.sources import (
    PalettableRecord,
    _cache_path,
    load_palettable_palette,
    parse_palettable_cache,
    parse_palette_data,
    serialize_palettable_records,
)
from simple_resume.shell.palettes.loader import (
    build_palettable_registry_snapshot,
    ensure_palettable_loaded,
    load_default_palettes,
)
from simple_resume.shell.palettes.remote import ColourLoversClient
from tests.bdd import Scenario


def test_parse_palette_data_creates_palette_objects(story: Scenario) -> None:
    story.given("a list of palette dictionaries")
    payload = [
        {"name": "Ocean", "colors": ["#003f5c", "#58508d"], "source": "test"},
        {"name": "Forest", "colors": ["#228b22", "#006400"]},  # No source/metadata
    ]

    story.when("parse_palette_data is called")
    palettes = parse_palette_data(payload)

    story.then("it returns Palette objects with correct attributes")
    assert len(palettes) == 2
    assert palettes[0].name == "Ocean"
    assert palettes[0].swatches == ("#003f5c", "#58508d")
    assert palettes[0].source == "test"
    assert palettes[1].name == "Forest"
    assert palettes[1].source == "default"  # Default when not provided
    assert palettes[1].metadata == {}  # Default when not provided


def test_parse_palettable_cache(story: Scenario) -> None:
    story.given("a list of palettable cache dictionaries")
    payload = [
        {
            "name": "Blues_3",
            "module": "palettable.colorbrewer.sequential",
            "attribute": "Blues_3",
            "category": "colorbrewer",
            "palette_type": "sequential",
            "size": 3,
        }
    ]

    story.when("parse_palettable_cache is called")
    records = parse_palettable_cache(payload)

    story.then("it returns PalettableRecord objects")
    assert len(records) == 1
    assert records[0].module == "palettable.colorbrewer.sequential"
    assert records[0].size == 3
    assert records[0].name == "Blues_3"


def test_serialize_palettable_records(story: Scenario) -> None:
    story.given("a list of PalettableRecord objects")
    records = [
        PalettableRecord(
            name="Blues_3",
            module="palettable.colorbrewer.sequential",
            attribute="Blues_3",
            category="colorbrewer",
            palette_type="sequential",
            size=3,
        )
    ]

    story.when("serialize_palettable_records is called")
    result = serialize_palettable_records(records)

    story.then("it returns serializable dictionaries")
    assert len(result) == 1
    assert result[0]["module"] == "palettable.colorbrewer.sequential"
    assert result[0]["size"] == 3
    assert result[0]["name"] == "Blues_3"


def test_load_default_palettes_returns_palettes(story: Scenario) -> None:
    story.given("the bundled default palettes file is present")
    palettes = load_default_palettes()

    story.then("at least one palette is loaded with hex swatches")
    assert palettes
    assert isinstance(palettes[0], Palette)
    assert palettes[0].swatches
    assert all(color.startswith("#") for color in palettes[0].swatches)


def test_ensure_bundled_palettes_returns_cached_records(
    monkeypatch: pytest.MonkeyPatch, story: Scenario
) -> None:
    story.given("palettable is available and a cache of records already exists")
    fake_module = SimpleNamespace(__path__=())
    monkeypatch.setitem(sys.modules, "palettable", fake_module)
    cached = [
        PalettableRecord(
            name="Sunset",
            module="palettable.sunset",
            attribute="SUNSET",
            category="sequential",
            palette_type="sequential",
            size=5,
        )
    ]

    with (
        patch(
            "simple_resume.shell.palettes.loader.load_cached_palettable",
            return_value=cached,
        ),
        patch(
            "simple_resume.shell.palettes.loader.discover_palettable"
        ) as mock_discover,
    ):
        records = ensure_palettable_loaded()

    story.then("cached metadata is returned without re-discovery")
    assert records == cached
    mock_discover.assert_not_called()


def test_ensure_bundled_palettes_discovers_when_cache_empty(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    story: Scenario,
) -> None:
    story.given("palettable is installed but the cache is empty")
    fake_module = SimpleNamespace(__path__=())
    monkeypatch.setitem(sys.modules, "palettable", fake_module)
    monkeypatch.setenv("SIMPLE_RESUME_PALETTE_CACHE_DIR", str(tmp_path))

    discovered = [
        PalettableRecord(
            name="Aurora",
            module="palettable.aurora",
            attribute="AURORA",
            category="misc",
            palette_type="diverging",
            size=6,
        )
    ]

    with (
        patch(
            "simple_resume.shell.palettes.loader.load_cached_palettable",
            return_value=[],
        ),
        patch(
            "simple_resume.shell.palettes.loader.discover_palettable",
            return_value=discovered,
        ) as mock_discover,
        patch("simple_resume.shell.palettes.loader.save_palettable_cache") as mock_save,
    ):
        records = ensure_palettable_loaded()

    story.then("records are discovered and saved to the cache directory")
    assert records == discovered
    mock_discover.assert_called_once()
    mock_save.assert_called_once_with(discovered)


def test_load_palettable_palette_normalises_hex_colors(
    monkeypatch: pytest.MonkeyPatch, story: Scenario
) -> None:
    story.given("a palettable record references colours without the leading hash")

    class FakePalette:
        name = "Ocean"
        type = "sequential"
        colors = ["FFAA00", "#112233"]
        hex_colors = ["FFAA00", "#112233"]

    fake_module = SimpleNamespace(OCEAN=FakePalette)
    monkeypatch.setitem(sys.modules, "palettable.fake", fake_module)
    record = PalettableRecord(
        name="Ocean",
        module="palettable.fake",
        attribute="OCEAN",
        category="sequential",
        palette_type="sequential",
        size=2,
    )

    with patch(
        "simple_resume.core.palettes.sources.import_module", return_value=fake_module
    ):
        palette = load_palettable_palette(record)

    story.then("the palette converts colours to #RRGGBB format and exposes metadata")
    assert palette is not None
    assert palette.swatches == ("#FFAA00", "#112233")
    assert palette.metadata["category"] == "sequential"


def test_load_palettable_palette_handles_exceptions(story: Scenario) -> None:
    story.given("importing the palette module raises an exception")
    record = PalettableRecord(
        name="Broken",
        module="palettable.broken",
        attribute="BROKEN",
        category="misc",
        palette_type="qualitative",
        size=3,
    )

    with patch(
        "simple_resume.core.palettes.sources.import_module",
        side_effect=RuntimeError("boom"),
    ):
        palette = load_palettable_palette(record)

    story.then("the loader returns None when errors occur")
    assert palette is None


def test_build_palettable_registry_snapshot_uses_loaded_records(
    story: Scenario,
) -> None:
    story.given("the registry builder receives discovered palettable records")
    records = [
        PalettableRecord(
            name="Forest",
            module="palettable.forest",
            attribute="FOREST",
            category="nature",
            palette_type="qualitative",
            size=4,
        )
    ]

    with patch(
        "simple_resume.shell.palettes.loader.discover_palettable",
        return_value=records,
    ):
        snapshot = build_palettable_registry_snapshot()

    story.then(
        "the snapshot references the record metadata and includes timing information"
    )
    assert snapshot["count"] == 1
    palettes = cast(list[dict[str, Any]], snapshot["palettes"])
    assert palettes
    first = palettes[0]
    assert first["name"] == "Forest"
    generated_at = snapshot["generated_at"]
    assert isinstance(generated_at, (int, float))
    assert generated_at > 0


def test_colourlovers_fetch_http_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, story: Scenario
) -> None:
    story.given("ColourLovers responds with an HTTP error")
    monkeypatch.setenv("SIMPLE_RESUME_ENABLE_REMOTE_PALETTES", "1")
    monkeypatch.setenv("SIMPLE_RESUME_PALETTE_CACHE_DIR", str(tmp_path))
    client = ColourLoversClient()

    headers = Message()
    http_error = HTTPError(
        url="https://www.colourlovers.com/api/palettes",
        code=503,
        msg="service unavailable",
        hdrs=headers,
        fp=None,
    )

    with patch("simple_resume.shell.palettes.remote.urlopen", side_effect=http_error):
        with pytest.raises(PaletteRemoteError, match="request failed"):
            client.fetch(num_results=1)

    story.then("PaletteRemoteError is propagated to the caller")


def test_colourlovers_fetch_invalid_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, story: Scenario
) -> None:
    story.given("ColourLovers returns an invalid JSON payload")
    monkeypatch.setenv("SIMPLE_RESUME_ENABLE_REMOTE_PALETTES", "1")
    monkeypatch.setenv("SIMPLE_RESUME_PALETTE_CACHE_DIR", str(tmp_path))
    client = ColourLoversClient()

    mock_response = Mock()
    mock_response.read.return_value = b"not-json"
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)

    with patch(
        "simple_resume.shell.palettes.remote.urlopen", return_value=mock_response
    ):
        with pytest.raises(PaletteRemoteError, match="invalid JSON"):
            client.fetch(num_results=1)

    story.then("a PaletteRemoteError is raised when JSON decoding fails")


def test_colourlovers_cache_key_uses_blake2b(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, story: Scenario
) -> None:
    story.given("ColourLovers cache keys are derived from request parameters")
    monkeypatch.setenv("SIMPLE_RESUME_PALETTE_CACHE_DIR", str(tmp_path))
    client = ColourLoversClient()

    params = {
        "format": "json",
        "numResults": 5,
        "orderCol": "new",
        "keywords": "ocean",
    }

    cache_path = client._cache_key(params)
    encoded = urlencode(sorted((key, str(value)) for key, value in params.items()))
    expected_digest = hashlib.blake2b(encoded.encode("utf-8")).hexdigest()

    story.then("the cache filename uses a BLAKE2b digest and resides in the cache dir")
    assert cache_path.name == f"{expected_digest}.json"
    assert cache_path.parent == tmp_path / "colourlovers"


def test_load_palettable_palette_from_core_with_hex_colors(
    monkeypatch: pytest.MonkeyPatch, story: Scenario
) -> None:
    story.given("a palettable palette object with hex_colors attribute")

    class FakePalette:
        hex_colors = ["#FF5733", "#33FF57"]

    fake_module = SimpleNamespace(TestPalette=FakePalette)
    monkeypatch.setitem(sys.modules, "palettable.test", fake_module)

    record = PalettableRecord(
        name="TestPalette",
        module="palettable.test",
        attribute="TestPalette",
        category="test",
        palette_type="qualitative",
        size=2,
    )

    story.when("load_palettable_palette is called from core")
    palette = load_palettable_palette(record)

    story.then("it returns a Palette with swatches and metadata")
    assert palette is not None
    assert palette.name == "TestPalette"
    assert palette.swatches == ("#FF5733", "#33FF57")
    assert palette.source == "palettable"
    assert palette.metadata["category"] == "test"
    assert palette.metadata["palette_type"] == "qualitative"
    assert palette.metadata["size"] == 2


def test_load_palettable_palette_with_colors_fallback(
    monkeypatch: pytest.MonkeyPatch, story: Scenario
) -> None:
    story.given("a palettable palette with colors but not hex_colors")

    class FakePalette:
        colors = ["AABBCC", "DDEEFF"]

    fake_module = SimpleNamespace(ColorsPalette=FakePalette)
    monkeypatch.setitem(sys.modules, "palettable.colors", fake_module)

    record = PalettableRecord(
        name="ColorsPalette",
        module="palettable.colors",
        attribute="ColorsPalette",
        category="misc",
        palette_type="sequential",
        size=2,
    )

    story.when("load_palettable_palette is called")
    palette = load_palettable_palette(record)

    story.then("it falls back to colors attribute and normalizes hex format")
    assert palette is not None
    assert palette.swatches == ("#AABBCC", "#DDEEFF")


def test_load_palettable_palette_returns_none_when_no_colors(
    monkeypatch: pytest.MonkeyPatch, story: Scenario
) -> None:
    story.given("a palettable palette with empty colors")

    class EmptyPalette:
        hex_colors: list[str] = []
        colors: list[tuple[int, int, int]] = []

    fake_module = SimpleNamespace(EmptyPal=EmptyPalette)
    monkeypatch.setitem(sys.modules, "palettable.empty", fake_module)

    record = PalettableRecord(
        name="EmptyPal",
        module="palettable.empty",
        attribute="EmptyPal",
        category="test",
        palette_type="sequential",
        size=0,
    )

    story.when("load_palettable_palette is called")
    palette = load_palettable_palette(record)

    story.then("it returns None when palette has no colors")
    assert palette is None


def test_load_palettable_palette_returns_none_on_import_error(
    story: Scenario,
) -> None:
    story.given("a record pointing to a non-existent module")

    record = PalettableRecord(
        name="NonExistent",
        module="palettable.nonexistent.module",
        attribute="SomePalette",
        category="test",
        palette_type="qualitative",
        size=5,
    )

    story.when("load_palettable_palette is called")
    palette = load_palettable_palette(record)

    story.then("it returns None when module import fails")
    assert palette is None


def test_load_palettable_palette_returns_none_on_attribute_error(
    monkeypatch: pytest.MonkeyPatch, story: Scenario
) -> None:
    story.given("a module that exists but doesn't have the attribute")

    fake_module = SimpleNamespace()  # No palette attribute
    monkeypatch.setitem(sys.modules, "palettable.noattr", fake_module)

    record = PalettableRecord(
        name="MissingAttr",
        module="palettable.noattr",
        attribute="NonExistentPalette",
        category="test",
        palette_type="sequential",
        size=3,
    )

    story.when("load_palettable_palette is called")
    palette = load_palettable_palette(record)

    story.then("it returns None when attribute doesn't exist")
    assert palette is None


def test_cache_path_returns_correct_path(story: Scenario) -> None:
    story.given("a cache filename")
    filename = "test_cache.json"

    story.when("_cache_path is called")
    result = _cache_path(filename)

    story.then("it returns the path in ~/.cache/simple_resume/")
    expected = Path.home() / ".cache" / "simple_resume" / filename
    assert result == expected
    assert result.name == filename
