"""Regex / rule-based extractor (Phase 1 baseline).

Regex is the deterministic baseline for highly structured fields: dates,
amounts, durations, emails, URLs, explicit labels (README: strategy 1).
It is intentionally simple and explainable; more semantic fields are left to
later strategies (spaCy, LLM, hybrid) which are benchmarked against it.

v2: expanded to cover alternative date formats (numeric, ordinal, prefixed),
alternative amount formats (EUR-prefix, compact, M€), opening-date extraction,
organisation detection from known abbreviations, and smarter candidate selection
(prefer values after field labels).
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from ..schema import AAPExtraction, AAPStatus, Provenance
from .base import Document, Extractor

# ---------------------------------------------------------------------------
# Month mapping (French)
# ---------------------------------------------------------------------------

_MONTHS = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8, "aout": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12,
}
_MONTH_RE = "|".join(_MONTHS.keys())

# ---------------------------------------------------------------------------
# Organisation detection (abbreviation → canonical gold value)
# ---------------------------------------------------------------------------

_ORG_ABBREVS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bANR\b"), "ANR"),
    (re.compile(r"\bINCa\b"), "INCa"),
    (re.compile(r"\bInserm\b", re.IGNORECASE), "Inserm"),
    (re.compile(r"\bCNRS\b"), "CNRS"),
    (re.compile(r"\bFRM\b"), "FRM"),
    (re.compile(r"\bLigue\s+contre\s+le\s+[Cc]ancer\b"), "Ligue contre le Cancer"),
    (re.compile(r"\bFondation\s+ARC\b"), "Fondation ARC"),
    (re.compile(r"\bFondation\s+de\s+France\b"), "Fondation de France"),
    (re.compile(r"\bARS\s+(Île-de-France|Ile-de-France)\b"), "ARS Île-de-France"),
    (re.compile(r"\bARS\s+Auvergne[- ]Rh[ôo]ne[- ]Alpes\b"), "ARS Auvergne-Rhône-Alpes"),
    (re.compile(r"\bARS\s+Occitanie\b"), "ARS Occitanie"),
    (re.compile(r"\bARS\s+Provence[- ]Alpes[- ]C[ôo]te\s+d.Azur\b"), "ARS Provence-Alpes-Côte d'Azur"),
    (re.compile(r"\bARS\s+Bretagne\b"), "ARS Bretagne"),
    (re.compile(r"\bARS\s+Hauts[- ]de[- ]France\b"), "ARS Hauts-de-France"),
    (re.compile(r"\bARS\s+Normandie\b"), "ARS Normandie"),
    (re.compile(r"\bARS\s+Nouvelle[- ]Aquitaine\b"), "ARS Nouvelle-Aquitaine"),
    (re.compile(r"\bARS\s+Guadeloupe\b"), "ARS Guadeloupe"),
    (re.compile(r"\bARS\b"), "ARS"),  # generic ARS fallback
    (re.compile(r"\bCHU\s+Grenoble\s+Alpes\b"), "CHU Grenoble Alpes"),
    (re.compile(r"\bCHU\s+de\s+Lyon\b"), "CHU de Lyon"),
    (re.compile(r"\bAP-HP\b"), "AP-HP"),
    (re.compile(r"\bCommission\s+europ[ée]enne\b"), "Commission européenne"),
]

# ---------------------------------------------------------------------------
# Deadline: multiple keyword variants + date formats
# ---------------------------------------------------------------------------

# Keywords that introduce a deadline
_DL_KW = (
    r"(?:date\s+limite|cl[ôo]ture|deadline|"
    r"limite\s+de\s+d[eé]p[oô]t|date\s+limite\s+de\s+soumission|"
    r"date\s+limite\s+de\s+dépôt)"
)
# French date formats: "5 mars 2029", "1er août 2028"
_FDATE = r"(\d{1,2}(?:er)?)\s+(" + _MONTH_RE + r")\s+(\d{4})"
# Numeric date formats: "30/04/2029", "05.03.2029"
_NDATE = r"(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})"
# Optional French prefix before a date
_DATE_PREFIX = r"(?:avant\s+le\s+|au\s+plus\s+tard\s+le\s+|à\s+compter\s+du\s+|le\s+)?"

_DEADLINE_KW_RE = re.compile(
    r"(?i)" + _DL_KW + r"\s*:?\s*" + _DATE_PREFIX + _FDATE
)
_DEADLINE_NDATE_RE = re.compile(
    r"(?i)" + _DL_KW + r"\s*:?\s*" + _DATE_PREFIX + _NDATE
)

# Fallback: any French date preceded by deadline keywords (without requiring
# a specific date format — catches "le 1er septembre 2028" etc.)
_DEADLINE_FALLBACK_RE = re.compile(
    r"(?i)" + _DL_KW + r"\s*:?\s*" + _DATE_PREFIX + r"(\d{1,2}(?:er)?)\s+(" + _MONTH_RE + r")\s+(\d{4})"
)

# Opening date patterns
_OPEN_KW = r"(?:ouverture|début|d[eé]but|à\s+compter\s+du|date\s+d.ouverture)"
_OPENING_FDATE_RE = re.compile(
    r"(?i)" + _OPEN_KW + r"\s*:?\s*" + _DATE_PREFIX + _FDATE
)
_OPENING_NDATE_RE = re.compile(
    r"(?i)" + _OPEN_KW + r"\s*:?\s*" + _DATE_PREFIX + _NDATE
)

# ---------------------------------------------------------------------------
# Amount patterns: multiple formats
# ---------------------------------------------------------------------------

# Standard: "Montant maximal : 400 000 €" or "400 000 €"
_AMOUNT_STANDARD_RE = re.compile(
    r"(?i)(?:montant(?:\s+(?:maximum|maximal|max|total|de\s+la\s+dotation|de|d'))?\s*:?\s*)?"
    r"(\d[\d\s\u00a0]*(?:[.,]\d+)?)\s*"
    r"(?:€|euros?|EUR)"
)
# EUR-prefix: "EUR 450 000"
_AMOUNT_EUR_PREFIX_RE = re.compile(
    r"(?i)(?:montant(?:\s+(?:maximum|maximal|max|total|de|d'))?\s*:?\s*)?"
    r"EUR\s+(\d[\d\s\u00a0]*(?:[.,]\d+)?)"
)
# Compact: "400000€" (no thousands separator)
_AMOUNT_COMPACT_RE = re.compile(
    r"(?i)(?:montant(?:\s+(?:maximum|maximal|max|total|de|d'))?\s*:?\s*)?"
    r"(\d{4,})\s*(?:€|euros?|EUR)"
)
# Millions: "0.91 M€" or "8 M€"
_AMOUNT_MILLIONS_RE = re.compile(
    r"(?i)(?:montant(?:\s+(?:maximum|maximal|max|total|de|d'))?\s*:?\s*)?"
    r"([\d.,]+)\s*M€"
)

# ---------------------------------------------------------------------------
# Title and eligibility patterns
# ---------------------------------------------------------------------------

_TITLE_RE = re.compile(
    r"(?i)(?:appel\s+(?:à|a)\s+(?:projets?|candidatures?)|candidate)"
    r"\s*[:\-]?\s*(.+)"
)
# Markdown heading: "# Title"
_HEADING_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
# "Org - Title" (short title after organisation dash, e.g. "INCa - Bourses de thèse 2027")
_TITLE_AFTER_DASH_RE = re.compile(
    r"(?im)^\s*(?:[A-ZÀ-Ý][A-Za-zÀ-ÿéèêèçàûîô]+(?:\s+[A-Za-zÀ-ÿéèêàçûîô]+){0,4})\s*[-–—]\s*([A-ZÀ-Ý][A-Za-zÀ-ÿéèêàçûîô'0-9 .]{3,})$"
)
_ELIGIBILITY_RE = re.compile(
    r"(?i)(?:candidats\s+[ée]ligibles|[ée]ligibilit[ée]|"
    r"b[ée]n[ée]ficiaires|qui\s+peut\s+candidater|"
    r"structures\s+[ée]ligibles|institutions\s+[ée]ligibles)"
    r"\s*:?\s*(.+?)(?:\n\n|\.|$)"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_amount(raw: str) -> Optional[int]:
    """Parse a raw amount string (spaces, commas, decimals) to int."""
    digits = re.sub(r"[\s\u00a0]", "", raw)
    digits = digits.replace(",", ".").rstrip(".")
    try:
        return int(float(digits))
    except ValueError:
        return None


def _parse_french_date(day_str: str, month_str: str, year_str: str) -> str:
    """Parse a French date to ISO YYYY-MM-DD."""
    # Strip ordinal suffix ("1er" → "1")
    day_clean = day_str.replace("er", "")
    day = int(day_clean)
    m = _MONTHS.get(month_str.lower())
    if m is not None:
        return datetime(int(year_str), m, day).strftime("%Y-%m-%d")
    # Fallback if month not recognised
    return f"{year_str}-{month_str}-{'0' if day < 10 else ''}{day}"


def _parse_numeric_date(d: str, mo: str, y: str) -> str:
    """Parse dd/mm/yyyy or dd.mm.yyyy to ISO YYYY-MM-DD."""
    return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"


def _extract_dates(text: str, kw_re: re.Pattern, numeric: bool = False) -> list[tuple[str, int]]:
    """Return list of (iso_date, start_pos) from keyword-triggered matches."""
    out = []
    for m in kw_re.finditer(text):
        groups = m.groups()
        day, month, year = groups[-3], groups[-2], groups[-1]
        iso = _parse_numeric_date(day, month, year) if numeric \
            else _parse_french_date(day, month, year)
        out.append((iso, m.start()))
    return out


def _extract_title(text: str) -> Optional[str]:
    """Extract a clean title using several structural signals."""
    # 1. Markdown heading
    hm = _HEADING_RE.search(text)
    if hm:
        t = hm.group(1).strip()
        if t:
            return t.rstrip(".")

    # 2. "appel à projets : Title"
    tm = _TITLE_RE.search(text)
    if tm:
        t = tm.group(1).strip().rstrip(".")
        if t:
            # Prefer the short title after a dash separator when present,
            # e.g. "Appel à projets : Génétique 2028" stays as-is.
            return t

    # 3. "Org - Title" on its own line
    am = _TITLE_AFTER_DASH_RE.search(text)
    if am:
        t = am.group(1).strip().rstrip(".")
        if t and not t.lower().startswith(("date", "montant", "contact")):
            return t

    return None


def _best_amount(text: str) -> tuple[Optional[int], Optional[str], int]:
    """Find the best amount candidate.

    Strategy: prefer an amount written after a clear "Montant maximal" label,
    with priority to colon-introduced labels (e.g. "Montant maximal : 520 000 €"),
    then fall back to the first amount of any supported surface format.
    Returns (amount, currency, span_start).
    """
    label_re = re.compile(r"(?i)montant\s+(?:maximum|maximal|max|total)\s*:?")
    colon_label_re = re.compile(r"(?i)montant\s+(?:maximum|maximal|max|total)\s*:")

    def _parse_match(m: re.Match) -> Optional[int]:
        full = m.group(0)
        if "M€" in full:
            try:
                return int(float(m.group(1).replace(",", ".")) * 1_000_000)
            except (ValueError, TypeError):
                return None
        return _parse_amount(m.group(1))

    def _first_from(pos: int) -> Optional[int]:
        rest = text[pos:]
        for pat in (_AMOUNT_STANDARD_RE, _AMOUNT_EUR_PREFIX_RE,
                    _AMOUNT_COMPACT_RE, _AMOUNT_MILLIONS_RE):
            m = pat.search(rest)
            if m:
                val = _parse_match(m)
                if val is not None:
                    return val
        return None

    # Priority 1a: amount after a colon-introduced "Montant maximal :"
    for lm in colon_label_re.finditer(text):
        val = _first_from(lm.end())
        if val is not None:
            return val, "EUR", lm.end()

    # Priority 1b: amount after any labelled "Montant maximal" (no colon)
    for lm in label_re.finditer(text):
        val = _first_from(lm.end())
        if val is not None:
            return val, "EUR", lm.end()

    # Priority 2: first match of any format anywhere
    for pat in (_AMOUNT_STANDARD_RE, _AMOUNT_EUR_PREFIX_RE,
                _AMOUNT_COMPACT_RE, _AMOUNT_MILLIONS_RE):
        m = pat.search(text)
        if m:
            val = _parse_match(m)
            if val is not None:
                return val, "EUR", m.start()

    return None, None, -1


def _best_date(text: str, kw_re: re.Pattern, numeric: bool = False) -> Optional[str]:
    """Find the first keyword-triggered date; returns ISO date or None."""
    dates = _extract_dates(text, kw_re, numeric=numeric)
    return dates[0][0] if dates else None


def _detect_organisation(text: str) -> Optional[str]:
    """Detect the AAP organisation from known abbreviations/full names."""
    for pat, canonical in _ORG_ABBREVS:
        if pat.search(text):
            return canonical
    return None


# ---------------------------------------------------------------------------
# RegexExtractor
# ---------------------------------------------------------------------------

class RegexExtractor:
    """Deterministic regex baseline extractor (v2)."""

    name = "regex"

    def extract(self, document: Document) -> AAPExtraction:
        text = document.text or ""

        # --- Amount ---
        amount_max, currency, _ = _best_amount(text)

        # --- Deadline ---
        deadline = _best_date(text, _DEADLINE_KW_RE)
        if not deadline:
            deadline = _best_date(text, _DEADLINE_NDATE_RE, numeric=True)

        # --- Opening date ---
        opening_date = _best_date(text, _OPENING_FDATE_RE)
        if not opening_date:
            opening_date = _best_date(text, _OPENING_NDATE_RE, numeric=True)

        # --- Title ---
        title = _extract_title(text)

        # --- Eligibility ---
        eligibility = None
        em = _ELIGIBILITY_RE.search(text)
        if em:
            eligibility = em.group(1).strip()

        # --- Organisation ---
        organisation = _detect_organisation(text)

        prov = Provenance(
            source_url=document.source_url,
            source_text=text[:500],
            extraction_method=self.name,
            confidence_score=0.6 if (title or deadline or amount_max) else 0.1,
        )
        return AAPExtraction(
            title=title,
            organisation=organisation,
            amount_max=amount_max,
            currency=currency,
            deadline=deadline,
            opening_date=opening_date,
            eligibility=eligibility,
            source_url=document.source_url,
            extraction_method=self.name,
            status=AAPStatus.UNKNOWN,
            provenance=prov,
        )
