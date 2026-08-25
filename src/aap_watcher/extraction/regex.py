"""Regex / rule-based extractor (Phase 1 baseline).

Regex is the deterministic baseline for highly structured fields: dates,
amounts, durations, emails, URLs, explicit labels (README: strategy 1).
It is intentionally simple and explainable; more semantic fields are left to
later strategies (spaCy, LLM, hybrid) which are benchmarked against it.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from ..schema import AAPExtraction, AAPStatus, Provenance
from .base import Document, Extractor

_FRENCH_MONTHS = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8, "aout": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12,
}
_MONTH_RE = "|".join(_FRENCH_MONTHS.keys())

_AMOUNT_RE = re.compile(
    r"(?i)(?:montant(?:\s+(?:maximum|max|total|de|d'?))?\s*:?\s*)?"
    r"(\d[\d\s\u00a0]*(?:[.,]\d+)?)\s*"
    r"(?:€|euros?|EUR)"
)
_DEADLINE_RE = re.compile(
    r"(?i)(?:date\s+limite|cl[ôo]ture|deadline|limite\s+de\s+d[eé]p[oô]t)\s*:?\s*"
    r"(?:le\s+)?(\d{1,2})\s+(" + _MONTH_RE + r")\s+(\d{4})"
)
_TITLE_RE = re.compile(r"(?i)(?:appel\s+à\s+projets|appel\s+à\s+candidatures|candidate)\s*[:\-]?\s*(.+)")
_ELIGIBILITY_RE = re.compile(
    r"(?i)(?:candidats\s+éligibles|éligibilit[ée]|b[ée]n[ée]ficiaires|qui\s+peut\s+candidater)\s*:?\s*(.+?)(?:\n\n|\.|$)"
)


def _parse_amount(raw: str) -> Optional[int]:
    digits = re.sub(r"[\s\u00a0]", "", raw)
    digits = digits.replace(",", ".").rstrip(".")
    try:
        return int(float(digits))
    except ValueError:
        return None


def _parse_french_date(day: str, month: str, year: str) -> str:
    m = _FRENCH_MONTHS.get(month.lower())
    if m is None:
        return f"{year}-{month}-{'0' if len(day) == 1 else ''}{day}"
    return datetime(int(year), m, int(day)).strftime("%Y-%m-%d")


class RegexExtractor:
    """Deterministic regex baseline extractor."""

    name = "regex"

    def extract(self, document: Document) -> AAPExtraction:
        text = document.text or ""
        amount_max = None
        currency = None
        m = _AMOUNT_RE.search(text)
        if m:
            amount_max = _parse_amount(m.group(1))
            currency = "EUR"

        deadline = None
        dm = _DEADLINE_RE.search(text)
        if dm:
            deadline = _parse_french_date(dm.group(1), dm.group(2), dm.group(3))

        title = None
        tm = _TITLE_RE.search(text)
        if tm:
            title = tm.group(1).strip().rstrip(".")

        eligibility = None
        em = _ELIGIBILITY_RE.search(text)
        if em:
            eligibility = em.group(1).strip()

        prov = Provenance(
            source_url=document.source_url,
            source_text=text[:500],
            extraction_method=self.name,
            confidence_score=0.6 if (title or deadline or amount_max) else 0.1,
        )
        return AAPExtraction(
            title=title,
            amount_max=amount_max,
            currency=currency,
            deadline=deadline,
            eligibility=eligibility,
            source_url=document.source_url,
            extraction_method=self.name,
            status=AAPStatus.UNKNOWN,
            provenance=prov,
        )
