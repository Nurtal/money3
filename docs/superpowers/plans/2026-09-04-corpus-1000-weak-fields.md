# Corpus Growth + Weak Fields Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Grow the gold corpus from 508 to ~1124 examples and improve F1 on `status`, `amount_min`, `research_topics`, and `eligible_applicants` — currently near-zero — by adding textual signals to the corpus and expanding extractor vocabularies.

**Architecture:** Two-pronged approach: (1) modify the corpus generator so every example carries gold `status`, `amount_min` ranges, and `eligible_applicants` in both the expected dict and the document prose; (2) expand the regex and dictionary extractors to detect these fields from the new textual signals. Hybrid gets it for free via merge. A shared `_detect_status()` utility avoids duplicating keyword logic.

**Tech Stack:** Python 3.12, pydantic, pytest, uv. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-09-04-corpus-1000-weak-fields-design.md`

## Global Constraints

- Line length ≤ 100 (ruff).
- `X | None` annotation style (not `Optional[X]`).
- No hand-estimated benchmark scores — results come from actual runs.
- Canonical AAP schema (`src/aap_watcher/schema.py`) unchanged — no ADR needed.
- All 98 existing tests must continue to pass after every task.
- `uv run pytest` is the test runner; no network access required.
- Extractors never invent missing info; `AAPStatus.UNKNOWN` default preserved.

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `src/aap_watcher/extraction/_status.py` | **Create** | Shared `detect_status(text) → AAPStatus` keyword detector |
| `src/aap_watcher/extraction/dictionary.py` | **Modify** | Expand `TOPICS` (~50→~80), `APPLICANTS` (~22→~37); add status detection |
| `src/aap_watcher/extraction/regex.py` | **Modify** | Add `amount_min` range parsing; add status keyword detection |
| `src/aap_watcher/extraction/hybrid.py` | **No change** | Merge already handles `amount_min`, `status`, `eligible_applicants` |
| `scripts/build_gold_corpus.py` | **Modify** | Add `_status_prose`, `_amount_range_prose`, `_APPLICANT_POOLS`; modify `_mk_example`, `_build_doc`, `_scale_from_conf`; `_TARGET_TOTAL=1000`; backfill hand-written examples; regenerate |
| `data/benchmark/gold/v1.jsonl` | **Regenerate** | ~1124 examples with all 4 fields populated |
| `tests/test_extraction_regex.py` | **Modify** | Add tests for `amount_min` range parsing and `status` detection |
| `tests/test_extractors.py` | **Modify** | Add tests for dictionary vocab expansion and status detection |
| `tests/test_status.py` | **Create** | Unit tests for shared `detect_status()` utility |
| `tests/test_benchmark.py` | **Modify** | Add test for `amount_min` normalisation and status field presence |
| `README.md` | **Modify** | Update benchmark numbers from real run |

---

### Task 1: Shared status detector utility

**Files:**
- Create: `src/aap_watcher/extraction/_status.py`
- Create: `tests/test_status.py`

**Interfaces:**
- Produces: `detect_status(text: str) → AAPStatus` — scans text for French status keywords and returns the matching `AAPStatus`, or `AAPStatus.UNKNOWN` if no keyword found. Case-insensitive, accent-tolerant matching.

- [ ] **Step 1: Write failing tests for `detect_status()`**

Create `tests/test_status.py`:

```python
from aap_watcher.extraction._status import detect_status
from aap_watcher.schema import AAPStatus


def test_detect_open():
    assert detect_status("Appel ouvert.") == AAPStatus.OPEN


def test_detect_open_variant():
    assert detect_status("Candidatures ouvertes.") == AAPStatus.OPEN


def test_detect_upcoming():
    assert detect_status("Appel à venir, ouverture prévue prochainement.") == AAPStatus.UPCOMING


def test_detect_closed():
    assert detect_status("Ce appel est clôturé.") == AAPStatus.CLOSED


def test_detect_closed_variant():
    assert detect_status("Candidatures closes.") == AAPStatus.CLOSED


def test_detect_cancelled():
    assert detect_status("Appel annulé.") == AAPStatus.CANCELLED


def test_detect_cancelled_variant():
    assert detect_status("Appel à projets annulé par l'organisme.") == AAPStatus.CANCELLED


def test_detect_closing_soon():
    assert detect_status("Clôture prochaine, date limite imminente.") == AAPStatus.CLOSING_SOON


def test_detect_unknown_when_no_marker():
    assert detect_status("L'appel finance la recherche.") == AAPStatus.UNKNOWN


def test_detect_unknown_empty():
    assert detect_status("") == AAPStatus.UNKNOWN


def test_case_insensitive():
    assert detect_status("APPEL OUVERT.") == AAPStatus.OPEN
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_status.py -v`
Expected: FAIL — module `aap_watcher.extraction._status` does not exist.

- [ ] **Step 3: Create the shared utility**

Create `src/aap_watcher/extraction/_status.py`:

```python
"""Shared status detection from French textual markers."""

from __future__ import annotations

import re

from aap_watcher.schema import AAPStatus

# Ordered so more specific patterns are checked first.
_STATUS_PATTERNS: list[tuple[re.Pattern[str], AAPStatus]] = [
    (re.compile(r"cl[oô]ture\s+prochaine|date\s+limite\s+imminente", re.I), AAPStatus.CLOSING_SOON),
    (re.compile(r"annul[eé]|annule", re.I), AAPStatus.CANCELLED),
    (re.compile(r"cl[oô]tur[eé]|clos|ferm[eé]", re.I), AAPStatus.CLOSED),
    (re.compile(r"à\s+venir|ouverture\s+(?:prévue|à\s+venir)", re.I), AAPStatus.UPCOMING),
    (re.compile(r"ouvert(?:es?)?", re.I), AAPStatus.OPEN),
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_status.py -v`
Expected: all 11 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/aap_watcher/extraction/_status.py tests/test_status.py
git commit -m "feat: add shared detect_status() French keyword detector"
```

---

### Task 2: Dictionary extractor — expand vocab + status

**Files:**
- Modify: `src/aap_watcher/extraction/dictionary.py`
- Modify: `tests/test_extractors.py`

**Interfaces:**
- Consumes: `detect_status()` from Task 1.
- Produces: `DictionaryExtractor.extract()` now sets `status` (when keyword found) and recognises a wider set of topics/applicants.

- [ ] **Step 1: Write failing tests for expanded vocabulary and status**

Add to `tests/test_extractors.py` (at the end, before the final blank lines):

```python
def test_dictionary_detects_status_open():
    ex = DictionaryExtractor().extract(Document(text="Appel ouvert. Candidatures ouvertes."))
    assert ex.status == "open"


def test_dictionary_detects_status_closed():
    ex = DictionaryExtractor().extract(Document(text="Ce appel est clôturé."))
    assert ex.status == "closed"


def test_dictionary_status_unknown_when_no_marker():
    ex = DictionaryExtractor().extract(Document(text="Financement recherche."))
    assert ex.status == "unknown"


def test_dictionary_expanded_topics():
    text = "Thématiques : biologie cellulaire, agronomie, cybersécurité."
    ex = DictionaryExtractor().extract(Document(text=text))
    topics = [t.lower() for t in ex.research_topics]
    assert "biologie cellulaire" in topics
    assert "agronomie" in topics
    assert "cybersécurité" in topics


def test_dictionary_expanded_applicants():
    text = "Candidats : CEA, MNHN, postdocs, organismes publics."
    ex = DictionaryExtractor().extract(Document(text=text))
    applicants = [a.lower() for a in ex.eligible_applicants]
    assert "cea" in applicants
    assert "mnhn" in applicants
    assert "postdocs" in applicants
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_extractors.py -v`
Expected: new tests FAIL (vocab not found or status not set).

- [ ] **Step 3: Expand `TOPICS` list in dictionary.py**

Add these entries to the `TOPICS` list in `src/aap_watcher/extraction/dictionary.py` (append to the existing list):

```python
# Phase 4+5 additions — covers _TOPIC_POOLS vocabulary from the corpus generator.
"biologie cellulaire",
"génétique",
"physique",
"chimie",
"mathématiques",
"algorithmique",
"cybersécurité",
"agronomie",
"alimentation",
"environnement",
"transition écologique",
"énergie",
"biodiversité",
"sciences de la vie",
"deep tech",
"biotechnologies",
"recherche clinique",
"recherche translationnelle",
"épidémiologie",
"microbiologie",
"infectiologie",
"virologie",
"pharmacovigilance",
"maladie d'alzheimer",
"neurodégénérescence",
"neurobiologie",
"accompagnement",
"sécurité sanitaire",
"sciences de la matière",
"calcul haute performance",
"éco-conception",
"ressources naturelles",
"muscle",
"médecine régénérative",
"épigénétique",
"médecine de précision",
```

- [ ] **Step 4: Expand `APPLICANTS` list in dictionary.py**

Add these entries to the `APPLICANTS` list in `src/aap_watcher/extraction/dictionary.py`:

```python
# Phase 4+5 additions — covers gold eligible_applicants vocabulary.
"cea",
"mnhn",
"ird",
"postdocs",
"organismes publics",
"établissements de santé",
"écoles d'ingénieurs",
"instituts cnrs",
"hôpitaux universitaires",
"cliniques",
"ehpad",
"associations de patients",
"entreprises innovantes",
"inserm",
```

- [ ] **Step 5: Add status detection to `DictionaryExtractor.extract()`**

In `src/aap_watcher/extraction/dictionary.py`, inside the `extract()` method, after the existing extraction logic (before `return extraction`), add:

```python
from aap_watcher.extraction._status import detect_status
extraction.status = detect_status(doc.text)
```

(The import can be at the top of the file.)

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_extractors.py -v`
Expected: all tests PASS including the 5 new ones.

- [ ] **Step 7: Commit**

```bash
git add src/aap_watcher/extraction/dictionary.py tests/test_extractors.py
git commit -m "feat: expand dictionary vocab + add status detection"
```

---

### Task 3: Regex extractor — amount_min + status

**Files:**
- Modify: `src/aap_watcher/extraction/regex.py`
- Modify: `tests/test_extraction_regex.py`

**Interfaces:**
- Consumes: `detect_status()` from Task 1.
- Produces: `RegexExtractor.extract()` now sets `amount_min` (when a range pattern is found) and `status` (when keyword found).

- [ ] **Step 1: Write failing tests for amount_min range parsing**

Add to `tests/test_extraction_regex.py`:

```python
AMOUNT_RANGE_DE_A = """
Appel à projets : Matériaux 2029

Budget : De 50 000 € à 400 000 €.
"""


def test_amount_min_from_de_a_range():
    ex = RegexExtractor().extract(Document(text=AMOUNT_RANGE_DE_A))
    assert ex.amount_min == 50000
    assert ex.amount_max == 400000


AMOUNT_RANGE_ENTRE = """
Appel à projets : Énergie 2029

Financement : Entre 100 000 et 500 000 EUR.
"""


def test_amount_min_from_entre_et_range():
    ex = RegexExtractor().extract(Document(text=AMOUNT_RANGE_ENTRE))
    assert ex.amount_min == 100000
    assert ex.amount_max == 500000


AMOUNT_RANGE_MONTANT = """
Appel à projets : Climat 2029

Montant : 3 000 000 à 5 000 000 €.
"""


def test_amount_min_from_montant_a_range():
    ex = RegexExtractor().extract(Document(text=AMOUNT_RANGE_MONTANT))
    assert ex.amount_min == 3000000
    assert ex.amount_max == 5000000


AMOUNT_NO_MIN = """
Appel à projets : Santé 2029

Montant maximal : 200 000 €.
"""


def test_amount_min_none_when_no_range():
    ex = RegexExtractor().extract(Document(text=AMOUNT_NO_MIN))
    assert ex.amount_min is None
```

- [ ] **Step 2: Write failing tests for status detection**

Add to `tests/test_extraction_regex.py`:

```python
def test_regex_detects_status_open():
    ex = RegexExtractor().extract(Document(text="Appel ouvert. Montant : 100 000 €."))
    assert ex.status == "open"


def test_regex_detects_status_closed():
    ex = RegexExtractor().extract(Document(text="Ce appel est clôturé."))
    assert ex.status == "closed"


def test_regex_detects_status_cancelled():
    ex = RegexExtractor().extract(Document(text="Appel annulé par l'organisme."))
    assert ex.status == "cancelled"


def test_regex_status_unknown_when_no_marker():
    ex = RegexExtractor().extract(Document(text="L'appel finance la recherche en physique."))
    assert ex.status == "unknown"
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_extraction_regex.py -v`
Expected: new `amount_min` and `status` tests FAIL.

- [ ] **Step 4: Add `_extract_amount_min()` to regex.py**

In `src/aap_watcher/extraction/regex.py`, add a new private function (place it near `_extract_amount`):

```python
import re as _re

_AMOUNT_MIN_PATTERNS: list[_re.Pattern[str]] = [
    # "de X à Y €" / "De X à Y EUR"
    _re.compile(r"(?:de|budget\s+de)\s+(\d[\d\s.,]*)\s*(?:€|EUR)?\s*à\s+(\d[\d\s.,]*)", _re.I),
    # "entre X et Y €"
    _re.compile(r"entre\s+(\d[\d\s.,]*)\s+et\s+(\d[\d\s.,]*)", _re.I),
    # "Montant : X à Y €"
    _re.compile(r"(?:montant|financement|budget)\s*[:\s]+(\d[\d\s.,]*)\s*(?:€|EUR)?\s*à\s+(\d[\d\s.,]*)", _re.I),
    # "minimum X €" or "min X €"
    _re.compile(r"(?:min(?:imum)?|à\s+partir\s+de)\s*[:\s]*(\d[\d\s.,]*)\s*(?:€|EUR)?", _re.I),
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
```

- [ ] **Step 5: Integrate `_extract_amount_min` and `detect_status` into `RegexExtractor.extract()`**

In `src/aap_watcher/extraction/regex.py`, inside the `extract()` method, after the existing amount extraction and before the return statement, add:

```python
from aap_watcher.extraction._status import detect_status

# ... inside extract(), after existing amount_max extraction:
min_val = _extract_amount_min(doc.text)
if min_val is not None:
    extraction.amount_min = min_val

extraction.status = detect_status(doc.text)
```

(The import can be at the top of the file.)

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_extraction_regex.py -v`
Expected: all tests PASS including the 8 new ones.

- [ ] **Step 7: Commit**

```bash
git add src/aap_watcher/extraction/regex.py tests/test_extraction_regex.py
git commit -m "feat: add amount_min range parsing and status detection to regex extractor"
```

---

### Task 4: Corpus generator — status markers + amount ranges + eligible_applicants + growth

**Files:**
- Modify: `scripts/build_gold_corpus.py`
- Modify: `tests/test_benchmark.py`

**Interfaces:**
- Produces: Every gold example carries `expected["status"]`, examples with `amount_min` have range prose, scaled examples have `eligible_applicants` in both prose and expected dict. Corpus grows to ~1124.

- [ ] **Step 1: Add `_status_prose()` helper**

In `scripts/build_gold_corpus.py`, add near the other `_prose` helpers (after `_amount_prose`):

```python
_STATUS_PROSE_VARIANTS: list[tuple[str, str]] = [
    ("ouvert", "Appel ouvert."),
    ("ouvert", "Ce appel à projets est ouvert."),
    ("ouvert", "Candidatures ouvertes."),
    ("upcoming", "Appel à venir, ouverture prévue prochainement."),
    ("closed", "Ce appel est clôturé."),
    ("closed", "Candidatures closes."),
    ("cancelled", "Appel annulé."),
    ("closing_soon", "Clôture prochaine, date limite imminente."),
    ("cancelled", "Appel à projets annulé par l'organisme."),
    ("closed", "Appel fermé."),
]


def _status_prose(status: str, variant: int) -> str:
    """Return a French textual marker for the given AAP status string."""
    target = status.lower()
    candidates = [text for key, text in _STATUS_PROSE_VARIANTS if key == target]
    if not candidates:
        return "Appel ouvert."
    return candidates[variant % len(candidates)]
```

- [ ] **Step 2: Add `_amount_range_prose()` helper**

In `scripts/build_gold_corpus.py`, add after `_amount_prose`:

```python
def _amount_range_prose(amount_min: int, amount_max: int, variant: int) -> str:
    """Render a funding range in French prose.

     0: "De 50 000 € à 400 000 €"
     1: "Entre 100 000 et 500 000 EUR"
     2: "Montant : 3 000 000 à 5 000 000 €"
     3: "Budget de 50 000€ à 150 000€"
    """
    mn = f"{amount_min:,}".replace(",", " ")
    mx = f"{amount_max:,}".replace(",", " ")
    if variant == 1:
        return f"Entre {mn} et {mx} EUR"
    if variant == 2:
        return f"Montant : {mn} à {mx} €"
    if variant == 3:
        return f"Budget de {amount_min:,}€ à {amount_max:,}€"
    return f"De {mn} € à {mx} €"
```

- [ ] **Step 3: Add `_APPLICANT_POOLS` dict**

In `scripts/build_gold_corpus.py`, add near `_TOPIC_POOLS`:

```python
_APPLICANT_POOLS: dict[str, list[str]] = {
    "Inserm": ["universités", "hôpitaux", "laboratoires"],
    "CNRS": ["universités", "laboratoires", "grands établissements"],
    "Inria": ["universités", "entreprises", "laboratoires publics"],
    "Inrae": ["universités", "entreprises agroalimentaires", "chercheurs"],
    "Bettencourt": ["universités", "grandes écoles"],
    "BPI": ["entreprises", "PME", "startups"],
    "Commission européenne": ["universités", "entreprises", "organismes publics"],
    "CHU": ["hôpitaux", "universités", "CHU"],
    "AP-HP": ["hôpitaux", "CHU", "chercheurs cliniciens"],
    "Institut Pasteur": ["universités", "laboratoires", "CHU"],
    "ADEME": ["entreprises", "collectivités", "associations"],
    "AFM-Téléthon": ["universités", "hôpitaux", "associations de patients"],
    "ANSM": ["entreprises pharmaceutiques", "hôpitaux", "laboratoires"],
    "Fondation pour la Recherche sur Alzheimer": ["universités", "hôpitaux", "associations"],
}


def _applicants_for(source: str) -> list[str]:
    """Pick 1-2 eligible applicant types for *source* deterministically."""
    import hashlib
    pool = _APPLICANT_POOLS.get(source, ["universités", "laboratoires"])
    h = int(hashlib.md5(source.encode()).hexdigest(), 16)
    n = 1 + h % 2  # 1 or 2
    # Deterministic pick: hash selects starting index.
    start = h % len(pool)
    return [pool[(start + i) % len(pool)] for i in range(n)]
```

- [ ] **Step 4: Add `_derive_status()` helper**

In `scripts/build_gold_corpus.py`, add near the other helpers:

```python
def _derive_status(day: int, month: int, year: int, ref_year: int = 2027) -> str:
    """Derive an AAP status string deterministically from dates.

    Uses ref_year=2027 as the "today" reference for the corpus generator.
    """
    import hashlib
    # Deterministic "cancelled" ~10% of the time: hash of (day,month,year) mod 10 == 0
    h = int(hashlib.md5(f"{day}-{month}-{year}".encode()).hexdigest(), 16)
    if h % 10 == 0:
        return "cancelled"
    if year < ref_year:
        return "closed"
    if year > ref_year:
        # Future: could be upcoming or open; use month to decide.
        if month <= 3:
            return "upcoming"
        return "open"
    # Same year as reference.
    if month <= 6:
        return "closing_soon"
    return "open"
```

- [ ] **Step 5: Modify `_build_doc()` to accept `status_line` and `applicants_line`**

In `scripts/build_gold_corpus.py`, modify `_build_doc` to accept two new optional parameters and render them in the document. In compact mode, append them as paragraphs after the amount line. In realistic mode, append as a section.

Add parameters `status_line: str | None = None` and `applicants_line: str | None = None` to the function signature. After the existing `amount_line` handling (both compact and realistic paths), add:

```python
if applicants_line:
    sec.append("")   # compact: blank line before
    sec.append(applicants_line)
if status_line:
    sec.append("")
    sec.append(status_line)
```

(Use `sec` in realistic mode; use the compact path's `body_paras` list equivalently.)

- [ ] **Step 6: Modify `_mk_example()` to accept `status` and `eligible_applicants` kwargs**

In `scripts/build_gold_corpus.py`, modify `_mk_example`:
1. Add `status: str | None = None` and `eligible_applicants: list[str] | None = None` parameters.
2. After the existing `amount_line` generation, add:

```python
status_line = None
if status:
    status_line = _status_prose(status, variant=0)
    ents.append(Ent("STATUS", status_line))

applicants_line = None
if eligible_applicants:
    applicants_line = "Candidats : " + ", ".join(eligible_applicants) + "."
    ents.append(Ent("ELIGIBLE_APPLICANTS", applicants_line))
```

3. Pass `status_line` and `applicants_line` to `_build_doc()`.
4. After the existing `expected` dict construction, add:

```python
if status:
    expected["status"] = status
```

- [ ] **Step 7: Modify `_scale_from_conf()` to emit status, eligible_applicants, and applicant prose**

In `scripts/build_gold_corpus.py`, modify `_scale_from_conf`:

1. After computing `topics`, derive status from dates:

```python
status = _derive_status(day, month, year)
```

2. Compute applicants:

```python
applicants = _applicants_for(org)
applicants_line = "Candidats : " + ", ".join(applicants) + "."
```

3. Add to `body_for_doc`:

```python
body_for_doc = body + " Thématiques : " + ", ".join(topics) + ". " + applicants_line
```

4. Add `status` and `eligible_applicants` to `expected_extra`:

```python
expected_extra={
    "geographical_scope": scope,
    "funding_type": funding_type,
    "research_topics": topics,
    "eligible_applicants": applicants,
    "status": status,
},
```

5. Pass `status=status` to `_mk_example()`.

- [ ] **Step 8: Modify hand-written EXAMPLES to backfill `status`**

For each hand-written example in `EXAMPLES` that has a deadline dict, add `status=_derive_status(day, month, year)` to its `_mk_example()` call. For examples without a deadline, add `status="open"`.

Also, for each hand-written example that does NOT have an applicants prose line in its body, add one. (Most already have "Candidats éligibles : ..." or "Institutions : ..." — verify and standardise to "Candidats : ..." where missing.)

This is a mechanical edit across ~100 hand-written entries. Use `replaceAll` or targeted edits.

- [ ] **Step 9: Set `_TARGET_TOTAL = 1000`**

In `scripts/build_gold_corpus.py`, change:

```python
_TARGET_TOTAL = 1000
```

- [ ] **Step 10: Regenerate the corpus**

Run: `uv run python scripts/build_gold_corpus.py`

Verify output:
- Count ~1124 examples
- All splits populated
- No entity offset mismatches
- No duplicate IDs

- [ ] **Step 11: Add test for corpus status field presence**

Add to `tests/test_benchmark.py`:

```python
def test_corpus_status_field_present():
    examples = load_corpus(CORPUS)
    with_status = [e for e in examples if e.expected.get("status")]
    # At least 90% of examples should have a status.
    assert len(with_status) >= len(examples) * 0.9


def test_corpus_amount_min_has_range_prose():
    examples = load_corpus(CORPUS)
    with_min = [e for e in examples if e.expected.get("amount_min")]
    for ex in with_min:
        assert "à" in ex.text or "entre" in ex.text.lower(), (
            f"[{ex.id}] amount_min={ex.expected['amount_min']} but no range prose in text"
        )
```

- [ ] **Step 12: Run full test suite**

Run: `uv run pytest`
Expected: all tests PASS.

- [ ] **Step 13: Commit**

```bash
git add scripts/build_gold_corpus.py data/benchmark/gold/v1.jsonl tests/test_benchmark.py
git commit -m "feat: grow corpus to ~1124, add status/amount_range/applicants to gold"
```

---

### Task 5: Benchmark verification + README update

**Files:**
- Modify: `README.md` (benchmark numbers only)

**Interfaces:**
- Consumes: corpus from Task 4, extractors from Tasks 1-3.

- [ ] **Step 1: Run benchmark on test split**

Run: `uv run aap-watcher benchmark --split test --field-matrix`

Capture output — this is the authoritative benchmark. Do NOT hand-estimate any numbers.

- [ ] **Step 2: Verify weak-field F1 improvements**

Check the field-matrix output:
- `status` F1 should now be > 0.00 (was unmeasurable/0).
- `amount_min` F1 should be > 0.00 (was 0).
- `research_topics` F1 should be higher than 0.07.
- `eligible_applicants` F1 should be higher than 0.16.

If any field is still 0.00, investigate and fix before proceeding.

- [ ] **Step 3: Run full benchmark**

Run: `uv run aap-watcher benchmark --split all --field-matrix`

- [ ] **Step 4: Update README benchmark section**

Replace the illustrative benchmark numbers in the README with the actual measured numbers from Step 3. Label them clearly as "measured on YYYY-MM-DD" so readers know they are real, not hand-estimated.

- [ ] **Step 5: Final full test suite**

Run: `uv run pytest`
Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add README.md
git commit -m "docs: update benchmark numbers from measured results"
```
