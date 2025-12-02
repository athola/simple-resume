#!/usr/bin/env python3
"""Provide configuration helpers and shared constants.

See `wiki/Path-Handling-Guide.md` for path handling conventions.
"""

from __future__ import annotations

import atexit
import os
import sys
from contextlib import ExitStack
from importlib import resources
from pathlib import Path
from typing import Union

from simple_resume.core.paths import Paths

# Keep an open handle to package resources so they're available even when the
# distribution is zipped (e.g., installed from a wheel).
_asset_stack = ExitStack()
PACKAGE_ROOT = _asset_stack.enter_context(
    resources.as_file(resources.files("simple_resume"))
)
ASSETS_ROOT = PACKAGE_ROOT / "shell" / "assets"
atexit.register(_asset_stack.close)

PATH_CONTENT = ASSETS_ROOT
TEMPLATE_LOC = ASSETS_ROOT / "templates"
STATIC_LOC = ASSETS_ROOT / "static"

# Legacy string-based paths preserved for configuration.
PATH_DATA = "resume_private"
PATH_INPUT = f"{PATH_DATA}/input"
PATH_OUTPUT = f"{PATH_DATA}/output"


if sys.version_info >= (3, 10):
    PathLike = str | os.PathLike[str]
else:
    PathLike = Union[str, os.PathLike[str]]


def resolve_paths(
    data_dir: PathLike | None = None,
    *,
    content_dir: PathLike | None = None,
    templates_dir: PathLike | None = None,
    static_dir: PathLike | None = None,
) -> Paths:
    """Return the active data, input, and output paths.

    Args:
        data_dir: Optional directory containing `input/` and `output/` folders.
            If omitted, the `RESUME_DATA_DIR` environment variable is used.
            If neither is provided, the default is `./resume_private`.
        content_dir: Optional override for the package content directory.
        templates_dir: Optional override for the templates directory.
        static_dir: Optional override for the static assets directory.

    Returns:
        A `Paths` dataclass with resolved data, template, and static paths.

    """
    base = data_dir or os.environ.get("RESUME_DATA_DIR") or PATH_DATA
    base_path = Path(base)

    if data_dir is None:
        data_path = Path(PATH_DATA)
        input_path = Path(PATH_INPUT)
        output_path = Path(PATH_OUTPUT)
    else:
        data_path = base_path
        input_path = base_path / "input"
        output_path = base_path / "output"

    content_path = Path(content_dir) if content_dir is not None else PATH_CONTENT
    templates_path = (
        Path(templates_dir) if templates_dir is not None else content_path / "templates"
    )
    static_path = (
        Path(static_dir) if static_dir is not None else content_path / "static"
    )

    return Paths(
        data=data_path,
        input=input_path,
        output=output_path,
        content=content_path,
        templates=templates_path,
        static=static_path,
    )


# Files
FILE_DEFAULT = "sample_1"
