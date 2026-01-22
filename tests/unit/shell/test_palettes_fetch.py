"""Test shell layer palette fetching with network I/O."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from simple_resume.core.exceptions import PaletteLookupError
from simple_resume.core.palettes import PaletteFetchRequest
from simple_resume.shell.palettes.fetch import execute_palette_fetch


class TestExecutePaletteFetch:
    """Test palette fetch execution in the shell layer."""

    def test_execute_palette_fetch_unsupported_source(self) -> None:
        """Test fetch with unsupported source raises error."""
        request = PaletteFetchRequest(
            source="unsupported",
            keywords=["test"],
            num_results=1,
            order_by="popular",
        )

        with pytest.raises(PaletteLookupError) as exc_info:
            execute_palette_fetch(request)

        assert "Unsupported remote source: unsupported" in str(exc_info.value)

    @patch("simple_resume.shell.palettes.fetch.ColourLoversClient")
    def test_execute_palette_fetch_success(self, mock_client_class: MagicMock) -> None:
        """Test successful palette fetch."""
        # Mock palette object
        mock_palette = MagicMock()
        mock_palette.name = "Ocean Breeze"
        mock_palette.swatches = ["#001122", "#003344", "#005566", "#007788"]
        mock_palette.metadata = {"url": "https://colourlovers.com/palette/123"}

        # Mock client
        mock_client = MagicMock()
        mock_client.fetch.return_value = [mock_palette]
        mock_client_class.return_value = mock_client

        request = PaletteFetchRequest(
            source="colourlovers",
            keywords=["ocean", "blue"],
            num_results=5,
            order_by="popular",
        )

        colors, metadata = execute_palette_fetch(request)

        assert colors == ["#001122", "#003344", "#005566", "#007788"]
        assert metadata == {
            "source": "colourlovers",
            "name": "Ocean Breeze",
            "attribution": {"url": "https://colourlovers.com/palette/123"},
            "size": 4,
        }

        mock_client_class.assert_called_once()
        mock_client.fetch.assert_called_once_with(
            keywords="ocean,blue",
            num_results=5,
            order_by="popular",
        )

    @patch("simple_resume.shell.palettes.fetch.ColourLoversClient")
    def test_execute_palette_fetch_no_keywords(
        self, mock_client_class: MagicMock
    ) -> None:
        """Test palette fetch without keywords."""
        mock_palette = MagicMock()
        mock_palette.name = "Random Palette"
        mock_palette.swatches = ["#FF0000", "#00FF00", "#0000FF"]
        mock_palette.metadata = {"url": "https://colourlovers.com/palette/456"}

        mock_client = MagicMock()
        mock_client.fetch.return_value = [mock_palette]
        mock_client_class.return_value = mock_client

        request = PaletteFetchRequest(
            source="colourlovers",
            keywords=[],
            num_results=10,
            order_by="newest",
        )

        colors, metadata = execute_palette_fetch(request)

        assert colors == ["#FF0000", "#00FF00", "#0000FF"]
        assert metadata["source"] == "colourlovers"
        assert metadata["name"] == "Random Palette"

        mock_client.fetch.assert_called_once_with(
            keywords=None,
            num_results=10,
            order_by="newest",
        )

    @patch("simple_resume.shell.palettes.fetch.ColourLoversClient")
    def test_execute_palette_fetch_multiple_palettes(
        self, mock_client_class: MagicMock
    ) -> None:
        """Test palette fetch returns first palette from multiple results."""
        # Create multiple mock palettes
        mock_palette1 = MagicMock()
        mock_palette1.name = "First Palette"
        mock_palette1.swatches = ["#111111", "#222222"]
        mock_palette1.metadata = {"id": 1}

        mock_palette2 = MagicMock()
        mock_palette2.name = "Second Palette"
        mock_palette2.swatches = ["#333333", "#444444"]
        mock_palette2.metadata = {"id": 2}

        mock_client = MagicMock()
        mock_client.fetch.return_value = [mock_palette1, mock_palette2]
        mock_client_class.return_value = mock_client

        request = PaletteFetchRequest(
            source="colourlovers",
            keywords=["test"],
            num_results=3,
            order_by="popular",
        )

        colors, metadata = execute_palette_fetch(request)

        # Should return the first palette only
        assert colors == ["#111111", "#222222"]
        assert metadata["name"] == "First Palette"
        assert metadata["size"] == 2

    @patch("simple_resume.shell.palettes.fetch.ColourLoversClient")
    def test_execute_palette_fetch_no_results(
        self, mock_client_class: MagicMock
    ) -> None:
        """Test palette fetch with no results raises error."""
        mock_client = MagicMock()
        mock_client.fetch.return_value = []  # No palettes found
        mock_client_class.return_value = mock_client

        request = PaletteFetchRequest(
            source="colourlovers",
            keywords=["nonexistent"],
            num_results=5,
            order_by="popular",
        )

        with pytest.raises(PaletteLookupError) as exc_info:
            execute_palette_fetch(request)

        assert "No palettes found for keywords: ['nonexistent']" in str(exc_info.value)

    @patch("simple_resume.shell.palettes.fetch.ColourLoversClient")
    def test_execute_palette_fetch_remote_source(
        self, mock_client_class: MagicMock
    ) -> None:
        """Test palette fetch with 'remote' source alias."""
        mock_palette = MagicMock()
        mock_palette.name = "Remote Palette"
        mock_palette.swatches = ["#AA11BB", "#CC22DD"]
        mock_palette.metadata = {"source": "remote_api"}

        mock_client = MagicMock()
        mock_client.fetch.return_value = [mock_palette]
        mock_client_class.return_value = mock_client

        request = PaletteFetchRequest(
            source="remote",
            keywords=["remote"],
            num_results=1,
            order_by="latest",
        )

        colors, metadata = execute_palette_fetch(request)

        assert colors == ["#AA11BB", "#CC22DD"]
        assert metadata["source"] == "remote"  # Should preserve original source

    @patch("simple_resume.shell.palettes.fetch.ColourLoversClient")
    def test_execute_palette_fetch_empty_swatches(
        self, mock_client_class: MagicMock
    ) -> None:
        """Test palette fetch with empty swatches list."""
        mock_palette = MagicMock()
        mock_palette.name = "Empty Palette"
        mock_palette.swatches = []  # Empty list
        mock_palette.metadata = {"id": 789}

        mock_client = MagicMock()
        mock_client.fetch.return_value = [mock_palette]
        mock_client_class.return_value = mock_client

        request = PaletteFetchRequest(
            source="colourlovers",
            keywords=["empty"],
            num_results=1,
            order_by="popular",
        )

        colors, metadata = execute_palette_fetch(request)

        assert colors == []  # Should return empty list
        assert metadata["size"] == 0
        assert metadata["name"] == "Empty Palette"
