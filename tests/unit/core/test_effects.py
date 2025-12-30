"""Tests for core Effect types.

Following TDD principles - these tests are written BEFORE implementation.
Tests verify that Effect types are immutable, descriptive, and type-safe.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from simple_resume.core.effects import (
    DeleteFile,
    Effect,
    MakeDirectory,
    OpenBrowser,
    RunCommand,
    WriteFile,
)
from tests.bdd import Scenario


class TestWriteFileEffect:
    """Tests for WriteFile effect creation and properties."""

    def test_write_file_effect_creation_with_string_content(
        self, story: Scenario
    ) -> None:
        """WriteFile effect can be created with string content."""
        story.given("a path and string content for a file write operation")
        story.when("creating a WriteFile effect with encoding")
        with TemporaryDirectory() as temp_dir:
            effect = WriteFile(
                path=Path(temp_dir) / "test.txt",
                content="Hello, World!",
                encoding="utf-8",
            )

            assert effect.path == Path(temp_dir) / "test.txt"
            assert effect.content == "Hello, World!"
            assert effect.encoding == "utf-8"

    def test_write_file_effect_creation_with_bytes_content(
        self, story: Scenario
    ) -> None:
        """WriteFile effect can be created with bytes content."""
        story.given("a path and binary content for a file write operation")
        story.when("creating a WriteFile effect with bytes")
        with TemporaryDirectory() as temp_dir:
            content_bytes = b"Binary data"
            effect = WriteFile(path=Path(temp_dir) / "test.bin", content=content_bytes)

            assert effect.path == Path(temp_dir) / "test.bin"
            assert effect.content == content_bytes
            assert effect.encoding == "utf-8"  # Default

    def test_write_file_effect_default_encoding(self, story: Scenario) -> None:
        """WriteFile effect uses utf-8 as default encoding."""
        story.given("a WriteFile effect created without explicit encoding")
        story.when("checking the encoding attribute")
        with TemporaryDirectory() as temp_dir:
            effect = WriteFile(path=Path(temp_dir) / "test.txt", content="Test")

            assert effect.encoding == "utf-8"

    def test_write_file_effect_is_immutable(self, story: Scenario) -> None:
        """WriteFile effect is immutable (frozen dataclass)."""
        story.given("a WriteFile effect instance")
        story.when("attempting to modify its attributes")
        with TemporaryDirectory() as temp_dir:
            effect = WriteFile(path=Path(temp_dir) / "test.txt", content="Test")

            with pytest.raises(AttributeError):
                effect.path = Path(temp_dir) / "other.txt"  # type: ignore

            with pytest.raises(AttributeError):
                effect.content = "Changed"  # type: ignore

    def test_write_file_effect_describe(self, story: Scenario) -> None:
        """WriteFile effect provides human-readable description."""
        story.given("a WriteFile effect with a specific path")
        story.when("calling the describe method")
        with TemporaryDirectory() as temp_dir:
            effect = WriteFile(path=Path(temp_dir) / "test.txt", content="Test")

            description = effect.describe()

            assert "Write file" in description or "write" in description.lower()
            test_path = str(Path(temp_dir) / "test.txt")
            assert test_path in description or "test.txt" in description

    def test_write_file_effect_is_effect_subclass(self, story: Scenario) -> None:
        """WriteFile is a subclass of Effect."""
        story.given("a WriteFile effect instance")
        story.when("checking its type hierarchy")
        with TemporaryDirectory() as temp_dir:
            effect = WriteFile(path=Path(temp_dir) / "test.txt", content="Test")

            assert isinstance(effect, Effect)


class TestMakeDirectoryEffect:
    """Tests for MakeDirectory effect creation and properties."""

    def test_make_directory_effect_creation(self, story: Scenario) -> None:
        """MakeDirectory effect can be created with path."""
        story.given("a target directory path")
        story.when("creating a MakeDirectory effect with parents=True")
        with TemporaryDirectory() as temp_dir:
            effect = MakeDirectory(path=Path(temp_dir) / "test_dir", parents=True)

            assert effect.path == Path(temp_dir) / "test_dir"
            assert effect.parents is True

    def test_make_directory_effect_default_parents(self, story: Scenario) -> None:
        """MakeDirectory effect defaults to creating parent directories."""
        story.given("a MakeDirectory effect created without explicit parents flag")
        story.when("checking the parents attribute")
        with TemporaryDirectory() as temp_dir:
            effect = MakeDirectory(path=Path(temp_dir) / "test_dir")

            assert effect.parents is True

    def test_make_directory_effect_is_immutable(self, story: Scenario) -> None:
        """MakeDirectory effect is immutable."""
        story.given("a MakeDirectory effect instance")
        story.when("attempting to modify its path attribute")
        with TemporaryDirectory() as temp_dir:
            effect = MakeDirectory(path=Path(temp_dir) / "test_dir")

            with pytest.raises(AttributeError):
                effect.path = Path(temp_dir) / "other"  # type: ignore

    def test_make_directory_effect_describe(self, story: Scenario) -> None:
        """MakeDirectory effect provides human-readable description."""
        story.given("a MakeDirectory effect with a specific path")
        story.when("calling the describe method")
        with TemporaryDirectory() as temp_dir:
            effect = MakeDirectory(path=Path(temp_dir) / "test_dir")

            description = effect.describe()

            assert "directory" in description.lower() or "dir" in description.lower()
            dir_path = str(Path(temp_dir) / "test_dir")
            assert dir_path in description or "test_dir" in description

    def test_make_directory_effect_is_effect_subclass(self, story: Scenario) -> None:
        """MakeDirectory is a subclass of Effect."""
        story.given("a MakeDirectory effect instance")
        story.when("checking its type hierarchy")
        with TemporaryDirectory() as temp_dir:
            effect = MakeDirectory(path=Path(temp_dir) / "test_dir")

            assert isinstance(effect, Effect)


class TestDeleteFileEffect:
    """Tests for DeleteFile effect creation and properties."""

    def test_delete_file_effect_creation(self, story: Scenario) -> None:
        """DeleteFile effect can be created with path."""
        story.given("a file path to delete")
        story.when("creating a DeleteFile effect")
        with TemporaryDirectory() as temp_dir:
            effect = DeleteFile(path=Path(temp_dir) / "test.txt")

            assert effect.path == Path(temp_dir) / "test.txt"

    def test_delete_file_effect_is_immutable(self, story: Scenario) -> None:
        """DeleteFile effect is immutable."""
        story.given("a DeleteFile effect instance")
        story.when("attempting to modify its path attribute")
        with TemporaryDirectory() as temp_dir:
            effect = DeleteFile(path=Path(temp_dir) / "test.txt")

            with pytest.raises(AttributeError):
                effect.path = Path(temp_dir) / "other.txt"  # type: ignore

    def test_delete_file_effect_describe(self, story: Scenario) -> None:
        """DeleteFile effect provides human-readable description."""
        story.given("a DeleteFile effect with a specific path")
        story.when("calling the describe method")
        with TemporaryDirectory() as temp_dir:
            effect = DeleteFile(path=Path(temp_dir) / "test.txt")

            description = effect.describe()

            assert "delete" in description.lower() or "remove" in description.lower()
            test_path = str(Path(temp_dir) / "test.txt")
            assert test_path in description or "test.txt" in description

    def test_delete_file_effect_is_effect_subclass(self, story: Scenario) -> None:
        """DeleteFile is a subclass of Effect."""
        story.given("a DeleteFile effect instance")
        story.when("checking its type hierarchy")
        with TemporaryDirectory() as temp_dir:
            effect = DeleteFile(path=Path(temp_dir) / "test.txt")

            assert isinstance(effect, Effect)


class TestOpenBrowserEffect:
    """Tests for OpenBrowser effect creation and properties."""

    def test_open_browser_effect_creation(self, story: Scenario) -> None:
        """OpenBrowser effect can be created with URL."""
        story.given("a URL to open in a browser")
        story.when("creating an OpenBrowser effect")
        effect = OpenBrowser(url="https://example.com")

        assert effect.url == "https://example.com"

    def test_open_browser_effect_is_immutable(self, story: Scenario) -> None:
        """OpenBrowser effect is immutable."""
        story.given("an OpenBrowser effect instance")
        story.when("attempting to modify its url attribute")
        effect = OpenBrowser(url="https://example.com")

        with pytest.raises(AttributeError):
            effect.url = "https://other.com"  # type: ignore

    def test_open_browser_effect_describe(self, story: Scenario) -> None:
        """OpenBrowser effect provides human-readable description."""
        story.given("an OpenBrowser effect with a specific URL")
        story.when("calling the describe method")
        effect = OpenBrowser(url="https://example.com")

        description = effect.describe()

        assert "browser" in description.lower() or "open" in description.lower()
        assert "https://example.com" in description or "example.com" in description

    def test_open_browser_effect_is_effect_subclass(self, story: Scenario) -> None:
        """OpenBrowser is a subclass of Effect."""
        story.given("an OpenBrowser effect instance")
        story.when("checking its type hierarchy")
        effect = OpenBrowser(url="https://example.com")

        assert isinstance(effect, Effect)


class TestRunCommandEffect:
    """Tests for RunCommand effect creation and properties."""

    def test_run_command_effect_creation(self, story: Scenario) -> None:
        """RunCommand effect can be created with command."""
        story.given("a command and working directory")
        story.when("creating a RunCommand effect")
        with TemporaryDirectory() as temp_dir:
            effect = RunCommand(command=["ls", "-la"], cwd=Path(temp_dir))

            assert effect.command == ["ls", "-la"]
            assert effect.cwd == Path(temp_dir)

    def test_run_command_effect_default_cwd(self, story: Scenario) -> None:
        """RunCommand effect defaults to None for cwd."""
        story.given("a RunCommand effect created without explicit cwd")
        story.when("checking the cwd attribute")
        effect = RunCommand(command=["echo", "hello"])

        assert effect.command == ["echo", "hello"]
        assert effect.cwd is None

    def test_run_command_effect_is_immutable(self, story: Scenario) -> None:
        """RunCommand effect is immutable."""
        story.given("a RunCommand effect instance")
        story.when("attempting to modify its command attribute")
        effect = RunCommand(command=["ls"])

        with pytest.raises(AttributeError):
            effect.command = ["pwd"]  # type: ignore

    def test_run_command_effect_describe(self, story: Scenario) -> None:
        """RunCommand effect provides human-readable description."""
        story.given("a RunCommand effect with a specific command")
        story.when("calling the describe method")
        effect = RunCommand(command=["ls", "-la"])

        description = effect.describe()

        assert "command" in description.lower() or "run" in description.lower()
        assert "ls -la" in description or "ls" in description

    def test_run_command_effect_is_effect_subclass(self, story: Scenario) -> None:
        """RunCommand is a subclass of Effect."""
        story.given("a RunCommand effect instance")
        story.when("checking its type hierarchy")
        effect = RunCommand(command=["ls"])

        assert isinstance(effect, Effect)


class TestEffectHierarchy:
    """Tests for Effect base class and hierarchy."""

    def test_effect_is_abstract(self, story: Scenario) -> None:
        """Effect base class is abstract and cannot be instantiated directly."""
        story.given("the Effect base class")
        story.when("attempting to instantiate it directly")
        with pytest.raises(TypeError):
            Effect()  # type: ignore

    def test_all_effects_have_describe_method(self, story: Scenario) -> None:
        """All effect types implement the describe() method."""
        story.given("instances of all effect types")
        story.when("checking for describe method implementation")
        with TemporaryDirectory() as temp_dir:
            effects = [
                WriteFile(path=Path(temp_dir) / "test.txt", content="test"),
                MakeDirectory(path=Path(temp_dir) / "dir"),
                DeleteFile(path=Path(temp_dir) / "test.txt"),
                OpenBrowser(url="https://example.com"),
                RunCommand(command=["ls"]),
            ]

            for effect in effects:
                assert hasattr(effect, "describe")
                assert callable(effect.describe)
                description = effect.describe()
                assert isinstance(description, str)
                assert len(description) > 0


class TestEffectEquality:
    """Tests for effect equality and hashing."""

    def test_write_file_effects_equal_with_same_values(self, story: Scenario) -> None:
        """Two WriteFile effects with same values are equal."""
        story.given("two WriteFile effects with identical path and content")
        story.when("comparing them for equality")
        with TemporaryDirectory() as temp_dir:
            effect1 = WriteFile(path=Path(temp_dir) / "test.txt", content="test")
            effect2 = WriteFile(path=Path(temp_dir) / "test.txt", content="test")

            assert effect1 == effect2

    def test_write_file_effects_not_equal_with_different_paths(
        self, story: Scenario
    ) -> None:
        """Two WriteFile effects with different paths are not equal."""
        story.given("two WriteFile effects with different paths")
        story.when("comparing them for equality")
        with TemporaryDirectory() as temp_dir:
            effect1 = WriteFile(path=Path(temp_dir) / "test1.txt", content="test")
            effect2 = WriteFile(path=Path(temp_dir) / "test2.txt", content="test")

            assert effect1 != effect2

    def test_write_file_effects_not_equal_with_different_content(
        self, story: Scenario
    ) -> None:
        """Two WriteFile effects with different content are not equal."""
        story.given("two WriteFile effects with different content")
        story.when("comparing them for equality")
        with TemporaryDirectory() as temp_dir:
            effect1 = WriteFile(path=Path(temp_dir) / "test.txt", content="test1")
            effect2 = WriteFile(path=Path(temp_dir) / "test.txt", content="test2")

            assert effect1 != effect2

    def test_effects_hashable_for_use_in_sets(self, story: Scenario) -> None:
        """Effects are hashable and can be used in sets."""
        story.given("multiple effects including duplicates")
        story.when("adding them to a set")
        with TemporaryDirectory() as temp_dir:
            effect1 = WriteFile(path=Path(temp_dir) / "test.txt", content="test")
            effect2 = MakeDirectory(path=Path(temp_dir) / "dir")
            effect3 = WriteFile(path=Path(temp_dir) / "test.txt", content="test")

            effect_set = {effect1, effect2, effect3}

            # effect1 and effect3 are equal, so set should have 2 elements
            assert len(effect_set) == 2
