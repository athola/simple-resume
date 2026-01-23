"""Exact keyword match scorer with fuzzy tolerance.

This scorer performs direct keyword matching between resume and job description:
- Exact word/phrase matching
- Fuzzy matching for spelling variations (using SequenceMatcher)
- Configurable keyword extraction from job descriptions

This is the most traditional ATS approach, simulating how older
systems filter resumes based on keyword presence.

Pros:
- Fast and simple
- Easy to understand and explain
- Good for hard requirements (e.g., specific technologies)

Cons:
- Misses semantic variations
- Penalizes creative language
- Vulnerable to keyword stuffing
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from simple_resume.core.ats.base import BaseScorer, ScorerResult
from simple_resume.core.ats.constants import (
    CRITICAL_KEYWORDS_THRESHOLD,
    MIN_KEYWORD_LENGTH,
    validate_threshold,
    validate_weight,
)


class KeywordScorer(BaseScorer):
    """Exact keyword match scorer with fuzzy tolerance.

    Performs direct keyword matching between resume and job description.
    Supports exact matching, fuzzy matching for typos, and configurable
    keyword extraction.
    """

    def __init__(
        self,
        weight: float = 1.0,
        fuzzy_threshold: float = 0.85,
        case_sensitive: bool = False,
        extract_keywords: bool = True,
        max_keywords: int = 50,
    ) -> None:
        """Initialize keyword scorer.

        Args:
            weight: Weight in tournament (default: 1.0, must be in [0, 1])
            fuzzy_threshold: Minimum similarity for fuzzy match (must be in [0, 1])
            case_sensitive: Whether to preserve case (default: False)
            extract_keywords: Whether to auto-extract keywords (default: True)
            max_keywords: Maximum keywords to extract from job description

        Raises:
            ValueError: If weight or fuzzy_threshold are outside [0, 1]

        """
        validate_weight(weight, "weight")
        validate_threshold(fuzzy_threshold, "fuzzy_threshold")
        super().__init__(weight=weight)
        self.fuzzy_threshold = fuzzy_threshold
        self.case_sensitive = case_sensitive
        self.extract_keywords = extract_keywords
        self.max_keywords = max_keywords

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for keyword matching.

        Args:
            text: Raw text input

        Returns:
            Cleaned text

        """
        if not self.case_sensitive:
            text = text.lower()
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract important keywords from text.

        Uses simple heuristics to identify likely keywords:
        - Technical terms (capitalized words, acronyms)
        - Skills (common patterns)
        - Experience phrases

        Args:
            text: Preprocessed text

        Returns:
            List of extracted keywords

        """
        keywords = []

        # Extract technical terms (words with internal caps, acronyms)
        # Pattern: CamelCase, ALL_CAPS, words with numbers
        technical_pattern = r"\b[A-Z]{2,}\b|\b[A-Z][a-z]+[A-Z][a-z]+\b|\b\w*\d\w*\b"
        technical_matches = re.findall(technical_pattern, text)
        keywords.extend(technical_matches)

        # Extract phrases in quotes (often important skills/technologies)
        quote_pattern = r'"([^"]+)"'
        quote_matches = re.findall(quote_pattern, text)
        keywords.extend(quote_matches)

        # Common skill/technology patterns
        # Words with 3+ consecutive consonants or specific patterns
        skill_pattern = (
            r"\b[A-Za-z]{3,}\s?(?:framework|library|language|platform|tool|database)\b"
        )
        skill_matches = re.findall(skill_pattern, text, re.IGNORECASE)
        keywords.extend(skill_matches)

        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            kw_clean = kw.strip().lower()
            if kw_clean and len(kw_clean) > MIN_KEYWORD_LENGTH and kw_clean not in seen:
                seen.add(kw_clean)
                unique_keywords.append(kw.strip())

        return unique_keywords[: self.max_keywords]

    def _fuzzy_match(
        self,
        keyword: str,
        text: str,
    ) -> tuple[bool, float]:
        """Perform fuzzy matching for a keyword against text.

        Uses SequenceMatcher for robust similarity calculation.

        Args:
            keyword: Keyword to find
            text: Text to search in

        Returns:
            (found, similarity_score)

        """
        # Direct match
        if keyword in text:
            return True, 1.0

        # Word boundary match
        pattern = r"\b" + re.escape(keyword) + r"\b"
        if re.search(pattern, text, re.IGNORECASE if not self.case_sensitive else 0):
            return True, 1.0

        # Fuzzy matching using SequenceMatcher
        # Check similarity with each word in text
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        words = text_lower.split()

        best_similarity = 0.0
        for word in words:
            # Use SequenceMatcher for proper fuzzy matching
            matcher = SequenceMatcher(None, keyword_lower, word, autojunk=False)
            similarity = matcher.ratio()
            best_similarity = max(best_similarity, similarity)

        return best_similarity >= self.fuzzy_threshold, best_similarity

    def score(
        self,
        resume_text: str,
        job_description: str,
        **kwargs: Any,
    ) -> ScorerResult:
        """Score resume against job description using exact keyword matching.

        Args:
            resume_text: Full resume text
            job_description: Full job description text
            **kwargs: Additional parameters including:
                - keywords: Optional list of specific keywords to match

        Returns:
            ScorerResult with keyword match score and details

        """
        # Handle edge cases
        if not resume_text.strip() or not job_description.strip():
            return ScorerResult(
                name="keyword_exact",
                score=0.0,
                weight=self.weight,
                details={
                    "exact_matches": 0,
                    "total_keywords": 0,
                    "matched_keywords": [],
                    "missing_keywords": [],
                    "error": "Empty input provided",
                },
            )

        # Preprocess texts
        resume_clean = self._preprocess_text(resume_text)
        job_clean = self._preprocess_text(job_description)

        # Get keywords to match (either provided or extracted)
        keywords = kwargs.get("keywords")
        if keywords is None and self.extract_keywords:
            keywords = self._extract_keywords(job_clean)
        elif keywords is None:
            # Use all unique words from job as keywords
            keywords = list(set(job_clean.split()))

        if not keywords:
            return ScorerResult(
                name="keyword_exact",
                score=0.0,
                weight=self.weight,
                details={
                    "exact_matches": 0,
                    "fuzzy_matches": 0,
                    "total_keywords": 0,
                    "matched_keywords": [],
                    "fuzzy_matched": [],
                    "missing_keywords": [],
                    "error": "No keywords to match",
                },
            )

        # Match keywords against resume
        matched_keywords = []
        missing_keywords = []
        fuzzy_matches = []

        for keyword in keywords:
            keyword_clean = keyword if self.case_sensitive else keyword.lower()
            found, similarity = self._fuzzy_match(keyword_clean, resume_clean)

            if found:
                if similarity >= 1.0:
                    matched_keywords.append(keyword)
                else:
                    fuzzy_matches.append((keyword, float(similarity)))
            else:
                missing_keywords.append(keyword)

        # Calculate score
        total_keywords = len(keywords)
        exact_match_count = len(matched_keywords)
        fuzzy_match_count = len(fuzzy_matches)

        # Weight exact matches higher than fuzzy matches
        exact_score = exact_match_count / total_keywords if total_keywords > 0 else 0.0
        fuzzy_bonus = (
            fuzzy_match_count / total_keywords * 0.5 if total_keywords > 0 else 0.0
        )

        overall_score = exact_score + fuzzy_bonus
        overall_score = min(1.0, overall_score)  # Cap at 1.0

        # Calculate component scores
        component_scores = {
            "exact_match_rate": exact_score,
            "fuzzy_match_rate": (
                fuzzy_match_count / total_keywords if total_keywords > 0 else 0.0
            ),
            "critical_keywords_present": (
                1.0
                if exact_match_count >= (total_keywords * CRITICAL_KEYWORDS_THRESHOLD)
                else 0.0
            ),
        }

        return ScorerResult(
            name="keyword_exact",
            score=overall_score,
            weight=self.weight,
            details={
                "exact_matches": exact_match_count,
                "fuzzy_matches": fuzzy_match_count,
                "total_keywords": total_keywords,
                "matched_keywords": matched_keywords,
                "fuzzy_matched": fuzzy_matches,
                "missing_keywords": missing_keywords,
                "match_rate": overall_score,
            },
            component_scores=component_scores,
        )
