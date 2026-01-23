"""Jaccard similarity + N-gram overlap scorer.

This scorer measures resume-job similarity using:
- Jaccard similarity: |A ∩ B| / |A ∪ B| (set intersection over union)
- N-gram overlap: Matching sequences of N words

This is a simple, interpretable approach that:
- Works well for exact phrase matching
- Has no model dependencies
- Is sensitive to word order and phrasing

Pros:
- Simple and interpretable
- Fast computation
- Good for exact phrase matching

Cons:
- Limited to surface-level matching
- Misses semantic variations (synonyms)
- No context understanding
"""

from __future__ import annotations

import re
from typing import Any

from simple_resume.core.ats.base import BaseScorer, ScorerResult
from simple_resume.core.ats.constants import (
    MAX_SHARED_NGRAMS,
    PHRASE_MATCH_BONUS_THRESHOLD,
    validate_ngram_range,
    validate_weight,
)


class JaccardScorer(BaseScorer):
    """Jaccard similarity + N-gram overlap scorer.

    Measures similarity between resume and job description using:
    1. Jaccard similarity on word sets
    2. N-gram overlap for phrase matching

    Jaccard formula: J(A,B) = |A ∩ B| / |A ∪ B|

    Range: 0.0 (no overlap) to 1.0 (identical)
    """

    def __init__(
        self,
        weight: float = 1.0,
        ngram_range: tuple[int, int] = (1, 3),
        case_sensitive: bool = False,
    ) -> None:
        """Initialize Jaccard scorer.

        Args:
            weight: Weight in tournament (default: 1.0, must be in [0, 1])
            ngram_range: Range of n-grams to generate (min_n, max_n), both >= 1
            case_sensitive: Whether to preserve case (default: False)

        Raises:
            ValueError: If weight is outside [0, 1] or ngram_range is invalid

        """
        validate_weight(weight, "weight")
        validate_ngram_range(ngram_range, "ngram_range")
        super().__init__(weight=weight)
        self.ngram_range = ngram_range
        self.case_sensitive = case_sensitive

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for n-gram generation.

        Args:
            text: Raw text input

        Returns:
            Cleaned text

        """
        if not self.case_sensitive:
            text = text.lower()
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove punctuation but keep word separators
        text = re.sub(r"[^\w\s]", " ", text)
        return text.strip()

    def _generate_ngrams(
        self,
        text: str,
        n: int,
    ) -> set[str]:
        """Generate n-grams from text.

        Args:
            text: Preprocessed text
            n: N-gram size (1=unigram, 2=bigram, etc.)

        Returns:
            Set of n-grams

        """
        words = text.split()
        if len(words) < n:
            return {text}  # Return entire text as single "gram" if too short

        ngrams = set()
        for i in range(len(words) - n + 1):
            ngram = " ".join(words[i : i + n])
            ngrams.add(ngram)
        return ngrams

    def _calculate_jaccard(
        self,
        set1: set[str],
        set2: set[str],
    ) -> float:
        """Calculate Jaccard similarity between two sets.

        Jaccard formula: J(A,B) = |A ∩ B| / |A ∪ B|

        Edge case convention: Returns 1.0 when both sets are empty.
        Rationale: Two empty documents are "identical" in terms of content
        (both have no words), which is the expected behavior for resume
        similarity scoring. An alternative mathematical approach would
        return 0.0 (undefined), but that would incorrectly signal
        dissimilarity for matching empty inputs.

        Args:
            set1: First set
            set2: Second set

        Returns:
            Jaccard similarity in [0, 1]

        """
        if not set1 and not set2:
            return 1.0  # Both empty = identical (see docstring rationale)
        if not set1 or not set2:
            return 0.0  # One empty = no overlap

        intersection = set1 & set2
        union = set1 | set2

        return len(intersection) / len(union)

    def score(
        self,
        resume_text: str,
        job_description: str,
        **kwargs: Any,
    ) -> ScorerResult:
        """Score resume against job description using Jaccard + n-gram overlap.

        Args:
            resume_text: Full resume text
            job_description: Full job description text
            **kwargs: Additional parameters (unused)

        Returns:
            ScorerResult with Jaccard similarity and n-gram details

        """
        # Handle edge cases
        if not resume_text.strip() or not job_description.strip():
            return ScorerResult(
                name="jaccard_ngram",
                score=0.0,
                weight=self.weight,
                details={
                    "jaccard_similarity": 0.0,
                    "ngram_range": self.ngram_range,
                    "shared_ngrams": [],
                    "error": "Empty input provided",
                },
            )

        # Preprocess texts
        resume_clean = self._preprocess_text(resume_text)
        job_clean = self._preprocess_text(job_description)

        # Calculate scores for each n-gram size
        ngram_scores = {}
        all_shared_ngrams = []

        for n in range(self.ngram_range[0], self.ngram_range[1] + 1):
            resume_ngrams = self._generate_ngrams(resume_clean, n)
            job_ngrams = self._generate_ngrams(job_clean, n)

            jaccard_score = self._calculate_jaccard(resume_ngrams, job_ngrams)
            ngram_scores[f"{n}-gram"] = float(jaccard_score)

            # Collect shared ngrams for analysis
            shared = resume_ngrams & job_ngrams
            if shared:
                for ngram in shared:
                    all_shared_ngrams.append((n, ngram))

        # Calculate overall score (weighted average of n-gram scores)
        # Higher n-grams get more weight (phrase matching > word matching)
        total_weight = 0.0
        weighted_score = 0.0
        for n in range(self.ngram_range[0], self.ngram_range[1] + 1):
            weight = n  # n=1 gets weight 1, n=2 gets weight 2, etc.
            total_weight += weight
            weighted_score += ngram_scores[f"{n}-gram"] * weight

        overall_score = weighted_score / total_weight if total_weight > 0 else 0.0

        # Sort shared n-grams by length (longer phrases first)
        all_shared_ngrams.sort(key=lambda x: x[0], reverse=True)
        # Limit to top shared n-grams
        top_shared = all_shared_ngrams[:MAX_SHARED_NGRAMS]

        # Calculate component scores
        component_scores = self._calculate_component_scores(resume_clean, job_clean)

        return ScorerResult(
            name="jaccard_ngram",
            score=overall_score,
            weight=self.weight,
            details={
                "jaccard_similarity": overall_score,
                "ngram_range": self.ngram_range,
                "ngram_scores": ngram_scores,
                "shared_ngrams": top_shared,
                "shared_count": len(all_shared_ngrams),
                "case_sensitive": self.case_sensitive,
            },
            component_scores=component_scores,
        )

    def _calculate_component_scores(
        self,
        resume_clean: str,
        job_clean: str,
    ) -> dict[str, float]:
        """Calculate component scores based on Jaccard analysis.

        Args:
            resume_clean: Preprocessed resume text
            job_clean: Preprocessed job description text

        Returns:
            Dictionary of component scores

        """
        # Word-level Jaccard (unigrams)
        resume_words = set(resume_clean.split())
        job_words = set(job_clean.split())

        word_jaccard = self._calculate_jaccard(resume_words, job_words)

        # Unique word ratio (how many unique words from job are in resume)
        unique_job_words = job_words - resume_words
        coverage = 1.0 - (len(unique_job_words) / len(job_words)) if job_words else 0.0

        return {
            "word_jaccard": word_jaccard,
            "job_keyword_coverage": coverage,
            "phrase_match_bonus": max(0.0, word_jaccard - PHRASE_MATCH_BONUS_THRESHOLD)
            * 2,
        }
