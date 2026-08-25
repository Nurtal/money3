"""Classical NLP extractor (Phase 3 baseline).

Classical techniques: tokenisation, sentence segmentation, keyword/rule
classification (README: strategy 3). This baseline adds *sentence-level*
eligibility extraction (more robust than the regex single-line match) and
title detection, complementing the dictionary gazetteer and regex strategies.
Pure-Python; no scikit-learn/NLTK dependency required to run.
"""

from __future__ import annotations

import re
from typing import Optional

from ..schema import AAPExtraction, AAPStatus, Provenance
from .base import Document, Extractor

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
_TITLE_RE = re.compile(r"(?i)(?:appel\s+à\s+projets|appel\s+à\s+candidatures)\s*[:\-]?\s*(.+)")
_ORG_RE = re.compile(r"\b([A-Z][A-Za-zÀ-ÿ]+(?:\s+[A-Z][A-Za-zÀ-ÿ]+){0,3})\b")
_ELIG_KW = re.compile(r"(?i)(?:candidats?\s+éligibles|éligibilit|qui\s+peut\s+candidater|bénéficiaires?)")

ORG_VOCAB = {
    "anr", "agence nationale de la recherche", "inca", "inserm", "cnrs",
    "fondation arc", "fondation de france", "ligue contre le cancer",
    "fondation pour la recherche médicale", "ars", "chu",
}


class ClassicalNLPExtractor:
    name = "classical_nlp"

    def extract(self, document: Document) -> AAPExtraction:
        text = document.text or ""
        sentences = [s.strip() for s in _SENT_SPLIT.split(text) if s.strip()]

        title = None
        tm = _TITLE_RE.search(text)
        if tm:
            title = tm.group(1).strip().rstrip(".")

        organisation = None
        for sent in sentences:
            for m in _ORG_RE.finditer(sent):
                cand = m.group(1).strip().lower()
                if cand in ORG_VOCAB:
                    organisation = m.group(1).strip()
                    break
            if organisation:
                break

        eligibility = None
        for sent in sentences:
            if _ELIG_KW.search(sent):
                eligibility = sent
                break

        topics = _detect_topics(text)

        prov = Provenance(
            source_url=document.source_url,
            source_text=text[:500],
            extraction_method=self.name,
            confidence_score=0.55 if (title or eligibility or organisation) else 0.1,
        )
        return AAPExtraction(
            title=title,
            organisation=organisation,
            eligibility=eligibility,
            research_topics=topics,
            source_url=document.source_url,
            extraction_method=self.name,
            status=AAPStatus.UNKNOWN,
            provenance=prov,
        )


_TOPICS = [
    "cancer", "immunologie", "maladies rares", "intelligence artificielle",
    "apprentissage automatique", "santé numérique", "santé publique",
    "recherche clinique", "biothérapies", "neurologie", "cardiologie",
    "génomique", "infectiologie",
]


def _detect_topics(text: str) -> list[str]:
    low = text.lower()
    return [t for t in _TOPICS if t in low]
