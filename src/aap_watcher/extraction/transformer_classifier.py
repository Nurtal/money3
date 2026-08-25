"""Transformer classification extractor (Phase 3 baseline, optional dependency).

Some AAP fields are better treated as classification tasks (funding type,
research topics, applicant type). Uses a HuggingFace zero-shot pipeline so no
fine-tuning is required for a first benchmark. Requires the ``transformers``
extra. Implements the shared ``Extractor`` interface.
"""

from __future__ import annotations

from ..schema import AAPExtraction, AAPStatus, Provenance
from .base import Document, Extractor

try:
    import transformers  # noqa: F401

    AVAILABLE = True
except ImportError:  # pragma: no cover
    transformers = None
    AVAILABLE = False

_FUNDING_LABELS = ["grant", "fellowship", "equipment", "training", "infrastructure", "other"]
_TOPIC_LABELS = [
    "cancer", "immunology", "rare diseases", "AI", "machine learning",
    "digital health", "public health", "clinical research",
]


class TransformerClassifierExtractor:
    name = "transformer_classifier"

    def __init__(self, model: str = "facebook/bart-large-mnli"):
        if not AVAILABLE:
            raise RuntimeError(
                "transformers/torch not installed. Add the 'transformers' extra."
            )
        from transformers import pipeline

        self.model = model
        self._clf = pipeline("zero-shot-classification", model=model)

    def extract(self, document: Document) -> AAPExtraction:
        text = document.text or ""
        funding = self._clf(text, _FUNDING_LABELS, multi_label=False)
        funding_type = funding["labels"][0] if funding["scores"][0] > 0.3 else None
        topic_res = self._clf(text, _TOPIC_LABELS, multi_label=True)
        topics = [
            lab for lab, sc in zip(topic_res["labels"], topic_res["scores"]) if sc > 0.5
        ]
        prov = Provenance(
            source_url=document.source_url,
            source_text=text[:500],
            extraction_method=self.name,
            model_version=self.model,
            confidence_score=0.75 if (funding_type or topics) else 0.1,
        )
        return AAPExtraction(
            funding_type=funding_type,
            research_topics=topics,
            source_url=document.source_url,
            extraction_method=self.name,
            status=AAPStatus.UNKNOWN,
            provenance=prov,
        )
