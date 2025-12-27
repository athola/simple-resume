"""Test remote palette providers with network I/O mocking."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

import pytest

from simple_resume.core.palettes.exceptions import (
    PaletteRemoteDisabled,
    PaletteRemoteError,
)
from simple_resume.shell.palettes.remote import (
    ColourLoversClient,
    _create_safe_request,
    _validate_url,
)


class TestValidateUrl:
    """Test URL validation for security."""

    def test_validate_url_https(self) -> None:
        """Test that HTTPS URLs are allowed."""
        _validate_url("https://example.com/api")  # Should not raise

    def test_validate_url_http(self) -> None:
        """Test that HTTP URLs are allowed."""
        _validate_url("http://example.com/api")  # Should not raise

    def test_validate_url_file_scheme(self) -> None:
        """Test that file:// scheme is blocked."""
        with pytest.raises(PaletteRemoteError) as exc_info:
            _validate_url("file:///etc/passwd")
        assert "Dangerous URL scheme blocked: file" in str(exc_info.value)

    def test_validate_url_ftp_scheme(self) -> None:
        """Test that ftp:// scheme is blocked."""
        with pytest.raises(PaletteRemoteError) as exc_info:
            _validate_url("ftp://example.com/file")
        assert "Dangerous URL scheme blocked: ftp" in str(exc_info.value)

    def test_validate_url_data_scheme(self) -> None:
        """Test that data: scheme is blocked."""
        with pytest.raises(PaletteRemoteError) as exc_info:
            _validate_url("data:text/plain,hello")
        assert "Dangerous URL scheme blocked: data" in str(exc_info.value)

    def test_validate_url_javascript_scheme(self) -> None:
        """Test that javascript: scheme is blocked."""
        with pytest.raises(PaletteRemoteError) as exc_info:
            _validate_url("javascript:alert(1)")
        assert "Dangerous URL scheme blocked: javascript" in str(exc_info.value)

    def test_validate_url_mailto_scheme(self) -> None:
        """Test that mailto: scheme is blocked."""
        with pytest.raises(PaletteRemoteError) as exc_info:
            _validate_url("mailto:user@example.com")
        assert "Dangerous URL scheme blocked: mailto" in str(exc_info.value)

    def test_validate_url_unknown_scheme(self) -> None:
        """Test that unknown schemes are rejected."""
        with pytest.raises(PaletteRemoteError) as exc_info:
            _validate_url("gopher://example.com")
        assert "Unsafe URL scheme: gopher" in str(exc_info.value)
        assert "Only allowed schemes are: http, https" in str(exc_info.value)


class TestCreateSafeRequest:
    """Test safe request creation."""

    def test_create_safe_request_valid_url(self) -> None:
        """Test creating a safe request with valid URL."""
        request = _create_safe_request(
            "https://example.com/api",
            {"User-Agent": "test"},
        )
        assert request.full_url == "https://example.com/api"
        assert request.headers["User-agent"] == "test"

    def test_create_safe_request_invalid_url(self) -> None:
        """Test that invalid URLs raise error."""
        with pytest.raises(PaletteRemoteError):
            _create_safe_request("file:///etc/passwd", {})


class TestColourLoversClient:
    """Test ColourLoversClient class."""

    @patch.dict("os.environ", {}, clear=True)
    def test_is_enabled_false_default(self) -> None:
        """Test that remote palettes are disabled by default."""
        client = ColourLoversClient()
        assert not client._is_enabled()

    @patch.dict("os.environ", {"SIMPLE_RESUME_ENABLE_REMOTE_PALETTES": "1"})
    def test_is_enabled_true_with_1(self) -> None:
        """Test that '1' enables remote palettes."""
        client = ColourLoversClient()
        assert client._is_enabled()

    @patch.dict("os.environ", {"SIMPLE_RESUME_ENABLE_REMOTE_PALETTES": "true"})
    def test_is_enabled_true_with_true(self) -> None:
        """Test that 'true' enables remote palettes."""
        client = ColourLoversClient()
        assert client._is_enabled()

    @patch.dict("os.environ", {"SIMPLE_RESUME_ENABLE_REMOTE_PALETTES": "yes"})
    def test_is_enabled_true_with_yes(self) -> None:
        """Test that 'yes' enables remote palettes."""
        client = ColourLoversClient()
        assert client._is_enabled()

    @patch.dict("os.environ", {"SIMPLE_RESUME_ENABLE_REMOTE_PALETTES": "0"})
    def test_is_enabled_false_with_0(self) -> None:
        """Test that '0' disables remote palettes."""
        client = ColourLoversClient()
        assert not client._is_enabled()

    @patch.dict("os.environ", {}, clear=True)
    def test_fetch_disabled(self) -> None:
        """Test that fetch raises error when disabled."""
        client = ColourLoversClient()
        with pytest.raises(PaletteRemoteDisabled) as exc_info:
            client.fetch()
        assert "Remote palettes disabled" in str(exc_info.value)
        assert "SIMPLE_RESUME_ENABLE_REMOTE_PALETTES=1" in str(exc_info.value)

    def test_cache_key_generation(self) -> None:
        """Test that cache keys are generated consistently."""
        client = ColourLoversClient()
        params1 = {"format": "json", "numResults": 10}
        params2 = {"numResults": 10, "format": "json"}  # Different order

        key1 = client._cache_key(params1)
        key2 = client._cache_key(params2)

        # Same params should generate same key regardless of order
        assert key1 == key2
        assert key1.suffix == ".json"

    @patch("simple_resume.shell.palettes.remote.Path.exists")
    def test_read_cache_missing_file(self, mock_exists: MagicMock) -> None:
        """Test reading cache when file doesn't exist."""
        mock_exists.return_value = False
        client = ColourLoversClient()
        result = client._read_cache(Path("/fake/cache.json"))
        assert result is None

    @patch("simple_resume.shell.palettes.remote.time.time")
    def test_read_cache_expired(self, mock_time: MagicMock) -> None:
        """Test reading cache when file is expired."""
        mock_time.return_value = 1000000  # Current time

        # Mock path object with exists and stat
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True

        # Mock file stat with old mtime (expired)
        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mtime = 900000  # 100000 seconds old
        mock_path.stat.return_value = mock_stat_obj

        client = ColourLoversClient(cache_ttl=50000)  # 50000 second TTL
        result = client._read_cache(mock_path)

        # Should return None because cache is expired (100000 > 50000)
        assert result is None

    @patch("simple_resume.shell.palettes.remote.time.time")
    def test_read_cache_valid(self, mock_time: MagicMock) -> None:
        """Test reading valid cache."""
        mock_time.return_value = 1000000  # Current time

        # Mock path object
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True

        # Mock file stat with recent mtime
        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mtime = 999000  # 1000 seconds old
        mock_path.stat.return_value = mock_stat_obj

        # Mock the file open and read
        mock_file_content = '[{"test": "data"}]'
        mock_file_handle = mock_path.open.return_value.__enter__.return_value
        mock_file_handle.read.return_value = mock_file_content

        client = ColourLoversClient(cache_ttl=50000)  # 50000 second TTL
        result = client._read_cache(mock_path)

        # Should return cached data because it's not expired (1000 < 50000)
        assert result == [{"test": "data"}]

    @patch("simple_resume.shell.palettes.remote.time.time")
    def test_read_cache_invalid_format(self, mock_time: MagicMock) -> None:
        """Test reading cache with invalid format returns None."""
        mock_time.return_value = 1000000

        # Mock path object
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True

        mock_stat_obj = MagicMock()
        mock_stat_obj.st_mtime = 999000
        mock_path.stat.return_value = mock_stat_obj

        # Mock file with non-list JSON data
        mock_file_content = '{"not": "list"}'
        mock_file_handle = mock_path.open.return_value.__enter__.return_value
        mock_file_handle.read.return_value = mock_file_content

        client = ColourLoversClient(cache_ttl=50000)
        result = client._read_cache(mock_path)

        # Should return None because data is not a list
        assert result is None

    def test_write_cache(self) -> None:
        """Test writing cache."""
        client = ColourLoversClient()
        test_data = [{"id": 1, "colors": ["#FF0000"]}]

        # Mock path object
        mock_path = MagicMock(spec=Path)
        mock_file_handle = MagicMock()
        mock_path.open.return_value.__enter__.return_value = mock_file_handle

        client._write_cache(mock_path, test_data)

        # Verify file was opened for writing
        mock_path.open.assert_called_once_with("w", encoding="utf-8")

    @patch.dict("os.environ", {"SIMPLE_RESUME_ENABLE_REMOTE_PALETTES": "1"})
    @patch("simple_resume.shell.palettes.remote.ColourLoversClient._read_cache")
    @patch("simple_resume.shell.palettes.remote.ColourLoversClient._write_cache")
    @patch("simple_resume.shell.palettes.remote.urlopen")
    def test_fetch_with_lover_id(
        self,
        mock_urlopen: MagicMock,
        mock_write_cache: MagicMock,
        mock_read_cache: MagicMock,
    ) -> None:
        """Test fetch with lover_id parameter."""
        # No cached data
        mock_read_cache.return_value = None

        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            [
                {
                    "id": 123,
                    "title": "Test Palette",
                    "colors": ["FF0000", "00FF00"],
                    "url": "https://colourlovers.com/palette/123",
                    "userName": "testuser",
                }
            ]
        ).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = ColourLoversClient()
        palettes = client.fetch(lover_id=42, num_results=10)

        assert len(palettes) == 1
        assert palettes[0].name == "Test Palette"

        # Verify lover_id was included in the request
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert "loverID=42" in request.full_url

    @patch.dict("os.environ", {"SIMPLE_RESUME_ENABLE_REMOTE_PALETTES": "1"})
    @patch("simple_resume.shell.palettes.remote.ColourLoversClient._read_cache")
    @patch("simple_resume.shell.palettes.remote.ColourLoversClient._write_cache")
    @patch("simple_resume.shell.palettes.remote.urlopen")
    def test_fetch_with_keywords(
        self,
        mock_urlopen: MagicMock,
        mock_write_cache: MagicMock,
        mock_read_cache: MagicMock,
    ) -> None:
        """Test fetch with keywords parameter."""
        # No cached data
        mock_read_cache.return_value = None

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            [
                {
                    "id": 456,
                    "title": "Ocean Theme",
                    "colors": ["0000FF"],
                    "url": "https://colourlovers.com/palette/456",
                    "userName": "oceanfan",
                }
            ]
        ).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = ColourLoversClient()
        palettes = client.fetch(keywords="ocean blue", num_results=5)

        assert len(palettes) == 1
        assert palettes[0].name == "Ocean Theme"

        # Verify keywords were included in the request
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert "keywords=ocean+blue" in request.full_url

    @patch.dict("os.environ", {"SIMPLE_RESUME_ENABLE_REMOTE_PALETTES": "1"})
    @patch("simple_resume.shell.palettes.remote.ColourLoversClient._read_cache")
    def test_fetch_from_cache(self, mock_read_cache: MagicMock) -> None:
        """Test that fetch returns cached data when available."""
        # Mock cached data
        cached_data = [
            {
                "id": 789,
                "title": "Cached Palette",
                "colors": ["AABBCC", "DDEEFF"],
                "url": "https://colourlovers.com/palette/789",
                "userName": "cacheuser",
            }
        ]
        mock_read_cache.return_value = cached_data

        client = ColourLoversClient()
        palettes = client.fetch(num_results=10)

        # Should return cached palettes
        assert len(palettes) == 1
        assert palettes[0].name == "Cached Palette"
        assert palettes[0].swatches == ("#AABBCC", "#DDEEFF")

    @patch.dict("os.environ", {"SIMPLE_RESUME_ENABLE_REMOTE_PALETTES": "1"})
    @patch("simple_resume.shell.palettes.remote.ColourLoversClient._write_cache")
    @patch("simple_resume.shell.palettes.remote.ColourLoversClient._read_cache")
    @patch("simple_resume.shell.palettes.remote.urlopen")
    def test_fetch_and_cache(
        self,
        mock_urlopen: MagicMock,
        mock_read_cache: MagicMock,
        mock_write_cache: MagicMock,
    ) -> None:
        """Test that fetch caches the response data."""
        # No cached data
        mock_read_cache.return_value = None

        # Mock HTTP response
        response_data = [
            {
                "id": 999,
                "title": "New Palette",
                "colors": ["112233"],
                "url": "https://colourlovers.com/palette/999",
                "userName": "newuser",
            }
        ]
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = ColourLoversClient()
        palettes = client.fetch(num_results=10)

        # Should return fetched palettes
        assert len(palettes) == 1
        assert palettes[0].name == "New Palette"

        # Verify cache was written
        mock_write_cache.assert_called_once()
        call_args = mock_write_cache.call_args
        cached_payload = call_args[0][1]
        assert cached_payload == response_data

    @patch.dict("os.environ", {"SIMPLE_RESUME_ENABLE_REMOTE_PALETTES": "1"})
    @patch("simple_resume.shell.palettes.remote.urlopen")
    def test_fetch_http_error(self, mock_urlopen: MagicMock) -> None:
        """Test that HTTP errors are handled properly."""
        mock_urlopen.side_effect = HTTPError(
            "https://example.com",
            404,
            "Not Found",
            {},
            None,
        )

        client = ColourLoversClient()
        with pytest.raises(PaletteRemoteError) as exc_info:
            client.fetch(num_results=10)

        assert "ColourLovers request failed" in str(exc_info.value)

    @patch.dict("os.environ", {"SIMPLE_RESUME_ENABLE_REMOTE_PALETTES": "1"})
    @patch("simple_resume.shell.palettes.remote.urlopen")
    def test_fetch_url_error(self, mock_urlopen: MagicMock) -> None:
        """Test that URL errors are handled properly."""
        mock_urlopen.side_effect = URLError("Connection refused")

        client = ColourLoversClient()
        with pytest.raises(PaletteRemoteError) as exc_info:
            client.fetch(num_results=10)

        assert "ColourLovers request failed" in str(exc_info.value)

    @patch.dict("os.environ", {"SIMPLE_RESUME_ENABLE_REMOTE_PALETTES": "1"})
    @patch("simple_resume.shell.palettes.remote.urlopen")
    def test_fetch_invalid_json(self, mock_urlopen: MagicMock) -> None:
        """Test that invalid JSON is handled properly."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"not valid json {{"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        client = ColourLoversClient()
        with pytest.raises(PaletteRemoteError) as exc_info:
            client.fetch(num_results=10)

        assert "invalid JSON" in str(exc_info.value)

    def test_palette_from_payload_basic(self) -> None:
        """Test creating palette from basic payload."""
        payload = {
            "id": 123,
            "title": "Test Palette",
            "colors": ["FF0000", "00FF00", "0000FF"],
            "url": "https://colourlovers.com/palette/123",
            "userName": "testuser",
        }

        palette = ColourLoversClient._palette_from_payload(payload)

        assert palette.name == "Test Palette"
        assert palette.swatches == ("#FF0000", "#00FF00", "#0000FF")
        assert palette.source == "colourlovers"
        assert palette.metadata["source_url"] == "https://colourlovers.com/palette/123"
        assert palette.metadata["id"] == 123
        assert palette.metadata["author"] == "testuser"

    def test_palette_from_payload_with_hash_prefix(self) -> None:
        """Test that colors already with # prefix are preserved."""
        payload = {
            "title": "Hash Palette",
            "colors": ["#AABBCC", "#DDEEFF"],
        }

        palette = ColourLoversClient._palette_from_payload(payload)

        assert palette.swatches == ("#AABBCC", "#DDEEFF")

    def test_palette_from_payload_missing_colors(self) -> None:
        """Test handling payload with missing colors."""
        payload = {
            "title": "No Colors",
        }

        palette = ColourLoversClient._palette_from_payload(payload)

        assert palette.swatches == ()
        assert palette.name == "No Colors"

    def test_palette_from_payload_invalid_colors_type(self) -> None:
        """Test handling payload with invalid colors type."""
        payload = {
            "title": "Invalid Colors",
            "colors": "not a list",  # Invalid type
        }

        palette = ColourLoversClient._palette_from_payload(payload)

        assert palette.swatches == ()

    def test_palette_from_payload_missing_title(self) -> None:
        """Test handling payload with missing title."""
        payload = {
            "colors": ["FF0000"],
        }

        palette = ColourLoversClient._palette_from_payload(payload)

        assert palette.name == "ColourLovers Palette"  # Default name

    def test_palette_from_payload_missing_metadata(self) -> None:
        """Test handling payload with missing metadata fields."""
        payload = {
            "title": "Minimal Palette",
            "colors": ["112233"],
        }

        palette = ColourLoversClient._palette_from_payload(payload)

        assert palette.metadata["source_url"] is None
        assert palette.metadata["id"] is None
        assert palette.metadata["author"] is None
