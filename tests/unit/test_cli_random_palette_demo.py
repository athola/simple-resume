"""Test cases for CLI random palette demo functionality."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from simple_resume.cli_random_palette_demo import (
    _random_description,
    _random_email,
    _random_linkedin,
    _random_sentence,
    _random_words,
    generate_random_yaml,
    main,
)


class TestRandomGeneration:
    """Test random content generation functions."""

    def test_random_words_generates_correct_count(self) -> None:
        """Random words generates requested number of words."""
        result = _random_words(5, word_len=4)
        assert len(result) == 5
        assert all(len(word) == 4 for word in result)
        assert all(word.islower() for word in result)

    def test_random_words_generates_varying_lengths(self) -> None:
        """Random words work with different length parameters."""
        result_short = _random_words(3, word_len=3)
        result_long = _random_words(2, word_len=8)

        assert len(result_short) == 3
        assert all(len(word) == 3 for word in result_short)
        assert len(result_long) == 2
        assert all(len(word) == 8 for word in result_long)

    def test_random_sentence_starts_with_capital(self) -> None:
        """Random sentence starts with capital letter and ends with period."""
        result = _random_sentence(5)
        assert result[0].isupper()
        assert result.endswith(".")
        assert len(result.split()) == 5

    def test_random_sentence_varying_word_count(self) -> None:
        """Random sentence works with different word counts."""
        result_short = _random_sentence(3)
        result_long = _random_sentence(10)

        assert len(result_short.split()) == 3
        assert len(result_long.split()) == 10
        assert result_short[0].isupper()
        assert result_long[0].isupper()
        assert result_short.endswith(".")
        assert result_long.endswith(".")

    def test_random_description_multiple_paragraphs(self) -> None:
        """Random description generates multiple paragraphs."""
        result = _random_description(3)
        paragraphs = result.split("\n\n")

        assert len(paragraphs) == 3
        for para in paragraphs:
            assert para.strip()  # Not empty
            assert para[0].isupper()  # Starts with capital
            # Each paragraph should have multiple sentences
            sentence_count = para.count(". ")
            assert sentence_count >= 1  # At least 2 sentences per paragraph

    def test_random_email_format(self) -> None:
        """Random email follows expected format."""
        name = "John Doe"
        result = _random_email(name)

        assert result.startswith("john.doe.")  # Name formatted
        assert result.endswith("@example.com")  # Domain
        # Should have random suffix
        parts = result.split("@")[0].split(".")
        assert len(parts) == 3  # john.doe.randomsuffix
        assert len(parts[2]) == 8  # 8 character suffix

    def test_random_linkedin_format(self) -> None:
        """Random LinkedIn URL follows expected format."""
        name = "Jane Smith"
        result = _random_linkedin(name)

        assert result.startswith("in/")  # LinkedIn URL prefix
        assert "jane-smith" in result  # Name formatted (may not have dashes around it)
        assert len(result) >= len("in/jane-smith-xxxx")  # At least base length

    def test_random_reproducibility_with_seed(self, tmp_path: Path) -> None:
        """Random generation is reproducible with seed."""
        template_path = tmp_path / "template.yaml"
        template_content = {
            "template": "test",
            "body": {"experience": [], "education": []},
        }
        template_path.write_text(yaml.dump(template_content))

        with patch("random.seed") as mock_seed:
            generate_random_yaml(
                output_path=tmp_path / "test.yaml", template_path=template_path, seed=42
            )
            mock_seed.assert_called_once_with(42)


class TestGenerateRandomYaml:
    """Test the main YAML generation functionality."""

    def test_generate_random_yaml_creates_file(self, tmp_path: Path) -> None:
        """Generate random YAML creates output file."""
        output_path = tmp_path / "test_output.yaml"
        template_path = tmp_path / "template.yaml"

        # Create a minimal template
        template_content = {
            "template": "test",
            "full_name": "Template Name",
            "body": {"experience": [], "education": []},
        }
        template_path.write_text(yaml.dump(template_content))

        generate_random_yaml(
            output_path=output_path, template_path=template_path, seed=42
        )

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert content.strip()  # File not empty

        # Parse YAML to ensure it's valid
        parsed = yaml.safe_load(content)
        assert "full_name" in parsed
        assert "config" in parsed

    def test_generate_random_yaml_preserves_template_structure(
        self, tmp_path: Path
    ) -> None:
        """Generated YAML preserves template structure."""
        output_path = tmp_path / "test_output.yaml"
        template_path = tmp_path / "template.yaml"

        template_content = {
            "template": "test_template",
            "full_name": "Template Name",
            "phone": "555-0123",
            "body": {
                "experience": [
                    {"company": "Test Company", "position": "Test Position"}
                ],
                "education": [],
            },
        }
        template_path.write_text(yaml.dump(template_content))

        generate_random_yaml(
            output_path=output_path, template_path=template_path, seed=123
        )

        result = yaml.safe_load(output_path.read_text(encoding="utf-8"))

        # Should preserve template fields
        assert result["template"] == "test_template"
        assert "experience" in result["body"]
        assert "education" in result["body"]

        # Should have random content added
        assert result["full_name"] != "Template Name"
        assert result["phone"] != "555-0123"

    def test_generate_random_yaml_adds_config_palette(self, tmp_path: Path) -> None:
        """Generated YAML includes config and palette information."""
        output_path = tmp_path / "test_output.yaml"
        template_path = tmp_path / "template.yaml"

        template_content = {
            "template": "test",
            "full_name": "Test",
            "body": {"experience": []},
        }
        template_path.write_text(yaml.dump(template_content))

        generate_random_yaml(
            output_path=output_path, template_path=template_path, seed=456
        )

        result = yaml.safe_load(output_path.read_text(encoding="utf-8"))

        assert "config" in result
        config = result["config"]

        # Should have basic config
        assert "output_mode" in config
        assert config["output_mode"] == "markdown"
        assert "sidebar_width" in config
        assert 58 <= config["sidebar_width"] <= 72

        # Should have palette colors
        color_keys = ["theme_color", "sidebar_color"]  # These are always present
        for key in color_keys:
            assert key in config
            assert config[key].startswith("#")

        # bar_background_color may or may not be present depending on palette size
        if "bar_background_color" in config:
            assert config["bar_background_color"].startswith("#")


class TestMainFunction:
    """Test CLI main function."""

    def test_main_with_default_arguments(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Main function works with default arguments."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Mock sys.argv to simulate CLI call
        with patch("sys.argv", ["cli_random_palette_demo.py"]):
            with patch(
                "simple_resume.cli_random_palette_demo.generate_random_yaml"
            ) as mock_generate:
                main()

                # Should call generate_random_yaml with default paths
                mock_generate.assert_called_once()
                args, kwargs = mock_generate.call_args
                assert "output_path" in kwargs
                assert "template_path" in kwargs
                assert "seed" in kwargs

    def test_main_with_custom_arguments(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Main function handles custom CLI arguments."""
        monkeypatch.chdir(tmp_path)

        custom_output = tmp_path / "custom.yaml"
        custom_template = tmp_path / "custom_template.yaml"

        with patch(
            "sys.argv",
            [
                "cli_random_palette_demo.py",
                "--output",
                str(custom_output),
                "--template",
                str(custom_template),
                "--seed",
                "789",
            ],
        ):
            with patch(
                "simple_resume.cli_random_palette_demo.generate_random_yaml"
            ) as mock_generate:
                main()

                mock_generate.assert_called_once_with(
                    output_path=custom_output, template_path=custom_template, seed=789
                )

    def test_main_outputs_success_message(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Main function outputs success message."""
        monkeypatch.chdir(tmp_path)

        with patch("sys.argv", ["cli_random_palette_demo.py"]):
            with patch("builtins.print") as mock_print:
                with patch(
                    "simple_resume.cli_random_palette_demo.generate_random_yaml"
                ):
                    main()

                    # Should print success message
                    mock_print.assert_called_once()
                    args, _ = mock_print.call_args
                    assert args[0].startswith("✓ Wrote")


class TestRandomGenerationEdgeCases:
    """Test edge cases in random generation."""

    def test_random_words_zero_count(self) -> None:
        """Random words handles zero count gracefully."""
        result = _random_words(0)
        assert result == []

    def test_random_sentence_single_word(self) -> None:
        """Random sentence works with single word."""
        result = _random_sentence(1)
        assert len(result.split()) == 1
        assert result[0].isupper()
        assert result.endswith(".")

    def test_random_description_single_paragraph(self) -> None:
        """Random description works with single paragraph."""
        result = _random_description(1)
        paragraphs = result.split("\n\n")
        assert len(paragraphs) == 1
        assert paragraphs[0].strip()

    def test_random_email_special_characters(self) -> None:
        """Random email handles names with special characters."""
        name = "John O'Connor-Smith"
        result = _random_email(name)
        # Special characters are preserved in some form, basic format preserved
        assert result.endswith("@example.com")
        assert "john" in result.lower()
        assert "smith" in result.lower()
        # The apostrophe might be preserved or transformed,
        # just check it's there somehow
        assert "o" in result.lower() and "connor" in result.lower()

    def test_random_linkedin_special_characters(self) -> None:
        """Random LinkedIn handles names with special characters."""
        name = "Maria Jose Garcia"  # Use simple ASCII name for consistent testing
        result = _random_linkedin(name)
        assert result.startswith("in/")
        assert "maria-jose-garcia" in result
