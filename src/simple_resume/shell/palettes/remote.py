"""Remote palette providers that perform network I/O."""

from __future__ import annotations

import hashlib
import json
import os
import time
from collections.abc import Mapping
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from simple_resume.core.palettes.common import Palette, get_cache_dir
from simple_resume.core.palettes.exceptions import (
    PaletteRemoteDisabled,
    PaletteRemoteError,
)

COLOURLOVERS_FLAG = "SIMPLE_RESUME_ENABLE_REMOTE_PALETTES"
COLOURLOVERS_CACHE_TTL_SECONDS = 60 * 60 * 12  # 12 hours


def _validate_url(url: str) -> None:
    """Raise if the provided URL uses an unsafe scheme."""
    parsed = urlparse(url)
    allowed_schemes = {"https", "http"}

    if parsed.scheme in {"file", "ftp", "data", "javascript", "mailto"}:
        raise PaletteRemoteError(f"Dangerous URL scheme blocked: {parsed.scheme}")

    if parsed.scheme not in allowed_schemes:
        raise PaletteRemoteError(
            f"Unsafe URL scheme: {parsed.scheme}. "
            f"Only allowed schemes are: {', '.join(sorted(allowed_schemes))}"
        )


def _create_safe_request(url: str, headers: dict[str, str]) -> Request:
    """Return a validated HTTP request object."""
    _validate_url(url)
    return Request(url, headers=headers)  # noqa: S310


class ColourLoversClient:
    """Thin wrapper around the ColourLovers palette API."""

    API_BASE = "https://www.colourlovers.com/api/palettes"

    def __init__(
        self,
        *,
        cache_ttl: int = COLOURLOVERS_CACHE_TTL_SECONDS,
        enable_flag: str = COLOURLOVERS_FLAG,
    ) -> None:
        """Initialize the ColourLoversClient.

        Args:
            cache_ttl: Time-to-live for cached palette data in seconds
            enable_flag: Environment variable flag to enable the client

        """
        self.cache_dir = get_cache_dir() / "colourlovers"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = cache_ttl
        self.enable_flag = enable_flag

    def _is_enabled(self) -> bool:
        """Check if remote palette fetching is enabled via environment variable."""
        return os.environ.get(self.enable_flag, "").lower() in {"1", "true", "yes"}

    def _cache_key(self, params: Mapping[str, object]) -> Path:
        """Generate a cache key (file path) for given request parameters."""
        encoded = urlencode(sorted((key, str(value)) for key, value in params.items()))
        digest = hashlib.blake2b(encoded.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.json"

    def _read_cache(self, path: Path) -> list[dict[str, object]] | None:
        """Read cached data from a file if not expired.

        Args:
            path: Path to the cache file.

        Returns:
            Cached data as a list of dictionaries, or None if no cache or expired.

        """
        if not path.exists():
            return None
        if time.time() - path.stat().st_mtime > self.cache_ttl:
            return None
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, list) else None

    def _write_cache(self, path: Path, payload: list[dict[str, object]]) -> None:
        """Write data to a cache file.

        Args:
            path: Path to the cache file.
            payload: Data to write to the cache file.

        """
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle)

    def fetch(
        self,
        *,
        lover_id: int | None = None,
        keywords: str | None = None,
        num_results: int = 20,
        order_by: str = "score",
    ) -> list[Palette]:
        """Fetch palettes from the ColourLovers API."""
        if not self._is_enabled():
            raise PaletteRemoteDisabled(
                "Remote palettes disabled. "
                "Set SIMPLE_RESUME_ENABLE_REMOTE_PALETTES=1 to opt in."
            )

        params: dict[str, object] = {
            "format": "json",
            "numResults": num_results,
            "orderCol": order_by,
        }
        if lover_id is not None:
            params["loverID"] = lover_id
        if keywords:
            params["keywords"] = keywords

        cache_path = self._cache_key(params)
        cached = self._read_cache(cache_path)
        if cached is not None:
            return [self._palette_from_payload(entry) for entry in cached]

        url = f"{self.API_BASE}?{urlencode(params)}"
        request = _create_safe_request(url, {"User-Agent": "simple-resume/0.1"})
        try:
            with urlopen(request, timeout=10) as response:  # noqa: S310  # nosec B310
                data = response.read()
        except (HTTPError, URLError) as exc:
            raise PaletteRemoteError(f"ColourLovers request failed: {exc}") from exc

        try:
            payload = json.loads(data.decode("utf-8"))
        except ValueError as exc:
            raise PaletteRemoteError("ColourLovers returned invalid JSON") from exc

        palettes = [self._palette_from_payload(entry) for entry in payload]
        self._write_cache(cache_path, payload)
        return palettes

    @staticmethod
    def _palette_from_payload(payload: Mapping[str, object]) -> Palette:
        raw_colors = payload.get("colors") or []
        if not isinstance(raw_colors, (list, tuple)):
            colors: list[object] = []
        else:
            colors = list(raw_colors)

        metadata = {
            "source_url": payload.get("url"),
            "id": payload.get("id"),
            "author": payload.get("userName"),
        }
        return Palette(
            name=str(payload.get("title", "ColourLovers Palette")),
            swatches=tuple(
                f"#{color}" if not str(color).startswith("#") else str(color)
                for color in colors
            ),
            source="colourlovers",
            metadata=metadata,
        )


__all__ = ["ColourLoversClient"]
