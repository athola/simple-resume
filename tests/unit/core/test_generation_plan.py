from __future__ import annotations

from pathlib import Path

from simple_resume.constants import OutputFormat
from simple_resume.core.generation_plan import (
    CommandType,
    GeneratePlanOptions,
    build_generation_plan,
)
from tests.bdd import Scenario


class TestBuildGenerationPlan:
    def test_single_resume_multiple_formats(
        self,
        tmp_path: Path,
        story: Scenario,
    ) -> None:
        story.given("a single resume request that needs multiple formats")
        options = GeneratePlanOptions(
            name="candidate",
            data_dir=tmp_path,
            template="modern",
            output_path=tmp_path / "candidate.pdf",
            output_dir=None,
            preview=False,
            open_after=False,
            browser=None,
            formats=[OutputFormat.PDF, OutputFormat.HTML],
            overrides={"theme_color": "#123456"},
        )

        story.when("the plan builder runs")
        commands = build_generation_plan(options)

        story.then("a single command is generated per requested format")
        assert len(commands) == 2
        assert all(cmd.kind is CommandType.SINGLE for cmd in commands)
        pdf_command = commands[0]
        assert pdf_command.config.name == "candidate"
        assert pdf_command.config.output_path == tmp_path / "candidate.pdf"
        assert pdf_command.overrides["theme_color"] == "#123456"

    def test_batch_plan_single_format(self, tmp_path: Path, story: Scenario) -> None:
        story.given("batch generation should produce a single format")
        output_dir = tmp_path / "output"
        options = GeneratePlanOptions(
            name=None,
            data_dir=tmp_path,
            template="modern",
            output_path=None,
            output_dir=output_dir,
            preview=True,
            open_after=True,
            browser="firefox",
            formats=[OutputFormat.PDF],
            overrides={},
        )

        commands = build_generation_plan(options)

        story.then("one batch-single command is produced")
        assert len(commands) == 1
        command = commands[0]
        assert command.kind is CommandType.BATCH_SINGLE
        assert command.format is OutputFormat.PDF
        assert command.config.output_dir == output_dir
        assert command.config.preview is True
        assert command.config.open_after is True

    def test_batch_plan_multiple_formats(self, tmp_path: Path, story: Scenario) -> None:
        story.given("batch generation should produce multiple formats at once")
        options = GeneratePlanOptions(
            name=None,
            data_dir=tmp_path,
            template=None,
            output_path=None,
            output_dir=tmp_path / "out",
            preview=False,
            open_after=False,
            browser=None,
            formats=[OutputFormat.PDF, OutputFormat.HTML],
            overrides={"color_scheme": "ocean"},
        )

        commands = build_generation_plan(options)

        story.then("a single batch-all command describes the work")
        assert len(commands) == 1
        command = commands[0]
        assert command.kind is CommandType.BATCH_ALL
        assert command.format is None
        assert command.config.formats == [OutputFormat.PDF, OutputFormat.HTML]
        assert command.overrides["color_scheme"] == "ocean"
