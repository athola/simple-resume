"""Report generator for ATS scoring results.

Generates storable, human-readable reports from tournament results
in YAML or JSON format.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from oyaml import dump as yaml_dump

from simple_resume.core.ats.base import ScorerName
from simple_resume.core.ats.constants import (
    COMPONENT_WEIGHT_EDUCATION,
    COMPONENT_WEIGHT_EXPERIENCE,
    COMPONENT_WEIGHT_FORMAT,
    COMPONENT_WEIGHT_KEYWORDS,
    COMPONENT_WEIGHT_SEMANTIC,
    COMPONENT_WEIGHT_SKILLS,
    JACCARD_RECOMMENDATION_THRESHOLD,
    MAX_MISSING_KEYWORDS,
    PRIORITY_LOW_THRESHOLD,
    PRIORITY_MEDIUM_THRESHOLD,
    SCORE_EXCELLENT_THRESHOLD,
    SCORE_FAIR_THRESHOLD,
    SCORE_GOOD_THRESHOLD,
    SCORE_POOR_THRESHOLD,
)
from simple_resume.core.ats.tournament import TournamentResult


class ATSReportGenerator:
    """Generates reports from ATS tournament results.

    Produces YAML or JSON reports with:
    - Overall score and ranking
    - Algorithm breakdown
    - Component scores
    - Recommendations for improvement
    - Raw data for analysis
    """

    def __init__(
        self,
        result: TournamentResult,
        resume_file: str | Path = "unknown",
        job_file: str | Path = "unknown",
        job_url: str = "",
    ) -> None:
        """Initialize report generator.

        Args:
            result: TournamentResult from scoring
            resume_file: Path or identifier for resume
            job_file: Path or identifier for job description
            job_url: URL of job posting (if applicable)

        """
        self.result = result
        self.resume_file = str(resume_file)
        self.job_file = str(job_file)
        self.job_url = job_url
        self.generated_at = datetime.now(timezone.utc).isoformat()

    def generate_yaml(self) -> str:
        """Generate YAML report.

        Returns:
            YAML-formatted report string

        """
        report_dict = self._generate_report_dict()
        return str(yaml_dump(report_dict, default_flow_style=False, sort_keys=False))

    def generate_json(self, indent: int = 2) -> str:
        """Generate JSON report.

        Args:
            indent: JSON indentation spaces

        Returns:
            JSON-formatted report string

        """
        report_dict = self._generate_report_dict()
        return json.dumps(report_dict, indent=indent, default=str)

    def _generate_report_dict(self) -> dict[str, Any]:
        """Generate report dictionary structure.

        Returns:
            Dictionary suitable for YAML/JSON serialization

        """
        # Convert overall score to 0-100 scale
        score_100 = self.result.overall_score * 100

        report = {
            "ats_scoring_report": {
                "metadata": self._generate_metadata(),
                "overall_score": {
                    "total": round(score_100, 2),
                    "normalized": round(self.result.overall_score, 4),
                    "status": self._get_status_label(score_100),
                },
                "algorithm_breakdown": self._generate_algorithm_breakdown(),
                "component_scores": self._generate_component_scores_100(),
                "recommendations": self._generate_recommendations(),
            }
        }

        # Add warnings section if any issues occurred (Issue #58)
        warnings = self._generate_warnings()
        if warnings:
            report["ats_scoring_report"]["warnings"] = warnings

        return report

    def _generate_metadata(self) -> dict[str, Any]:
        """Generate metadata section."""
        return {
            "generated_at": self.generated_at,
            "resume_file": self.resume_file,
            "job_description_file": self.job_file,
            "job_url": self.job_url,
            "algorithms_used": self.result.metadata.get("scorer_names", []),
            "scorer_version": "0.2.0",
        }

    def _generate_algorithm_breakdown(self) -> list[dict[str, Any]]:
        """Generate algorithm breakdown section."""
        breakdown = []

        for result in self.result.algorithm_results:
            algorithm_dict = {
                "name": result.name,
                "score": round(result.score, 4),
                "weight": result.weight,
                "weighted_score": round(result.weighted_score, 4),
                "score_100": round(result.score * 100, 2),
            }

            # Add algorithm-specific details
            if "cosine_similarity" in result.details:
                algorithm_dict["cosine_similarity"] = round(
                    result.details["cosine_similarity"], 4
                )

            if "shared_keywords" in result.details:
                shared = result.details["shared_keywords"]
                if shared and isinstance(shared[0], tuple):
                    algorithm_dict["shared_keywords_count"] = len(shared)
                    algorithm_dict["top_shared_keywords"] = [
                        kw[0] if len(kw) > 1 else kw for kw in shared[:5]
                    ]
                elif shared:
                    algorithm_dict["shared_keywords_count"] = len(shared)

            if "matched_keywords" in result.details:
                algorithm_dict["matched_keywords_count"] = len(
                    result.details.get("matched_keywords", [])
                )
                algorithm_dict["missing_keywords_count"] = len(
                    result.details.get("missing_keywords", [])
                )

            breakdown.append(algorithm_dict)

        return breakdown

    def _generate_component_scores_100(self) -> dict[str, Any]:
        """Generate component scores on 0-100 scale."""
        # Map refined rubric components to algorithm scores
        components_100: dict[str, Any] = {}

        # Experience score (weighted average from relevant components)
        experience_relevance = self.result.component_breakdown.get(
            "experience_relevance", 0.0
        )
        jaccard = self.result.component_breakdown.get("word_jaccard", 0.0)
        components_100["experience_relevance"] = round(
            (experience_relevance * 0.6 + jaccard * 0.4) * 100, 2
        )

        # Skills/Keywords
        exact_match = self.result.component_breakdown.get("exact_match_rate", 0.0)
        keyword_density = self.result.component_breakdown.get("keyword_density", 0.0)
        components_100["skill_match"] = round(
            (exact_match * 0.7 + keyword_density * 0.3) * 100, 2
        )

        # Semantic similarity
        semantic = self.result.component_breakdown.get("jaccard_similarity", 0.0)
        components_100["semantic_similarity"] = round(semantic * 100, 2)

        # Keyword coverage
        coverage = self.result.component_breakdown.get("job_keyword_coverage", 0.0)
        components_100["keyword_coverage"] = round(coverage * 100, 2)

        # Overall component breakdown
        components_100["_weights"] = {
            "experience": COMPONENT_WEIGHT_EXPERIENCE,
            "skills": COMPONENT_WEIGHT_SKILLS,
            "semantic": COMPONENT_WEIGHT_SEMANTIC,
            "keywords": COMPONENT_WEIGHT_KEYWORDS,
            "education": COMPONENT_WEIGHT_EDUCATION,
            "format": COMPONENT_WEIGHT_FORMAT,
        }

        return components_100

    def _generate_recommendations(self) -> dict[str, Any]:
        """Generate recommendations based on scores."""
        score_100 = self.result.overall_score * 100

        top_improvements: list[dict[str, Any]] = []
        recommendations = {
            "priority": self._get_priority_level(score_100),
            "overall_assessment": self._get_assessment(score_100),
            "top_improvements": top_improvements,
        }

        # Analyze algorithm results for specific recommendations
        for result in self.result.algorithm_results:
            if result.name == ScorerName.KEYWORD_EXACT:
                missing = result.details.get("missing_keywords", [])
                if missing and len(missing) <= MAX_MISSING_KEYWORDS:
                    keyword_list = ", ".join(missing[:5])
                    top_improvements.append(
                        {
                            "category": "keywords",
                            "suggestion": f"Add missing keywords: {keyword_list}",
                            "impact": f"+{len(missing) * 2} points potential",
                        }
                    )

            if result.name == ScorerName.JACCARD_NGRAM:
                if result.score < JACCARD_RECOMMENDATION_THRESHOLD:
                    top_improvements.append(
                        {
                            "category": "phrasing",
                            "suggestion": (
                                "Use more job description phrases in your resume"
                            ),
                            "impact": "+5-10 points potential",
                        }
                    )

        return recommendations

    def _get_status_label(self, score: float) -> str:
        """Get status label based on score."""
        if score >= SCORE_EXCELLENT_THRESHOLD:
            return "Excellent"
        elif score >= SCORE_GOOD_THRESHOLD:
            return "Good"
        elif score >= SCORE_FAIR_THRESHOLD:
            return "Fair"
        elif score >= SCORE_POOR_THRESHOLD:
            return "Poor"
        else:
            return "Very Poor"

    def _get_priority_level(self, score: float) -> str:
        """Get priority level for improvements."""
        if score >= PRIORITY_LOW_THRESHOLD:
            return "LOW"
        elif score >= PRIORITY_MEDIUM_THRESHOLD:
            return "MEDIUM"
        else:
            return "HIGH"

    def _get_assessment(self, score: float) -> str:
        """Get overall assessment text."""
        if score >= SCORE_EXCELLENT_THRESHOLD:
            return "Strong match for this position. Consider applying with confidence."
        elif score >= SCORE_GOOD_THRESHOLD:
            return "Good match. Minor improvements could strengthen candidacy."
        elif score >= SCORE_FAIR_THRESHOLD:
            return "Moderate match. Consider tailoring resume more specifically."
        elif score >= SCORE_POOR_THRESHOLD:
            return "Weak match. Significant improvements recommended before applying."
        else:
            return "Poor match. Resume does not align well with requirements."

    def _generate_warnings(self) -> list[dict[str, str]]:
        """Generate warnings section from scorer errors and failed scorers.

        Extracts error messages from ScorerResult.details and failed_scorers
        to surface non-fatal issues to users.

        Returns:
            List of warning dictionaries with source and message keys

        """
        warnings: list[dict[str, str]] = []

        # Collect errors from algorithm results
        for alg_result in self.result.algorithm_results:
            error = alg_result.details.get("error")
            if error:
                warnings.append({"source": alg_result.name, "message": str(error)})

        # Collect failed scorer information
        if self.result.failed_scorers:
            for scorer_name, error_msg in self.result.failed_scorers:
                warnings.append({"source": scorer_name, "message": str(error_msg)})

        # Tournament-level errors
        if "error" in self.result.metadata:
            warnings.append(
                {
                    "source": "tournament",
                    "message": str(self.result.metadata["error"]),
                }
            )

        return warnings
