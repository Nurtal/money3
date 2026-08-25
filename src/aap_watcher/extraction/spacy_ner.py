"""spaCy NER extractor (Phase 3 baseline, optional dependency).

Requires the ``spacy`` extra and a French model (e.g. ``fr_core_news_sm``):

    uv pip install "aap-watcher[spacy]" && python -m spacy download fr_core_news_sm

The class implements the shared ``Extractor`` interface. If spaCy is not
installed, instantiating it raises a clear error rather than producing fake
results. NER entities are mapped to AAP fields; dates/amounts are normalised.
"""

from __future__ import annotations

from typing import Optional

from ..schema import AAPExtraction, AAPStatus, Provenance
from .base import Document, Extractor

try:
    import spacy  # noqa: F401

    AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only when spacy missing
    spacy = None
    AVAILABLE = False


class SpacyNerExtractor:
    name = "spacy_ner"

    def __init__(self, model: str = "fr_core_news_sm", custom: bool = False):
        if not AVAILABLE:
            raise RuntimeError(
                "spaCy is not installed. Add the 'spacy' extra and download a model."
            )
        self.model = model
        self.custom = custom
        self._nlp = spacy.load(model)

    def extract(self, document: Document) -> AAPExtraction:
        import re

        from ..benchmark.normalisation import normalize_amount, normalize_date

        doc = self._nlp(document.text or "")
        organisation = None
        deadline = None
        amount_max = None
        for ent in doc.ents:
            if ent.label_ in ("ORG", "ORGANIZATION") and organisation is None:
                organisation = ent.text
            elif ent.label_ in ("DATE",) and deadline is None:
                deadline = normalize_date(ent.text)
            elif ent.label_ in ("MONEY", "CARDINAL") and amount_max is None:
                amount_max = normalize_amount(ent.text)

        prov = Provenance(
            source_url=document.source_url,
            source_text=document.text[:500],
            extraction_method=self.name,
            model_version=self.model,
            confidence_score=0.7 if (organisation or deadline or amount_max) else 0.1,
        )
        return AAPExtraction(
            organisation=organisation,
            deadline=deadline,
            amount_max=amount_max,
            currency="EUR" if amount_max else None,
            source_url=document.source_url,
            extraction_method=self.name,
            status=AAPStatus.UNKNOWN,
            provenance=prov,
        )
