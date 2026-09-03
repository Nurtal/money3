"""Research profile (Phase 7).

A user describes what they look for: research areas, associated technologies,
a minimum funding level and the relevant geographies. The profile is used as
input to the relevance scorer, which ranks AAPs by how well they match.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ResearchProfile(BaseModel):
    """Personalised funding-discovery criteria (README: Phase 7)."""

    research_topics: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    amount_min: int | None = None
    geographies: list[str] = Field(default_factory=list)
