"""Registry of extraction strategies.

Returns instances of every strategy whose dependencies are available, so the
benchmark can compare all runnable approaches on the same corpus. Strategies
whose optional dependencies (spaCy, transformers, openai) are missing are
skipped silently — they are not faked.
"""

from __future__ import annotations

from .base import Extractor
from .classical_nlp import ClassicalNLPExtractor
from .dictionary import DictionaryExtractor
from .hybrid import HybridExtractor
from .regex import RegexExtractor

_OPTIONAL = [
    ("spacy_ner", "spacy_ner", "SpacyNerExtractor"),
    ("transformers_ner", "transformer_ner", "TransformerNerExtractor"),
    ("transformers_ner", "transformer_ner", "CamemBertNerExtractor"),
    ("transformer_classifier", "transformer_classifier", "TransformerClassifierExtractor"),
    ("llm", "llm", "LLMExtractor"),
]


def available_extractors() -> list[Extractor]:
    extractors: list[Extractor] = [
        RegexExtractor(),
        DictionaryExtractor(),
        ClassicalNLPExtractor(),
        HybridExtractor(),
    ]
    for module_name, _, class_name in _OPTIONAL:
        try:
            mod = __import__(f"aap_watcher.extraction.{module_name}", fromlist=[class_name])
            cls = getattr(mod, class_name)
            extractors.append(cls())
        except Exception:
            continue
    return extractors


def available_extractor_names() -> list[str]:
    return [getattr(e, "name", type(e).__name__) for e in available_extractors()]
