from __future__ import annotations

import sys
from email.message import Message
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock, patch
from urllib.error import HTTPError

import pytest

from simple_resume.palettes.common import Palette
from simple_resume.palettes.exceptions import PaletteRemoteError
from simple_resume.palettes.sources import (
    ColourLoversClient,
    PalettableRecord,
    build_palettable_registry_snapshot,
    ensure_bundled_palettes_loaded,
    load_default_palettes,
    load_palettable_palette,
)


def test_load_default_palettes_returns_palettes(story) -> None:
    story.given("the bundled default palettes file is present")
    palettes = load_default_palettes()

    story.then("at least one palette is loaded with hex swatches")
    assert palettes
    assert isinstance(palettes[0], Palette)
    assert palettes[0].swatches
    assert all(color.startswith("#") for color in palettes[0].swatches)


def test_load_default_palettes_handles_missing_file(tmp_path: Path, story) -> None:
    story.given("the default palette file cannot be found")
    missing_file = tmp_path / "missing.json"

    with patch(
        "simple_resume.palettes.sources._default_file", return_value=missing_file
    ):
        palettes = load_default_palettes()

    story.then("the loader falls back to an empty list")
    assert palettes == []


def test_ensure_bundled_palettes_returns_cached_records(
    monkeypatch: pytest.MonkeyPatch, story
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
            "simple_resume.palettes.sources._load_cached_palettable",
            return_value=cached,
        ),
        patch("simple_resume.palettes.sources._discover_palettable") as mock_discover,
    ):
        records = ensure_bundled_palettes_loaded()

    story.then("cached metadata is returned without re-discovery")
    assert records == cached
    mock_discover.assert_not_called()


def test_ensure_bundled_palettes_discovers_when_cache_empty(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    story,
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
            "simple_resume.palettes.sources._load_cached_palettable", return_value=[]
        ),
        patch(
            "simple_resume.palettes.sources._discover_palettable",
            return_value=discovered,
        ) as mock_discover,
        patch("simple_resume.palettes.sources._save_palettable") as mock_save,
    ):
        records = ensure_bundled_palettes_loaded()

    story.then("records are discovered and saved to the cache directory")
    assert records == discovered
    mock_discover.assert_called_once()
    mock_save.assert_called_once_with(discovered)


def test_load_palettable_palette_normalises_hex_colors(
    monkeypatch: pytest.MonkeyPatch, story
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
        "simple_resume.palettes.sources.import_module", return_value=fake_module
    ):
        palette = load_palettable_palette(record)

    story.then("the palette converts colours to #RRGGBB format and exposes metadata")
    assert palette is not None
    assert palette.swatches == ("#FFAA00", "#112233")
    assert palette.metadata["category"] == "sequential"


def test_load_palettable_palette_handles_exceptions(story) -> None:
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
        "simple_resume.palettes.sources.import_module", side_effect=RuntimeError("boom")
    ):
        palette = load_palettable_palette(record)

    story.then("the loader returns None when errors occur")
    assert palette is None


def test_build_palettable_registry_snapshot_uses_loaded_records(story) -> None:
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
        "simple_resume.palettes.sources.ensure_bundled_palettes_loaded",
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
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, story
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

    with patch("simple_resume.palettes.sources.urlopen", side_effect=http_error):
        with pytest.raises(PaletteRemoteError, match="request failed"):
            client.fetch(num_results=1)

    story.then("PaletteRemoteError is propagated to the caller")


def test_colourlovers_fetch_invalid_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, story
) -> None:
    story.given("ColourLovers returns an invalid JSON payload")
    monkeypatch.setenv("SIMPLE_RESUME_ENABLE_REMOTE_PALETTES", "1")
    monkeypatch.setenv("SIMPLE_RESUME_PALETTE_CACHE_DIR", str(tmp_path))
    client = ColourLoversClient()

    mock_response = Mock()
    mock_response.read.return_value = b"not-json"
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)

    with patch("simple_resume.palettes.sources.urlopen", return_value=mock_response):
        with pytest.raises(PaletteRemoteError, match="invalid JSON"):
            client.fetch(num_results=1)

    story.then("a PaletteRemoteError is raised when JSON decoding fails")
