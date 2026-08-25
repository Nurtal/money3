"""Normalisation helpers for benchmark matching.

The README requires both *exact match* and *normalised match* metrics: a raw
string such as "15 octobre 2026" should normalise to the same value as
"15/10/2026". Centralising normalisation here keeps extractor code and
benchmark evaluation consistent.
"""

from __future__ import annotations

import re
import unicodedata

_LIST_FIELDS = {"eligible_applicants", "research_topics", "documents"}

_FRENCH_MONTHS = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8, "aout": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12,
}
_MONTH_RE = "|".join(_FRENCH_MONTHS.keys())


def normalize_text(value) -> str:
    if value is None:
        return ""
    s = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    s = s.lower()
    s = re.sub(r"[\s\u00a0]+", " ", s)
    s = re.sub(r"[^\w\s]", "", s)
    return s.strip()


def normalize_date(value) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})$", s)
    if m:
        return s
    m = re.match(r"(\d{1,2})[/.](\d{1,2})[/.](\d{2,4})$", s)
    if m:
        d, mo, y = m.groups()
        y = "20" + y if len(y) == 2 else y
        return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
    m = re.match(rf"(\d{{1,2}})\s+({_MONTH_RE})\s+(\d{{4}})$", s, re.IGNORECASE)
    if m:
        d, mo, y = m.groups()
        month = _FRENCH_MONTHS.get(mo.lower())
        if month:
            return f"{int(y):04d}-{month:02d}-{int(d):02d}"
    return normalize_text(s)


def normalize_amount(value) -> int:
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    digits = re.sub(r"[^0-9.,-]", "", str(value))
    digits = digits.replace(",", ".").rstrip(".")
    try:
        return int(float(digits))
    except ValueError:
        return 0


def normalize_value(field: str, value) -> object:
    if field in _LIST_FIELDS:
        if value is None:
            return frozenset()
        items = value if isinstance(value, (list, tuple, set)) else [value]
        return frozenset(normalize_text(v) for v in items)
    if field in {"amount_min", "amount_max"}:
        return normalize_amount(value)
    if field in {"deadline", "opening_date"}:
        return normalize_date(value)
    if field in {"confidence_score", "status"}:
        return normalize_text(value)
    return normalize_text(value)
