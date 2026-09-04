"""Canonical AAP schema.

This module is the single source of truth for the AAP data model. It must NOT
be changed casually: per the project conventions any modification to the
canonical schema requires an explicit Architectural Decision Record (ADR).
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AAPStatus(str, Enum):
    """Lifecycle states for an AAP (README: AAP lifecycle)."""

    UPCOMING = "upcoming"
    OPEN = "open"
    CLOSING_SOON = "closing_soon"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"


class Provenance(BaseModel):
    """Traceability metadata required for every extracted value.

    The project mandates that extracted data remains traceable to its source
    (source text/url, method, model + prompt version, timestamp).
    """

    source_url: Optional[str] = None
    source_text: Optional[str] = None
    extraction_method: str
    model_version: Optional[str] = None
    prompt_version: Optional[str] = None
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class AAPExtraction(BaseModel):
    """Canonical, normalised representation of a single AAP.

    Mirrors the field table in the README. ``None`` means the value was not
    extracted; extractors must never invent missing information.
    """

    title: Optional[str] = None
    organisation: Optional[str] = None
    description: Optional[str] = None
    amount_min: Optional[int] = None
    amount_max: Optional[int] = None
    currency: Optional[str] = None
    opening_date: Optional[str] = None
    deadline: Optional[str] = None
    eligibility: Optional[str] = None
    eligible_applicants: list[str] = Field(default_factory=list)
    research_topics: list[str] = Field(default_factory=list)
    geographical_scope: Optional[str] = None
    project_duration: Optional[str] = None
    funding_type: Optional[str] = None
    application_url: Optional[str] = None
    source_url: Optional[str] = None
    documents: list[str] = Field(default_factory=list)
    contact: Optional[str] = None
    status: AAPStatus = AAPStatus.UNKNOWN
    last_updated: Optional[str] = None
    scraped_at: Optional[datetime] = None
    extraction_method: str = "unknown"
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    provenance: Optional[Provenance] = None
    selected_projects: list[str] = Field(default_factory=list)

    def dedupe_key(self) -> str:
        """Stable key used for basic deduplication (README: basic dedup)."""
        if self.source_url:
            return self.source_url.rstrip("/").lower()
        base = (self.title or "").strip().lower()
        org = (self.organisation or "").strip().lower()
        return f"{org}|{base}"
