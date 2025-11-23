#!/usr/bin/env python3
"""Command line helpers for palette discovery."""

from __future__ import annotations

import argparse
import json
import sys

from simple_resume.shell.palettes.loader import (
    build_palettable_snapshot,
    get_palette_registry,
)


def cmd_snapshot(args: argparse.Namespace) -> int:
    """Export current palettable registry snapshot to JSON."""
    snapshot = build_palettable_snapshot()
    output = json.dumps(snapshot, indent=2)
    if args.output:
        args.output.write(output)
        args.output.write("\n")
    else:
        print(output)
    return 0


def cmd_list(_: argparse.Namespace) -> int:
    """List all available palette names with preview colors."""
    registry = get_palette_registry()
    for palette in registry.list():
        print(f"{palette.name}: {', '.join(palette.swatches[:6])}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for palette CLI."""
    parser = argparse.ArgumentParser(description="Palette utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    snap = subparsers.add_parser("snapshot", help="Build palettable snapshot")
    snap.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("w", encoding="utf-8"),
        help="Output file (defaults to stdout)",
    )
    snap.set_defaults(func=cmd_snapshot)

    list_cmd = subparsers.add_parser("list", help="List available palettes")
    list_cmd.set_defaults(func=cmd_list)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the palette CLI with given arguments."""
    parser = build_parser()
    args = parser.parse_args(argv)
    result = args.func(args)
    return int(result) if result is not None else 0


def snapshot() -> None:
    """Entry point for palette-snapshot command."""
    sys.exit(main(["snapshot"]))


def palette_list() -> None:
    """Entry point for palette-list command."""
    sys.exit(main(["list"]))


if __name__ == "__main__":
    sys.exit(main())
