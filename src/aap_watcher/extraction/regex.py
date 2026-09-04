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

from ..schema import AAPExtraction, Provenance
from ._status import detect_status
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

#: (canonical gold value, [compiled search patterns]) — abbreviations AND the
#: full French names that appear as the issuing organisation.
_ORG_NAMES: list[tuple[str, list[re.Pattern]]] = [
    ("ANR", [re.compile(r"\bANR\b"), re.compile(r"Agence nationale\s+de\s+la\s+[Rr]echerche")]),
    ("INCa", [re.compile(r"\bINCa\b"), re.compile(r"Institut national\s+(?:du|de)\s+[Cc]ancer(?:ologie)?")]),
    ("Inserm", [re.compile(r"\bInserm\b"), re.compile(r"Institut national\s+de\s+la\s+sant[ée]")]),
    ("CNRS", [re.compile(r"\bCNRS\b"), re.compile(r"[Cc]entre national\s+de\s+la\s+[Rr]echerche")]),
    ("FRM", [re.compile(r"\bFRM\b"), re.compile(r"Fondation pour\s+la\s+[Rr]echerche\s+[Mm][ée]dicale")]),
    ("Ligue contre le Cancer", [re.compile(r"Ligue\s+contre\s+le\s+[Cc]ancer")]),
    ("Fondation ARC", [re.compile(r"Fondation\s+ARC")]),
    ("Fondation de France", [re.compile(r"Fondation\s+de\s+France")]),
    ("ARS Île-de-France", [re.compile(r"ARS\s+(?:[ÎI]le-de-France)"), re.compile(r"\bARS\s+IDF\b")]),
    ("ARS Auvergne-Rhône-Alpes", [re.compile(r"ARS\s+Auvergne[- ]Rh[ôo]ne[- ]Alpes"), re.compile(r"\bARS\s+AURA\b")]),
    ("ARS Occitanie", [re.compile(r"ARS\s+Occitanie")]),
    ("ARS Provence-Alpes-Côte d'Azur", [re.compile(r"ARS\s+Provence[- ]Alpes[- ]C[ôo]te")]),
    ("ARS PACA", [re.compile(r"ARS\s+PACA")]),
    ("ARS Bretagne", [re.compile(r"ARS\s+Bretagne")]),
    ("ARS Hauts-de-France", [re.compile(r"ARS\s+Hauts[- ]de[- ]France")]),
    ("ARS Normandie", [re.compile(r"ARS\s+Normandie")]),
    ("ARS Nouvelle-Aquitaine", [re.compile(r"ARS\s+Nouvelle[- ]Aquitaine")]),
    ("ARS Guadeloupe", [re.compile(r"ARS\s+Guadeloupe")]),
    ("ARS", [re.compile(r"\bARS\b")]),
    ("CHU Grenoble Alpes", [re.compile(r"CHU\s+Grenoble\s+Alpes")]),
    ("CHU de Lyon", [re.compile(r"CHU\s+de\s+Lyon")]),
    ("AP-HP", [re.compile(r"\bAP-HP\b"), re.compile(r"Assistance Publique")]),
    ("Commission européenne", [re.compile(r"Commission\s+europ[ée]enne")]),
    ("Inria", [re.compile(r"\bInria\b"), re.compile(r"[Ii]nstitut national\s+de\s+recherche\s+(?:en\s+)?informatique")]),
    ("Inrae", [re.compile(r"\bInrae\b"), re.compile(r"[Ii]nstitut national\s+de\s+recherche\s+(?:pour\s+l'agriculture|pour\s+l’agriculture)")]),
    ("Bettencourt", [re.compile(r"Bettencourt")]),
    ("BPI", [re.compile(r"\bBpifrance\b"), re.compile(r"\bBPI\b")]),
    ("Institut Pasteur", [re.compile(r"Institut\s+Pasteur"), re.compile(r"\bPasteur\b")]),
    ("ADEME", [re.compile(r"\bADEME\b"), re.compile(r"[Aa]gence\s+(?:de\s+la\s+)?transition\s+[ée]cologique"), re.compile(r"[Aa]gence\s+de\s+l'environnement")]),
    ("AFM-Téléthon", [re.compile(r"AFM[- ]T[ée]l[ée]thon"), re.compile(r"Association\s+fran[çc]aise\s+contre\s+les\s+myopathies")]),
    ("ANSM", [re.compile(r"\bANSM\b"), re.compile(r"[Aa]gence nationale\s+de\s+s[ée]curit[ée]\s+du\s+m[ée]dicament")]),
    ("Fondation pour la Recherche sur Alzheimer", [re.compile(r"Fondation\s+(?:pour\s+la\s+)?[Rr]echerche\s+(?:sur\s+(?:la\s+)?|Alzheimer)")]),
    ("ARS", [re.compile(r"\bARS\b")]),
]

#: Announcer verbs that identify the organisation issuing the call.
_ANNOUNCER_VERBS = re.compile(
    r"\b(?:lance|soutient|finance|ouvre|porte|organise|propose|publie|"
    r"met\s+en\s+place|co-public)\w*\b",
    re.IGNORECASE,
)


def _org_in_snippet(snippet: str) -> Optional[str]:
    """Return the canonical org whose pattern appears in ``snippet``."""
    for canonical, pats in _ORG_NAMES:
        for p in pats:
            if p.search(snippet):
                return canonical
    return None


def _detect_organisation(text: str) -> Optional[str]:
    """Detect the AAP organisation, prioritising the issuing (announcer) body.

    A call's real issuer normally *launches / funds / supports* it — that org
    appears right before an announcer verb, or in the title line. Partner
    institutions (CNRS, Inserm, …) that only appear later (eligibility, contact)
    must not override the announcer.
    """
    # 1. Announcer: org immediately followed by a launch verb.
    for canonical, pats in _ORG_NAMES:
        for p in pats:
            for m in p.finditer(text):
                after = text[m.end():m.end() + 50]
                if _ANNOUNCER_VERBS.search(after):
                    return canonical

    # 2. Issuer named in the title / opening line.
    head = text[:200]
    org = _org_in_snippet(head)
    if org:
        return org

    # 3. Issuer in the very first line.
    first_line = text.split("\n", 1)[0]
    org = _org_in_snippet(first_line)
    if org:
        return org

    # 4. Fallback: full-text abbreviation scan.
    return _org_in_snippet(text)


#: Geographical scope implied by the issuing organisation (domain prior: an ARS
#: call is regional, the European Commission targets Europe, national research
#: bodies — ANR, INCa, FRM, Fondations, Inserm, CNRS, CHU, AP-HP — default to
#: France).
_SCOPE_BY_ORG: dict[str, str] = {
    "Commission européenne": "Europe",
    "ARS Île-de-France": "Île-de-France",
    "ARS Auvergne-Rhône-Alpes": "Auvergne-Rhône-Alpes",
    "ARS Occitanie": "Occitanie",
    "ARS Provence-Alpes-Côte d'Azur": "Provence-Alpes-Côte d'Azur",
    "ARS PACA": "PACA",
    "ARS Bretagne": "Bretagne",
    "ARS Hauts-de-France": "Hauts-de-France",
    "ARS Normandie": "Normandie",
    "ARS Nouvelle-Aquitaine": "Nouvelle-Aquitaine",
    "ARS Guadeloupe": "Guadeloupe",
}
_DEFAULT_SCOPE = "France"


def _scope_for(organisation: Optional[str]) -> Optional[str]:
    if not organisation:
        return None
    return _SCOPE_BY_ORG.get(organisation, _DEFAULT_SCOPE)


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
# Recurring: "22 000 € par an pendant 3 ans" (annual × duration)
_AMOUNT_RECURRING_RE = re.compile(
    r"(?i)(\d[\d\s\u00a0]*(?:[.,]\d+)?)\s*(?:€|euros?|EUR)\s+par\s+an"
    r"(?:\s+(?:pendant|sur|pour))?\s*(\d+)\s+ans?"
)

# ---------------------------------------------------------------------------
# Title and eligibility patterns
# ---------------------------------------------------------------------------

_TITLE_RE = re.compile(
    r"(?i)(?:appel\s+(?:à|a)\s+(?:projets?|candidatures?)|candidate)"
    r"\s*[:\-]?\s*(.+)"
)
# Official AAP call id, e.g. "HEALTH-2028" or "ANR-23-CE10" — used as the title
# by funders (Horizon Europe style call identifiers).
_AAP_CODE_RE = re.compile(r"\b[A-Z]{2,}-\d{4}\b")
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


# ---------------------------------------------------------------------------
# Amount-min: range patterns
# ---------------------------------------------------------------------------

_AMOUNT_MIN_PATTERNS: list[re.Pattern[str]] = [
    # "de X à Y €" / "De X à Y EUR"
    re.compile(
        r"(?:de|budget\s+de)\s+(\d[\d\s.,]*)\s*(?:€|EUR)?\s*à\s+(\d[\d\s.,]*)",
        re.IGNORECASE,
    ),
    # "entre X et Y €"
    re.compile(
        r"entre\s+(\d[\d\s.,]*)\s+et\s+(\d[\d\s.,]*)",
        re.IGNORECASE,
    ),
    # "Montant : X à Y €"
    re.compile(
        r"(?:montant|financement|budget)\s*[:\s]+"
        r"(\d[\d\s.,]*)\s*(?:€|EUR)?\s*à\s+(\d[\d\s.,]*)",
        re.IGNORECASE,
    ),
    # "minimum X €" or "min X €" or "à partir de X €"
    re.compile(
        r"(?:min(?:imum)?|à\s+partir\s+de)\s*[:\s]*(\d[\d\s.,]*)\s*(?:€|EUR)?",
        re.IGNORECASE,
    ),
]


def _clean_amount(raw: str) -> int | None:
    """Strip spaces/thousands separators and convert to int."""
    digits = raw.replace(" ", "").replace(".", "").replace(",", "")
    try:
        return int(digits)
    except ValueError:
        return None


def _extract_amount_min(text: str) -> int | None:
    """Return the minimum amount from a range pattern in *text*, or None."""
    for pat in _AMOUNT_MIN_PATTERNS:
        m = pat.search(text)
        if m:
            groups = m.groups()
            val = _clean_amount(groups[0])
            if val is not None and val > 0:
                return val
    return None


# Patterns that indicate a range (used to skip the lower bound in _best_amount).
_RANGE_KW_RE = re.compile(
    r"(?i)(?:de|entre|montant|financement|budget)\s"
    r".*?\d[\d\s.,]*\s*(?:€|EUR)?\s*à\s+\d[\d\s.,]*",
)


def _range_spans(text: str) -> list[tuple[int, int, int]]:
    """Return list of (start, mid, end) for range patterns.

    ``mid`` is the approximate position of the separator (à/et) — amounts
    before ``mid`` are the lower bound (amount_min); amounts at or after
    ``mid`` are the upper bound (amount_max).
    """
    out: list[tuple[int, int, int]] = []
    for m in _RANGE_KW_RE.finditer(text):
        full = m.group(0)
        sep = full.rfind("à")
        if sep == -1:
            sep = full.rfind("et")
        mid = m.start() + sep if sep != -1 else m.start() + len(full) // 2
        out.append((m.start(), mid, m.end()))
    return out


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
    # 0. Official call id (e.g. "HEALTH-2028") takes precedence when present.
    cm = _AAP_CODE_RE.search(text)
    if cm:
        return cm.group(0)

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

    Strategy:
      * recurring annual grants ("22 000 € par an pendant 3 ans") sum to
        annual × duration;
      * amounts inside range patterns ("de X à Y €", "entre X et Y €") are
        skipped — the lower bound is handled by _extract_amount_min;
      * otherwise prefer an amount written right after a clear "Montant
        maximal" label (colon-introduced first), taking the *nearest* amount to
        the label so distracters elsewhere in the doc cannot win;
      * finally fall back to the first amount of any supported surface format.
    Returns (amount, currency, span_start).
    """
    spans = _range_spans(text)

    def _in_range(pos: int) -> bool:
        """Return True if *pos* is the lower bound of a range pattern."""
        return any(s <= pos < mid for s, mid, _e in spans)

    def _parse_match(m: re.Match) -> Optional[int]:
        full = m.group(0)
        if "M€" in full:
            try:
                return int(float(m.group(1).replace(",", ".")) * 1_000_000)
            except (ValueError, TypeError):
                return None
        return _parse_amount(m.group(1))

    def _amounts_from(pos: int) -> list[tuple[int, Optional[int]]]:
        """All (start, value) amount candidates at or after ``pos``."""
        rest = text[pos:]
        found: list[tuple[int, Optional[int]]] = []
        for pat in (_AMOUNT_STANDARD_RE, _AMOUNT_EUR_PREFIX_RE,
                    _AMOUNT_COMPACT_RE, _AMOUNT_MILLIONS_RE):
            for m in pat.finditer(rest):
                abs_pos = pos + m.start()
                if _in_range(abs_pos):
                    continue
                val = _parse_match(m)
                if val is not None:
                    found.append((abs_pos, val))
        found.sort()
        return found

    def _nearest_from(pos: int) -> Optional[int]:
        found = _amounts_from(pos)
        return found[0][1] if found else None

    # Priority 0: recurring annual grant → total over the duration.
    rm = _AMOUNT_RECURRING_RE.search(text)
    if rm:
        try:
            annual = _parse_amount(rm.group(1).replace(" ", ""))
            years = int(rm.group(2))
            if annual is not None and years > 0:
                return annual * years, "EUR", rm.start()
        except (ValueError, TypeError):
            pass

    # Priority 1a: amount after a colon-introduced "Montant maximal :"
    colon_label_re = re.compile(r"(?i)montant\s+(?:maximum|maximal|max|total)\s*:")
    # Priority 1b: amount after any labelled "Montant maximal" (no colon)
    label_re = re.compile(r"(?i)montant\s+(?:maximum|maximal|max|total)\s*:?")

    for lm in colon_label_re.finditer(text):
        val = _nearest_from(lm.end())
        if val is not None:
            return val, "EUR", lm.end()
    for lm in label_re.finditer(text):
        val = _nearest_from(lm.end())
        if val is not None:
            return val, "EUR", lm.end()

    # Priority 2: first match of any format anywhere (skip range spans).
    for pat in (_AMOUNT_STANDARD_RE, _AMOUNT_EUR_PREFIX_RE,
                _AMOUNT_COMPACT_RE, _AMOUNT_MILLIONS_RE):
        for m in pat.finditer(text):
            if _in_range(m.start()):
                continue
            val = _parse_match(m)
            if val is not None:
                return val, "EUR", m.start()

    return None, None, -1


def _best_date(text: str, kw_re: re.Pattern, numeric: bool = False) -> Optional[str]:
    """Find the first keyword-triggered date; returns ISO date or None."""
    dates = _extract_dates(text, kw_re, numeric=numeric)
    return dates[0][0] if dates else None


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

        # --- Amount min ---
        min_val = _extract_amount_min(text)

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

        # --- Geographical scope ---
        geographical_scope = _scope_for(organisation)

        prov = Provenance(
            source_url=document.source_url,
            source_text=text[:500],
            extraction_method=self.name,
            confidence_score=0.6 if (title or deadline or amount_max) else 0.1,
        )
        return AAPExtraction(
            title=title,
            organisation=organisation,
            geographical_scope=geographical_scope,
            amount_min=min_val,
            amount_max=amount_max,
            currency=currency,
            deadline=deadline,
            opening_date=opening_date,
            eligibility=eligibility,
            source_url=document.source_url,
            extraction_method=self.name,
            status=detect_status(text),
            provenance=prov,
        )
