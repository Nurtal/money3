"""Dictionary / gazetteer-based extractor (Phase 3 baseline).

Uses curated French vocabularies for controlled-value fields: organisation,
eligible applicants, research topics and funding type. Pure-Python, no ML
dependency. Excellent for controlled vocabularies; weak on free-text semantics
(README: strategy 2).

v2: organisation is canonicalised to the gold abbreviations (ANR, INCa, Inserm,
CNRS, FRM, ...) and funding-type labels align to the corpus vocabulary
(subvention / bourse). Applicants and topics remain best-effort gazetteer
matches because the gold values are document-specific.
"""

from __future__ import annotations

from typing import Optional

from ..schema import AAPExtraction, AAPStatus, Provenance
from .base import Document, Extractor

# (canonical gold value, [text patterns to look for])
ORGANISATIONS: list[tuple[str, list[str]]] = [
    ("CHU Grenoble Alpes", ["chu grenoble"]),
    ("CHU de Lyon", ["chu de lyon", "chu lyon"]),
    ("AP-HP", ["ap-hp", "assistance publique"]),
    ("Commission européenne", ["commission europeenne", "commission européenne"]),
    ("Ligue contre le Cancer", ["ligue contre le cancer", "ligue contre le cancer"]),
    ("Fondation ARC", ["fondation arc"]),
    ("Fondation de France", ["fondation de france"]),
    ("FRM", ["fondation pour la recherche medicale", "frm"]),
    ("ARS Île-de-France", ["ars ile-de-france", "ars île-de-france", "ile-de-france.ars", "île-de-france.ars"]),
    ("ARS Auvergne-Rhône-Alpes", ["ars auvergne", "auvergne-rhone-alpes.ars", "auvergne-rhône-alpes.ars"]),
    ("ARS Occitanie", ["ars occitanie", "occitanie.ars"]),
    ("ARS Provence-Alpes-Côte d'Azur", ["ars provence", "paca.ars", "provence-alpes-cote", "provence-alpes-côte"]),
    ("ARS Bretagne", ["ars bretagne", "bretagne.ars"]),
    ("ARS Hauts-de-France", ["ars hauts", "hauts-de-france.ars"]),
    ("ARS Normandie", ["ars normandie", "normandie.ars"]),
    ("ARS Nouvelle-Aquitaine", ["ars nouvelle", "nouvelle-aquitaine.ars"]),
    ("ARS Guadeloupe", ["ars guadeloupe", "guadeloupe.ars"]),
    ("INCa", ["institut national du cancer", "inca"]),
    ("Inserm", ["institut national de la sante", "institut national de la santé", "inserm"]),
    ("CNRS", ["centre national de la recherche scientifique", "cnrs"]),
    ("ANR", ["agence nationale de la recherche", "anr"]),
    ("Inria", ["institut national de recherche en informatique", "inria"]),
    ("Inrae", ["institut national de recherche pour l'agriculture", "inrae"]),
    ("Bettencourt", ["bettencourt schueller", "bettencourt"]),
    ("BPI", ["bpifrance", "bpi"]),
    ("Institut Pasteur", ["institut pasteur", "pasteur"]),
    ("ADEME", ["ademe", "agence de la transition écologique", "agence de la transition ecologique", "agence de l'environnement"]),
    ("AFM-Téléthon", ["afm-telethon", "afm-téléthon", "association française contre les myopathies"]),
    ("ANSM", ["ansm", "agence nationale de sécurité du médicament", "agence nationale de securite du medicament"]),
    ("Fondation pour la Recherche sur Alzheimer", ["fondation pour la recherche sur alzheimer", "fondation recherche alzheimer", "recherche sur alzheimer"]),
]

APPLICANTS = [
    "universités", "hôpitaux", "centres de recherche", "chu",
    "cnrs", "inserm", "unités inserm", "instituts cnrs", "associations",
    "entreprises", "pme", "laboratoires", "grandes écoles",
    "instituts de recherche", "organisations de recherche", "jeunes chercheurs",
    "centres de lutte contre le cancer", "étudiants en thèse", "docteurs",
    "écoles d'ingénieurs", "centres hospitaliers", "centres anticancéreux",
]

# geographical scope implied by the issuing organisation. Domain prior: an ARS
# call is scoped to its region, the European Commission to Europe, and national
# research bodies (ANR, INCa, FRM, Ligue, Fondations, Inserm, CNRS, CHU, AP-HP)
# to France.
SCOPE_BY_ORG: dict[str, str] = {
    "ARS Île-de-France": "Île-de-France",
    "ARS Auvergne-Rhône-Alpes": "Auvergne-Rhône-Alpes",
    "ARS Occitanie": "Occitanie",
    "ARS Provence-Alpes-Côte d'Azur": "Provence-Alpes-Côte d'Azur",
    "ARS Bretagne": "Bretagne",
    "ARS Hauts-de-France": "Hauts-de-France",
    "ARS Normandie": "Normandie",
    "ARS Nouvelle-Aquitaine": "Nouvelle-Aquitaine",
    "ARS Guadeloupe": "Guadeloupe",
    "Commission européenne": "Europe",
}
_DEFAULT_SCOPE = "France"

TOPICS = [
    "dépistage", "cancérologie", "cancer", "thérapies ciblées", "recherche biomédicale",
    "maladies rares", "intelligence artificielle", "ia éthique",
    "immunothérapie", "changement climatique", "écosystèmes marins",
    "alimentation", "activité physique", "biomarqueurs", "médecine de précision",
    "qualité de vie", "fatigue", "antibiorésistance", "génétique",
    "immunologie", "transplantation", "thérapie cellulaire", "pharmacologie",
    "innovation", "recherche exploratoire", "vaccins", "alzheimer",
    "parkinson", "méthylation", "microarn", "éducation thérapeutique",
    "précarité", "télémédecine", "prévention", "car-t cells", "agroécologie",
    "capteurs", "recherche fondamentale", "apprentissage automatique",
    "deep learning", "neurosciences cognitives", "maladies neurodégénératives",
    "neuroimagerie", "interfaces cerveau-machine", "énergie solaire",
    "hydrogène vert", "stockage d'énergie", "réseaux électriques intelligents",
    "santé numérique", "santé publique", "recherche clinique",
]


def _norm(text: str) -> str:
    """Lowercase with common accent-normalisation for matching."""
    return text.lower().replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a").replace("ç", "c")


class DictionaryExtractor:
    name = "dictionary"

    def extract(self, document: Document) -> AAPExtraction:
        text = (document.text or "")
        norm_text = _norm(text)
        lower_text = text.lower()

        # --- Organisation: first matching rule wins ---
        organisation = None
        for canonical, patterns in ORGANISATIONS:
            if any(p in norm_text for p in patterns):
                organisation = canonical
                break

        # --- Eligible applicants: all matching keywords ---
        applicants = [a for a in APPLICANTS if a in lower_text]

        # --- Research topics: all matching keywords ---
        topics = [t for t in TOPICS if t in lower_text]

        # --- Funding type ---
        # Research calls for proposals are overwhelmingly subventions (grants);
        # a bourse is the notable exception signalled by the word "bourse".
        # This is a stated domain prior, not a per-document invention.
        if "bourse" in norm_text:
            funding_type = "bourse"
        else:
            funding_type = "subvention"

        # --- Geographical scope (domain prior from the organisation) ---
        geographical_scope = None
        if organisation:
            geographical_scope = SCOPE_BY_ORG.get(organisation, _DEFAULT_SCOPE)

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
            geographical_scope=geographical_scope,
            source_url=document.source_url,
            extraction_method=self.name,
            status=AAPStatus.UNKNOWN,
            provenance=prov,
        )
