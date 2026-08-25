"""Hybrid extractor (Phase 3).

Combines multiple independent strategies and merges their outputs. The README's
core hypothesis (H6) is that a hybrid of regex + gazetteer + NLP may beat any
single approach; this must be *tested*, not assumed. Each field takes the first
non-null value across the composed extractors (deterministic, no LLM yet).
"""

from __future__ import annotations

from typing import Iterable

from ..schema import AAPExtraction, Provenance
from .base import Document, Extractor
from .classical_nlp import ClassicalNLPExtractor
from .dictionary import DictionaryExtractor
from .regex import RegexExtractor

_FIELDS = [
    "title", "organisation", "description", "amount_min", "amount_max",
    "currency", "opening_date", "deadline", "eligibility",
    "eligible_applicants", "research_topics", "geographical_scope",
    "project_duration", "funding_type", "application_url", "contact",
]


class HybridExtractor:
    name = "hybrid"

    def __init__(self, extractors: Iterable[Extractor] | None = None):
        self.extractors = list(extractors) if extractors else [
            RegexExtractor(),
            DictionaryExtractor(),
            ClassicalNLPExtractor(),
        ]

    def extract(self, document: Document) -> AAPExtraction:
        merged: dict = {}
        source_text = None
        source_url = document.source_url
        model_parts = []
        confidences = []
        for ex in self.extractors:
            model_parts.append(getattr(ex, "name", type(ex).__name__))
            partial = ex.extract(document)
            if partial.provenance:
                if source_text is None:
                    source_text = partial.provenance.source_text
                if partial.provenance.confidence_score is not None:
                    confidences.append(partial.provenance.confidence_score)
            for field in _FIELDS:
                val = getattr(partial, field, None)
                if val is None or (isinstance(val, (list, str)) and len(val) == 0):
                    continue
                if field not in merged:
                    merged[field] = val

        prov = Provenance(
            source_url=source_url,
            source_text=source_text,
            extraction_method=self.name,
            model_version="+".join(model_parts),
            confidence_score=max(confidences) if confidences else 0.0,
        )
        return AAPExtraction(
            source_url=source_url,
            extraction_method=self.name,
            status=merged.get("status") or AAPExtraction().status,
            provenance=prov,
            **{k: v for k, v in merged.items() if k != "status"},
        )
