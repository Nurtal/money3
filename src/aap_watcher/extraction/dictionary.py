"""Dictionary / gazetteer-based extractor (Phase 3 baseline).

Uses curated French vocabularies for controlled-value fields: organisation,
eligible applicants, research topics and funding type. Pure-Python, no ML
dependency. Excellent for controlled vocabularies; weak on free-text semantics
(README: strategy 2).
"""

from __future__ import annotations

from typing import Optional

from ..schema import AAPExtraction, AAPStatus, Provenance
from .base import Document, Extractor

ORGANISATIONS = [
    "Agence Nationale de la Recherche", "ANR",
    "Institut National du Cancer", "INCa",
    "Institut National de la Santé et de la Recherche Médicale", "INSERM",
    "Centre National de la Recherche Scientifique", "CNRS",
    "Fondation ARC", "Fondation de France",
    "Fondation pour la Recherche Médicale", "Ligue contre le Cancer",
    "Agences Régionales de Santé", "ARS",
]

APPLICANTS = [
    "universités", "université", "laboratoires", "laboratoire", "CHU",
    "hôpitaux", "hôpital", "entreprises", "PME", "associations", "fondations",
    "organismes de recherche", "INSERM", "CNRS", "cliniciens", "chercheurs",
    "équipes", "start-up", "collectivités",
]

TOPICS = [
    "cancer", "immunologie", "maladies rares", "intelligence artificielle",
    "apprentissage automatique", "santé numérique", "santé publique",
    "recherche clinique", "biothérapies", "neurologie", "cardiologie",
    "génomique", "infectiologie", "pédiatrie", "radiologie",
]

FUNDING_TYPE_RULES = [
    ("bourse", "fellowship"),
    ("équipement", "equipment"),
    ("infrastructure", "infrastructure"),
    ("formation", "training"),
    ("subvention", "grant"),
    ("financement", "grant"),
    ("aide", "grant"),
]


class DictionaryExtractor:
    name = "dictionary"

    def extract(self, document: Document) -> AAPExtraction:
        text = (document.text or "").lower()

        organisation = None
        for org in ORGANISATIONS:
            if org.lower() in text:
                organisation = org
                break

        applicants = [a for a in APPLICANTS if a.lower() in text]
        topics = [t for t in TOPICS if t.lower() in text]

        funding_type = None
        for kw, label in FUNDING_TYPE_RULES:
            if kw in text:
                funding_type = label
                break

        prov = Provenance(
            source_url=document.source_url,
            source_text=document.text[:500],
            extraction_method=self.name,
            confidence_score=0.5 if (organisation or topics or applicants) else 0.1,
        )
        return AAPExtraction(
            organisation=organisation,
            eligible_applicants=applicants,
            research_topics=topics,
            funding_type=funding_type,
            source_url=document.source_url,
            extraction_method=self.name,
            status=AAPStatus.UNKNOWN,
            provenance=prov,
        )
