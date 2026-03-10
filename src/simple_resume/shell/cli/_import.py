"""LinkedIn import CLI handler.

Reads a LinkedIn profile from a file (HTML or text), converts it
to simple-resume YAML format, and writes the result to disk.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import yaml

from simple_resume.core.exceptions import SimpleResumeError
from simple_resume.shell.cli._errors import _handle_unexpected_error

logger = logging.getLogger(__name__)


def handle_import_command(args: argparse.Namespace) -> int:
    """Import a LinkedIn profile and convert to simple-resume YAML.

    Args:
        args: Parsed CLI arguments containing ``linkedin`` path
            and optional ``output`` path.

    Returns:
        Exit code (0 for success, non-zero for failure).

    """
    from simple_resume.core.importers.linkedin import (  # noqa: PLC0415 - optional dep
        linkedin_to_simple_resume,
    )
    from simple_resume.shell.importers.linkedin_fetcher import (  # noqa: PLC0415 - optional dep
        read_linkedin_file,
    )

    linkedin_path: str = args.linkedin
    output_path: Path | None = getattr(args, "output", None)

    try:
        # Read and parse LinkedIn profile
        profile = read_linkedin_file(linkedin_path)
        if not profile:
            print(f"Error: No profile data extracted from {linkedin_path}")
            return 1

        # Convert to simple-resume format
        resume_data = linkedin_to_simple_resume(profile)

        # Determine output path
        if output_path is None:
            source = Path(linkedin_path)
            output_path = source.with_suffix(".yaml")

        # Write YAML output
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            yaml.dump(resume_data, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
        print(f"Resume imported: {output_path}")
        return 0

    except (FileNotFoundError, ValueError) as exc:
        logger.error("Import error: %s", exc)
        print(f"Import error: {exc}")
        return 1
    except SimpleResumeError as exc:
        logger.error("Import error: %s", exc)
        print(f"Import error: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - safety net
        return _handle_unexpected_error(exc, "LinkedIn import")


__all__ = ["handle_import_command"]
