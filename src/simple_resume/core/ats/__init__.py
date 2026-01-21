"""ATS (Applicant Tracking System) scoring module.

This module provides resume screening and job matching capabilities using
multiple NLP algorithms in a tournament-style scoring system.
"""

from simple_resume.core.ats.base import BaseScorer, ExtractedEntities, ScorerResult
from simple_resume.core.ats.entities import EntityExtractor, extract_entities
from simple_resume.core.ats.jaccard import JaccardScorer
from simple_resume.core.ats.keyword import KeywordScorer
from simple_resume.core.ats.reports import ATSReportGenerator
from simple_resume.core.ats.tfidf import TFIDFScorer
from simple_resume.core.ats.tournament import (
    ATSTournament,
    TournamentResult,
    score_resume,
)

__all__ = [
    "BaseScorer",
    "ScorerResult",
    "ExtractedEntities",
    "EntityExtractor",
    "extract_entities",
    "TFIDFScorer",
    "JaccardScorer",
    "KeywordScorer",
    "ATSTournament",
    "TournamentResult",
    "score_resume",
    "ATSReportGenerator",
]
