"""ATS (Applicant Tracking System) scoring module.

This module provides resume screening and job matching capabilities using
multiple NLP algorithms in a tournament-style scoring system.
"""

from simple_resume.core.ats.base import (
    BaseScorer,
    Degree,
    DegreeType,
    ExtractedEntities,
    ScorerName,
    ScorerResult,
    ScorerSelection,
)
from simple_resume.core.ats.entities import (
    EntityExtractor,
    ParsedDocument,
    extract_entities,
    parse,
)
from simple_resume.core.ats.jaccard import JaccardScorer
from simple_resume.core.ats.keyword import KeywordScorer
from simple_resume.core.ats.reports import ATSReportGenerator
from simple_resume.core.ats.tfidf import TFIDFScorer
from simple_resume.core.ats.tournament import (
    ATSTournament,
    TournamentResult,
    score_resume,
)

# BERT scorer is optional - only available if sentence-transformers installed
try:
    from simple_resume.core.ats.bert import BERTScorer
except ImportError:
    BERTScorer = None  # type: ignore[assignment, misc]

__all__ = [
    "BaseScorer",
    "Degree",
    "DegreeType",
    "ScorerName",
    "ScorerResult",
    "ScorerSelection",
    "ExtractedEntities",
    "EntityExtractor",
    "ParsedDocument",
    "extract_entities",
    "parse",
    "TFIDFScorer",
    "JaccardScorer",
    "KeywordScorer",
    "BERTScorer",
    "ATSTournament",
    "TournamentResult",
    "score_resume",
    "ATSReportGenerator",
]
