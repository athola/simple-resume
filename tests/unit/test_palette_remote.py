from __future__ import annotations

import json
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from simple_resume.palettes.exceptions import PaletteRemoteDisabled
from simple_resume.palettes.sources import ColourLoversClient


@pytest.fixture
def palette_cache_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    cache = tmp_path / "cache"
    monkeypatch.setenv("SIMPLE_RESUME_PALETTE_CACHE_DIR", str(cache))
    monkeypatch.setenv("SIMPLE_RESUME_ENABLE_REMOTE_PALETTES", "1")
    return cache


def _mock_response(payload: list[dict[str, object]]) -> Mock:
    data = json.dumps(payload).encode("utf-8")
    mock_response = Mock()
    mock_response.read.return_value = data
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=False)
    return mock_response


def test_colourlovers_client_fetches_and_caches(story, palette_cache_dir: Path) -> None:
    payload = [
        {
            "title": "Sunset",
            "colors": ["FFAA00", "FF5500"],
            "url": "https://colourlovers.com/palette/1",
            "id": 1,
            "userName": "tester",
        }
    ]

    colourlovers_cache = palette_cache_dir / "colourlovers"
    if colourlovers_cache.exists():
        shutil.rmtree(colourlovers_cache)

    with patch(
        "simple_resume.palettes.sources.urlopen", return_value=_mock_response(payload)
    ) as mock_urlopen:
        story.given("ColourLovers remote palettes are enabled and cache is empty")
        client = ColourLoversClient()
        palettes = client.fetch(num_results=1)

        story.then("a network call occurs and palettes are normalised to hex strings")
        assert len(palettes) == 1
        assert palettes[0].swatches[0].startswith("#")
        mock_urlopen.assert_called_once()

        story.when("fetching again with the populated cache")
        palettes = client.fetch(num_results=1)

        story.then("no additional network calls are performed")
        assert len(palettes) == 1
        assert mock_urlopen.call_count == 1
        cache_files = list((palette_cache_dir / "colourlovers").rglob("*.json"))
        assert cache_files, "Expected cache file to be written"


def test_colourlovers_disabled_by_default(
    story, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("SIMPLE_RESUME_ENABLE_REMOTE_PALETTES", raising=False)
    client = ColourLoversClient()
    story.given("remote palettes are disabled")
    with pytest.raises(PaletteRemoteDisabled):
        client.fetch()
