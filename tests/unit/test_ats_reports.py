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
