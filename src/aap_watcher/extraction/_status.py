"""Shared status detection from French textual markers."""

from __future__ import annotations

import re

from aap_watcher.schema import AAPStatus

# Ordered so more specific patterns are checked first.
_STATUS_PATTERNS: list[tuple[re.Pattern[str], AAPStatus]] = [
    (re.compile(r"cl[oô]ture\s+prochaine|date\s+limite\s+imminente", re.IGNORECASE), AAPStatus.CLOSING_SOON),
    (re.compile(r"annul[eé]|annule", re.IGNORECASE), AAPStatus.CANCELLED),
    (re.compile(r"cl[oô]tur[eé]|clos|ferm[eé]", re.IGNORECASE), AAPStatus.CLOSED),
    (re.compile(r"à\s+venir|ouverture\s+(?:prévue|à\s+venir)", re.IGNORECASE), AAPStatus.UPCOMING),
    (re.compile(r"ouvert(?:es?)?", re.IGNORECASE), AAPStatus.OPEN),
]


def detect_status(text: str) -> AAPStatus:
    """Return the AAPStatus whose French keyword appears in *text*.

    Returns ``AAPStatus.UNKNOWN`` when no marker is found (no false
    positives).
    """
    for pattern, status in _STATUS_PATTERNS:
        if pattern.search(text):
            return status
    return AAPStatus.UNKNOWN
