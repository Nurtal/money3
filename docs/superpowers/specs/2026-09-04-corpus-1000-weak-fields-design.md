# Design: Grow gold corpus to ~1000 & improve 4 weak extraction fields

## Context

The AAP Watcher benchmark currently scores 508 gold examples across 5 extractors. Four fields have near-zero F1 on the test split (227 docs):

| Field | Root cause | Current F1 (test) |
|---|---|---|
| `status` | No gold example sets `status`; no textual markers; all extractors hardcode `UNKNOWN`. Field is **unmeasurable** — `g_has` is always `False` so it never counts. | 0.00 |
| `amount_min` | `_amount_prose()` renders only one amount; `amount_min` is set in gold `expected` but never in prose. Extractors have no pattern for it. | 0.00 |
| `research_topics` | Gold topics from `_TOPIC_POOLS` (e.g. "biologie cellulaire", "agronomie") are absent from the dictionary's 50-item `TOPICS` list. Set-exact matching (frozenset equality after normalisation) means partial overlap = 0. | 0.07 |
| `eligible_applicants` | ~300 scaled examples have no `eligible_applicants` at all. Hand-written values include "CEA", "MNHN", "postdocs" absent from the dictionary's 22-item `APPLICANTS` list. | 0.16 |

The README targets 500–1000 examples. Growing to ~1000 while fixing these fields is the work.

## Goal

- Grow `data/benchmark/gold/v1.jsonl` from 508 → ~1124 examples (target 1000, inherent overshoot from variant-based scaling).
- Make `status` measurable: emit gold status in every example, add textual markers, add status detection to extractors.
- Make `amount_min` extractable: render ranges in prose, add regex parsing.
- Improve `research_topics` / `eligible_applicants`: expand dictionary gazetteers to cover the corpus vocabulary; add `eligible_applicants` to scaled examples with prose.

## Design decisions (approved)

1. **Statuses**: inject a textual marker ("appel ouvert", "clôturé", "annulé", "à venir", "clôture prochaine") into every document and set `expected["status"]`. Derive status from dates where possible. Use 5 statuses: OPEN, UPCOMING, CLOSED, CANCELLED, CLOSING_SOON.
2. **Vocabulary alignment**: expand the dictionary extractor's `TOPICS` and `APPLICANTS` lists to cover `_TOPIC_POOLS` topics and the gold `eligible_applicants` vocabulary, rather than constraining gold topics to the existing dict list.
3. **Corpus growth**: set `_TARGET_TOTAL = 1000` → ~1124 examples. Accept overshoot (same mechanism as current 500→508).

## Part 1: Corpus generator changes

### 1a. `status` — gold + textual markers

**File**: `scripts/build_gold_corpus.py`

Add a `_status_prose(status, variant)` helper that renders a status marker in French:

```
variant 0: "Appel ouvert."
variant 1: "Ce appel à projets est ouvert."
variant 2: "Candidatures ouvertes."
variant 3: "Appel à venir, ouverture prévue prochainement."
variant 4: "Ce appel est clôturé."
variant 5: "Candidatures closes."
variant 6: "Appel annulé."
variant 7: "Clôture prochaine, date limite imminente."
variant 8: "Appel à projets annulé par l'organisme."
variant 9: "Appel fermé."
```

**Derive status** deterministically for each example, using a fixed reference year of 2027 (all hand-written examples have deadlines ≤2027; scaled examples range 2028-2033):
- If deadline year < 2027: CLOSED.
- If opening year > 2027: UPCOMING.
- If no opening/deadline dates: OPEN (most common).
- If deadline year == 2027 and deadline month ≤ 6: CLOSING_SOON (deadline near).
- Otherwise: OPEN.
- A deterministic ~10% subset gets CANCELLED instead: examples whose `eid` hash is divisible by 10. This replaces what would otherwise be OPEN.

**`_mk_example` changes**: accept an optional `status` kwarg. When provided, render a status prose line (via `_status_prose`) in `_build_doc`, add the text as an entity span `("STATUS", marker_text)`, and set `expected["status"]`.

**`_scale_from_conf` changes**: pass a derived status based on dates to `_mk_example`. The status is deterministic (based on year/month/day hash).

**`_build_doc` changes**: add an optional `status_line` parameter, placed at the end of the document body (after amount line, before contact). Each `status_line` is rendered as a standalone paragraph.

**Hand-written examples**: backfill `status` by adding a status marker line to each hand-written `body` list and `expected["status"]`. This is a large edit to the EXAMPLES list but is mechanical: for each example, pick a status based on its deadline year (pre-2028 → CLOSED/CANCELLED, 2028+ → OPEN/UPCOMING).

**Entity annotations**: the marker text is added as a `("STATUS", marker_text)` entity so the NER benchmark also exercises status detection. Keep the marker text as a simple substring of the document text (same pattern as other entities).

**Entity offset validation**: `_build_doc` must place the status line verbatim at a known offset so the entity `start`/`end` can be computed. Same mechanism used for other entities (append to `text`, track offset).

### 1b. `amount_min` — render ranges

**File**: `scripts/build_gold_corpus.py`

Add a `_amount_range_prose(amount_min, amount_max, variant)` helper:

```
variant 0: "De 50 000 € à 400 000 €"
variant 1: "Entre 100 000 et 500 000 EUR"
variant 2: "Montant : 3 000 000 à 5 000 000 €"
variant 3: "Budget de 50 000€ à 150 000€"
```

**`_mk_example` changes**: when `amount` has a `"min"` key, call `_amount_range_prose(min, value, variant)` instead of `_amount_prose(value, variant)` for the amount line. The AMOUNT entity span covers the entire range text.

**`_amount_prose` stays** for examples without `amount_min` (single-amount docs).

**Hand-written examples**: for the ~15 hand-written examples that have `amount_min` in `expected`, update their `amount` dict to include `"min"` and change the prose accordingly. The `_mk_example` path already handles `amount.min`; these hand-written ones use `_mk_example` (they pass `amount=dict(value=X, min=Y, variant=Z)`).

### 1c. `eligible_applicants` — scaled examples + prose

**File**: `scripts/build_gold_corpus.py`

**`_scale_from_conf` changes**: add an `_APPLICANT_POOLS` dict keyed by source name (same keys as `_TOPIC_POOLS`), each containing 2-4 candidate strings (e.g. `"universités"`, `"hôpitaux"`, `"laboratoires"`, `"entreprises"`). For each scaled example, pick 1-2 applicants deterministically from the source pool, add them to `expected_extra["eligible_applicants"]`, and render a "Candidats : X, Y." line in the document body.

**`_mk_example` changes**: accept optional `eligible_applicants` in `expected_extra`, add a prose line to the body if present. Add a `("ELIGIBLE_APPLICANTS", text)` entity span.

**`_build_doc` changes**: accept an optional `applicants_line` parameter, placed after the topics line.

**Hand-written examples**: already have `eligible_applicants` in `expected`. Ensure they also have a "Candidats : ..." prose line (most already do via hand-written body paragraphs; verify the remaining).

## Part 2: Extractor changes

### 2a. `regex.py` — amount_min + status

**File**: `src/aap_watcher/extraction/regex.py`

**`amount_min` parsing**: add regex patterns to `_extract_amount_min(text)`:
- `r"(?:de|entre|à partir de|min(?:imum)?[:\s]+)\s*(\d[\d\s,.]*)"` + amount processing
- `r"(\d[\d\s,.]*)\s*€?\s*à\s*(\d[\d\s,.]*)"` — in a range, group 1 is min
- `r"entre\s+(\d[\d\s,.]*)\s+et\s+(\d[\d\s,.]*)"` — "entre X et Y", group 1 is min

Called from `extract()` to set `amount_min` when found.

**`status` detection**: add `_extract_status(text)` mapping French keywords → `AAPStatus`:
- `"(?:appel\s+)?ouvert"` → OPEN
- `"(?:appel\s+)?à venir|ouverture\s+(?:prévue|à venir)"` → UPCOMING
- `"clôturé|clos|fermé|cloture"` → CLOSED
- `"annulé|annule"` → CANCELLED
- `"clôture\s+prochaine|date\s+limite\s+imminente"` → CLOSING_SOON

Return `UNKNOWN` if no keyword matches (no FP). Called from `extract()`.

### 2b. `dictionary.py` — vocabulary expansion + status

**File**: `src/aap_watcher/extraction/dictionary.py`

**`TOPICS` list**: expand to include all `_TOPIC_POOLS` topics from the corpus generator. Add ~30 new entries covering: "biologie cellulaire", "génétique", "physique", "chimie", "mathématiques", "algorithmique", "cybersécurité", "agronomie", "alimentation", "environnement", "transition écologique", "énergie", "biodiversité", "sciences de la vie", "deep tech", "biotechnologies", "recherche clinique", "recherche translationnelle", "épidémiologie", "microbiologie", "virologie", "infectiologie", "pharmacovigilance", "maladie d'alzheimer", "neurodégénérescence", etc. (~30 new entries, bringing total from ~50 to ~80).

**`APPLICANTS` list**: expand to include gold applicant vocabulary: "CEA", "MNHN", "IRD", "postdocs", "organismes publics", "établissements de santé", "écoles d'ingénieurs", "instituts CNRS", "hospitaux universitaires", "cliniques", "EHPAD", "centres de recherche", "associations de patients", "entreprises innovantes", etc. (~15 new entries, bringing total from ~22 to ~37).

**`status` detection**: add status keyword detection (same logic as regex, or shared utility). Map keywords → `AAPStatus` and set `status` on the extraction.

**`eligible_applicants`**: the existing substring search (`a in lower_text`) already works if the vocabulary covers the gold terms. The expansion handles this.

### 2c. `hybrid.py` — no merge changes needed

**File**: `src/aap_watcher/extraction/hybrid.py`

The `_FIELDS` list already includes `amount_min`, `eligible_applicants`, `research_topics`, `status`. The merge takes the first non-null value from component extractors. Since regex and dictionary now set these fields, hybrid automatically gets them. No code changes needed.

### 2d. Shared status extraction (optional utility)

Extract the keyword→AAPStatus mapping into a shared `_detect_status(text)` function in `src/aap_watcher/extraction/_status.py` (or inline in regex.py/dictionary.py if preferred). Both regex and dictionary use the same detection logic.

## Part 3: Testing & verification

### Corpus regeneration
- `uv run python scripts/build_gold_corpus.py` → verify count ~1124, splits populated, entity offsets valid, no duplicate IDs.
- Spot-check: every example has `expected["status"]`, examples with `amount_min` have range prose, scaled examples have `eligible_applicants`.

### Extractor tests
- `tests/test_extractors.py`: add tests for:
  - `amount_min` extraction from range prose ("de 50 000 à 400 000 €" → 50000)
  - `status` extraction ("appel ouvert" → OPEN, "clôturé" → CLOSED, "annulé" → CANCELLED)
  - Expanded dictionary vocabulary (new topics/applicants found in text)
  - Hand-written examples with status markers

### Full test suite
- `uv run pytest` → all tests pass (existing 98+ new).

### Benchmark verification
- `uv run aap-watcher benchmark --split test --field-matrix` → measure F1 on the 4 weak fields.
- `uv run aap-watcher benchmark --split all --field-matrix` → full benchmark for README update.

### Benchmark-protocol note
The canonical AAP schema (`src/aap_watcher/schema.py`) is **unchanged**. The gold corpus gains real `status`/`amount_min`/`eligible_applicants` values with textual signals — this is an enhancement within the existing benchmark protocol. No ADR required.

## Files touched

| File | Change |
|---|---|
| `scripts/build_gold_corpus.py` | Add status/amount-range/eligible-applicants rendering; `_TARGET_TOTAL = 1000`; expand seeds; backfill hand-written examples |
| `data/benchmark/gold/v1.jsonl` | Regenerated (~1124 examples, all 4 fields populated) |
| `src/aap_watcher/extraction/regex.py` | Add `amount_min` regex, `status` keyword detection, topics/applicants from prose |
| `src/aap_watcher/extraction/dictionary.py` | Expand `TOPICS` (~80), `APPLICANTS` (~37); add status detection |
| `src/aap_watcher/extraction/hybrid.py` | No changes (merge handles new fields automatically) |
| `tests/test_extractors.py` | Add tests for amount_min, status, expanded vocabulary |
| `README.md` | Update benchmark numbers from real run (never hand-estimate) |

## Implementation order

1. Corpus generator: add `_status_prose`, `_amount_range_prose`, `_APPLICANT_POOLS`; modify `_mk_example`, `_build_doc`, `_scale_from_conf`; backfill hand-written examples; set `_TARGET_TOTAL = 1000`; regenerate.
2. Dictionary extractor: expand `TOPICS`, `APPLICANTS`; add status detection.
3. Regex extractor: add `amount_min` regex, `status` detection.
4. Tests: add new tests for the 4 fields.
5. Benchmark: run, measure, update README.
