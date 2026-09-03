"""Discovery (Phase 7): personalised funding matching and relevance ranking."""

from .profile import ResearchProfile
from .scoring import Matchable, rank, score

__all__ = ["Matchable", "ResearchProfile", "rank", "score"]
