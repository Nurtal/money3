"""Transformer / CamemBERT NER extractor (Phase 3 baseline, optional dependency).

Requires the ``transformers`` extra (PyTorch). Uses a HuggingFace token-
classification pipeline. French-specific models (CamemBERT) should be
explicitly benchmarked per the README. Implements the shared ``Extractor``
interface; raises a clear error if the framework is missing.
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


class TransformerNerExtractor:
    """Token-classification extractor (BERT / CamemBERT / RoBERTa)."""

    name = "transformer_ner"

    def __init__(self, model: str = "camembert-base", aggregation: str = "simple"):
        if not AVAILABLE:
            raise RuntimeError(
                "transformers/torch not installed. Add the 'transformers' extra."
            )
        from transformers import pipeline

        self.model = model
        self._ner = pipeline("ner", model=model, aggregation_strategy=aggregation)

    def extract(self, document: Document) -> AAPExtraction:
        from ..benchmark.normalisation import normalize_amount, normalize_date

        ents = self._ner(document.text or "")
        organisation = None
        deadline = None
        amount_max = None
        for e in ents:
            label = e.get("entity_group") or e.get("entity", "")
            if label.endswith("ORG") and organisation is None:
                organisation = e["word"]
            elif label.endswith("DATE") and deadline is None:
                deadline = normalize_date(e["word"])
            elif label.endswith("MONEY") or label.endswith("CARDINAL"):
                if amount_max is None:
                    amount_max = normalize_amount(e["word"])
        prov = Provenance(
            source_url=document.source_url,
            source_text=document.text[:500],
            extraction_method=self.name,
            model_version=self.model,
            confidence_score=0.8 if (organisation or deadline or amount_max) else 0.1,
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


class CamemBertNerExtractor(TransformerNerExtractor):
    name = "camembert_ner"

    def __init__(self, model: str = "camembert-base", aggregation: str = "simple"):
        super().__init__(model=model, aggregation=aggregation)
