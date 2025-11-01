"""Integration test covering editable installs and CLI execution."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

import pytest

from easyresume import config


def _checked_call(
    command: Sequence[str],
    *,
    cwd: Path,
    suppress_output: bool = False,
) -> None:
    """Run a trusted subprocess command in tests."""
    subprocess.run(  # noqa: S603
        list(command),
        cwd=cwd,
        check=True,
        stdout=subprocess.DEVNULL if suppress_output else None,
        stderr=subprocess.DEVNULL if suppress_output else None,
    )


@pytest.mark.integration
def test_generate_html_cli_after_editable_install(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """Ensure the CLI runs from a fresh working directory post `pip install -e ..`."""
    repo_root = config.PACKAGE_ROOT.parent.parent
    work_dir = Path(tempfile.mkdtemp(dir=repo_root))
    try:
        try:
            _checked_call(
                [sys.executable, "-m", "pip", "--version"],
                cwd=work_dir,
                suppress_output=True,
            )
        except subprocess.CalledProcessError:
            _checked_call(
                [sys.executable, "-m", "ensurepip", "--upgrade"],
                cwd=work_dir,
            )

        _checked_call(
            [sys.executable, "-m", "pip", "install", "-e", ".."],
            cwd=work_dir,
        )

        cli_path = Path(sys.executable).parent / "generate-html"
        assert cli_path.exists(), (
            "generate-html entry point not found after installation"
        )

        data_dir = work_dir / "data"
        input_dir = data_dir / "input"
        output_dir = data_dir / "output"
        input_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)

        sample_input = repo_root / "sample" / "input" / "sample_1.yaml"
        (input_dir / "sample_1.yaml").write_text(
            sample_input.read_text(encoding="utf-8"), encoding="utf-8"
        )

        _checked_call(
            [str(cli_path), "--data-dir", str(data_dir)],
            cwd=work_dir,
        )

        generated_html = output_dir / "sample_1.html"
        assert generated_html.exists()
        assert generated_html.read_text(encoding="utf-8")
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
