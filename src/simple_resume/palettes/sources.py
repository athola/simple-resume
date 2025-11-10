#!/usr/bin/env python3
"""Provide palette sources: bundled datasets, palettable integration, remote APIs."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import pkgutil
import time
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

import palettable
from palettable.palette import Palette as PalettablePalette

from .common import Palette, get_cache_dir
from .exceptions import (
    PaletteRemoteDisabled,
    PaletteRemoteError,
)

logger = logging.getLogger(__name__)


def _validate_url(url: str) -> None:
    """Validate that a URL uses a safe scheme.

    Only HTTPS and HTTP schemes are allowed for security. This prevents
    access to local files (`file://`) and other potentially unsafe schemes.
    """
    parsed = urlparse(url)
    allowed_schemes = {"https", "http"}

    # Explicitly check for dangerous schemes before checking allowed schemes
    if parsed.scheme in {"file", "ftp", "data", "javascript", "mailto"}:
        raise PaletteRemoteError(f"Dangerous URL scheme blocked: {parsed.scheme}")

    if parsed.scheme not in allowed_schemes:
        raise PaletteRemoteError(
            f"Unsafe URL scheme: {parsed.scheme}. "
            f"Only allowed schemes are: {', '.join(sorted(allowed_schemes))}"
        )


def _create_safe_request(url: str, headers: dict[str, str]) -> Request:
    """Create a safe HTTP request with validation.

    The URL is validated to use only HTTPS/HTTP schemes before creating the request.
    This prevents access to local files and other unsafe schemes.
    """
    _validate_url(url)
    # Safety: URL scheme validated above before creating the request.
    return Request(url, headers=headers)  # noqa: S310


DEFAULT_DATA_FILENAME = "default_palettes.json"
PALETTABLE_CACHE = "palettable_registry.json"
COLOURLOVERS_FLAG = "SIMPLE_RESUME_ENABLE_REMOTE_PALETTES"
COLOURLOVERS_CACHE_TTL_SECONDS = 60 * 60 * 12  # 12 hours
PALETTE_MODULE_CATEGORY_INDEX = 2
MIN_MODULE_NAME_PARTS = 2


@dataclass(frozen=True)
class PalettableRecord:
    """Define metadata describing a palette provided by `palettable`."""

    name: str
    module: str
    attribute: str
    category: str
    palette_type: str
    size: int

    def to_dict(self) -> dict[str, object]:
        """Convert a record to dictionary representation."""
        return {
            "name": self.name,
            "module": self.module,
            "attribute": self.attribute,
            "category": self.category,
            "palette_type": self.palette_type,
            "size": self.size,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> PalettableRecord:
        """Create a record from a dictionary."""
        return cls(
            name=str(data["name"]),
            module=str(data["module"]),
            attribute=str(data["attribute"]),
            category=str(data["category"]),
            palette_type=str(data["palette_type"]),
            size=int(data["size"])
            if isinstance(data["size"], (int, float, str))
            else 0,
        )


def _data_dir() -> Path:
    """Return the data directory."""
    return Path(__file__).resolve().parent / "data"


def _default_file() -> Path:
    """Return the default palette file path."""
    return _data_dir() / "default_palettes.json"


def load_default_palettes() -> list[Palette]:
    """Load the bundled default palettes shipped with the package."""
    path = _default_file()
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    palettes: list[Palette] = []
    for entry in payload:
        palettes.append(
            Palette(
                name=entry["name"],
                swatches=tuple(entry["colors"]),
                source=entry.get("source", "default"),
                metadata=entry.get("metadata", {}),
            )
        )
    return palettes


def _cache_path(filename: str) -> Path:
    """Return the cache file path."""
    cache_dir = get_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / filename


def _iter_palette_modules() -> Iterator[str]:
    """Iterate over `palettable` modules."""
    for module_info in pkgutil.walk_packages(
        palettable.__path__, palettable.__name__ + "."
    ):
        if not module_info.ispkg:
            yield module_info.name


def _discover_palettable() -> list[PalettableRecord]:
    """Discover and return all `palettable` records."""
    records: list[PalettableRecord] = []
    for module_name in _iter_palette_modules():
        try:
            module = import_module(module_name)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Skipping module %s: %s", module_name, exc)
            continue

        if module_name.count(".") >= MIN_MODULE_NAME_PARTS:
            category = module_name.split(".")[PALETTE_MODULE_CATEGORY_INDEX]
        else:
            category = "misc"
        for attribute in dir(module):
            value = getattr(module, attribute)
            if isinstance(value, PalettablePalette):
                records.append(
                    PalettableRecord(
                        name=value.name,
                        module=module_name,
                        attribute=attribute,
                        category=category,
                        palette_type=value.type,
                        size=len(value.colors),
                    )
                )
    logger.info("Discovered %d palettable palettes", len(records))
    return records


def _load_cached_palettable() -> list[PalettableRecord]:
    """Load cached `palettable` records."""
    cache_file = _cache_path(PALETTABLE_CACHE)
    if not cache_file.exists():
        return []
    with cache_file.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return [PalettableRecord.from_dict(item) for item in payload]


def _save_palettable(records: Iterable[PalettableRecord]) -> None:
    """Save `palettable` records to cache."""
    data = [record.to_dict() for record in records]
    cache_file = _cache_path(PALETTABLE_CACHE)
    with cache_file.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
    size_bytes = cache_file.stat().st_size
    logger.info("Stored palettable registry cache (%d bytes)", size_bytes)


def ensure_bundled_palettes_loaded() -> list[PalettableRecord]:
    """Return cached `palettable` metadata, discovering when necessary."""
    records = _load_cached_palettable()
    if records:
        return records

    records = _discover_palettable()
    _save_palettable(records)
    return records


def load_palettable_palette(record: PalettableRecord) -> Palette | None:
    """Resolve a `Palettable` palette into our `Palette` type."""
    try:
        module = import_module(record.module)
        palette_obj = getattr(module, record.attribute)
        raw_colors = getattr(palette_obj, "hex_colors", None) or getattr(
            palette_obj, "colors", []
        )
        colors = tuple(
            str(color if str(color).startswith("#") else f"#{color}")
            for color in raw_colors
        )
        if not colors:
            return None
        metadata = {
            "category": record.category,
            "palette_type": record.palette_type,
            "size": record.size,
        }
        return Palette(
            name=record.name,
            swatches=colors,
            source="palettable",
            metadata=metadata,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug(
            "Unable to load palettable palette %s.%s: %s",
            record.module,
            record.attribute,
            exc,
        )
        return None


def build_palettable_registry_snapshot() -> dict[str, object]:
    """Generate a metadata snapshot and report JSON footprint."""
    records = ensure_bundled_palettes_loaded()
    snapshot = {
        "generated_at": time.time(),
        "count": len(records),
        "palettes": [record.to_dict() for record in records],
    }
    payload = json.dumps(snapshot).encode("utf-8")
    logger.info("Palettable snapshot size: %.2f KB", len(payload) / 1024)
    return snapshot


# ---------------------------------------------------------------------------
# ColourLovers remote adapter
# ---------------------------------------------------------------------------


class ColourLoversClient:
    """Provide a thin wrapper around the ColourLovers palette API."""

    API_BASE = "https://www.colourlovers.com/api/palettes"

    def __init__(
        self,
        *,
        cache_ttl: int = COLOURLOVERS_CACHE_TTL_SECONDS,
        enable_flag: str = COLOURLOVERS_FLAG,
    ) -> None:
        """Initialize the ColourLovers API client."""
        self.cache_dir = get_cache_dir() / "colourlovers"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = cache_ttl
        self.enable_flag = enable_flag

    def _is_enabled(self) -> bool:
        return os.environ.get(self.enable_flag, "").lower() in {"1", "true", "yes"}

    def _cache_key(self, params: Mapping[str, object]) -> Path:
        encoded = urlencode(sorted((key, str(value)) for key, value in params.items()))
        digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.json"

    def _read_cache(self, path: Path) -> list[dict[str, object]] | None:
        if not path.exists():
            return None
        if time.time() - path.stat().st_mtime > self.cache_ttl:
            return None
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
            if isinstance(data, list):
                return data
            return None

    def _write_cache(self, path: Path, payload: list[dict[str, object]]) -> None:
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
            # Safety: URL validated and request constructed via _create_safe_request.
            # Bandit B310: urlopen call uses HTTPS endpoint with enforced timeout.
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
        """Convert a raw API payload to a `Palette` object."""
        raw_colors = payload.get("colors") or []
        # Ensure raw_colors is iterable
        if not isinstance(raw_colors, (list, tuple)):
            colors: list[object] = []
        else:
            colors = list(raw_colors)
        name = payload.get("title", "ColourLovers Palette")
        metadata = {
            "source_url": payload.get("url"),
            "id": payload.get("id"),
            "author": payload.get("userName"),
        }
        return Palette(
            name=str(name),
            swatches=tuple(
                f"#{color}" if not str(color).startswith("#") else str(color)
                for color in colors
            ),
            source="colourlovers",
            metadata=metadata,
        )


__all__ = [
    "ColourLoversClient",
    "PalettableRecord",
    "build_palettable_registry_snapshot",
    "ensure_bundled_palettes_loaded",
    "load_default_palettes",
    "load_palettable_palette",
]
