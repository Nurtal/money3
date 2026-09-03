"""Relevance scoring (Phase 7).

Ranks AAPs against a researcher profile. Pure functions over :class:`Matchable`
(decoupled from the database layer) so they are easy to test and reuse; the API
builds ``Matchable`` objects from persisted rows.

Weights (sum = 100):
  * 60  topic/technology overlap (token Jaccard on research_topics)
  * 25  funding: full if profile.amount_min is satisfied, partial if the AAP
        carries no amount, 0 otherwise
  * 15  geography: full if a listed geography matches the AAP scope, neutral
        (split) when no geography is constrained

These are deliberate, transparent defaults — no claim of optimality, and they
can be tuned from benchmark results if needed.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

_TOPIC_WEIGHT = 60
_AMOUNT_WEIGHT = 25
_GEO_WEIGHT = 15


@dataclass
class Matchable:
    """Minimal view of an AAP needed for relevance scoring."""

    id: int | None = None
    title: str | None = None
    topics: Sequence[str] = ()
    amount_max: int | None = None
    geographical_scope: str | None = None
    status: str | None = None


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _norm(terms: Iterable[str]) -> set[str]:
    return {t.strip().lower() for t in terms if t and t.strip()}


def _geo_bonus(geographies: Sequence[str], scope: str | None) -> float:
    if not geographies:
        return _GEO_WEIGHT / 2  # neutral when geography is unconstrained
    if not scope:
        return 0.0
    wanted = _norm(geographies)
    tokens = _norm(scope.replace(",", " ").replace(";", " ").replace("/", " ").split())
    return _GEO_WEIGHT if (wanted & tokens) else 0.0


def score(
    *,
    item: Matchable,
    research_topics: Sequence[str] = (),
    technologies: Sequence[str] = (),
    amount_min: int | None = None,
    geographies: Sequence[str] = (),
) -> float:
    """Return a relevance score in [0, 100] for one AAP against a profile."""
    profile_terms = _norm(list(research_topics) + list(technologies))
    aap_terms = _norm(item.topics)
    topic_score = _TOPIC_WEIGHT * _jaccard(profile_terms, aap_terms)

    if amount_min is None:
        amount_score = _AMOUNT_WEIGHT / 2  # neutral when no funding constraint
    elif item.amount_max is not None and item.amount_max >= amount_min:
        amount_score = _AMOUNT_WEIGHT
    elif item.amount_max is None:
        amount_score = _AMOUNT_WEIGHT / 2
    else:
        amount_score = 0.0

    geo_score = _geo_bonus(geographies, item.geographical_scope)

    return round(min(100.0, topic_score + amount_score + geo_score), 1)


def rank(
    *,
    research_topics: Sequence[str] = (),
    technologies: Sequence[str] = (),
    amount_min: int | None = None,
    geographies: Sequence[str] = (),
    item_pool: Sequence[Matchable],
) -> list[tuple[Matchable, float]]:
    """Score every AAP in ``item_pool`` and return them scored, desc."""
    scored = [
        (it, score(
            item=it, research_topics=research_topics, technologies=technologies,
            amount_min=amount_min, geographies=geographies,
        ))
        for it in item_pool
    ]
    return sorted(scored, key=lambda t: t[1], reverse=True)
