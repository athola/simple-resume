"""Tests for shell/effect_executor.py - effect execution functionality."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from simple_resume.core.effects import (
    DeleteFile,
    MakeDirectory,
    OpenBrowser,
    RunCommand,
    WriteFile,
)
from simple_resume.shell.effect_executor import EffectExecutor


class TestEffectExecutor:
    """Tests for EffectExecutor class."""

    def test_execute_write_file(self, tmp_path: Path) -> None:
        """Test executing a WriteFile effect."""
        executor = EffectExecutor()
        file_path = tmp_path / "test.txt"
        effect = WriteFile(path=file_path, content="test content")

        executor.execute(effect)

        assert file_path.exists()
        assert file_path.read_text() == "test content"

    def test_execute_make_directory(self, tmp_path: Path) -> None:
        """Test executing a MakeDirectory effect."""
        executor = EffectExecutor()
        dir_path = tmp_path / "new_dir"
        effect = MakeDirectory(path=dir_path)

        executor.execute(effect)

        assert dir_path.exists()
        assert dir_path.is_dir()

    def test_execute_delete_file(self, tmp_path: Path) -> None:
        """Test executing a DeleteFile effect."""
        executor = EffectExecutor()
        file_path = tmp_path / "to_delete.txt"
        file_path.write_text("delete me")
        effect = DeleteFile(path=file_path)

        executor.execute(effect)

        assert not file_path.exists()

    def test_execute_delete_file_missing(self, tmp_path: Path) -> None:
        """Test executing DeleteFile on non-existent file is safe."""
        executor = EffectExecutor()
        file_path = tmp_path / "nonexistent.txt"
        effect = DeleteFile(path=file_path)

        # Should not raise
        executor.execute(effect)

    def test_execute_open_browser(self) -> None:
        """Test executing an OpenBrowser effect."""
        executor = EffectExecutor()
        effect = OpenBrowser(url="https://example.com")

        with patch("webbrowser.open") as mock_open:
            executor.execute(effect)
            mock_open.assert_called_once_with("https://example.com")

    def test_execute_run_command(self, tmp_path: Path) -> None:
        """Test executing a RunCommand effect."""
        executor = EffectExecutor()
        effect = RunCommand(command=["echo", "hello"], cwd=tmp_path)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            executor.execute(effect)
            mock_run.assert_called_once_with(
                ["echo", "hello"], cwd=tmp_path, check=True
            )

    def test_execute_run_command_rejects_unsafe_chars_in_list(self) -> None:
        """Test that RunCommand rejects unsafe characters in list commands."""
        executor = EffectExecutor()
        effect = RunCommand(command=["echo", "hello; rm -rf /"], cwd=None)

        with pytest.raises(ValueError, match="Unsafe command"):
            executor.execute(effect)

    def test_execute_run_command_rejects_pipe_in_list(self) -> None:
        """Test that RunCommand rejects pipe character in list commands."""
        executor = EffectExecutor()
        effect = RunCommand(command=["echo", "hello | cat"], cwd=None)

        with pytest.raises(ValueError, match="Unsafe command"):
            executor.execute(effect)

    def test_execute_unknown_effect_raises(self) -> None:
        """Test that unknown effect type raises ValueError."""
        executor = EffectExecutor()

        class UnknownEffect:
            pass

        with pytest.raises(ValueError, match="Unknown effect type"):
            executor.execute(UnknownEffect())  # type: ignore[arg-type]

    def test_execute_many_effects(self, tmp_path: Path) -> None:
        """Test executing multiple effects in sequence."""
        executor = EffectExecutor()
        dir_path = tmp_path / "batch_dir"
        file_path = dir_path / "batch_file.txt"
        effects = [
            MakeDirectory(path=dir_path),
            WriteFile(path=file_path, content="batch content"),
        ]

        executor.execute_many(effects)

        assert dir_path.exists()
        assert file_path.exists()
        assert file_path.read_text() == "batch content"

    def test_execute_run_command_rejects_unsafe_ampersand(self) -> None:
        """Test that RunCommand rejects ampersand character in commands."""
        executor = EffectExecutor()
        effect = RunCommand(command=["echo", "hello && rm -rf /"], cwd=None)

        with pytest.raises(ValueError, match="Unsafe command"):
            executor.execute(effect)
