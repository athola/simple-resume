"""Tests for ScoringMode enum, tournament mode handling, and --mode CLI flag.

Covers Tasks 12-14 of issue #62: ScoringMode enum, tournament weight
selection by mode, and the CLI --mode argument.
"""

from __future__ import annotations

import pytest

from simple_resume.core.ats import (
    ATSTournament,
    KeywordScorer,
    ScoringMode,
)
from simple_resume.core.ats.constants import (
    FALLBACK_JACCARD_WEIGHT,
    FALLBACK_KEYWORD_WEIGHT,
    FALLBACK_TFIDF_WEIGHT,
    HUMAN_BERT_WEIGHT,
    HUMAN_FALLBACK_JACCARD_WEIGHT,
    HUMAN_FALLBACK_KEYWORD_WEIGHT,
    HUMAN_FALLBACK_TFIDF_WEIGHT,
    HUMAN_JACCARD_WEIGHT,
    HUMAN_KEYWORD_WEIGHT,
    HUMAN_TFIDF_WEIGHT,
)
from simple_resume.shell.cli._screen import _build_tournament
from simple_resume.shell.cli.main import create_parser
from tests.bdd import Scenario

# ================================================================
# Task 12: ScoringMode enum and weight constants
# ================================================================


class TestScoringModeConstants:
    """ScoringMode enum values and weight invariants."""

    def test_ats_enum_value(self, story: Scenario) -> None:
        story.given("the ScoringMode enum")
        story.when("accessing the ATS variant")
        story.then("its value is 'ats'")
        assert ScoringMode.ATS.value == "ats"

    def test_human_enum_value(self, story: Scenario) -> None:
        story.given("the ScoringMode enum")
        story.when("accessing the HUMAN_REVIEWER variant")
        story.then("its value is 'human'")
        assert ScoringMode.HUMAN_REVIEWER.value == "human"

    def test_scoring_mode_is_str_subclass(self, story: Scenario) -> None:
        story.given("the ScoringMode enum")
        story.when("checking its type hierarchy")
        story.then("it is a str subclass for argparse compatibility")
        assert isinstance(ScoringMode.ATS, str)

    def test_human_bert_weights_sum_to_one(self, story: Scenario) -> None:
        story.given("human reviewer weights with BERT")
        total = (
            HUMAN_BERT_WEIGHT
            + HUMAN_TFIDF_WEIGHT
            + HUMAN_JACCARD_WEIGHT
            + HUMAN_KEYWORD_WEIGHT
        )
        story.when("summing all weights")
        story.then("they sum to 1.0")
        assert total == pytest.approx(1.0)

    def test_human_fallback_weights_sum_to_one(self, story: Scenario) -> None:
        story.given("human reviewer fallback weights (no BERT)")
        total = (
            HUMAN_FALLBACK_TFIDF_WEIGHT
            + HUMAN_FALLBACK_JACCARD_WEIGHT
            + HUMAN_FALLBACK_KEYWORD_WEIGHT
        )
        story.when("summing all weights")
        story.then("they sum to 1.0")
        assert total == pytest.approx(1.0)

    def test_construct_from_string(self, story: Scenario) -> None:
        story.given("the string 'human'")
        story.when("constructing a ScoringMode from it")
        mode = ScoringMode("human")
        story.then("it equals HUMAN_REVIEWER")
        assert mode is ScoringMode.HUMAN_REVIEWER


# ================================================================
# Task 13: ATSTournament scoring_mode parameter
# ================================================================


class TestTournamentScoringMode:
    """ATSTournament respects scoring_mode for weight selection."""

    def test_default_mode_is_ats(self, story: Scenario) -> None:
        story.given("a tournament created with default arguments")
        tournament = ATSTournament(include_bert=False)

        story.when("checking the scoring mode")
        story.then("it defaults to ATS")
        assert tournament._scoring_mode == ScoringMode.ATS

    def test_human_mode_uses_fallback_weights(self, story: Scenario) -> None:
        story.given("a tournament in HUMAN_REVIEWER mode without BERT")
        tournament = ATSTournament(
            scoring_mode=ScoringMode.HUMAN_REVIEWER,
            include_bert=False,
        )

        story.when("inspecting the scorer weights")
        weights = {type(s).__name__: s.weight for s in tournament.scorers}

        story.then("human fallback weights are applied")
        assert weights["TFIDFScorer"] == pytest.approx(HUMAN_FALLBACK_TFIDF_WEIGHT)
        assert weights["JaccardScorer"] == pytest.approx(HUMAN_FALLBACK_JACCARD_WEIGHT)
        assert weights["KeywordScorer"] == pytest.approx(HUMAN_FALLBACK_KEYWORD_WEIGHT)

    def test_ats_mode_uses_default_fallback_weights(self, story: Scenario) -> None:
        story.given("a tournament in ATS mode without BERT")
        tournament = ATSTournament(
            scoring_mode=ScoringMode.ATS,
            include_bert=False,
        )

        story.when("inspecting the scorer weights")
        weights = {type(s).__name__: s.weight for s in tournament.scorers}

        story.then("default ATS fallback weights are applied")
        assert weights["TFIDFScorer"] == pytest.approx(FALLBACK_TFIDF_WEIGHT)
        assert weights["JaccardScorer"] == pytest.approx(FALLBACK_JACCARD_WEIGHT)
        assert weights["KeywordScorer"] == pytest.approx(FALLBACK_KEYWORD_WEIGHT)

    def test_explicit_scorers_override_mode(self, story: Scenario) -> None:
        story.given("explicit scorers passed to the tournament")
        custom = [KeywordScorer(weight=1.0)]
        tournament = ATSTournament(
            scorers=custom,
            scoring_mode=ScoringMode.HUMAN_REVIEWER,
        )

        story.when("inspecting the scorers list")
        story.then("the explicit scorers are used, not defaults")
        assert len(tournament.scorers) == 1
        assert isinstance(tournament.scorers[0], KeywordScorer)
        assert tournament.scorers[0].weight == 1.0

    def test_human_mode_enables_creative_expansion(self, story: Scenario) -> None:
        story.given("a tournament in HUMAN_REVIEWER mode without BERT")
        tournament = ATSTournament(
            scoring_mode=ScoringMode.HUMAN_REVIEWER,
            include_bert=False,
        )

        story.when("finding the KeywordScorer")
        kw_scorers = [s for s in tournament.scorers if isinstance(s, KeywordScorer)]

        story.then("creative expansion is enabled on the keyword scorer")
        assert len(kw_scorers) == 1
        assert kw_scorers[0]._config.enable_creative_expansion is True

    def test_ats_mode_disables_creative_expansion(self, story: Scenario) -> None:
        story.given("a tournament in ATS mode without BERT")
        tournament = ATSTournament(
            scoring_mode=ScoringMode.ATS,
            include_bert=False,
        )

        story.when("finding the KeywordScorer")
        kw_scorers = [s for s in tournament.scorers if isinstance(s, KeywordScorer)]

        story.then("creative expansion is disabled on the keyword scorer")
        assert len(kw_scorers) == 1
        assert kw_scorers[0]._config.enable_creative_expansion is False


# ================================================================
# Task 14: CLI --mode flag
# ================================================================


class TestCliModeFlag:
    """CLI parser accepts --mode and defaults to 'ats'."""

    def test_parser_accepts_mode_ats(self, story: Scenario) -> None:
        story.given("screen command with --mode ats")
        parser = create_parser()
        args = parser.parse_args(["screen", "resume.txt", "job.txt", "--mode", "ats"])

        story.when("parsing arguments")
        story.then("args.mode is 'ats'")
        assert args.mode == "ats"

    def test_parser_accepts_mode_human(self, story: Scenario) -> None:
        story.given("screen command with --mode human")
        parser = create_parser()
        args = parser.parse_args(["screen", "resume.txt", "job.txt", "--mode", "human"])

        story.when("parsing arguments")
        story.then("args.mode is 'human'")
        assert args.mode == "human"

    def test_parser_default_mode_is_ats(self, story: Scenario) -> None:
        story.given("screen command without --mode flag")
        parser = create_parser()
        args = parser.parse_args(["screen", "resume.txt", "job.txt"])

        story.when("parsing arguments")
        story.then("args.mode defaults to 'ats'")
        assert args.mode == "ats"

    def test_parser_rejects_invalid_mode(self, story: Scenario) -> None:
        story.given("screen command with --mode invalid")
        parser = create_parser()

        story.when("parsing arguments with an invalid mode")
        with pytest.raises(SystemExit):
            parser.parse_args(["screen", "resume.txt", "job.txt", "--mode", "bad"])

        story.then("the parser exits with an error")


class TestBuildTournamentWithMode:
    """_build_tournament passes scoring_mode correctly."""

    def test_all_scorers_passes_mode(self, story: Scenario) -> None:
        story.given("scorer selection 'all' with HUMAN_REVIEWER mode")
        tournament = _build_tournament("all", scoring_mode=ScoringMode.HUMAN_REVIEWER)

        story.when("inspecting the tournament's scoring mode")
        story.then("HUMAN_REVIEWER mode is set")
        assert tournament._scoring_mode == ScoringMode.HUMAN_REVIEWER

    def test_keyword_scorer_gets_creative_expansion(self, story: Scenario) -> None:
        story.given("scorer selection 'keyword' with HUMAN_REVIEWER mode")
        tournament = _build_tournament(
            "keyword",
            scoring_mode=ScoringMode.HUMAN_REVIEWER,
        )

        story.when("inspecting the keyword scorer config")
        kw = tournament.scorers[0]
        assert isinstance(kw, KeywordScorer)

        story.then("creative expansion is enabled")
        assert kw._config.enable_creative_expansion is True

    def test_keyword_scorer_no_expansion_in_ats(self, story: Scenario) -> None:
        story.given("scorer selection 'keyword' with ATS mode")
        tournament = _build_tournament("keyword", scoring_mode=ScoringMode.ATS)

        story.when("inspecting the keyword scorer config")
        kw = tournament.scorers[0]
        assert isinstance(kw, KeywordScorer)

        story.then("creative expansion is disabled")
        assert kw._config.enable_creative_expansion is False

    def test_default_mode_is_ats(self, story: Scenario) -> None:
        story.given("_build_tournament called without scoring_mode")
        tournament = _build_tournament("all")

        story.when("inspecting the tournament's scoring mode")
        story.then("it defaults to ATS")
        assert tournament._scoring_mode == ScoringMode.ATS
