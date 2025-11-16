"""Test cases for CLI random palette demo functionality."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from simple_resume.cli.random_palette_demo import (
    _random_description,
    _random_email,
    _random_linkedin,
    _random_name,
    _random_sentence,
    _random_words,
    generate_random_yaml,
    main,
)
from tests.bdd import Scenario


class TestRandomGeneration:
    """Test random content generation functions."""

    def test_random_name_generates_realistic_names(self, story: Scenario) -> None:
        story.given("a request for random names")
        story.when("_random_name generates names")
        name1 = _random_name()
        name2 = _random_name()

        story.then("names contain first and last name with proper capitalization")
        assert " " in name1
        parts1 = name1.split()
        assert len(parts1) == 2
        assert parts1[0][0].isupper()
        assert parts1[1][0].isupper()

        assert " " in name2
        parts2 = name2.split()
        assert len(parts2) == 2

    def test_random_sentence_generates_realistic_content(self, story: Scenario) -> None:
        story.given("different context types for sentence generation")
        story.when("_random_sentence generates sentences")
        general = _random_sentence("general")
        accomplishment = _random_sentence("accomplishment")
        project = _random_sentence("project")

        story.then("sentences are readable and context-appropriate")
        assert len(general) > 10
        assert isinstance(general, str)
        assert len(accomplishment) > 10
        assert isinstance(accomplishment, str)
        assert len(project) > 10
        assert isinstance(project, str)

    def test_random_sentence_default_context(self, story: Scenario) -> None:
        story.given("no explicit context")
        story.when("_random_sentence is called with defaults")
        result = _random_sentence()

        story.then("a general technical sentence is generated")
        assert len(result) > 10
        assert isinstance(result, str)

    def test_random_description_multiple_paragraphs(self, story: Scenario) -> None:
        story.given("a requirement for three descriptive paragraphs")
        story.when("_random_description is called")
        result = _random_description(3)
        paragraphs = result.split("\n\n")

        story.then("each paragraph contains realistic technical content")
        assert len(paragraphs) == 3
        for para in paragraphs:
            assert para.strip()
            assert len(para) > 20  # Paragraphs should be substantial

    def test_random_email_format(self, story: Scenario) -> None:
        story.given("a full name used to derive an email")
        story.when("_random_email generates the address")
        result = _random_email("John Doe")

        story.then("the address encodes name, suffix, and domain correctly")
        assert result.startswith("john.doe.")
        assert result.endswith("@example.com")
        parts = result.split("@")[0].split(".")
        assert len(parts) == 3
        assert len(parts[2]) == 8

    def test_random_linkedin_format(self, story: Scenario) -> None:
        story.given("a candidate name for LinkedIn slug generation")
        story.when("_random_linkedin produces a path")
        result = _random_linkedin("Jane Smith")

        story.then("the slug starts with in/ and embeds the normalized name")
        assert result.startswith("in/")
        assert "jane-smith" in result
        assert len(result) >= len("in/jane-smith-xxxx")

    def test_random_reproducibility_with_seed(
        self,
        story: Scenario,
        tmp_path: Path,
    ) -> None:
        story.given("a template file and a deterministic seed")
        template_path = tmp_path / "template.yaml"
        template_path.write_text(
            yaml.dump({"template": "test", "body": {"experience": [], "education": []}})
        )

        story.when("generate_random_yaml runs with seed=42")
        with patch("random.seed") as mock_seed:
            generate_random_yaml(
                output_path=tmp_path / "test.yaml", template_path=template_path, seed=42
            )

        story.then("random.seed is invoked so output becomes reproducible")
        mock_seed.assert_called_once_with(42)


class TestGenerateRandomYaml:
    """Test the main YAML generation functionality."""

    def test_generate_random_yaml_creates_file(
        self,
        story: Scenario,
        tmp_path: Path,
    ) -> None:
        story.given("a template YAML file and destination path")
        output_path = tmp_path / "test_output.yaml"
        template_path = tmp_path / "template.yaml"
        template_path.write_text(
            yaml.dump(
                {
                    "template": "test",
                    "full_name": "Template Name",
                    "body": {"experience": [], "education": []},
                }
            )
        )

        story.when("generate_random_yaml writes a new resume")
        generate_random_yaml(
            output_path=output_path, template_path=template_path, seed=42
        )

        story.then("the file exists, contains YAML, and includes config metadata")
        assert output_path.exists()
        parsed = yaml.safe_load(output_path.read_text(encoding="utf-8"))
        assert parsed["full_name"]
        assert "config" in parsed

    def test_generate_random_yaml_preserves_template_structure(
        self, story: Scenario, tmp_path: Path
    ) -> None:
        story.given("a template file containing specific body structure")
        output_path = tmp_path / "test_output.yaml"
        template_path = tmp_path / "template.yaml"
        template_path.write_text(
            yaml.dump(
                {
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
            )
        )

        story.when("generate_random_yaml derives new content")
        generate_random_yaml(
            output_path=output_path, template_path=template_path, seed=123
        )
        result = yaml.safe_load(output_path.read_text(encoding="utf-8"))

        story.then("structural fields remain while user fields become randomized")
        assert result["template"] == "test_template"
        assert set(result["body"].keys()) >= {"experience", "education"}
        assert result["full_name"] != "Template Name"
        assert result["phone"] != "555-0123"

    def test_generate_random_yaml_adds_config_palette(
        self, story: Scenario, tmp_path: Path
    ) -> None:
        story.given("a minimal template without config data")
        output_path = tmp_path / "test_output.yaml"
        template_path = tmp_path / "template.yaml"
        template_path.write_text(
            yaml.dump(
                {
                    "template": "test",
                    "full_name": "Test",
                    "body": {"experience": []},
                }
            )
        )

        story.when("generate_random_yaml populates config and palette metadata")
        generate_random_yaml(
            output_path=output_path, template_path=template_path, seed=456
        )
        result = yaml.safe_load(output_path.read_text(encoding="utf-8"))

        story.then("the config block includes sane defaults and sidebar sizing")
        config = result["config"]
        assert config["output_mode"] == "markdown"
        assert 58 <= config["sidebar_width"] <= 72

        # Should have palette colors
        color_keys = ["theme_color", "sidebar_color", "bold_color"]
        for key in color_keys:
            assert key in config
            assert config[key].startswith("#")

        # bar_background_color may or may not be present depending on palette size
        if "bar_background_color" in config:
            assert config["bar_background_color"].startswith("#")


class TestMainFunction:
    """Test CLI main function."""

    def test_main_with_default_arguments(
        self, story: Scenario, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        story.given("no CLI overrides are provided")
        monkeypatch.chdir(tmp_path)

        story.when("main() executes with default argv")
        with (
            patch("sys.argv", ["cli_random_palette_demo.py"]),
            patch(
                "simple_resume.cli.random_palette_demo.generate_random_yaml"
            ) as mock_generate,
        ):
            main()

        story.then("generate_random_yaml is invoked with computed defaults")
        mock_generate.assert_called_once()
        assert "output_path" in mock_generate.call_args.kwargs
        assert "template_path" in mock_generate.call_args.kwargs
        assert "seed" in mock_generate.call_args.kwargs

    def test_main_with_custom_arguments(
        self, story: Scenario, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        story.given("custom output, template, and seed arguments")
        monkeypatch.chdir(tmp_path)
        custom_output = tmp_path / "custom.yaml"
        custom_template = tmp_path / "custom_template.yaml"

        story.when("main() parses the CLI invocation")
        with (
            patch(
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
            ),
            patch(
                "simple_resume.cli.random_palette_demo.generate_random_yaml"
            ) as mock_generate,
        ):
            main()

        story.then("the generator is called with the provided paths and seed")
        mock_generate.assert_called_once_with(
            output_path=custom_output, template_path=custom_template, seed=789
        )

    def test_main_outputs_success_message(
        self, story: Scenario, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        story.given("default CLI invocation that succeeds")
        monkeypatch.chdir(tmp_path)

        story.when("main() completes and prints status")
        with (
            patch("sys.argv", ["cli_random_palette_demo.py"]),
            patch("builtins.print") as mock_print,
            patch("simple_resume.cli.random_palette_demo.generate_random_yaml"),
        ):
            main()

        story.then("a success message is emitted")
        mock_print.assert_called_once()
        assert mock_print.call_args[0][0].startswith("Wrote")


class TestRandomGenerationEdgeCases:
    """Test edge cases in random generation."""

    def test_random_words_zero_count(self, story: Scenario) -> None:
        story.given("a request for zero random words")
        story.when("_random_words executes")
        result = _random_words(0)

        story.then("an empty list is returned without error")
        assert result == []

    def test_random_sentence_general_structure(self, story: Scenario) -> None:
        story.given("a short general sentence request")
        story.when("_random_sentence is invoked in general mode")
        result = _random_sentence("general")

        story.then("the output is capitalized, punctuated, and multi-worded")
        assert len(result.split()) >= 3
        assert result[0].isupper()
        assert result.endswith(".")

    def test_random_description_single_paragraph(self, story: Scenario) -> None:
        story.given("only one paragraph is requested")
        story.when("_random_description generates content")
        result = _random_description(1)

        story.then("exactly one non-empty paragraph is produced")
        paragraphs = result.split("\n\n")
        assert len(paragraphs) == 1
        assert paragraphs[0].strip()

    def test_random_email_special_characters(self, story: Scenario) -> None:
        story.given("a name containing apostrophes and hyphens")
        story.when("_random_email formats the address")
        result = _random_email("John O'Connor-Smith")

        story.then("name fragments appear alongside the default domain")
        assert result.endswith("@example.com")
        lower = result.lower()
        assert "john" in lower and "smith" in lower
        assert "o" in lower and "connor" in lower

    def test_random_linkedin_special_characters(self, story: Scenario) -> None:
        story.given("a multi-part name for LinkedIn slugging")
        story.when("_random_linkedin builds the slug")
        result = _random_linkedin("Maria Jose Garcia")

        story.then("normalized components appear in the in/ path")
        assert result.startswith("in/")
        assert "maria-jose-garcia" in result
