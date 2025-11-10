from __future__ import annotations

import pytest

from tests.bdd import scenario


class TestScenarioHelper:
    def test_summary_includes_all_sections(self) -> None:
        story = scenario("Render palette list")
        story.given("an installed palette registry")
        story.when("the CLI lists palettes")
        story.then("the palette names are printed")
        story.background(data_dir="fixtures/palettes", palette_count=42)
        story.note("Covers CLI happy path")

        summary = story.summary()

        assert "Scenario: Render palette list" in summary
        assert "Given:" in summary and "When:" in summary and "Then:" in summary
        assert "Notes:" in summary and "Context:" in summary
        assert "palette_count: 42" in summary

    def test_expect_raises_with_contextual_summary(self) -> None:
        story = scenario("Handle invalid palette")
        story.given("an unknown palette name")
        story.when("the registry lookup runs")

        with pytest.raises(AssertionError) as excinfo:
            story.expect(False, "Palette lookup should fail")

        message = str(excinfo.value)
        assert "Palette lookup should fail" in message
        assert "Scenario: Handle invalid palette" in message
        assert "Given:" in message and "When:" in message
