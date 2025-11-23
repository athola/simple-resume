#!/usr/bin/env python3
"""Provide palette sources: bundled datasets, palettable integration, remote APIs."""

from __future__ import annotations

import json
import logging
import pkgutil
import time
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any

import palettable
from palettable.palette import Palette as PalettablePalette

from .common import Palette, get_cache_dir

logger = logging.getLogger(__name__)

# NOTE: Network-related functions (_validate_url, _create_safe_request) and
# ColourLoversClient have been moved to shell/palettes/remote.py

DEFAULT_DATA_FILENAME = "default_palettes.json"
PALETTABLE_CACHE = "palettable_registry.json"
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


def parse_palette_data(payload: list[dict[str, Any]]) -> list[Palette]:
    """Parse palette JSON data into Palette objects (pure function).

    Args:
        payload: List of palette dictionaries with 'name', 'colors', etc.

    Returns:
        List of Palette objects.

    """
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
    """Return the cache file path.

    NOTE: Assumes cache directory already exists. Directory creation
    should be handled by the shell layer before calling core functions.
    """
    cache_dir = get_cache_dir()
    # Directory creation moved to shell layer
    return cache_dir / filename


def _iter_palette_modules() -> Iterator[str]:
    """Iterate over `palettable` modules."""
    for module_info in pkgutil.walk_packages(
        palettable.__path__, palettable.__name__ + "."
    ):
        if not module_info.ispkg:
            yield module_info.name


def discover_palettable() -> list[PalettableRecord]:
    """Discover and return all `palettable` records (pure function)."""
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


def parse_palettable_cache(payload: list[dict[str, Any]]) -> list[PalettableRecord]:
    """Parse palettable cache JSON into records (pure function)."""
    return [PalettableRecord.from_dict(item) for item in payload]


def serialize_palettable_records(
    records: Iterable[PalettableRecord],
) -> list[dict[str, Any]]:
    """Serialize palettable records to JSON-serializable dicts (pure function)."""
    return [record.to_dict() for record in records]


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
    records = discover_palettable()
    snapshot = {
        "generated_at": time.time(),
        "count": len(records),
        "palettes": [record.to_dict() for record in records],
    }
    payload = json.dumps(snapshot).encode("utf-8")
    logger.info("Palettable snapshot size: %.2f KB", len(payload) / 1024)
    return snapshot


__all__ = [
    "PalettableRecord",
    "build_palettable_registry_snapshot",
    "discover_palettable",
    "load_palettable_palette",
    "parse_palette_data",
    "parse_palettable_cache",
    "serialize_palettable_records",
]
