"""Unit tests for ATS report generator."""

from __future__ import annotations

import json

import pytest

from simple_resume import ATSReportGenerator, TournamentResult
from simple_resume.core.ats.base import ScorerResult


@pytest.fixture
def sample_tournament_result() -> TournamentResult:
    """Create a sample tournament result for testing."""
    algorithm_results = [
        ScorerResult(
            name="keyword_exact",
            score=0.6,
            weight=0.3,
            details={
                "matched_keywords": ["python", "django"],
                "missing_keywords": ["flask", "fastapi"],
            },
        ),
        ScorerResult(
            name="jaccard_ngram",
            score=0.4,
            weight=0.3,
            details={
                "cosine_similarity": 0.75,
            },
        ),
        ScorerResult(
            name="tfidf_cosine",
            score=0.7,
            weight=0.4,
            details={
                "shared_keywords": [("python", 0.8), ("django", 0.6)],
            },
        ),
    ]

    return TournamentResult(
        overall_score=0.57,  # Weighted average
        algorithm_results=algorithm_results,
        component_breakdown={
            "experience_relevance": 0.5,
            "exact_match_rate": 0.6,
            "keyword_density": 0.5,
            "jaccard_similarity": 0.4,
            "job_keyword_coverage": 0.6,
            "word_jaccard": 0.3,
        },
        metadata={
            "scorer_names": ["keyword_exact", "jaccard_ngram", "tfidf_cosine"],
        },
    )


class TestATSReportGenerator:
    """Test suite for ATSReportGenerator."""

    def test_initialization(self, sample_tournament_result: TournamentResult) -> None:
        """Test report generator initialization."""
        generator = ATSReportGenerator(
            result=sample_tournament_result,
            resume_file="resume.yaml",
            job_file="job.txt",
            job_url="https://example.com/job",
        )

        assert generator.result == sample_tournament_result
        assert generator.resume_file == "resume.yaml"
        assert generator.job_file == "job.txt"
        assert generator.job_url == "https://example.com/job"
        assert isinstance(generator.generated_at, str)

    def test_initialization_with_defaults(
        self, sample_tournament_result: TournamentResult
    ) -> None:
        """Test report generator initialization with default values."""
        generator = ATSReportGenerator(result=sample_tournament_result)

        assert generator.resume_file == "unknown"
        assert generator.job_file == "unknown"
        assert generator.job_url == ""

    def test_generate_yaml_returns_string(
        self, sample_tournament_result: TournamentResult
    ) -> None:
        """Test YAML generation returns valid string."""
        generator = ATSReportGenerator(result=sample_tournament_result)
        yaml_report = generator.generate_yaml()

        assert isinstance(yaml_report, str)
        assert len(yaml_report) > 0
        assert "ats_scoring_report:" in yaml_report
        assert "metadata:" in yaml_report
        assert "overall_score:" in yaml_report

    def test_generate_json_returns_valid_json(
        self, sample_tournament_result: TournamentResult
    ) -> None:
        """Test JSON generation returns valid JSON string."""
        generator = ATSReportGenerator(result=sample_tournament_result)
        json_report = generator.generate_json()

        assert isinstance(json_report, str)
        parsed = json.loads(json_report)
        assert "ats_scoring_report" in parsed

    def test_metadata_generation(
        self, sample_tournament_result: TournamentResult
    ) -> None:
        """Test metadata section generation."""
        generator = ATSReportGenerator(
            result=sample_tournament_result,
            resume_file="test.yaml",
            job_file="job.txt",
            job_url="https://example.com",
        )

        metadata = generator._generate_metadata()

        assert metadata["resume_file"] == "test.yaml"
        assert metadata["job_description_file"] == "job.txt"
        assert metadata["job_url"] == "https://example.com"
        assert "generated_at" in metadata
        assert isinstance(metadata["algorithms_used"], list)
        assert len(metadata["algorithms_used"]) == 3

    def test_algorithm_breakdown(
        self, sample_tournament_result: TournamentResult
    ) -> None:
        """Test algorithm breakdown generation."""
        generator = ATSReportGenerator(result=sample_tournament_result)
        breakdown = generator._generate_algorithm_breakdown()

        assert len(breakdown) == 3

        # Check keyword_exact result
        keyword_result = next(r for r in breakdown if r["name"] == "keyword_exact")
        assert keyword_result["matched_keywords_count"] == 2
        assert keyword_result["missing_keywords_count"] == 2
        assert "score" in keyword_result
        assert "weight" in keyword_result

    def test_component_scores_generation(
        self, sample_tournament_result: TournamentResult
    ) -> None:
        """Test component scores generation."""
        generator = ATSReportGenerator(result=sample_tournament_result)
        components = generator._generate_component_scores_100()

        assert "experience_relevance" in components
        assert "skill_match" in components
        assert "semantic_similarity" in components
        assert "keyword_coverage" in components
        assert "_weights" in components

        # All scores should be between 0 and 100
        for key, value in components.items():
            if key != "_weights":
                assert 0 <= value <= 100, f"{key}: {value}"

    def test_status_label_excellent(self) -> None:
        """Test status label for excellent score."""
        result = TournamentResult(
            overall_score=0.85,
            algorithm_results=[],
            component_breakdown={},
            metadata={"scorer_names": []},
        )
        generator = ATSReportGenerator(result=result)

        assert generator._get_status_label(85) == "Excellent"
        assert generator._get_status_label(80) == "Excellent"

    def test_status_label_good(self) -> None:
        """Test status label for good score."""
        result = TournamentResult(
            overall_score=0.7,
            algorithm_results=[],
            component_breakdown={},
            metadata={"scorer_names": []},
        )
        generator = ATSReportGenerator(result=result)

        assert generator._get_status_label(75) == "Good"
        assert generator._get_status_label(65) == "Good"

    def test_status_label_fair(self) -> None:
        """Test status label for fair score."""
        result = TournamentResult(
            overall_score=0.55,
            algorithm_results=[],
            component_breakdown={},
            metadata={"scorer_names": []},
        )
        generator = ATSReportGenerator(result=result)

        assert generator._get_status_label(60) == "Fair"
        assert generator._get_status_label(50) == "Fair"

    def test_status_label_poor(self) -> None:
        """Test status label for poor score."""
        result = TournamentResult(
            overall_score=0.4,
            algorithm_results=[],
            component_breakdown={},
            metadata={"scorer_names": []},
        )
        generator = ATSReportGenerator(result=result)

        assert generator._get_status_label(40) == "Poor"
        assert generator._get_status_label(35) == "Poor"

    def test_status_label_very_poor(self) -> None:
        """Test status label for very poor score."""
        result = TournamentResult(
            overall_score=0.2,
            algorithm_results=[],
            component_breakdown={},
            metadata={"scorer_names": []},
        )
        generator = ATSReportGenerator(result=result)

        assert generator._get_status_label(30) == "Very Poor"
        assert generator._get_status_label(0) == "Very Poor"

    def test_priority_levels(self) -> None:
        """Test priority level classification."""
        result = TournamentResult(
            overall_score=0.5,
            algorithm_results=[],
            component_breakdown={},
            metadata={"scorer_names": []},
        )
        generator = ATSReportGenerator(result=result)

        assert generator._get_priority_level(80) == "LOW"
        assert generator._get_priority_level(70) == "LOW"
        assert generator._get_priority_level(60) == "MEDIUM"
        assert generator._get_priority_level(50) == "MEDIUM"
        assert generator._get_priority_level(40) == "HIGH"

    def test_assessment_text(self) -> None:
        """Test assessment text generation."""
        result = TournamentResult(
            overall_score=0.5,
            algorithm_results=[],
            component_breakdown={},
            metadata={"scorer_names": []},
        )
        generator = ATSReportGenerator(result=result)

        excellent_assessment = generator._get_assessment(85)
        good_assessment = generator._get_assessment(70)
        fair_assessment = generator._get_assessment(55)
        poor_assessment = generator._get_assessment(40)
        very_poor_assessment = generator._get_assessment(20)

        assert "confidence" in excellent_assessment.lower()
        assert "minor" in good_assessment.lower()
        assert "tailoring" in fair_assessment.lower()
        assert "significant" in poor_assessment.lower()
        assert "does not align" in very_poor_assessment.lower()


# ============================================================================
# Issue #69: Threshold Boundary Tests for Report Generator
# ============================================================================


class TestReportGeneratorThresholdBoundaries:
    """Test suite for exact threshold boundary conditions."""

    @pytest.fixture
    def make_generator(self):
        """Create ATSReportGenerator with specific score."""

        def _make(score: float) -> ATSReportGenerator:
            result = TournamentResult(
                overall_score=score,
                algorithm_results=[],
                component_breakdown={},
                metadata={"scorer_names": []},
            )
            return ATSReportGenerator(result=result)

        return _make

    # -------------------------------------------------------------------------
    # Status Label Boundary Tests (SCORE_EXCELLENT_THRESHOLD = 80)
    # -------------------------------------------------------------------------

    def test_status_label_excellent_at_exactly_80(self, make_generator) -> None:
        """Test that score of exactly 80 returns 'Excellent'."""
        generator = make_generator(0.80)
        assert generator._get_status_label(80) == "Excellent"

    def test_status_label_good_at_79_99(self, make_generator) -> None:
        """Test that score of 79.99 returns 'Good' (not 'Excellent')."""
        generator = make_generator(0.7999)
        assert generator._get_status_label(79.99) == "Good"

    def test_status_label_good_at_exactly_65(self, make_generator) -> None:
        """Test that score of exactly 65 returns 'Good'."""
        generator = make_generator(0.65)
        assert generator._get_status_label(65) == "Good"

    def test_status_label_fair_at_64_99(self, make_generator) -> None:
        """Test that score of 64.99 returns 'Fair' (not 'Good')."""
        generator = make_generator(0.6499)
        assert generator._get_status_label(64.99) == "Fair"

    def test_status_label_fair_at_exactly_50(self, make_generator) -> None:
        """Test that score of exactly 50 returns 'Fair'."""
        generator = make_generator(0.50)
        assert generator._get_status_label(50) == "Fair"

    def test_status_label_poor_at_49_99(self, make_generator) -> None:
        """Test that score of 49.99 returns 'Poor' (not 'Fair')."""
        generator = make_generator(0.4999)
        assert generator._get_status_label(49.99) == "Poor"

    def test_status_label_poor_at_exactly_35(self, make_generator) -> None:
        """Test that score of exactly 35 returns 'Poor'."""
        generator = make_generator(0.35)
        assert generator._get_status_label(35) == "Poor"

    def test_status_label_very_poor_at_34_99(self, make_generator) -> None:
        """Test that score of 34.99 returns 'Very Poor' (not 'Poor')."""
        generator = make_generator(0.3499)
        assert generator._get_status_label(34.99) == "Very Poor"

    def test_status_label_very_poor_at_zero(self, make_generator) -> None:
        """Test that score of 0 returns 'Very Poor'."""
        generator = make_generator(0.0)
        assert generator._get_status_label(0) == "Very Poor"

    def test_status_label_excellent_at_100(self, make_generator) -> None:
        """Test that score of 100 returns 'Excellent'."""
        generator = make_generator(1.0)
        assert generator._get_status_label(100) == "Excellent"

    # -------------------------------------------------------------------------
    # Priority Level Boundary Tests (LOW=70, MEDIUM=50)
    # -------------------------------------------------------------------------

    def test_priority_low_at_exactly_70(self, make_generator) -> None:
        """Test that score of exactly 70 returns 'LOW' priority."""
        generator = make_generator(0.70)
        assert generator._get_priority_level(70) == "LOW"

    def test_priority_medium_at_69_99(self, make_generator) -> None:
        """Test that score of 69.99 returns 'MEDIUM' priority (not 'LOW')."""
        generator = make_generator(0.6999)
        assert generator._get_priority_level(69.99) == "MEDIUM"

    def test_priority_medium_at_exactly_50(self, make_generator) -> None:
        """Test that score of exactly 50 returns 'MEDIUM' priority."""
        generator = make_generator(0.50)
        assert generator._get_priority_level(50) == "MEDIUM"

    def test_priority_high_at_49_99(self, make_generator) -> None:
        """Test that score of 49.99 returns 'HIGH' priority (not 'MEDIUM')."""
        generator = make_generator(0.4999)
        assert generator._get_priority_level(49.99) == "HIGH"

    def test_priority_high_at_zero(self, make_generator) -> None:
        """Test that score of 0 returns 'HIGH' priority."""
        generator = make_generator(0.0)
        assert generator._get_priority_level(0) == "HIGH"

    def test_priority_low_at_100(self, make_generator) -> None:
        """Test that score of 100 returns 'LOW' priority."""
        generator = make_generator(1.0)
        assert generator._get_priority_level(100) == "LOW"

    # -------------------------------------------------------------------------
    # Assessment Text Boundary Tests
    # -------------------------------------------------------------------------

    def test_assessment_changes_at_80_boundary(self, make_generator) -> None:
        """Test that assessment text changes at 80 threshold."""
        generator = make_generator(0.80)
        assessment_at_80 = generator._get_assessment(80)
        assessment_at_79 = generator._get_assessment(79.99)

        assert "confidence" in assessment_at_80.lower()
        assert "confidence" not in assessment_at_79.lower()

    def test_assessment_changes_at_65_boundary(self, make_generator) -> None:
        """Test that assessment text changes at 65 threshold."""
        generator = make_generator(0.65)
        assessment_at_65 = generator._get_assessment(65)
        assessment_at_64 = generator._get_assessment(64.99)

        assert "minor" in assessment_at_65.lower()
        assert "minor" not in assessment_at_64.lower()

    def test_assessment_changes_at_50_boundary(self, make_generator) -> None:
        """Test that assessment text changes at 50 threshold."""
        generator = make_generator(0.50)
        assessment_at_50 = generator._get_assessment(50)
        assessment_at_49 = generator._get_assessment(49.99)

        assert "tailoring" in assessment_at_50.lower()
        assert "tailoring" not in assessment_at_49.lower()

    def test_assessment_changes_at_35_boundary(self, make_generator) -> None:
        """Test that assessment text changes at 35 threshold."""
        generator = make_generator(0.35)
        assessment_at_35 = generator._get_assessment(35)
        assessment_at_34 = generator._get_assessment(34.99)

        assert "significant" in assessment_at_35.lower()
        assert "does not align" in assessment_at_34.lower()
