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
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

from simple_resume.core.ats.base import BaseScorer, ScorerResult
from simple_resume.core.ats.constants import (
    CRITICAL_KEYWORDS_THRESHOLD,
    MIN_FALLBACK_WORD_LENGTH,
    MIN_KEYWORD_LENGTH,
    validate_threshold,
)
from simple_resume.core.ats.creative_terms import (
    Industry,
    expand_term,
    is_creative_term,
)

_STOPWORDS: frozenset[str] = frozenset(
    {
        "the",
        "and",
        "for",
        "are",
        "but",
        "not",
        "you",
        "all",
        "can",
        "had",
        "her",
        "was",
        "one",
        "our",
        "out",
        "has",
        "have",
        "been",
        "were",
        "being",
        "will",
        "with",
        "this",
        "that",
        "from",
        "they",
        "would",
        "there",
        "their",
        "what",
        "about",
        "which",
        "when",
        "make",
        "like",
        "just",
        "over",
        "such",
        "into",
        "than",
        "them",
        "some",
        "could",
        "other",
        "experience",
        "work",
        "working",
        "team",
        "ability",
    }
)


@dataclass(frozen=True)
class KeywordScorerConfig:
    """Configuration for keyword scoring behavior.

    Attributes:
        fuzzy_threshold: Minimum similarity ratio for fuzzy matching (0-1)
        case_sensitive: Whether matching preserves case
        extract_keywords: Whether to auto-extract keywords from job text
        max_keywords: Cap on keywords extracted from job description
        enable_creative_expansion: Expand creative synonyms during matching
        industry: Industry context for creative term mappings
        max_length_diff: Max character length difference for fuzzy candidates

    """

    fuzzy_threshold: float = 0.85
    case_sensitive: bool = False
    extract_keywords: bool = True
    max_keywords: int = 50
    enable_creative_expansion: bool = False
    industry: Industry = Industry.GENERAL
    max_length_diff: int = 3

    def __post_init__(self) -> None:
        """Validate configuration values."""
        validate_threshold(self.fuzzy_threshold, "fuzzy_threshold")


class KeywordScorer(BaseScorer):
    """Exact keyword match scorer with fuzzy tolerance.

    Performs direct keyword matching between resume and job description.
    Supports exact matching, fuzzy matching for typos, and configurable
    keyword extraction.
    """

    def __init__(
        self,
        weight: float = 1.0,
        config: KeywordScorerConfig | None = None,
    ) -> None:
        """Initialize keyword scorer.

        Args:
            weight: Weight in tournament (default: 1.0, must be in [0, 1])
            config: Scoring configuration (uses defaults if None)

        Raises:
            ValueError: If weight is outside [0, 1]

        """
        super().__init__(weight=weight)
        self._config = config or KeywordScorerConfig()

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for keyword matching.

        Args:
            text: Raw text input

        Returns:
            Cleaned text

        """
        if not self._config.case_sensitive:
            text = text.lower()
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    # -- Keyword extraction strategies -------------------------------------------

    @staticmethod
    def _extract_technical_terms(text: str) -> list[str]:
        """Extract CamelCase, ALL_CAPS, and alphanumeric technical terms."""
        pattern = r"\b[A-Z]{2,}\b|\b[A-Z][a-z]+[A-Z][a-z]+\b|\b\w*\d\w*\b"
        return re.findall(pattern, text)

    @staticmethod
    def _extract_quoted_phrases(text: str) -> list[str]:
        """Extract phrases enclosed in double quotes."""
        return re.findall(r'"([^"]+)"', text)

    @staticmethod
    def _extract_skill_patterns(text: str) -> list[str]:
        """Extract words followed by framework/library/language/etc."""
        pattern = (
            r"\b[A-Za-z]{3,}\s?(?:framework|library|language|platform|tool|database)\b"
        )
        return re.findall(pattern, text, re.IGNORECASE)

    @staticmethod
    def _extract_capitalized_words(text: str) -> list[str]:
        """Extract capitalized words (proper nouns, technologies)."""
        return re.findall(r"\b[A-Z][a-z]{2,}\b", text)

    @staticmethod
    def _extract_significant_words(text: str) -> list[str]:
        """Fallback: extract non-stopword words of 4+ characters."""
        results = []
        for word in text.split():
            word_clean = re.sub(r"[^\w]", "", word)
            if (
                len(word_clean) >= MIN_FALLBACK_WORD_LENGTH
                and word_clean.lower() not in _STOPWORDS
                and not word_clean.isdigit()
            ):
                results.append(word_clean)
        return results

    def _deduplicate_keywords(self, keywords: list[str]) -> list[str]:
        """Remove duplicates while preserving order, capped at max_keywords."""
        seen: set[str] = set()
        unique: list[str] = []
        for kw in keywords:
            kw_clean = kw.strip().lower()
            if kw_clean and len(kw_clean) > MIN_KEYWORD_LENGTH and kw_clean not in seen:
                seen.add(kw_clean)
                unique.append(kw.strip())
        return unique[: self._config.max_keywords]

    # -- Main extraction -------------------------------------------------------

    def _extract_keywords(
        self, text: str, original_text: str | None = None
    ) -> list[str]:
        """Extract important keywords from text.

        Applies multiple heuristic strategies in order, falling back to
        significant-word extraction when pattern-based methods find nothing.

        Args:
            text: Preprocessed text
            original_text: Original text before preprocessing (for case-sensitive
                pattern matching). Falls back to text if not provided.

        Returns:
            List of extracted keywords

        """
        if original_text is None:
            original_text = text

        keywords: list[str] = []
        keywords.extend(self._extract_technical_terms(original_text))
        keywords.extend(self._extract_quoted_phrases(original_text))
        keywords.extend(self._extract_skill_patterns(original_text))
        keywords.extend(self._extract_capitalized_words(original_text))

        if not keywords:
            keywords.extend(self._extract_significant_words(text))

        return self._deduplicate_keywords(keywords)

    def _fuzzy_match(
        self,
        keyword: str,
        text: str,
        *,
        word_set: frozenset[str] | None = None,
        words: list[str] | None = None,
    ) -> tuple[bool, float]:
        """Perform fuzzy matching for a keyword against text.

        Uses SequenceMatcher for robust similarity calculation with
        optimizations: set-based exact lookup and length filtering.

        Args:
            keyword: Keyword to find
            text: Text to search in
            word_set: Pre-computed set of words for O(1) exact matching
            words: Pre-computed word list for fuzzy matching

        Returns:
            (found, similarity_score)

        """
        keyword_lower = keyword.lower()

        # Fast path: exact set lookup (O(1) vs O(n) substring scan)
        if word_set is not None and keyword_lower in word_set:
            return True, 1.0

        # Direct substring match
        if keyword in text:
            return True, 1.0

        # Word boundary match
        pattern = r"\b" + re.escape(keyword) + r"\b"
        if re.search(
            pattern, text, re.IGNORECASE if not self._config.case_sensitive else 0
        ):
            return True, 1.0

        # Fuzzy matching with length filtering and early exit
        if words is None:
            words = text.lower().split()
        keyword_len = len(keyword_lower)

        best_similarity = 0.0
        for word in words:
            # Skip words with large length differences (can't be similar)
            if abs(len(word) - keyword_len) > self._config.max_length_diff:
                continue
            matcher = SequenceMatcher(None, keyword_lower, word, autojunk=False)
            similarity = matcher.ratio()
            if similarity >= self._config.fuzzy_threshold:
                return True, similarity
            best_similarity = max(best_similarity, similarity)

        return best_similarity >= self._config.fuzzy_threshold, best_similarity

    def _error_result(self, error: str) -> ScorerResult:
        """Build a zero-score result for error or validation failure cases."""
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
                "creative_terms_expanded": [],
                "error": error,
            },
        )

    def _expand_creative_terms(
        self, keywords: list[str]
    ) -> tuple[set[str], list[dict[str, str]]]:
        """Build expanded keyword set from creative term synonyms.

        Args:
            keywords: Original keywords to expand

        Returns:
            Tuple of (expanded_keywords set, creative_terms_found list)

        """
        expanded: set[str] = set()
        found: list[dict[str, str]] = []
        if not self._config.enable_creative_expansion:
            return expanded, found
        for keyword in keywords:
            if is_creative_term(keyword, self._config.industry):
                synonym = expand_term(keyword, self._config.industry)
                if synonym:
                    found.append({"creative": keyword, "expanded": synonym})
                    expanded.add(synonym)
        return expanded, found

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
            return self._error_result("Empty input provided")

        # Preprocess texts (save originals for case-sensitive pattern matching)
        resume_clean = self._preprocess_text(resume_text)
        job_clean = self._preprocess_text(job_description)

        # Get keywords to match (either provided or extracted)
        keywords = kwargs.get("keywords")
        if keywords is None and self._config.extract_keywords:
            keywords = self._extract_keywords(job_clean, original_text=job_description)
        elif keywords is None:
            # Use all unique words from job as keywords
            keywords = list(set(job_clean.split()))

        if not keywords:
            return self._error_result("No keywords to match")

        # Match keywords against resume
        matched_keywords = []
        missing_keywords = []
        fuzzy_matches = []

        # Work on a copy to avoid mutating the caller's list
        keywords = list(keywords)

        # Expand creative terms into additional match candidates
        expanded_keywords, creative_terms_found = self._expand_creative_terms(keywords)

        # Track original keyword count before adding expansions
        total_keywords = len(keywords)

        # Match original keywords plus expanded terms against resume
        all_match_terms = keywords + list(expanded_keywords)

        # Pre-compute word set and list once for all keyword comparisons
        resume_words = resume_clean.split()
        resume_word_set = frozenset(resume_words)

        for keyword in all_match_terms:
            keyword_clean = keyword if self._config.case_sensitive else keyword.lower()
            found, similarity = self._fuzzy_match(
                keyword_clean,
                resume_clean,
                word_set=resume_word_set,
                words=resume_words,
            )

            if found:
                if similarity >= 1.0:
                    matched_keywords.append(keyword)
                else:
                    fuzzy_matches.append((keyword, float(similarity)))
            else:
                missing_keywords.append(keyword)

        # Calculate score (total_keywords based on original keywords, not expanded)
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
                "creative_terms_expanded": creative_terms_found,
            },
            component_scores=component_scores,
        )
