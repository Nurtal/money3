"""spaCy NER extractor (Phase 3 baseline, optional dependency).

Requires the ``spacy`` extra and a French model (e.g. ``fr_core_news_md``):

    uv pip install "aap-watcher[spacy]" && python -m spacy download fr_core_news_md

The class implements the shared ``Extractor`` interface. If spaCy is not
installed, instantiating it raises a clear error rather than producing fake
results. NER entities (ORG, DATE, MONEY) are mapped to AAP fields and
normalised through the same normalisation helpers used by the benchmark so
its outputs are directly comparable to the other strategies.

Weaknesses of a stock spaCy NER (acknowledged in the README): CONTROLLED
vocabulary fields (research topics, eligible applicants), the canonical
geographical scope, and the issuing organisation (NER often returns a partner
institution, not the announcer). To stay comparable and honest, this extractor
only materialises fields NER can reasonably support and canonicalises the
organisation through the shared gazetteer used by the other extractors.
"""

from __future__ import annotations

import re

from ..schema import AAPExtraction, AAPStatus, Provenance
from .base import Document
from .dictionary import _DEFAULT_SCOPE, SCOPE_BY_ORG
from .regex import _detect_organisation

try:
    import spacy

    AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only when spacy missing
    spacy = None
    AVAILABLE = False


class SpacyNerExtractor:
    name = "spacy_ner"

    def __init__(self, model: str = "fr_core_news_md", custom: bool = False):
        if not AVAILABLE:
            raise RuntimeError(
                "spaCy is not installed. Add the 'spacy' extra and download a model."
            )
        self.model = model
        self.custom = custom
        self._nlp = spacy.load(model)

    def extract(self, document: Document) -> AAPExtraction:
        from ..benchmark.normalisation import normalize_amount, normalize_date

        text = document.text or ""
        doc = self._nlp(text)

        # --- Organisation: prefer the shared gazetteer (announcer detection),
        # fall back to a NER ORG entity.
        organisation = _detect_organisation(text)
        if not organisation:
            for ent in doc.ents:
                if ent.label_ in ("ORG", "ORGANIZATION"):
                    organisation = ent.text
                    break

        # --- Deadline / opening: NER DATE entities, prefer the one most likely
        # to be the deadline (label-adjacent "date limite"/"clôture").
        deadline = None
        opening_date = None
        for ent in doc.ents:
            if ent.label_ == "DATE":
                iso = normalize_date(ent.text)
                if not iso or "-" not in iso:
                    continue
                before = text[max(0, ent.start_char - 30):ent.start_char].lower()
                if re.search(r"(date\s+limite|cl[ôo]ture|deadline|soumission)", before):
                    if deadline is None:
                        deadline = iso
                elif re.search(r"(ouverture|d[ée]but|à\s+compter\s+du)", before):
                    if opening_date is None:
                        opening_date = iso
                else:
                    if deadline is None:
                        deadline = iso

        # --- Amount: use NER MONEY entity.
        amount_max = None
        currency = None
        for ent in doc.ents:
            if ent.label_ in ("MONEY", "CARDINAL"):
                amt = normalize_amount(ent.text)
                if amt:
                    if amount_max is None:
                        amount_max = amt
                        currency = "EUR"
                    break

        # --- Date labels in the text might not be caught by NER; fall back
        # to regex-based extraction for robustness.
        if deadline is None or opening_date is None:
            from .regex import (
                _DEADLINE_KW_RE,
                _DEADLINE_NDATE_RE,
                _OPENING_FDATE_RE,
                _OPENING_NDATE_RE,
                _best_date,
            )

            if deadline is None:
                deadline = _best_date(text, _DEADLINE_KW_RE)
                if not deadline:
                    deadline = _best_date(text, _DEADLINE_NDATE_RE, numeric=True)
            if opening_date is None:
                opening_date = _best_date(text, _OPENING_FDATE_RE)
                if not opening_date:
                    opening_date = _best_date(text, _OPENING_NDATE_RE, numeric=True)

        # --- Title (reuse lexical strategy; NER has no external title span).
        from .regex import _extract_title

        title = _extract_title(text)

        # --- Eligibility: reuse the shared sentence-level keyword approach.
        from .classical_nlp import _ELIG_KW, _SENT_SPLIT

        eligibility = None
        for sent in _SENT_SPLIT.split(text):
            sent = sent.strip()
            if sent and _ELIG_KW.search(sent):
                eligibility = sent
                break

        # --- Geographical scope from the canonical organisation.
        geographical_scope = SCOPE_BY_ORG.get(organisation or "", _DEFAULT_SCOPE) if organisation else None

        has_values = bool(organisation or deadline or amount_max or title or eligibility)
        prov = Provenance(
            source_url=document.source_url,
            source_text=text[:500],
            extraction_method=self.name,
            model_version=self.model,
            confidence_score=0.7 if has_values else 0.1,
        )
        return AAPExtraction(
            title=title,
            organisation=organisation,
            geographical_scope=geographical_scope,
            amount_max=amount_max,
            currency=currency,
            deadline=deadline,
            opening_date=opening_date,
            eligibility=eligibility if eligibility else None,
            source_url=document.source_url,
            extraction_method=self.name,
            status=AAPStatus.UNKNOWN,
            provenance=prov,
        )
