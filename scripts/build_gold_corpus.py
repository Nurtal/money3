"""Generate the gold-standard corpus for AAP Watcher benchmarking.

This script produces ``data/benchmark/gold/v1.jsonl``. Entity offsets are
computed automatically from the document text so they always match the
.source text. Run from the repository root:

    uv run python scripts/build_gold_corpus.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "benchmark" / "gold" / "v1.jsonl"

# ---------------------------------------------------------------------------
# Entity result: label, canonical text, and the occurrence index to use when a
# label appears several times in the document (defaults to the first hit).
# ---------------------------------------------------------------------------


@dataclass
class Ent:
    label: str
    text: str
    nth: int = 0


@dataclass
class Example:
    id: str
    split: str
    source_url: str
    text: str
    expected: dict
    entities: list = field(default_factory=list)

    @property
    def entity_annotations(self) -> list[dict]:
        out = []
        for e in self.entities:
            # Find the (nth+1)-th occurrence of the span in the text.
            start = -1
            for _ in range(e.nth + 1):
                start = self.text.find(e.text, start + 1)
            if start == -1:
                raise ValueError(
                    f"[{self.id}] span {e.text!r} (nth={e.nth}) not found in text"
                )
            out.append(
                {
                    "text": e.text,
                    "label": e.label,
                    "start": start,
                    "end": start + len(e.text),
                }
            )
        return out

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "split": self.split,
            "source_url": self.source_url,
            "text": self.text,
            "expected": self.expected,
        }
        if self.entities:
            d["entities"] = self.entity_annotations
        return d


# ---------------------------------------------------------------------------
# Corpus definition. Entities only need label + text; offsets are computed.
# ---------------------------------------------------------------------------

EXAMPLES: list[Example] = [
    Example(
        "anr-blanc-2027", "test",
        "https://anr.fr/fr/les-appels-a-projets/blanc-2027.html",
"""\
Appel à projets : AAP Blanc 2027

L'Agence nationale de la recherche (ANR) lance l'appel à projets AAP Blanc 2027.
Ce programme finance des projets de recherche fondamentale dans toutes les disciplines scientifiques.

Date limite de soumission : 15 octobre 2027
Date d'ouverture : 15 juin 2027
Montant maximal par projet : 400 000 €
Durée maximale du projet : 48 mois

Éligibilité : Les équipes de recherche des établissements publics de recherche, des universités et des organismes du secteur public de la recherche sont éligibles.
Le coordinateur doit être un chercheur confirmé (au moins HDR ou équivalent).

Thématiques : Recherche fondamentale, toutes disciplines.

Contact : blanc@anr.fr""",
        {
            "title": "AAP Blanc 2027",
            "organisation": "ANR",
            "deadline": "2027-10-15",
            "opening_date": "2027-06-15",
            "amount_max": 400000,
            "currency": "EUR",
            "eligibility": "Les équipes de recherche des établissements publics de recherche, des universités et des organismes du secteur public de la recherche sont éligibles.",
            "eligible_applicants": ["établissements publics de recherche", "universités", "organismes du secteur public de la recherche"],
            "research_topics": ["recherche fondamentale"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 octobre 2027"), Ent("OPENING_DATE", "15 juin 2027"), Ent("AMOUNT", "400 000 €")],
    ),
    Example(
        "anr-ia-2027", "test",
        "https://anr.fr/fr/les-appels-a-projets/ia-2027.html",
"""\
Appel à projets : AAP Intelligenze Artificielle 2027

L'ANR lance l'appel à projets dédié à l'intelligence artificielle.

Ce programme vise à soutenir la recherche en IA, incluant l'apprentissage automatique, le traitement du langage naturel, la vision par ordinateur et l'IA responsable.

Date limite : 3 décembre 2027
Ouverture : 1er septembre 2027
Budget maximal : 600 000 €
Durée : 36 mois maximum

Éligibilité : Laboratoires de recherche publics et privés en France. Les partenariats industriels sont encouragés.
Candidats éligibles : enseignants-chercheurs, chercheurs CNRS, Inria, Inserm.

Thèmes : intelligence artificielle, apprentissage automatique, deep learning, IA éthique.

Site web : https://anr.fr/ia-2027""",
        {
            "title": "AAP Intelligenze Artificielle 2027",
            "organisation": "ANR",
            "deadline": "2027-12-03",
            "opening_date": "2027-09-01",
            "amount_max": 600000,
            "currency": "EUR",
            "eligibility": "Laboratoires de recherche publics et privés en France.",
            "eligible_applicants": ["enseignants-chercheurs", "chercheurs CNRS", "Inria", "Inserm"],
            "research_topics": ["intelligence artificielle", "apprentissage automatique", "deep learning", "IA éthique"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "3 décembre 2027"), Ent("OPENING_DATE", "1er septembre 2027"), Ent("AMOUNT", "600 000 €")],
    ),
    Example(
        "anr-cancer-2028", "train",
        "https://anr.fr/fr/les-appels-a-projets/cancer-2028.html",
"""\
Appel à projets : Programme Cancer 2028

L'ANR publie l'appel à projets Cancer 2028 en collaboration avec l'INCa.

Ce programme finance la recherche fondamentale et translationnelle en cancérologie.

Date limite de dépôt : 15 mars 2028
Date d'ouverture : 10 janvier 2028
Montant maximal : 350 000 €
Durée maximale : 36 mois

Éligibilité : Équipes de recherche en cancérologie, universités, centres anticancéreux.
Le coordinateur doit être chercheur ou enseignant-chercheur.

Thématiques : biologie du cancer, thérapies ciblées, immunothérapie, détection précoce.

Contact : cancer@anr.fr""",
        {
            "title": "Programme Cancer 2028",
            "organisation": "ANR",
            "deadline": "2028-03-15",
            "opening_date": "2028-01-10",
            "amount_max": 350000,
            "currency": "EUR",
            "eligibility": "Équipes de recherche en cancérologie, universités, centres anticancéreux.",
            "eligible_applicants": ["universités", "centres anticancéreux"],
            "research_topics": ["biologie du cancer", "thérapies ciblées", "immunothérapie", "détection précoce"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 mars 2028"), Ent("OPENING_DATE", "10 janvier 2028"), Ent("AMOUNT", "350 000 €")],
    ),
    Example(
        "anr-neuro-2027", "train",
        "https://anr.fr/fr/les-appels-a-projets/neuro-2027.html",
"""\
Appel à projets : AAP Neurosciences 2027

L'Agence nationale de la recherche lance l'AAP Neurosciences 2027.

Ce programme soutient la recherche en neurosciences fondamentales et cliniques.

Date limite : 8 novembre 2027
Ouverture : 15 juillet 2027
Budget maximal : 500 000 €
Durée : 48 mois maximum

Éligibilité : Laboratoires de neurosciences, universités, CHU, INSERM.
Coordinateur : chercheur ou enseignant-chercheur confirmé.

Thématiques : neurosciences cognitives, maladies neurodégénératives, neuroimagerie, interfaces cerveau-machine.

Email : neuro@anr.fr""",
        {
            "title": "AAP Neurosciences 2027",
            "organisation": "ANR",
            "deadline": "2027-11-08",
            "opening_date": "2027-07-15",
            "amount_max": 500000,
            "currency": "EUR",
            "eligibility": "Laboratoires de neurosciences, universités, CHU, INSERM.",
            "eligible_applicants": ["universités", "CHU", "INSERM"],
            "research_topics": ["neurosciences cognitives", "maladies neurodégénératives", "neuroimagerie", "interfaces cerveau-machine"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "8 novembre 2027"), Ent("OPENING_DATE", "15 juillet 2027"), Ent("AMOUNT", "500 000 €")],
    ),
    Example(
        "anr-energie-2028", "test",
        "https://anr.fr/fr/les-appels-a-projets/energie-2028.html",
"""\
Appel à projets : AAP Énergie 2028

L'ANR lance l'appel à projets Énergie pour la transition écologique.

Financement de la recherche sur les énergies renouvelables, le stockage et l'efficacité énergétique.

Date limite : 20 janvier 2028
Ouverture : 1er octobre 2027
Montant maximal : 450 000 €
Durée maximale : 36 mois

Éligibilité : Équipes de recherche en sciences de l'énergie, universités, grandes écoles, organismes publics.
Candidats : chercheurs et enseignants-chercheurs.

Thématiques : énergie solaire, hydrogène vert, stockage d'énergie, réseaux électriques intelligents.

Site : https://anr.fr/energie-2028""",
        {
            "title": "AAP Énergie 2028",
            "organisation": "ANR",
            "deadline": "2028-01-20",
            "opening_date": "2027-10-01",
            "amount_max": 450000,
            "currency": "EUR",
            "eligibility": "Équipes de recherche en sciences de l'énergie, universités, grandes écoles, organismes publics.",
            "eligible_applicants": ["universités", "grandes écoles", "organismes publics"],
            "research_topics": ["énergie solaire", "hydrogène vert", "stockage d'énergie", "réseaux électriques intelligents"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "20 janvier 2028"), Ent("OPENING_DATE", "1er octobre 2027"), Ent("AMOUNT", "450 000 €")],
    ),
    Example(
        "anr-transport-2027", "train",
        "https://anr.fr/fr/les-appels-a-projets/transport-2027.html",
"""\
Appel à projets : AAP Transport durable 2027

L'ANR soutient la recherche sur la mobilité durable.

Ce programme finance des projets sur les transports intelligents et la décarbonation.

Date limite de soumission : 25 septembre 2027
Date d'ouverture : 1er juin 2027
Budget maximal : 380 000 €
Durée : 42 mois maximum

Éligibilité : Laboratoires de transport, universités, Institut VEDECOM, IFSTTAR.
Coordinateur : chercheur confirmé.

Thématiques : véhicules électriques, mobilité partagée, planification urbaine, logistique verte.

Contact : transport@anr.fr""",
        {
            "title": "AAP Transport durable 2027",
            "organisation": "ANR",
            "deadline": "2027-09-25",
            "opening_date": "2027-06-01",
            "amount_max": 380000,
            "currency": "EUR",
            "eligibility": "Laboratoires de transport, universités, Institut VEDECOM, IFSTTAR.",
            "eligible_applicants": ["universités", "Institut VEDECOM", "IFSTTAR"],
            "research_topics": ["véhicules électriques", "mobilité partagée", "planification urbaine", "logistique verte"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "25 septembre 2027"), Ent("OPENING_DATE", "1er juin 2027"), Ent("AMOUNT", "380 000 €")],
    ),
    Example(
        "anr-biodiv-2028", "test",
        "https://anr.fr/fr/les-appels-a-projets/biodiversite-2028.html",
"""\
Appel à projets : AAP Biodiversité et écosystèmes 2028

L'ANR lance un appel à projets dédié à la préservation de la biodiversité.

Recherche fondamentale et appliquée sur la biodiversité, les écosystèmes et les services écosystémiques.

Date limite : 12 avril 2028
Ouverture : 20 janvier 2028
Montant maximal : 420 000 €
Durée maximale : 48 mois

Éligibilité : Écologues, biologistes de la conservation, géographes.
Institutions : universités, CNRS, MNHN, IRD.

Thématiques : biodiversité, conservation, changement climatique, pollinisateurs, écosystèmes marins.

Email : biodiv@anr.fr""",
        {
            "title": "AAP Biodiversité et écosystèmes 2028",
            "organisation": "ANR",
            "deadline": "2028-04-12",
            "opening_date": "2028-01-20",
            "amount_max": 420000,
            "currency": "EUR",
            "eligibility": "Écologues, biologistes de la conservation, géographes.",
            "eligible_applicants": ["universités", "CNRS", "MNHN", "IRD"],
            "research_topics": ["biodiversité", "conservation", "changement climatique", "pollinisateurs", "écosystèmes marins"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "12 avril 2028"), Ent("OPENING_DATE", "20 janvier 2028"), Ent("AMOUNT", "420 000 €")],
    ),
    Example(
        "anr-matiere-2027", "train",
        "https://anr.fr/fr/les-appels-a-projets/matiere-condensee-2027.html",
"""\
Appel à projets : AAP Matière condensée 2027

L'Agence nationale de la recherche finance la recherche en physique de la matière condensée.

Ce programme couvre la physique du solide, des matériaux, de la photonique et de la nanotechnologie.

Date limite : 5 décembre 2027
Ouverture : 15 août 2027
Budget maximal : 350 000 €
Durée : 36 mois maximum

Éligibilité : Physiciens, chimistes des matériaux.
Institutions éligibles : universités, CNRS, CEA, écoles d'ingénieurs.

Thématiques : supraconductivité, matériaux 2D, spintronique, photonique quantique.

Contact : matiere@anr.fr""",
        {
            "title": "AAP Matière condensée 2027",
            "organisation": "ANR",
            "deadline": "2027-12-05",
            "opening_date": "2027-08-15",
            "amount_max": 350000,
            "currency": "EUR",
            "eligibility": "Physiciens, chimistes des matériaux.",
            "eligible_applicants": ["universités", "CNRS", "CEA", "écoles d'ingénieurs"],
            "research_topics": ["supraconductivité", "matériaux 2D", "spintronique", "photonique quantique"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "5 décembre 2027"), Ent("OPENING_DATE", "15 août 2027"), Ent("AMOUNT", "350 000 €")],
    ),
    Example(
        "inca-prevention-2028", "test",
        "https://www.e-cancer.fr/Institut-national-du-cancer/Appels-a-projets/prevention-cancer-2028",
"""\
INCa - Appel à projets : Prévention des cancers 2028

L'Institut national du cancer (INCa) lance l'appel à projets Prévention des cancers 2028.

Ce programme finance la recherche sur la prévention primaire et secondaire des cancers.

Date limite : 30 juin 2028
Ouverture : 15 mars 2028
Montant maximal : 200 000 €
Durée maximale : 24 mois

Éligibilité : Équipes de recherche en santé publique, épidémiologie, prévention.
Institutions : universités, écoles de santé publique, centres de recherche en santé.

Thématiques : dépistage, facteurs de risque, tabagisme, alimentation, activité physique.

Contact : prevention@e-cancer.fr""",
        {
            "title": "Prévention des cancers 2028",
            "organisation": "INCa",
            "deadline": "2028-06-30",
            "opening_date": "2028-03-15",
            "amount_max": 200000,
            "currency": "EUR",
            "eligibility": "Équipes de recherche en santé publique, épidémiologie, prévention.",
            "eligible_applicants": ["universités", "écoles de santé publique", "centres de recherche en santé"],
            "research_topics": ["dépistage", "facteurs de risque", "tabagisme", "alimentation", "activité physique"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "30 juin 2028"), Ent("OPENING_DATE", "15 mars 2028"), Ent("AMOUNT", "200 000 €")],
    ),
    Example(
        "inca-recherche-2027", "test",
        "https://www.e-cancer.fr/Institut-national-du-cancer/Appels-a-projets/recherche-cancer-2027",
"""\
INCa - Appel à projets : Recherche translationnelle en cancérologie 2027

L'INCa soutient la recherche translationnelle en cancérologie.

Ce programme vise à accélérer le transfert des découvertes fondamentales vers la clinique.

Date limite : 15 septembre 2027
Ouverture : 1er mai 2027
Montant maximal : 300 000 €
Durée maximale : 36 mois

Éligibilité : Équipes mixtes recherche-clinique, centres intégrés de recherche sur le cancer.
Coordinateur : médecin-chercheur ou chercheur.

Thématiques : biomarqueurs, essais thérapeutiques, médecine de précision, résistance aux traitements.

Contact : translationnelle@e-cancer.fr""",
        {
            "title": "Recherche translationnelle en cancérologie 2027",
            "organisation": "INCa",
            "deadline": "2027-09-15",
            "opening_date": "2027-05-01",
            "amount_max": 300000,
            "currency": "EUR",
            "eligibility": "Équipes mixtes recherche-clinique, centres intégrés de recherche sur le cancer.",
            "eligible_applicants": ["médecin-chercheur", "chercheur"],
            "research_topics": ["biomarqueurs", "essais thérapeutiques", "médecine de précision", "résistance aux traitements"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 septembre 2027"), Ent("OPENING_DATE", "1er mai 2027"), Ent("AMOUNT", "300 000 €")],
    ),
    Example(
        "inca-soutien-2028", "train",
        "https://www.e-cancer.fr/Institut-national-du-cancer/Appels-a-projets/soutien-equipe-2028",
"""\
INCa - Appel à projets : Soutien aux équipes de recherche 2028

L'INCa offre un soutien aux équipes de recherche en cancérologie pour le renforcement de leurs capacités.

Date limite : 1er août 2028
Ouverture : 1er avril 2028
Montant maximal : 150 000 €
Durée maximale : 24 mois

Éligibilité : Équipes de recherche en cancérologie avec un minimum de 3 chercheurs.
Institutions : centres de recherche, universités, hôpitaux.

Thématiques : soutien à l'équipement, formation, collaboration internationale.

Contact : soutien@e-cancer.fr""",
        {
            "title": "Soutien aux équipes de recherche 2028",
            "organisation": "INCa",
            "deadline": "2028-08-01",
            "opening_date": "2028-04-01",
            "amount_max": 150000,
            "currency": "EUR",
            "eligibility": "Équipes de recherche en cancérologie avec un minimum de 3 chercheurs.",
            "eligible_applicants": ["centres de recherche", "universités", "hôpitaux"],
            "research_topics": ["soutien à l'équipement", "formation", "collaboration internationale"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "1er août 2028"), Ent("OPENING_DATE", "1er avril 2028"), Ent("AMOUNT", "150 000 €")],
    ),
    Example(
        "inca-radioprotection-2027", "test",
        "https://www.e-cancer.fr/Institut-national-du-cancer/Appels-a-projets/radioprotection-2027",
"""\
INCa - Appel à projets : Radioprotection et cancérogénèse 2027

L'INCa finance la recherche sur les effets des rayonnements ionisants.

Date limite : 20 novembre 2027
Ouverture : 10 septembre 2027
Montant maximal : 180 000 €
Durée maximale : 24 mois

Éligibilité : Physiciens radioprotection, biologistes, oncologues.
Institutions : universités, CEA, IRSN, centres hospitaliers.

Thématiques : dosimétrie, radiothérapie, risque radiologique, cancérogénèse.

Contact : radio@e-cancer.fr""",
        {
            "title": "Radioprotection et cancérogénèse 2027",
            "organisation": "INCa",
            "deadline": "2027-11-20",
            "opening_date": "2027-09-10",
            "amount_max": 180000,
            "currency": "EUR",
            "eligibility": "Physiciens radioprotection, biologistes, oncologues.",
            "eligible_applicants": ["universités", "CEA", "IRSN", "centres hospitaliers"],
            "research_topics": ["dosimétrie", "radiothérapie", "risque radiologique", "cancérogénèse"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "20 novembre 2027"), Ent("OPENING_DATE", "10 septembre 2027"), Ent("AMOUNT", "180 000 €")],
    ),
    Example(
        "inca-support-psycho-2028", "train",
        "https://www.e-cancer.fr/Institut-national-du-cancer/Appels-a-projets/soutien-psychologique-2028",
"""\
INCa - Appel à projets : Soutien psychologique des patients 2028

L'INCa lance un appel sur le soutien psychologique aux patients atteints de cancer.

Date limite : 15 juillet 2028
Ouverture : 15 mars 2028
Montant maximal : 120 000 €
Durée maximale : 18 mois

Éligibilité : Psychologues, psychiatres, travailleurs sociaux en milieu oncologique.
Institutions : centres de lutte contre le cancer, CHU, associations de patients.

Thématiques : qualité de vie, fatigue, troubles du sommeil, accompagnement fin de vie.

Contact : psycho@e-cancer.fr""",
        {
            "title": "Soutien psychologique des patients 2028",
            "organisation": "INCa",
            "deadline": "2028-07-15",
            "opening_date": "2028-03-15",
            "amount_max": 120000,
            "currency": "EUR",
            "eligibility": "Psychologues, psychiatres, travailleurs sociaux en milieu oncologique.",
            "eligible_applicants": ["centres de lutte contre le cancer", "CHU", "associations de patients"],
            "research_topics": ["qualité de vie", "fatigue", "troubles du sommeil", "accompagnement fin de vie"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 juillet 2028"), Ent("OPENING_DATE", "15 mars 2028"), Ent("AMOUNT", "120 000 €")],
    ),
    Example(
        "ars-environnement-2028", "test",
        "https://www.ars.sante.fr/aaps/environnement-sante-2028",
"""\
ARS Île-de-France - Appel à projets : Environnement et santé 2028

L'Agence régionale de santé Île-de-France lance l'appel à projets Environnement et santé 2028.

Ce programme finance la recherche sur les impacts environnementaux sur la santé.

Date limite : 30 mai 2028
Ouverture : 1er février 2028
Montant maximal : 80 000 €
Durée maximale : 18 mois

Éligibilité : Équipes de recherche en santé environnementale.
Institutions : universités franciliennes, hôpitaux, associations.

Thématiques : pollution de l'air, qualité de l'eau, nuisances sonores, canicule et santé.

Contact : environnement@ars-idf.fr""",
        {
            "title": "Environnement et santé 2028",
            "organisation": "ARS Île-de-France",
            "deadline": "2028-05-30",
            "opening_date": "2028-02-01",
            "amount_max": 80000,
            "currency": "EUR",
            "eligibility": "Équipes de recherche en santé environnementale.",
            "eligible_applicants": ["universités franciliennes", "hôpitaux", "associations"],
            "research_topics": ["pollution de l'air", "qualité de l'eau", "nuisances sonores", "canicule et santé"],
            "geographical_scope": "Île-de-France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "30 mai 2028"), Ent("OPENING_DATE", "1er février 2028"), Ent("AMOUNT", "80 000 €")],
    ),
    Example(
        "ars-addictions-2027", "test",
        "https://www.ars.sante.fr/aaps/addictions-2027",
"""\
ARS Occitanie - Appel à projets : Addictions 2027

L'ARS Occitanie soutient la recherche sur les addictions.

Programme de recherche sur la prévention et la prise en charge des addictions.

Date limite : 15 octobre 2027
Ouverture : 15 juillet 2027
Montant maximal : 50 000 €
Durée maximale : 12 mois

Éligibilité : Addictologues, psychologues, éducateurs spécialisés.
Institutions : hôpitaux, centres de soins, CMPP, universités.

Thématiques : alcool, tabac, cannabis, jeux vidéo, addictions comportementales.

Contact : addictions@ars-occitanie.fr""",
        {
            "title": "Addictions 2027",
            "organisation": "ARS Occitanie",
            "deadline": "2027-10-15",
            "opening_date": "2027-07-15",
            "amount_max": 50000,
            "currency": "EUR",
            "eligibility": "Addictologues, psychologues, éducateurs spécialisés.",
            "eligible_applicants": ["hôpitaux", "centres de soins", "CMPP", "universités"],
            "research_topics": ["alcool", "tabac", "cannabis", "jeux vidéo", "addictions comportementales"],
            "geographical_scope": "Occitanie",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 octobre 2027"), Ent("OPENING_DATE", "15 juillet 2027"), Ent("AMOUNT", "50 000 €")],
    ),
    Example(
        "ars-obesite-2028", "train",
        "https://www.ars.sante.fr/aaps/obesite-nutrition-2028",
"""\
ARS Auvergne-Rhône-Alpes - Appel à projets : Obésité et nutrition 2028

L'ARS AURA lance l'appel à projets Obésité et nutrition 2028.

Recherche sur la prévention et la prise en charge de l'obésité et des troubles nutritionnels.

Date limite : 20 juin 2028
Ouverture : 20 janvier 2028
Montant maximal : 60 000 €
Durée maximale : 12 mois

Éligibilité : Nutritionnistes, diététiciens, endocrinologues.
Institutions : CHU, centres hospitaliers, universités.

Thématiques : obésité infantile, alimentation, activité physique, chirurgie bariatrique.

Contact : nutrition@ars-aura.fr""",
        {
            "title": "Obésité et nutrition 2028",
            "organisation": "ARS Auvergne-Rhône-Alpes",
            "deadline": "2028-06-20",
            "opening_date": "2028-01-20",
            "amount_max": 60000,
            "currency": "EUR",
            "eligibility": "Nutritionnistes, diététiciens, endocrinologues.",
            "eligible_applicants": ["CHU", "centres hospitaliers", "universités"],
            "research_topics": ["obésité infantile", "alimentation", "activité physique", "chirurgie bariatrique"],
            "geographical_scope": "Auvergne-Rhône-Alpes",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "20 juin 2028"), Ent("OPENING_DATE", "20 janvier 2028"), Ent("AMOUNT", "60 000 €")],
    ),
    Example(
        "ars-mental-2027", "test",
        "https://www.ars.sante.fr/aaps/sante-mentale-2027",
"""\
ARS Bretagne - Appel à projets : Santé mentale 2027

L'ARS Bretagne soutient la recherche sur la santé mentale.

Programme de recherche sur la prévention du suicide, la dépression et les troubles anxieux.

Date limite : 10 septembre 2027
Ouverture : 10 juin 2027
Montant maximal : 40 000 €
Durée maximale : 12 mois

Éligibilité : Psychiatres, psychologues, infirmiers en psychiatrie.
Institutions : centres médico-psychologiques, hôpitaux, universités.

Thématiques : prévention suicide, dépression, troubles anxieux, santé mentale des jeunes.

Contact : mental@ars-bretagne.fr""",
        {
            "title": "Santé mentale 2027",
            "organisation": "ARS Bretagne",
            "deadline": "2027-09-10",
            "opening_date": "2027-06-10",
            "amount_max": 40000,
            "currency": "EUR",
            "eligibility": "Psychiatres, psychologues, infirmiers en psychiatrie.",
            "eligible_applicants": ["centres médico-psychologiques", "hôpitaux", "universités"],
            "research_topics": ["prévention suicide", "dépression", "troubles anxieux", "santé mentale des jeunes"],
            "geographical_scope": "Bretagne",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "10 septembre 2027"), Ent("OPENING_DATE", "10 juin 2027"), Ent("AMOUNT", "40 000 €")],
    ),
    Example(
        "ars-antibioresistance-2028", "train",
        "https://www.ars.sante.fr/aaps/antibioresistance-2028",
"""\
ARS PACA - Appel à projets : Antibiorésistance 2028

L'ARS PACA lance un appel à projets sur l'antibiorésistance.

Recherche sur la prévention des infections associées aux soins et l'utilisation raisonnée des antibiotiques.

Date limite : 1er novembre 2028
Ouverture : 1er août 2028
Montant maximal : 70 000 €
Durée maximale : 18 mois

Éligibilité : Infectiologues, hygiénistes, microbiologistes.
Institutions : hôpitaux, laboratoires de microbiologie, universités.

Thématiques : antibiorésistance, hygiene, bactéries multirésistantes, antibiotiques.

Contact : abr@ars-paca.fr""",
        {
            "title": "Antibiorésistance 2028",
            "organisation": "ARS PACA",
            "deadline": "2028-11-01",
            "opening_date": "2028-08-01",
            "amount_max": 70000,
            "currency": "EUR",
            "eligibility": "Infectiologues, hygiénistes, microbiologistes.",
            "eligible_applicants": ["hôpitaux", "laboratoires de microbiologie", "universités"],
            "research_topics": ["antibiorésistance", "hygiene", "bactéries multirésistantes", "antibiotiques"],
            "geographical_scope": "PACA",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "1er novembre 2028"), Ent("OPENING_DATE", "1er août 2028"), Ent("AMOUNT", "70 000 €")],
    ),
    Example(
        "fondation-arc-2028", "test",
        "https://www.fondation-arc.org/appel-a-projets/recherche-cancer-sein-2028",
"""\
Fondation ARC - Appel à projets : Recherche sur le cancer du sein 2028

La Fondation ARC pour la recherche sur le cancer lance l'appel à projets Cancer du sein 2028.

Ce programme finance la recherche fondamentale et clinique sur le cancer du sein.

Date limite : 15 avril 2028
Ouverture : 15 janvier 2028
Montant maximal : 250 000 €
Durée maximale : 36 mois

Éligibilité : Équipes de recherche en oncologie, biologistes, cliniciens.
Institutions : centres de recherche, universités, centres anticancéreux.

Thématiques : cancer du sein, dépistage, thérapies ciblées, génétique.

Contact : appel@fondation-arc.org""",
        {
            "title": "Recherche sur le cancer du sein 2028",
            "organisation": "Fondation ARC",
            "deadline": "2028-04-15",
            "opening_date": "2028-01-15",
            "amount_max": 250000,
            "currency": "EUR",
            "eligibility": "Équipes de recherche en oncologie, biologistes, cliniciens.",
            "eligible_applicants": ["centres de recherche", "universités", "centres anticancéreux"],
            "research_topics": ["cancer du sein", "dépistage", "thérapies ciblées", "génétique"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 avril 2028"), Ent("OPENING_DATE", "15 janvier 2028"), Ent("AMOUNT", "250 000 €")],
    ),
    Example(
        "fondation-arc-lymphome-2027", "test",
        "https://www.fondation-arc.org/appel-a-projets/lymphomes-2027",
"""\
Fondation ARC - Appel à projets : Lymphomes 2027

La Fondation ARC finance la recherche sur les lymphomes.

Programme dédié à la compréhension et au traitement des lymphomes non hodgkiniens et hodgkiniens.

Date limite : 20 septembre 2027
Ouverture : 20 juin 2027
Montant maximal : 200 000 €
Durée maximale : 36 mois

Éligibilité : Hématologues, oncologues, immunologistes.
Institutions : centres de recherche, hôpitaux, universités.

Thématiques : lymphomes, immunologie, transplantation, thérapie cellulaire.

Contact : lymphome@fondation-arc.org""",
        {
            "title": "Lymphomes 2027",
            "organisation": "Fondation ARC",
            "deadline": "2027-09-20",
            "opening_date": "2027-06-20",
            "amount_max": 200000,
            "currency": "EUR",
            "eligibility": "Hématologues, oncologues, immunologistes.",
            "eligible_applicants": ["centres de recherche", "hôpitaux", "universités"],
            "research_topics": ["lymphomes", "immunologie", "transplantation", "thérapie cellulaire"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "20 septembre 2027"), Ent("OPENING_DATE", "20 juin 2027"), Ent("AMOUNT", "200 000 €")],
    ),
    Example(
        "fondation-arc-postdoc-2028", "train",
        "https://www.fondation-arc.org/appel-a-projets/bourses-postdoc-2028",
"""\
Fondation ARC - Bourses postdoctorales 2028

La Fondation ARC offre des bourses postdoctorales pour la recherche en cancérologie.

Ces bourses permettent aux jeunes chercheurs de se former dans des laboratoires d'excellence.

Date limite : 1er mars 2028
Ouverture : 1er novembre 2027
Montant : 35 000 € par an pendant 2 ans
Durée : 24 mois

Éligibilité : Jeunes chercheurs ayant soutenu leur thèse depuis moins de 2 ans.
Thèse en cancérologie ou domaine connexe.

Thématiques : cancérologie, recherche biomédicale.

Contact : bourses@fondation-arc.org""",
        {
            "title": "Bourses postdoctorales 2028",
            "organisation": "Fondation ARC",
            "deadline": "2028-03-01",
            "opening_date": "2027-11-01",
            "amount_max": 70000,
            "currency": "EUR",
            "eligibility": "Jeunes chercheurs ayant soutenu leur thèse depuis moins de 2 ans.",
            "eligible_applicants": ["jeunes chercheurs"],
            "research_topics": ["cancérologie", "recherche biomédicale"],
            "geographical_scope": "France",
            "funding_type": "bourse",
        },
        [Ent("DEADLINE", "1er mars 2028"), Ent("OPENING_DATE", "1er novembre 2027"), Ent("AMOUNT", "35 000 €")],
    ),
    Example(
        "fondation-arc-young-2027", "train",
        "https://www.fondation-arc.org/appel-a-projets/chercheurs-2027",
"""\
Fondation ARC - Aide aux jeunes chercheurs 2027

La Fondation ARC soutient les jeunes chercheurs en cancérologie.

Subvention de démarrage pour les jeunes équipes de recherche.

Date limite : 15 décembre 2027
Ouverture : 15 septembre 2027
Montant maximal : 50 000 €
Durée maximale : 12 mois

Éligibilité : Chercheurs de moins de 40 ans, équipe de 3 personnes minimum.
Institutions : laboratoires publics ou privés.

Thématiques : cancérologie, tout domaine.

Contact : jeunes@fondation-arc.org""",
        {
            "title": "Aide aux jeunes chercheurs 2027",
            "organisation": "Fondation ARC",
            "deadline": "2027-12-15",
            "opening_date": "2027-09-15",
            "amount_max": 50000,
            "currency": "EUR",
            "eligibility": "Chercheurs de moins de 40 ans, équipe de 3 personnes minimum.",
            "eligible_applicants": ["jeunes chercheurs"],
            "research_topics": ["cancérologie"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 décembre 2027"), Ent("OPENING_DATE", "15 septembre 2027"), Ent("AMOUNT", "50 000 €")],
    ),
    Example(
        "frm-recherche-2028", "test",
        "https://www.frm.org/appels/recherche-fondamentale-2028",
"""\
Fondation pour la Recherche Médicale - Appel à projets : Recherche fondamentale 2028

La FRM lance l'appel à projets Recherche fondamentale 2028.

Ce programme finance la recherche biomédicale fondamentale dans tous les domaines.

Date limite : 1er octobre 2028
Ouverture : 1er juillet 2028
Montant maximal : 200 000 €
Durée maximale : 36 mois

Éligibilité : Équipes de recherche biomédicale.
Institutions : universités, INSERM, CNRS, hôpitaux.

Thématiques : biologie cellulaire, génétique, immunologie, neurosciences.

Contact : appel@frm.org""",
        {
            "title": "Recherche fondamentale 2028",
            "organisation": "FRM",
            "deadline": "2028-10-01",
            "opening_date": "2028-07-01",
            "amount_max": 200000,
            "currency": "EUR",
            "eligibility": "Équipes de recherche biomédicale.",
            "eligible_applicants": ["universités", "INSERM", "CNRS", "hôpitaux"],
            "research_topics": ["biologie cellulaire", "génétique", "immunologie", "neurosciences"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "1er octobre 2028"), Ent("OPENING_DATE", "1er juillet 2028"), Ent("AMOUNT", "200 000 €")],
    ),
    Example(
        "frm-urgence-2027", "test",
        "https://www.frm.org/appels/projets-urgence-2027",
"""\
Fondation pour la Recherche Médicale - Appel à projets en urgence 2027

La FRM lance un appel à projets en urgence pour répondre à une crise sanitaire.

Programme accéléré pour des projets de recherche à court terme.

Date limite : 30 jours après publication
Montant maximal : 100 000 €
Durée maximale : 12 mois

Éligibilité : Toute équipe de recherche ayant un protocole prêt à mettre en œuvre.
Pas de restriction d'institution.

Thématiques : épidémiologie, maladies infectieuses, urgences sanitaires.

Contact : urgence@frm.org""",
        {
            "title": "Projets en urgence 2027",
            "organisation": "FRM",
            "amount_max": 100000,
            "currency": "EUR",
            "eligibility": "Toute équipe de recherche ayant un protocole prêt à mettre en œuvre.",
            "eligible_applicants": ["toute équipe de recherche"],
            "research_topics": ["épidémiologie", "maladies infectieuses", "urgences sanitaires"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("AMOUNT", "100 000 €")],
    ),
    Example(
        "frm-phd-2028", "train",
        "https://www.frm.org/appels/bourses-doctorat-2028",
"""\
Fondation pour la Recherche Médicale - Bourses de doctorat 2028

La FRM offre des bourses de doctorat en recherche biomédicale.

Financement de thèses pour les jeunes chercheurs.

Date limite : 15 février 2028
Ouverture : 15 octobre 2027
Montant : 25 000 € par an pendant 3 ans
Durée : 36 mois

Éligibilité : Étudiants inscrits en thèse, en première ou deuxième année.
Sujet de thèse en recherche biomédicale.

Thématiques : biologie, médecine, pharmacologie.

Contact : these@frm.org""",
        {
            "title": "Bourses de doctorat 2028",
            "organisation": "FRM",
            "deadline": "2028-02-15",
            "opening_date": "2027-10-15",
            "amount_max": 75000,
            "currency": "EUR",
            "eligibility": "Étudiants inscrits en thèse, en première ou deuxième année.",
            "eligible_applicants": ["étudiants en thèse"],
            "research_topics": ["biologie", "médecine", "pharmacologie"],
            "geographical_scope": "France",
            "funding_type": "bourse",
        },
        [Ent("DEADLINE", "15 février 2028"), Ent("OPENING_DATE", "15 octobre 2027"), Ent("AMOUNT", "25 000 €")],
    ),
    Example(
        "frm-equipement-2027", "train",
        "https://www.frm.org/appels/equipement-2027",
"""\
Fondation pour la Recherche Médicale - Aide à l'équipement 2027

La FRM finance l'acquisition d'équipements de recherche.

Programme d'équipement pour les laboratoires de recherche biomédicale.

Date limite : 15 novembre 2027
Ouverture : 15 août 2027
Montant maximal : 150 000 €
Durée maximale : 12 mois

Éligibilité : Laboratoires de recherche biomédicale.
Institutions : universités, INSERM, CNRS.

Thématiques : équipement de laboratoire, biotechnologies.

Contact : equipement@frm.org""",
        {
            "title": "Aide à l'équipement 2027",
            "organisation": "FRM",
            "deadline": "2027-11-15",
            "opening_date": "2027-08-15",
            "amount_max": 150000,
            "currency": "EUR",
            "eligibility": "Laboratoires de recherche biomédicale.",
            "eligible_applicants": ["universités", "INSERM", "CNRS"],
            "research_topics": ["équipement de laboratoire", "biotechnologies"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 novembre 2027"), Ent("OPENING_DATE", "15 août 2027"), Ent("AMOUNT", "150 000 €")],
    ),
    Example(
        "frm-postdoc-2028", "test",
        "https://www.frm.org/appels/postdoc-2028",
"""\
Fondation pour la Recherche Médicale - Bourses postdoctorales 2028

La FRM offre des bourses postdoctorales en recherche biomédicale.

Financement de postes postdoctoraux dans des laboratoires d'excellence.

Date limite : 1er avril 2028
Ouverture : 1er décembre 2027
Montant : 32 000 € par an pendant 2 ans
Durée : 24 mois

Éligibilité : Docteurs ayant soutenu leur thèse depuis moins de 3 ans.
Thèse en domaine biomédical.

Thématiques : recherche biomédicale, tout domaine.

Contact : postdoc@frm.org""",
        {
            "title": "Bourses postdoctorales 2028",
            "organisation": "FRM",
            "deadline": "2028-04-01",
            "opening_date": "2027-12-01",
            "amount_max": 64000,
            "currency": "EUR",
            "eligibility": "Docteurs ayant soutenu leur thèse depuis moins de 3 ans.",
            "eligible_applicants": ["docteurs"],
            "research_topics": ["recherche biomédicale"],
            "geographical_scope": "France",
            "funding_type": "bourse",
        },
        [Ent("DEADLINE", "1er avril 2028"), Ent("OPENING_DATE", "1er décembre 2027"), Ent("AMOUNT", "32 000 €")],
    ),
    Example(
        "ligue-cancer-2028", "test",
        "https://www.ligue-cancer.net/appel-a-projets/recherche-2028",
"""\
Ligue contre le Cancer - Appel à projets : Recherche en cancérologie 2028

La Ligue contre le Cancer lance l'appel à projets Recherche 2028.

Ce programme finance la recherche fondamentale en cancérologie.

Date limite : 15 mai 2028
Ouverture : 15 février 2028
Montant maximal : 180 000 €
Durée maximale : 36 mois

Éligibilité : Équipes de recherche en cancérologie.
Institutions : laboratoires publics, universités, centres de recherche.

Thématiques : biologie tumorale, microenvironnement, metastases, angiogenèse.

Contact : recherche@ligue-cancer.net""",
        {
            "title": "Recherche en cancérologie 2028",
            "organisation": "Ligue contre le Cancer",
            "deadline": "2028-05-15",
            "opening_date": "2028-02-15",
            "amount_max": 180000,
            "currency": "EUR",
            "eligibility": "Équipes de recherche en cancérologie.",
            "eligible_applicants": ["laboratoires publics", "universités", "centres de recherche"],
            "research_topics": ["biologie tumorale", "microenvironnement", "metastases", "angiogenèse"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 mai 2028"), Ent("OPENING_DATE", "15 février 2028"), Ent("AMOUNT", "180 000 €")],
    ),
    Example(
        "ligue-cancer-bourses-2027", "train",
        "https://www.ligue-cancer.net/appel-a-projets/bourses-recherche-2027",
"""\
Ligue contre le Cancer - Bourses de recherche 2027

La Ligue contre le Cancer offre des bourses de recherche aux jeunes chercheurs.

Programme de bourses doctorales et postdoctorales en cancérologie.

Date limite : 1er septembre 2027
Ouverture : 1er juin 2027
Montant : 20 000 € par an pendant 3 ans (doctorat) ou 30 000 € par an pendant 2 ans (postdoc)
Durée : 24-36 mois

Éligibilité : Doctorants ou jeunes docteurs en cancérologie.

Thématiques : cancérologie, recherche translationnelle.

Contact : bourses@ligue-cancer.net""",
        {
            "title": "Bourses de recherche 2027",
            "organisation": "Ligue contre le Cancer",
            "deadline": "2027-09-01",
            "opening_date": "2027-06-01",
            "amount_max": 60000,
            "currency": "EUR",
            "eligibility": "Doctorants ou jeunes docteurs en cancérologie.",
            "eligible_applicants": ["doctorants", "jeunes docteurs"],
            "research_topics": ["cancérologie", "recherche translationnelle"],
            "geographical_scope": "France",
            "funding_type": "bourse",
        },
        [Ent("DEADLINE", "1er septembre 2027"), Ent("OPENING_DATE", "1er juin 2027"), Ent("AMOUNT", "20 000 €")],
    ),
    Example(
        "ligue-cancer-innovation-2028", "test",
        "https://www.ligue-cancer.net/appel-a-projets/innovation-2028",
"""\
Ligue contre le Cancer - Appel à projets : Innovation en cancérologie 2028

La Ligue contre le Cancer soutient l'innovation en cancérologie.

Programme de recherche translationnelle et d'innovation thérapeutique.

Date limite : 1er juillet 2028
Ouverture : 1er avril 2028
Montant maximal : 250 000 €
Durée maximale : 36 mois

Éligibilité : Équipes mixtes recherche-industrie.
Institutions : laboratoires, hôpitaux, entreprises biotech.

Thématiques : thérapie cellulaire, CRISPR, RNA, médecine de précision.

Contact : innovation@ligue-cancer.net""",
        {
            "title": "Innovation en cancérologie 2028",
            "organisation": "Ligue contre le Cancer",
            "deadline": "2028-07-01",
            "opening_date": "2028-04-01",
            "amount_max": 250000,
            "currency": "EUR",
            "eligibility": "Équipes mixtes recherche-industrie.",
            "eligible_applicants": ["laboratoires", "hôpitaux", "entreprises biotech"],
            "research_topics": ["thérapie cellulaire", "CRISPR", "RNA", "médecine de précision"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "1er juillet 2028"), Ent("OPENING_DATE", "1er avril 2028"), Ent("AMOUNT", "250 000 €")],
    ),
    Example(
        "ligue-cancer-equipe-2027", "train",
        "https://www.ligue-cancer.net/appel-a-projets/equipes-2027",
"""\
Ligue contre le Cancer - Label d'équipes 2027

La Ligue contre le Cancer accorde des labels aux équipes de recherche d'excellence.

Financement pluriannuel pour les équipes structurées.

Date limite : 1er octobre 2027
Ouverture : 1er juillet 2027
Montant maximal : 300 000 €
Durée maximale : 48 mois

Éligibilité : Équipes de recherche reconnues en cancérologie.
Minimum 5 publications dans les 5 dernières années.

Thématiques : cancérologie, tout domaine.

Contact : equipes@ligue-cancer.net""",
        {
            "title": "Label d'équipes 2027",
            "organisation": "Ligue contre le Cancer",
            "deadline": "2027-10-01",
            "opening_date": "2027-07-01",
            "amount_max": 300000,
            "currency": "EUR",
            "eligibility": "Équipes de recherche reconnues en cancérologie.",
            "eligible_applicants": ["équipes de recherche"],
            "research_topics": ["cancérologie"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "1er octobre 2027"), Ent("OPENING_DATE", "1er juillet 2027"), Ent("AMOUNT", "300 000 €")],
    ),
    Example(
        "fondation-france-2028", "test",
        "https://www.fondationdefrance.org/appels/aide-recherche-2028",
"""\
Fondation de France - Aide à la recherche 2028

La Fondation de France lance l'appel à projets Aide à la recherche 2028.

Programme de soutien à la recherche scientifique dans tous les domaines.

Date limite : 15 juin 2028
Ouverture : 15 janvier 2028
Montant maximal : 100 000 €
Durée maximale : 24 mois

Éligibilité : Jeunes chercheurs, équipes émergentes.
Institutions : universités, laboratoires publics.

Thématiques : sciences, humanités, sciences sociales.

Contact : recherche@fondationdefrance.org""",
        {
            "title": "Aide à la recherche 2028",
            "organisation": "Fondation de France",
            "deadline": "2028-06-15",
            "opening_date": "2028-01-15",
            "amount_max": 100000,
            "currency": "EUR",
            "eligibility": "Jeunes chercheurs, équipes émergentes.",
            "eligible_applicants": ["universités", "laboratoires publics"],
            "research_topics": ["sciences", "humanités", "sciences sociales"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 juin 2028"), Ent("OPENING_DATE", "15 janvier 2028"), Ent("AMOUNT", "100 000 €")],
    ),
    Example(
        "fondation-france-handicap-2027", "train",
        "https://www.fondationdefrance.org/appels/handicap-recherche-2027",
"""\
Fondation de France - Recherche sur le handicap 2027

La Fondation de France finance la recherche sur le handicap.

Programme de recherche sur l'autonomie et l'inclusion des personnes en situation de handicap.

Date limite : 1er novembre 2027
Ouverture : 1er août 2027
Montant maximal : 80 000 €
Durée maximale : 18 mois

Éligibilité : Chercheurs en sciences du handicap, ergothérapeutes, psychologues.
Institutions : centres de recherche, hôpitaux, universités.

Thématiques : handicap moteur, autisme, déficience visuelle, accessibilité.

Contact : handicap@fondationdefrance.org""",
        {
            "title": "Recherche sur le handicap 2027",
            "organisation": "Fondation de France",
            "deadline": "2027-11-01",
            "opening_date": "2027-08-01",
            "amount_max": 80000,
            "currency": "EUR",
            "eligibility": "Chercheurs en sciences du handicap, ergothérapeutes, psychologues.",
            "eligible_applicants": ["centres de recherche", "hôpitaux", "universités"],
            "research_topics": ["handicap moteur", "autisme", "déficience visuelle", "accessibilité"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "1er novembre 2027"), Ent("OPENING_DATE", "1er août 2027"), Ent("AMOUNT", "80 000 €")],
    ),
    Example(
        "fondation-france-education-2028", "test",
        "https://www.fondationdefrance.org/appels/education-recherche-2028",
"""\
Fondation de France - Recherche en éducation 2028

La Fondation de France soutient la recherche en éducation.

Programme sur l'éducation, la formation et l'accompagnement des élèves.

Date limite : 1er septembre 2028
Ouverture : 1er mai 2028
Montant maximal : 60 000 €
Durée maximale : 18 mois

Éligibilité : Chercheurs en sciences de l'éducation, psychologues, enseignants-chercheurs.
Institutions : universités, écoles normales supérieures, INRP.

Thématiques : éducation inclusive, numérique éducatif, décrochage scolaire.

Contact : education@fondationdefrance.org""",
        {
            "title": "Recherche en éducation 2028",
            "organisation": "Fondation de France",
            "deadline": "2028-09-01",
            "opening_date": "2028-05-01",
            "amount_max": 60000,
            "currency": "EUR",
            "eligibility": "Chercheurs en sciences de l'éducation, psychologues, enseignants-chercheurs.",
            "eligible_applicants": ["universités", "écoles normales supérieures", "INRP"],
            "research_topics": ["éducation inclusive", "numérique éducatif", "décrochage scolaire"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "1er septembre 2028"), Ent("OPENING_DATE", "1er mai 2028"), Ent("AMOUNT", "60 000 €")],
    ),
    Example(
        "fondation-france-starter-2027", "train",
        "https://www.fondationdefrance.org/appels/starter-recherche-2027",
"""\
Fondation de France - Starter recherche 2027

La Fondation de France lance le programme Starter recherche pour les projets innovants.

Financement de projets exploratoires et innovants.

Date limite : 15 décembre 2027
Ouverture : 15 septembre 2027
Montant maximal : 30 000 €
Durée maximale : 12 mois

Éligibilité : Jeunes chercheurs, postdocs, équipes émergentes.
Pas de restriction de domaine.

Thématiques : innovation, recherche exploratoire, tout domaine.

Contact : starter@fondationdefrance.org""",
        {
            "title": "Starter recherche 2027",
            "organisation": "Fondation de France",
            "deadline": "2027-12-15",
            "opening_date": "2027-09-15",
            "amount_max": 30000,
            "currency": "EUR",
            "eligibility": "Jeunes chercheurs, postdocs, équipes émergentes.",
            "eligible_applicants": ["jeunes chercheurs", "postdocs", "équipes émergentes"],
            "research_topics": ["innovation", "recherche exploratoire"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 décembre 2027"), Ent("OPENING_DATE", "15 septembre 2027"), Ent("AMOUNT", "30 000 €")],
    ),
    Example(
        "horizon-europe-health-2028", "test",
        "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic/details/HEALTH-2028",
"""\
Horizon Europe - Appel à projets : Santé 2028

La Commission européenne lance l'appel à projets HEALTH-2028 dans le cadre d'Horizon Europe.

Ce programme finance la recherche et l'innovation en santé au niveau européen.

Date limite : 15 mars 2028
Ouverture : 15 novembre 2027
Montant maximal : 5 000 000 €
Durée maximale : 60 mois

Éligibilité : Consortium d'au moins 3 organisations de 3 pays différents de l'UE.
Institutions : universités, hôpitaux, entreprises, organisations de recherche.

Thématiques : maladies rares, santé numérique, pharmacologie, santé publique.

Contact : health@ec.europa.eu""",
        {
            "title": "HEALTH-2028",
            "organisation": "Commission européenne",
            "deadline": "2028-03-15",
            "opening_date": "2027-11-15",
            "amount_max": 5000000,
            "currency": "EUR",
            "eligibility": "Consortium d'au moins 3 organisations de 3 pays différents de l'UE.",
            "eligible_applicants": ["universités", "hôpitaux", "entreprises", "organisations de recherche"],
            "research_topics": ["maladies rares", "santé numérique", "pharmacologie", "santé publique"],
            "geographical_scope": "Europe",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 mars 2028"), Ent("OPENING_DATE", "15 novembre 2027"), Ent("AMOUNT", "5 000 000 €")],
    ),
    Example(
        "horizon-europe-green-2028", "test",
        "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic/details/CLIMATE-2028",
"""\
Horizon Europe - Appel à projets : Climat et énergie 2028

La Commission européenne lance l'appel CLIMATE-2028 dans le cadre d'Horizon Europe.

Recherche et innovation pour la transition verte et la neutralité carbone.

Date limite : 1er juin 2028
Ouverture : 1er février 2028
Montant maximal : 3 000 000 €
Durée maximale : 48 mois

Éligibilité : Consortium multinational d'au moins 3 pays européens.
Institutions : tous types d'organisations de recherche.

Thématiques : décarbonation, énergies renouvelables, adaptation climatique, économie circulaire.

Contact : climate@ec.europa.eu""",
        {
            "title": "CLIMATE-2028",
            "organisation": "Commission européenne",
            "deadline": "2028-06-01",
            "opening_date": "2028-02-01",
            "amount_max": 3000000,
            "currency": "EUR",
            "eligibility": "Consortium multinational d'au moins 3 pays européens.",
            "eligible_applicants": ["universités", "organisations de recherche", "entreprises"],
            "research_topics": ["décarbonation", "énergies renouvelables", "adaptation climatique", "économie circulaire"],
            "geographical_scope": "Europe",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "1er juin 2028"), Ent("OPENING_DATE", "1er février 2028"), Ent("AMOUNT", "3 000 000 €")],
    ),
    Example(
        "horizon-europe-digital-2027", "train",
        "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic/details/DIGITAL-2027",
"""\
Horizon Europe - Appel à projets : Numérique 2027

La Commission européenne lance l'appel DIGITAL-2027.

Recherche et innovation dans les technologies numériques.

Date limite : 15 septembre 2027
Ouverture : 15 mai 2027
Montant maximal : 4 000 000 €
Durée maximale : 48 mois

Éligibilité : Consortium d'au moins 3 organisations de 3 pays européens.
Institutions : tous types.

Thématiques : intelligence artificielle, cybersécurité, cloud computing, jumeaux numériques.

Contact : digital@ec.europa.eu""",
        {
            "title": "DIGITAL-2027",
            "organisation": "Commission européenne",
            "deadline": "2027-09-15",
            "opening_date": "2027-05-15",
            "amount_max": 4000000,
            "currency": "EUR",
            "eligibility": "Consortium d'au moins 3 organisations de 3 pays européens.",
            "eligible_applicants": ["universités", "entreprises", "organisations de recherche"],
            "research_topics": ["intelligence artificielle", "cybersécurité", "cloud computing", "jumeaux numériques"],
            "geographical_scope": "Europe",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 septembre 2027"), Ent("OPENING_DATE", "15 mai 2027"), Ent("AMOUNT", "4 000 000 €")],
    ),
    Example(
        "horizon-europe-food-2028", "train",
        "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic/details/FOOD-2028",
"""\
Horizon Europe - Appel à projets : Alimentation 2028

La Commission européenne lance l'appel FOOD-2028.

Recherche sur la sécurité alimentaire et l'alimentation durable.

Date limite : 1er octobre 2028
Ouverture : 1er juin 2028
Montant maximal : 2 500 000 €
Durée maximale : 48 mois

Éligibilité : Consortium multinational, 3 pays européens minimum.
Institutions : universités, entreprises agroalimentaires, centres de recherche.

Thématiques : agriculture durable, alimentation saine, réduction du gaspillage, protéines alternatives.

Contact : food@ec.europa.eu""",
        {
            "title": "FOOD-2028",
            "organisation": "Commission européenne",
            "deadline": "2028-10-01",
            "opening_date": "2028-06-01",
            "amount_max": 2500000,
            "currency": "EUR",
            "eligibility": "Consortium multinational, 3 pays européens minimum.",
            "eligible_applicants": ["universités", "entreprises agroalimentaires", "centres de recherche"],
            "research_topics": ["agriculture durable", "alimentation saine", "réduction du gaspillage", "protéines alternatives"],
            "geographical_scope": "Europe",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "1er octobre 2028"), Ent("OPENING_DATE", "1er juin 2028"), Ent("AMOUNT", "2 500 000 €")],
    ),
    Example(
        "anr-demesnil-2028", "train",
        "https://anr.fr/fr/les-appels-a-projets/demesnil-2028.html",
"""\
Appel à projets : AAP Démesnil 2028

L'ANR lance l'AAP Démesnil pour les projets exploratoires.

Programme de financement de courte durée pour des idées innovantes.

Date limite : 10 janvier 2028
Ouverture : 10 octobre 2027
Montant maximal : 50 000 €
Durée maximale : 18 mois

Éligibilité : Jeunes chercheurs, équipes émergentes.
Institutions : universités, laboratoires publics.

Thématiques : recherche exploratoire, interdisciplinaire.

Contact : demesnil@anr.fr""",
        {
            "title": "AAP Démesnil 2028",
            "organisation": "ANR",
            "deadline": "2028-01-10",
            "opening_date": "2027-10-10",
            "amount_max": 50000,
            "currency": "EUR",
            "eligibility": "Jeunes chercheurs, équipes émergentes.",
            "eligible_applicants": ["universités", "laboratoires publics"],
            "research_topics": ["recherche exploratoire", "interdisciplinaire"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "10 janvier 2028"), Ent("OPENING_DATE", "10 octobre 2027"), Ent("AMOUNT", "50 000 €")],
    ),
    Example(
        "inca-these-2027", "train",
        "https://www.e-cancer.fr/Institut-national-du-cancer/Appels-a-projets/bourses-these-2027",
"""\
INCa - Bourses de thèse 2027

L'INCa offre des bourses de thèse en cancérologie.

Financement de thèses pour les doctorants en recherche cancérologique.

Date limite : 15 octobre 2027
Ouverture : 15 juillet 2027
Montant : 22 000 € par an pendant 3 ans
Durée : 36 mois

Éligibilité : Étudiants inscrits en thèse, en première année.
Sujet en cancérologie.

Thématiques : cancérologie, recherche biomédicale.

Contact : these@e-cancer.fr""",
        {
            "title": "Bourses de thèse 2027",
            "organisation": "INCa",
            "deadline": "2027-10-15",
            "opening_date": "2027-07-15",
            "amount_max": 66000,
            "currency": "EUR",
            "eligibility": "Étudiants inscrits en thèse, en première année.",
            "eligible_applicants": ["étudiants en thèse"],
            "research_topics": ["cancérologie", "recherche biomédicale"],
            "geographical_scope": "France",
            "funding_type": "bourse",
        },
        [Ent("DEADLINE", "15 octobre 2027"), Ent("OPENING_DATE", "15 juillet 2027"), Ent("AMOUNT", "22 000 €")],
    ),
    Example(
        "ars-covid-2028", "test",
        "https://www.ars.sante.fr/aaps/covid-2028",
"""\
ARS Île-de-France - Appel à projets : COVID-19 et séquelles 2028

L'ARS IDF lance un appel sur les séquelles du COVID-19.

Recherche sur le COVID long et les impacts à long terme.

Date limite : 30 avril 2028
Ouverture : 30 janvier 2028
Montant maximal : 90 000 €
Durée maximale : 18 mois

Éligibilité : Pneumologues, cardiologues, neurologues.
Institutions : CHU, hôpitaux, universités.

Thématiques : COVID long, fatigue chronique, atteintes pulmonaires, neurologiques.

Contact : covid@ars-idf.fr""",
        {
            "title": "COVID-19 et séquelles 2028",
            "organisation": "ARS Île-de-France",
            "deadline": "2028-04-30",
            "opening_date": "2028-01-30",
            "amount_max": 90000,
            "currency": "EUR",
            "eligibility": "Pneumologues, cardiologues, neurologues.",
            "eligible_applicants": ["CHU", "hôpitaux", "universités"],
            "research_topics": ["COVID long", "fatigue chronique", "atteintes pulmonaires", "neurologiques"],
            "geographical_scope": "Île-de-France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "30 avril 2028"), Ent("OPENING_DATE", "30 janvier 2028"), Ent("AMOUNT", "90 000 €")],
    ),
    Example(
        "fondation-arc-prostate-2027", "train",
        "https://www.fondation-arc.org/appel-a-projets/cancer-prostate-2027",
"""\
Fondation ARC - Appel à projets : Cancer de la prostate 2027

La Fondation ARC finance la recherche sur le cancer de la prostate.

Programme de recherche fondamentale et translationnelle.

Date limite : 1er décembre 2027
Ouverture : 1er septembre 2027
Montant maximal : 200 000 €
Durée maximale : 36 mois

Éligibilité : Urologues, oncologues, biologistes.
Institutions : centres de recherche, universités, hôpitaux.

Thématiques : cancer de la prostate, dépistage, chirurgie, hormonothérapie.

Contact : prostate@fondation-arc.org""",
        {
            "title": "Cancer de la prostate 2027",
            "organisation": "Fondation ARC",
            "deadline": "2027-12-01",
            "opening_date": "2027-09-01",
            "amount_max": 200000,
            "currency": "EUR",
            "eligibility": "Urologues, oncologues, biologistes.",
            "eligible_applicants": ["centres de recherche", "universités", "hôpitaux"],
            "research_topics": ["cancer de la prostate", "dépistage", "chirurgie", "hormonothérapie"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "1er décembre 2027"), Ent("OPENING_DATE", "1er septembre 2027"), Ent("AMOUNT", "200 000 €")],
    ),
    Example(
        "ligue-cancer-env-2028", "test",
        "https://www.ligue-cancer.net/appel-a-projets/environnement-cancer-2028",
"""\
Ligue contre le Cancer - Appel à projets : Environnement et cancer 2028

La Ligue contre le Cancer étudie les liens entre environnement et cancer.

Programme de recherche sur les facteurs environnementaux du cancer.

Date limite : 15 août 2028
Ouverture : 15 mai 2028
Montant maximal : 150 000 €
Durée maximale : 36 mois

Éligibilité : Épidémiologistes, toxicologues, environnementalistes.
Institutions : centres de recherche, universités, instituts.

Thématiques : perturbateurs endocriniens, pollution, cancer environnemental.

Contact : environnement@ligue-cancer.net""",
        {
            "title": "Environnement et cancer 2028",
            "organisation": "Ligue contre le Cancer",
            "deadline": "2028-08-15",
            "opening_date": "2028-05-15",
            "amount_max": 150000,
            "currency": "EUR",
            "eligibility": "Épidémiologistes, toxicologues, environnementalistes.",
            "eligible_applicants": ["centres de recherche", "universités", "instituts"],
            "research_topics": ["perturbateurs endocriniens", "pollution", "cancer environnemental"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 août 2028"), Ent("OPENING_DATE", "15 mai 2028"), Ent("AMOUNT", "150 000 €")],
    ),
    Example(
        "frm-immuno-2028", "train",
        "https://www.frm.org/appels/immunologie-2028",
"""\
Fondation pour la Recherche Médicale - Appel à projets : Immunologie 2028

La FRM lance l'appel à projets Immunologie 2028.

Recherche sur le système immunitaire et les maladies auto-immunes.

Date limite : 15 novembre 2028
Ouverture : 15 août 2028
Montant maximal : 180 000 €
Durée maximale : 36 mois

Éligibilité : Immunologistes, rhumatologues, endocrinologues.
Institutions : universités, INSERM, hôpitaux.

Thématiques : auto-immunité, transplantation, vaccins, inflammation.

Contact : immunologie@frm.org""",
        {
            "title": "Immunologie 2028",
            "organisation": "FRM",
            "deadline": "2028-11-15",
            "opening_date": "2028-08-15",
            "amount_max": 180000,
            "currency": "EUR",
            "eligibility": "Immunologistes, rhumatologues, endocrinologues.",
            "eligible_applicants": ["universités", "INSERM", "hôpitaux"],
            "research_topics": ["auto-immunité", "transplantation", "vaccins", "inflammation"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 novembre 2028"), Ent("OPENING_DATE", "15 août 2028"), Ent("AMOUNT", "180 000 €")],
    ),
    Example(
        "fondation-france-aging-2027", "test",
        "https://www.fondationdefrance.org/appels/vieillissement-2027",
"""\
Fondation de France - Recherche sur le vieillissement 2027

La Fondation de France soutient la recherche sur le vieillissement.

Programme sur le vieillissement sain et les maladies neurodégénératives.

Date limite : 15 octobre 2027
Ouverture : 15 juillet 2027
Montant maximal : 70 000 €
Durée maximale : 18 mois

Éligibilité : Gérontologues, neurologues, psychologues.
Institutions : centres de recherche, hôpitaux, EHPAD.

Thématiques : Alzheimer, Parkinson, dépendance, maintien de l'autonomie.

Contact : vieillissement@fondationdefrance.org""",
        {
            "title": "Recherche sur le vieillissement 2027",
            "organisation": "Fondation de France",
            "deadline": "2027-10-15",
            "opening_date": "2027-07-15",
            "amount_max": 70000,
            "currency": "EUR",
            "eligibility": "Gérontologues, neurologues, psychologues.",
            "eligible_applicants": ["centres de recherche", "hôpitaux", "EHPAD"],
            "research_topics": ["Alzheimer", "Parkinson", "dépendance", "maintien de l'autonomie"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 octobre 2027"), Ent("OPENING_DATE", "15 juillet 2027"), Ent("AMOUNT", "70 000 €")],
    ),
    Example(
        "horizon-europe-marie-curie-2028", "test",
        "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic/details/MSCA-2028",
"""\
Horizon Europe - MSCA Postdoctoral Fellowships 2028

La Commission européenne lance les bourses MSCA Postdoctoral Fellowships 2028.

Mobilité et formation des chercheurs postdoctoraux au niveau européen.

Date limite : 15 septembre 2028
Ouverture : 15 avril 2028
Montant maximal : 250 000 €
Durée maximale : 24 mois

Éligibilité : Docteurs ayant soutenu leur thèse depuis moins de 8 ans.
Mobilité internationale requise.

Thématiques : recherche interdisciplinaire, innovation, transfert de compétences.

Contact : msca@ec.europa.eu""",
        {
            "title": "MSCA Postdoctoral Fellowships 2028",
            "organisation": "Commission européenne",
            "deadline": "2028-09-15",
            "opening_date": "2028-04-15",
            "amount_max": 250000,
            "currency": "EUR",
            "eligibility": "Docteurs ayant soutenu leur thèse depuis moins de 8 ans.",
            "eligible_applicants": ["docteurs"],
            "research_topics": ["recherche interdisciplinaire", "innovation", "transfert de compétences"],
            "geographical_scope": "Europe",
            "funding_type": "bourse",
        },
        [Ent("DEADLINE", "15 septembre 2028"), Ent("OPENING_DATE", "15 avril 2028"), Ent("AMOUNT", "250 000 €")],
    ),
    Example(
        "anr-ethique-2028", "train",
        "https://anr.fr/fr/les-appels-a-projets/ethique-recherche-2028.html",
"""\
Appel à projets : AAP Éthique de la recherche 2028

L'ANR lance l'AAP Éthique de la recherche 2028.

Financement de projets sur l'éthique de la recherche scientifique.

Date limite : 1er février 2028
Ouverture : 1er novembre 2027
Montant maximal : 80 000 €
Durée maximale : 24 mois

Éligibilité : Philosophes, juristes, éthiciens.
Institutions : universités, comités d'éthique, centres de recherche.

Thématiques : IA éthique, bioéthique, éthique de la recherche, data éthique.

Contact : ethique@anr.fr""",
        {
            "title": "AAP Éthique de la recherche 2028",
            "organisation": "ANR",
            "deadline": "2028-02-01",
            "opening_date": "2027-11-01",
            "amount_max": 80000,
            "currency": "EUR",
            "eligibility": "Philosophes, juristes, éthiciens.",
            "eligible_applicants": ["universités", "comités d'éthique", "centres de recherche"],
            "research_topics": ["IA éthique", "bioéthique", "éthique de la recherche", "data éthique"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "1er février 2028"), Ent("OPENING_DATE", "1er novembre 2027"), Ent("AMOUNT", "80 000 €")],
    ),
    Example(
        "ligue-cancer-epigenetique-2028", "train",
        "https://www.ligue-cancer.net/appel-a-projets/epigenetique-2028",
"""\
Ligue contre le Cancer - Appel à projets : Épigénétique et cancer 2028

La Ligue contre le Cancer finance la recherche en épigénétique du cancer.

Programme sur les mécanismes épigénétiques dans le développement tumoral.

Date limite : 1er juin 2028
Ouverture : 1er mars 2028
Montant maximal : 200 000 €
Durée maximale : 36 mois

Éligibilité : Épigénéticiens, biologistes moléculaires.
Institutions : centres de recherche, universités.

Thématiques : épigénétique, méthylation, microARN, chromatine.

Contact : epigenetique@ligue-cancer.net""",
        {
            "title": "Épigénétique et cancer 2028",
            "organisation": "Ligue contre le Cancer",
            "deadline": "2028-06-01",
            "opening_date": "2028-03-01",
            "amount_max": 200000,
            "currency": "EUR",
            "eligibility": "Épigénéticiens, biologistes moléculaires.",
            "eligible_applicants": ["centres de recherche", "universités"],
            "research_topics": ["épigénétique", "méthylation", "microARN", "chromatine"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "1er juin 2028"), Ent("OPENING_DATE", "1er mars 2028"), Ent("AMOUNT", "200 000 €")],
    ),
    Example(
        "cancer-2027", "test",
        "https://anr.fr/AAP/cancer-2027",
"""\
Appel à projets : Programme Cancer 2027

Date limite : 15 octobre 2026
Montant maximum : 500 000 €

Cet appel est publié par l'ANR.
Candidats éligibles : Les universités, les laboratoires et les CHU peuvent candidater.""",
        {
            "title": "Programme Cancer 2027",
            "deadline": "2026-10-15",
            "amount_max": 500000,
            "currency": "EUR",
            "organisation": "ANR",
            "research_topics": ["cancer"],
            "eligibility": "Les universités, les laboratoires et les CHU peuvent candidater.",
        },
        [Ent("DEADLINE", "15 octobre 2026"), Ent("AMOUNT", "500 000 €")],
    ),
    Example(
        "ia-sante-2028", "test",
        "https://anr.fr/AAP/ia-sante-2028",
"""\
Appel à projets : IA en santé 2028

Date limite : 03 mai 2028
Montant maximum : 1 200 000 €""",
        {
            "title": "IA en santé 2028",
            "deadline": "2028-05-03",
            "amount_max": 1200000,
            "currency": "EUR",
        },
        [Ent("DEADLINE", "03 mai 2028"), Ent("AMOUNT", "1 200 000 €")],
    ),
    Example(
        "biotherapies-2026", "train",
        "https://anr.fr/AAP/biotherapies-2026",
"""\
Appel à projets : Biothérapies 2026

Date limite : 30 novembre 2026
Montant maximum : 250 000 €""",
        {
            "title": "Biothérapies 2026",
            "deadline": "2026-11-30",
            "amount_max": 250000,
            "currency": "EUR",
        },
        [Ent("DEADLINE", "30 novembre 2026"), Ent("AMOUNT", "250 000 €")],
    ),
    Example(  # NEW
        "inserm-appel-2028", "test",
        "https://www.inserm.fr/appels-a-projets/mitochondrie-2028",
"""\
Inserm - Appel à projets : Mitochondries et métabolisme 2028

L'Institut national de la santé et de la recherche médicale (Inserm) lance l'appel à projets Mitochondries et métabolisme 2028.

Ce programme finance la recherche fondamentale sur la biologie des mitochondries et les maladies métaboliques.

Date limite : 30 juin 2028
Ouverture : 1er mars 2028
Montant maximal : 400 000 €
Durée maximale : 36 mois

Éligibilité : Équipes de recherche en biologie cellulaire, métabolisme et génétique.
Institutions : unités Inserm, universités, instituts hospitalo-universitaires.

Thématiques : mitochondries, métabolisme énergétique, maladies métaboliques, vieillissement cellulaire.

Contact : mitochondrie@inserm.fr""",
        {
            "title": "Mitochondries et métabolisme 2028",
            "organisation": "Inserm",
            "deadline": "2028-06-30",
            "opening_date": "2028-03-01",
            "amount_max": 400000,
            "currency": "EUR",
            "eligibility": "Équipes de recherche en biologie cellulaire, métabolisme et génétique.",
            "eligible_applicants": ["unités Inserm", "universités", "instituts hospitalo-universitaires"],
            "research_topics": ["mitochondries", "métabolisme énergétique", "maladies métaboliques", "vieillissement cellulaire"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "30 juin 2028"), Ent("OPENING_DATE", "1er mars 2028"), Ent("AMOUNT", "400 000 €")],
    ),
    Example(  # NEW
        "inserm-horizon-2028", "test",
        "https://www.inserm.fr/appels-a-projets/genetique-humaine-2028",
"""\
Inserm - Appel à projets : Génétique humaine 2028

L'Inserm soutient la recherche en génétique humaine et génomique.

Ce programme finance des projets sur les maladies génétiques rares et la médecine génomique.

Date limite : 15 septembre 2028
Ouverture : 15 avril 2028
Montant maximal : 350 000 €
Durée maximale : 36 mois

Éligibilité : Généticiens, génomiciens, bioinformaticiens.
Institutions : unités Inserm, CHU, plateformes de génomique.

Thématiques : maladies rares, séquençage, variabilité génétique, pharmacogénomique.

Contact : genetique@inserm.fr""",
        {
            "title": "Génétique humaine 2028",
            "organisation": "Inserm",
            "deadline": "2028-09-15",
            "opening_date": "2028-04-15",
            "amount_max": 350000,
            "currency": "EUR",
            "eligibility": "Généticiens, génomiciens, bioinformaticiens.",
            "eligible_applicants": ["unités Inserm", "CHU", "plateformes de génomique"],
            "research_topics": ["maladies rares", "séquençage", "variabilité génétique", "pharmacogénomique"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 septembre 2028"), Ent("OPENING_DATE", "15 avril 2028"), Ent("AMOUNT", "350 000 €")],
    ),
    Example(  # NEW
        "cnrs-soleil-2028", "test",
        "https://www.cnrs.fr/appels-a-projets/soleil-2028",
"""\
CNRS - Appel à projets : Sciences de l'Univers 2028

Le CNRS lance l'appel à projets Sciences de l'Univers 2028.

Ce programme finance la recherche en astrophysique, planétologie et cosmologie.

Date limite : 15 avril 2028
Ouverture : 15 janvier 2028
Montant maximal : 300 000 €
Durée maximale : 48 mois

Éligibilité : Chercheurs et enseignants-chercheurs des unités CNRS.
Institutions : instituts CNRS, universités, observatoires.

Thématiques : astrophysique, cosmologie, exoplanètes, matière noire, instruments spatiaux.

Contact : univers@cnrs.fr""",
        {
            "title": "Sciences de l'Univers 2028",
            "organisation": "CNRS",
            "deadline": "2028-04-15",
            "opening_date": "2028-01-15",
            "amount_max": 300000,
            "currency": "EUR",
            "eligibility": "Chercheurs et enseignants-chercheurs des unités CNRS.",
            "eligible_applicants": ["instituts CNRS", "universités", "observatoires"],
            "research_topics": ["astrophysique", "cosmologie", "exoplanètes", "matière noire", "instruments spatiaux"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 avril 2028"), Ent("OPENING_DATE", "15 janvier 2028"), Ent("AMOUNT", "300 000 €")],
    ),
    Example(  # NEW
        "cnrs-occan-2027", "train",
        "https://www.cnrs.fr/appels-a-projets/pole-2027",
"""\
CNRS - Appel à projets : Écologie des milieux extrêmes 2027

Le CNRS soutient la recherche sur les milieux extrêmes (pôles, abysses, déserts).

Ce programme finance des expéditions et projets de recherche en environnement extrême.

Date limite : 10 novembre 2027
Ouverture : 10 juillet 2027
Montant maximal : 250 000 €
Durée maximale : 36 mois

Éligibilité : Écologues, océanographes, glaciologues.
Institutions : instituts CNRS, universités, IPEV.

Thématiques : océanographie, glaciologie, climat polaire, biodiversité abyssale, expéditions.

Contact : externe@cnrs.fr""",
        {
            "title": "Écologie des milieux extrêmes 2027",
            "organisation": "CNRS",
            "deadline": "2027-11-10",
            "opening_date": "2027-07-10",
            "amount_max": 250000,
            "currency": "EUR",
            "eligibility": "Écologues, océanographes, glaciologues.",
            "eligible_applicants": ["instituts CNRS", "universités", "IPEV"],
            "research_topics": ["océanographie", "glaciologie", "climat polaire", "biodiversité abyssale", "expéditions"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "10 novembre 2027"), Ent("OPENING_DATE", "10 juillet 2027"), Ent("AMOUNT", "250 000 €")],
    ),
    Example(  # NEW
        "chu-paris-2028", "test",
        "https://www.aphp.fr/appels-a-projets/translation-2028",
"""\
AP-HP - Appel à projets : Recherche translationnelle clinique 2028

L'Assistance Publique - Hôpitaux de Paris lance l'appel à projets Recherche translationnelle clinique 2028.

Ce programme finance des projets de recherche clinique innovants menés dans les hôpitaux de l'AP-HP.

Date limite : 30 septembre 2028
Ouverture : 1er juin 2028
Montant maximal : 250 000 €
Durée maximale : 36 mois

Éligibilité : Médecins hospitalo-universitaires, pharmaciens, chercheurs cliniciens.
Institutions : hôpitaux AP-HP, unités de recherche clinique, universités.

Thématiques : essais cliniques, biomarqueurs, imagerie médicale, thérapeutiques innovantes.

Contact : translation@aphp.fr""",
        {
            "title": "Recherche translationnelle clinique 2028",
            "organisation": "AP-HP",
            "deadline": "2028-09-30",
            "opening_date": "2028-06-01",
            "amount_max": 250000,
            "currency": "EUR",
            "eligibility": "Médecins hospitalo-universitaires, pharmaciens, chercheurs cliniciens.",
            "eligible_applicants": ["hôpitaux AP-HP", "unités de recherche clinique", "universités"],
            "research_topics": ["essais cliniques", "biomarqueurs", "imagerie médicale", "thérapeutiques innovantes"],
            "geographical_scope": "Île-de-France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "30 septembre 2028"), Ent("OPENING_DATE", "1er juin 2028"), Ent("AMOUNT", "250 000 €")],
    ),
    Example(  # NEW
        "chu-lyon-2027", "train",
        "https://www.chu-lyon.fr/appels-a-projets/recherche-soins-2027",
"""\
CHU de Lyon - Appel à projets : Recherche en soins 2027

Les Hospices Civils de Lyon lancent l'appel à projets Recherche en soins 2027.

Ce programme finance la recherche paramédicale et en sciences infirmières menée au sein des établissements.

Date limite : 15 décembre 2027
Ouverture : 1er octobre 2027
Montant maximal : 40 000 €
Durée maximale : 24 mois

Éligibilité : Infirmiers, kinésithérapeutes, orthophonistes, sages-femmes.
Institutions : établissements de santé, instituts de formation paramédicale.

Thématiques : organisation des soins, éducation thérapeutique, qualité de vie des soignants.

Contact : soins@chu-lyon.fr""",
        {
            "title": "Recherche en soins 2027",
            "organisation": "CHU de Lyon",
            "deadline": "2027-12-15",
            "opening_date": "2027-10-01",
            "amount_max": 40000,
            "currency": "EUR",
            "eligibility": "Infirmiers, kinésithérapeutes, orthophonistes, sages-femmes.",
            "eligible_applicants": ["établissements de santé", "instituts de formation paramédicale"],
            "research_topics": ["organisation des soins", "éducation thérapeutique", "qualité de vie des soignants"],
            "geographical_scope": "Auvergne-Rhône-Alpes",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 décembre 2027"), Ent("OPENING_DATE", "1er octobre 2027"), Ent("AMOUNT", "40 000 €")],
    ),
    Example(  # NEW
        "ars-hdf-2028", "test",
        "https://www.ars-hauts-de-france.sante.fr/aaps/vulnerables-2028",
"""\
ARS Hauts-de-France - Appel à projets : Personnes vulnérables 2028

L'ARS Hauts-de-France lance l'appel à projets Personnes vulnérables 2028.

Ce programme finance des actions de recherche et d'innovation sociale pour les publics vulnérables.

Date limite : 30 mars 2028
Ouverture : 1er décembre 2027
Montant maximal : 30 000 €
Durée maximale : 12 mois

Éligibilité : Structures sanitaires, médico-sociales et sociales.
Institutions : associations, hôpitaux, établissements médico-sociaux.

Thématiques : précarité, personnes âgées, handicap, sans-abrisme.

Contact : vulnerables@ars-hdf.fr""",
        {
            "title": "Personnes vulnérables 2028",
            "organisation": "ARS Hauts-de-France",
            "deadline": "2028-03-30",
            "opening_date": "2027-12-01",
            "amount_max": 30000,
            "currency": "EUR",
            "eligibility": "Structures sanitaires, médico-sociales et sociales.",
            "eligible_applicants": ["associations", "hôpitaux", "établissements médico-sociaux"],
            "research_topics": ["précarité", "personnes âgées", "handicap", "sans-abrisme"],
            "geographical_scope": "Hauts-de-France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "30 mars 2028"), Ent("OPENING_DATE", "1er décembre 2027"), Ent("AMOUNT", "30 000 €")],
    ),
    Example(  # NEW
        "anr-jeune-chercheur-2028", "train",
        "https://anr.fr/fr/les-appels-a-projets/jcjc-2028.html",
"""\
Appel à projets : AAP Jeunes chercheurs 2028

L'Agence nationale de la recherche lance l'appel à projets dédié aux jeunes chercheurs et jeunes chercheuses (JCJC).

Ce programme finance le premier projet de recherche de chercheurs en début de carrière.

Date limite : 5 octobre 2028
Ouverture : 5 juin 2028
Montant maximal : 150 000 €
Durée maximale : 24 mois

Éligibilité : Chercheurs ayant obtenu leur doctorat il y a moins de 5 ans.
Chargés de recherche, maîtres de conférences.
Toutes disciplines, hors projets déjà financés.

Thématiques : toutes disciplines scientifiques.

Contact : jcjc@anr.fr""",
        {
            "title": "AAP Jeunes chercheurs 2028",
            "organisation": "ANR",
            "deadline": "2028-10-05",
            "opening_date": "2028-06-05",
            "amount_max": 150000,
            "currency": "EUR",
            "eligibility": "Chercheurs ayant obtenu leur doctorat il y a moins de 5 ans.",
            "eligible_applicants": ["chargés de recherche", "maîtres de conférences"],
            "research_topics": ["toutes disciplines scientifiques"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "5 octobre 2028"), Ent("OPENING_DATE", "5 juin 2028"), Ent("AMOUNT", "150 000 €")],
    ),
    Example(  # NEW
        "ars-ara-diabete-2028", "train",
        "https://www.ars-auvergne-rhone-alpes.sante.fr/aaps/diabete-2028",
"""\
ARS Auvergne-Rhône-Alpes - Appel à projets : Diabète 2028

L'ARS AURA lance l'appel à projets Diabète 2028 pour la recherche régionale.

Ce programme finance des projets de recherche sur le parcours de soins du patient diabétique.

Date limite : 15 mai 2028
Ouverture : 15 février 2028
Montant maximal : 45 000 €
Durée maximale : 24 mois

Éligibilité : Chercheurs en santé, soignants, associations de patients.
Institutions : CHU, universités, maisons de santé pluriprofessionnelles.

Thématiques : diabète de type 1 et 2, éducation thérapeutique, télémédecine, prévention.

Contact : diabete@ars-ara.fr""",
        {
            "title": "Diabète 2028",
            "organisation": "ARS Auvergne-Rhône-Alpes",
            "deadline": "2028-05-15",
            "opening_date": "2028-02-15",
            "amount_max": 45000,
            "currency": "EUR",
            "eligibility": "Chercheurs en santé, soignants, associations de patients.",
            "eligible_applicants": ["CHU", "universités", "maisons de santé pluriprofessionnelles"],
            "research_topics": ["diabète de type 1 et 2", "éducation thérapeutique", "télémédecine", "prévention"],
            "geographical_scope": "Auvergne-Rhône-Alpes",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 mai 2028"), Ent("OPENING_DATE", "15 février 2028"), Ent("AMOUNT", "45 000 €")],
    ),
    Example(  # NEW
        "inserm-jeune-2027", "train",
        "https://www.inserm.fr/appels-a-projets/atip-avenir-2027",
"""\
Inserm - Appel à projets : ATIP-Avenir 2027

L'Inserm lance l'appel à projets ATIP-Avenir pour les jeunes équipes de recherche.

Ce programme permet la création de nouvelles équipes de recherche indépendantes.

Date limite : 1er décembre 2027
Ouverture : 1er septembre 2027
Montant maximal : 100 000 €
Durée maximale : 36 mois

Éligibilité : Chercheurs recrutés récemment, créant une nouvelle équipe dans une unité Inserm ou associée.
Poste permanent ou équivalent requis.

Thématiques : toutes thématiques biomédicales.

Contact : atip-avenir@inserm.fr""",
        {
            "title": "ATIP-Avenir 2027",
            "organisation": "Inserm",
            "deadline": "2027-12-01",
            "opening_date": "2027-09-01",
            "amount_max": 100000,
            "currency": "EUR",
            "eligibility": "Chercheurs recrutés récemment, créant une nouvelle équipe dans une unité Inserm ou associée.",
            "eligible_applicants": ["chercheurs recrutés récemment"],
            "research_topics": ["toutes thématiques biomédicales"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "1er décembre 2027"), Ent("OPENING_DATE", "1er septembre 2027"), Ent("AMOUNT", "100 000 €")],
    ),
    Example(  # NEW
        "ligue-cancer-colorectal-2028", "test",
        "https://www.ligue-cancer.net/appel-a-projets/cancer-colorectal-2028",
"""\
Ligue contre le Cancer - Appel à projets : Cancer colorectal 2028

La Ligue contre le Cancer lance l'appel à projets Cancer colorectal 2028.

Ce programme soutient la recherche sur le dépistage et le traitement du cancer colorectal.

Date limite : 30 juin 2028
Ouverture : 1er avril 2028
Montant maximal : 160 000 €
Durée maximale : 36 mois

Éligibilité : Gastro-entérologues, oncologues, épidémiologistes.
Institutions : centres de recherche, hôpitaux, universités.

Thématiques : cancer colorectal, dépistage, coloscopie, microbiote, chirurgie mini-invasive.

Contact : colorectal@ligue-cancer.net""",
        {
            "title": "Cancer colorectal 2028",
            "organisation": "Ligue contre le Cancer",
            "deadline": "2028-06-30",
            "opening_date": "2028-04-01",
            "amount_max": 160000,
            "currency": "EUR",
            "eligibility": "Gastro-entérologues, oncologues, épidémiologistes.",
            "eligible_applicants": ["centres de recherche", "hôpitaux", "universités"],
            "research_topics": ["cancer colorectal", "dépistage", "coloscopie", "microbiote", "chirurgie mini-invasive"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "30 juin 2028"), Ent("OPENING_DATE", "1er avril 2028"), Ent("AMOUNT", "160 000 €")],
    ),
    Example(  # NEW
        "fondation-arc-hemato-2028", "train",
        "https://www.fondation-arc.org/appel-a-projets/hematologie-2028",
"""\
Fondation ARC - Appel à projets : Hématologie maligne 2028

La Fondation ARC finance la recherche en hématologie maligne.

Ce programme porte sur les leucémies, lymphomes et myélomes.

Date limite : 20 mai 2028
Ouverture : 20 février 2028
Montant maximal : 220 000 €
Durée maximale : 36 mois

Éligibilité : Hématologues, oncologues, généticiens.
Institutions : centres de recherche, hôpitaux, universités.

Thématiques : leucémies, myélomes, CAR-T cells, thérapies ciblées, résistance.

Contact : hemato@fondation-arc.org""",
        {
            "title": "Hématologie maligne 2028",
            "organisation": "Fondation ARC",
            "deadline": "2028-05-20",
            "opening_date": "2028-02-20",
            "amount_max": 220000,
            "currency": "EUR",
            "eligibility": "Hématologues, oncologues, généticiens.",
            "eligible_applicants": ["centres de recherche", "hôpitaux", "universités"],
            "research_topics": ["leucémies", "myélomes", "CAR-T cells", "thérapies ciblées", "résistance"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "20 mai 2028"), Ent("OPENING_DATE", "20 février 2028"), Ent("AMOUNT", "220 000 €")],
    ),
    Example(  # NEW
        "frm-cardio-2028", "test",
        "https://www.frm.org/appels/cardiovasculaire-2028",
"""\
Fondation pour la Recherche Médicale - Appel à projets : Maladies cardiovasculaires 2028

La FRM lance l'appel à projets Maladies cardiovasculaires 2028.

Ce programme finance la recherche sur les maladies du cœur et des vaisseaux.

Date limite : 15 octobre 2028
Ouverture : 15 juin 2028
Montant maximal : 220 000 €
Durée maximale : 36 mois

Éligibilité : Cardiologues, chercheurs en biologie cardiovasculaire.
Institutions : universités, Inserm, INRAE, hôpitaux.

Thématiques : insuffisance cardiaque, athérosclérose, arythmies, valvulopathies, hypertension.

Contact : cardio@frm.org""",
        {
            "title": "Maladies cardiovasculaires 2028",
            "organisation": "FRM",
            "deadline": "2028-10-15",
            "opening_date": "2028-06-15",
            "amount_max": 220000,
            "currency": "EUR",
            "eligibility": "Cardiologues, chercheurs en biologie cardiovasculaire.",
            "eligible_applicants": ["universités", "Inserm", "INRAE", "hôpitaux"],
            "research_topics": ["insuffisance cardiaque", "athérosclérose", "arythmies", "valvulopathies", "hypertension"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 octobre 2028"), Ent("OPENING_DATE", "15 juin 2028"), Ent("AMOUNT", "220 000 €")],
    ),
    Example(  # NEW
        "fondation-france-migrations-2027", "train",
        "https://www.fondationdefrance.org/appels/migrations-2027",
"""\
Fondation de France - Recherche sur les migrations 2027

La Fondation de France lance l'appel à projets Recherche sur les migrations 2027.

Ce programme finance la recherche en sciences humaines et sociales sur les migrations et l'intégration.

Date limite : 1er septembre 2027
Ouverture : 1er mai 2027
Montant maximal : 50 000 €
Durée maximale : 18 mois

Éligibilité : Sociologues, géographes, historiens, démographes.
Institutions : universités, CNRS, centres de recherche en sciences humaines.

Thématiques : migrations, intégration, politiques migratoires, exil, xénophobie.

Contact : migrations@fondationdefrance.org""",
        {
            "title": "Recherche sur les migrations 2027",
            "organisation": "Fondation de France",
            "deadline": "2027-09-01",
            "opening_date": "2027-05-01",
            "amount_max": 50000,
            "currency": "EUR",
            "eligibility": "Sociologues, géographes, historiens, démographes.",
            "eligible_applicants": ["universités", "CNRS", "centres de recherche en sciences humaines"],
            "research_topics": ["migrations", "intégration", "politiques migratoires", "exil", "xénophobie"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "1er septembre 2027"), Ent("OPENING_DATE", "1er mai 2027"), Ent("AMOUNT", "50 000 €")],
    ),
    Example(  # NEW
        "anr-villes-2028", "test",
        "https://anr.fr/fr/les-appels-a-projets/villes-durables-2028.html",
"""\
Appel à projets : AAP Villes et territoires durables 2028

L'ANR lance l'appel à projets Villes et territoires durables 2028.

Ce programme finance la recherche sur la ville durable, les mobilités et le cadre de vie.

Date limite : 15 février 2028
Ouverture : 15 octobre 2027
Montant maximal : 280 000 €
Durée maximale : 36 mois

Éligibilité : Urbanistes, architectes, géographes, ingénieurs.
Institutions : universités, grandes écoles, laboratoires publics.

Thématiques : ville durable, urbanisme, mobilité, sobriété foncière, bâtiment bas carbone.

Contact : villes@anr.fr""",
        {
            "title": "AAP Villes et territoires durables 2028",
            "organisation": "ANR",
            "deadline": "2028-02-15",
            "opening_date": "2027-10-15",
            "amount_max": 280000,
            "currency": "EUR",
            "eligibility": "Urbanistes, architectes, géographes, ingénieurs.",
            "eligible_applicants": ["universités", "grandes écoles", "laboratoires publics"],
            "research_topics": ["ville durable", "urbanisme", "mobilité", "sobriété foncière", "bâtiment bas carbone"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 février 2028"), Ent("OPENING_DATE", "15 octobre 2027"), Ent("AMOUNT", "280 000 €")],
    ),
    Example(  # NEW
        "inserm-neurotech-2028", "train",
        "https://www.inserm.fr/appels-a-projets/neurotech-2028",
"""\
Inserm - Appel à projets : Neurotechnologies 2028

L'Inserm lance l'appel à projets Neurotechnologies 2028.

Ce programme finance le développement de neurotechnologies pour la recherche et la clinique.

Date limite : 30 août 2028
Ouverture : 1er mai 2028
Montant maximal : 450 000 €
Durée maximale : 36 mois

Éligibilité : Neurobiologistes, ingénieurs, informaticiens, cliniciens.
Institutions : unités Inserm, CNRS, universités, centres de cancérologie.

Thématiques : optogénétique, électrophysiologie, interfaces neuronales, stimulation cérébrale profonde.

Contact : neurotech@inserm.fr""",
        {
            "title": "Neurotechnologies 2028",
            "organisation": "Inserm",
            "deadline": "2028-08-30",
            "opening_date": "2028-05-01",
            "amount_max": 450000,
            "currency": "EUR",
            "eligibility": "Neurobiologistes, ingénieurs, informaticiens, cliniciens.",
            "eligible_applicants": ["unités Inserm", "CNRS", "universités", "centres de cancérologie"],
            "research_topics": ["optogénétique", "électrophysiologie", "interfaces neuronales", "stimulation cérébrale profonde"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "30 août 2028"), Ent("OPENING_DATE", "1er mai 2028"), Ent("AMOUNT", "450 000 €")],
    ),
    Example(  # NEW
        "cnrs-math-2027", "train",
        "https://www.cnrs.fr/appels-a-projets/mathematiques-2027",
"""\
CNRS - Appel à projets : Mathématiques et interactions 2027

Le CNRS lance l'appel à projets Mathématiques et interactions 2027.

Ce programme finance la recherche en mathématiques pures et appliquées.

Date limite : 1er juin 2027
Ouverture : 1er mars 2027
Montant maximal : 120 000 €
Durée maximale : 36 mois

Éligibilité : Mathématiciens, chercheurs en mathématiques appliquées.
Institutions : instituts CNRS, universités, INRIA.

Thématiques : algèbre, géométrie, analyse, probabilités, mathématiques du vivant.

Contact : maths@cnrs.fr""",
        {
            "title": "Mathématiques et interactions 2027",
            "organisation": "CNRS",
            "deadline": "2027-06-01",
            "opening_date": "2027-03-01",
            "amount_max": 120000,
            "currency": "EUR",
            "eligibility": "Mathématiciens, chercheurs en mathématiques appliquées.",
            "eligible_applicants": ["instituts CNRS", "universités", "INRIA"],
            "research_topics": ["algèbre", "géométrie", "analyse", "probabilités", "mathématiques du vivant"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "1er juin 2027"), Ent("OPENING_DATE", "1er mars 2027"), Ent("AMOUNT", "120 000 €")],
    ),
    Example(  # NEW
        "inca-cervical-2028", "test",
        "https://www.e-cancer.fr/Institut-national-du-cancer/Appels-a-projets/cancer-cervical-2028",
"""\
INCa - Appel à projets : Cancer du col de l'utérus 2028

L'INCa lance l'appel à projets Cancer du col de l'utérus 2028.

Ce programme finance la recherche sur la prévention et le traitement du cancer du col de l'utérus.

Date limite : 30 novembre 2028
Ouverture : 1er septembre 2028
Montant maximal : 140 000 €
Durée maximale : 24 mois

Éligibilité : Gynécologues oncologues, virologues, épidémiologistes.
Institutions : centres de lutte contre le cancer, CHU, universités.

Thématiques : HPV, dépistage, vaccination, conisation, surveillance.

Contact : cervical@e-cancer.fr""",
        {
            "title": "Cancer du col de l'utérus 2028",
            "organisation": "INCa",
            "deadline": "2028-11-30",
            "opening_date": "2028-09-01",
            "amount_max": 140000,
            "currency": "EUR",
            "eligibility": "Gynécologues oncologues, virologues, épidémiologistes.",
            "eligible_applicants": ["centres de lutte contre le cancer", "CHU", "universités"],
            "research_topics": ["HPV", "dépistage", "vaccination", "conisation", "surveillance"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "30 novembre 2028"), Ent("OPENING_DATE", "1er septembre 2028"), Ent("AMOUNT", "140 000 €")],
    ),
    Example(  # NEW
        "anr-ocean-2027", "test",
        "https://anr.fr/fr/les-appels-a-projets/oceans-climat-2027.html",
"""\
Appel à projets : AAP Océans et climat 2027

L'ANR lance l'appel à projets Océans et climat 2027.

Ce programme finance la recherche sur le rôle des océans dans le système climatique.

Date limite : 20 octobre 2027
Ouverture : 20 juin 2027
Montant maximal : 350 000 €
Durée maximale : 48 mois

Éligibilité : Océanographes, climatologues, biologistes marins.
Institutions : universités, Ifremer, CNRS, IRD.

Thématiques : océan et climat, acidification, montée des eaux, courants, écosystèmes marins.

Contact : ocean@anr.fr""",
        {
            "title": "AAP Océans et climat 2027",
            "organisation": "ANR",
            "deadline": "2027-10-20",
            "opening_date": "2027-06-20",
            "amount_max": 350000,
            "currency": "EUR",
            "eligibility": "Océanographes, climatologues, biologistes marins.",
            "eligible_applicants": ["universités", "Ifremer", "CNRS", "IRD"],
            "research_topics": ["océan et climat", "acidification", "montée des eaux", "courants", "écosystèmes marins"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "20 octobre 2027"), Ent("OPENING_DATE", "20 juin 2027"), Ent("AMOUNT", "350 000 €")],
    ),
    Example(  # NEW
        "horizon-europe-agriculture-2028", "train",
        "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic/details/AGRI-2028",
"""\
Horizon Europe - Appel à projets : Agriculture et sols 2028

La Commission européenne lance l'appel AGRI-2028 dans le cadre d'Horizon Europe.

Recherche sur la santé des sols et l'agriculture durable.

Date limite : 15 novembre 2028
Ouverture : 15 juillet 2028
Montant maximal : 3 500 000 €
Durée maximale : 48 mois

Éligibilité : Consortium d'au moins 3 organisations de 3 pays européens.
Institutions : universités, instituts agronomiques, entreprises.

Thématiques : santé des sols, agriculture de précision, agroécologie, carbone du sol, irrigation.

Contact : agri@ec.europa.eu""",
        {
            "title": "AGRI-2028",
            "organisation": "Commission européenne",
            "deadline": "2028-11-15",
            "opening_date": "2028-07-15",
            "amount_max": 3500000,
            "currency": "EUR",
            "eligibility": "Consortium d'au moins 3 organisations de 3 pays européens.",
            "eligible_applicants": ["universités", "instituts agronomiques", "entreprises"],
            "research_topics": ["santé des sols", "agriculture de précision", "agroécologie", "carbone du sol", "irrigation"],
            "geographical_scope": "Europe",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 novembre 2028"), Ent("OPENING_DATE", "15 juillet 2028"), Ent("AMOUNT", "3 500 000 €")],
    ),
    Example(  # NEW
        "ars-normandie-2027", "test",
        "https://www.ars-normandie.sante.fr/aaps/alimentation2027",
"""\
ARS Normandie - Appel à projets : Alimentation et santé 2027

L'ARS Normandie lance l'appel à projets Alimentation et santé 2027.

Ce programme finance la recherche sur la nutrition et la santé en région.

Date limite : 30 septembre 2027
Ouverture : 1er juillet 2027
Montant maximal : 35 000 €
Durée maximale : 12 mois

Éligibilité : Nutritionnistes, épidémiologistes, professionnels de santé.
Institutions : hôpitaux, universités, associations de santé publique.

Thématiques : obésité, malnutrition, rééquilibrage alimentaire.

Contact : alimentation@ars-normandie.fr""",
        {
            "title": "Alimentation et santé 2027",
            "organisation": "ARS Normandie",
            "deadline": "2027-09-30",
            "opening_date": "2027-07-01",
            "amount_max": 35000,
            "currency": "EUR",
            "eligibility": "Nutritionnistes, épidémiologistes, professionnels de santé.",
            "eligible_applicants": ["hôpitaux", "universités", "associations de santé publique"],
            "research_topics": ["obésité", "malnutrition", "rééquilibrage alimentaire"],
            "geographical_scope": "Normandie",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "30 septembre 2027"), Ent("OPENING_DATE", "1er juillet 2027"), Ent("AMOUNT", "35 000 €")],
    ),
    Example(  # NEW
        "fondation-arc-cerebral-2028", "train",
        "https://www.fondation-arc.org/appel-a-projets/tumeurs-cerebrales-2028",
"""\
Fondation ARC - Appel à projets : Tumeurs cérébrales 2028

La Fondation ARC finance la recherche sur les tumeurs cérébrales.

Ce programme porte sur les gliomes, glioblastomes et métastases cérébrales.

Date limite : 15 septembre 2028
Ouverture : 15 juin 2028
Montant maximal : 240 000 €
Durée maximale : 36 mois

Éligibilité : Neuro-oncologues, neurochirurgiens, biologistes.
Institutions : centres de recherche, hôpitaux, universités.

Thématiques : gliomes, glioblastomes, métastases cérébrales, radiochirurgie, oncologie moléculaire.

Contact : cerebral@fondation-arc.org""",
        {
            "title": "Tumeurs cérébrales 2028",
            "organisation": "Fondation ARC",
            "deadline": "2028-09-15",
            "opening_date": "2028-06-15",
            "amount_max": 240000,
            "currency": "EUR",
            "eligibility": "Neuro-oncologues, neurochirurgiens, biologistes.",
            "eligible_applicants": ["centres de recherche", "hôpitaux", "universités"],
            "research_topics": ["gliomes", "glioblastomes", "métastases cérébrales", "radiochirurgie", "oncologie moléculaire"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 septembre 2028"), Ent("OPENING_DATE", "15 juin 2028"), Ent("AMOUNT", "240 000 €")],
    ),
    Example(  # NEW
        "cnrs-quantique-2028", "train",
        "https://www.cnrs.fr/appels-a-projets/quantique-2028",
"""\
CNRS - Appel à projets : Technologies quantiques 2028

Le CNRS lance l'appel à projets Technologies quantiques 2028.

Ce programme finance la recherche sur l'informatique quantique et les capteurs quantiques.

Date limite : 15 mars 2028
Ouverture : 15 novembre 2027
Montant maximal : 500 000 €
Durée maximale : 48 mois

Éligibilité : Physiciens, informaticiens, ingénieurs.
Institutions : instituts CNRS, INRIA, grandes écoles, universités.

Thématiques : ordinateur quantique, qubits, cryptographie quantique, capteurs, simulation quantique.

Contact : quantique@cnrs.fr""",
        {
            "title": "Technologies quantiques 2028",
            "organisation": "CNRS",
            "deadline": "2028-03-15",
            "opening_date": "2027-11-15",
            "amount_max": 500000,
            "currency": "EUR",
            "eligibility": "Physiciens, informaticiens, ingénieurs.",
            "eligible_applicants": ["instituts CNRS", "INRIA", "grandes écoles", "universités"],
            "research_topics": ["ordinateur quantique", "qubits", "cryptographie quantique", "capteurs", "simulation quantique"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 mars 2028"), Ent("OPENING_DATE", "15 novembre 2027"), Ent("AMOUNT", "500 000 €")],
    ),
    Example(  # NEW
        "ligue-cancer-cutane-2028", "test",
        "https://www.ligue-cancer.net/appel-a-projets/melanome-2028",
"""\
Ligue contre le Cancer - Appel à projets : Mélanome 2028

La Ligue contre le Cancer lance l'appel à projets Mélanome 2028.

Ce programme finance la recherche sur le mélanome et les cancers de la peau.

Date limite : 15 mars 2028
Ouverture : 15 décembre 2027
Montant maximal : 170 000 €
Durée maximale : 36 mois

Éligibilité : Dermato-oncologues, immunologistes, dermatologues.
Institutions : centres de recherche, hôpitaux, universités.

Thématiques : mélanome, immunothérapie, dermatoscopie, UV, métastases cutanées.

Contact : melanome@ligue-cancer.net""",
        {
            "title": "Mélanome 2028",
            "organisation": "Ligue contre le Cancer",
            "deadline": "2028-03-15",
            "opening_date": "2027-12-15",
            "amount_max": 170000,
            "currency": "EUR",
            "eligibility": "Dermato-oncologues, immunologistes, dermatologues.",
            "eligible_applicants": ["centres de recherche", "hôpitaux", "universités"],
            "research_topics": ["mélanome", "immunothérapie", "dermatoscopie", "UV", "métastases cutanées"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 mars 2028"), Ent("OPENING_DATE", "15 décembre 2027"), Ent("AMOUNT", "170 000 €")],
    ),
    Example(  # NEW
        "fondation-france-jeunesse-2027", "train",
        "https://www.fondationdefrance.org/appels/jeunesse-2027",
"""\
Fondation de France - Recherche sur la jeunesse 2027

La Fondation de France soutient la recherche sur la jeunesse et l'insertion.

Ce programme finance des études sur les parcours des jeunes.

Date limite : 1er octobre 2027
Ouverture : 1er juin 2027
Montant maximal : 40 000 €
Durée maximale : 18 mois

Éligibilité : Sociologues, psychologues, économistes.
Institutions : universités, CNRS, centres de recherche.

Thématiques : décrochage, insertion professionnelle, jeunesse précarisée, engagement.

Contact : jeunesse@fondationdefrance.org""",
        {
            "title": "Recherche sur la jeunesse 2027",
            "organisation": "Fondation de France",
            "deadline": "2027-10-01",
            "opening_date": "2027-06-01",
            "amount_max": 40000,
            "currency": "EUR",
            "eligibility": "Sociologues, psychologues, économistes.",
            "eligible_applicants": ["universités", "CNRS", "centres de recherche"],
            "research_topics": ["décrochage", "insertion professionnelle", "jeunesse précarisée", "engagement"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "1er octobre 2027"), Ent("OPENING_DATE", "1er juin 2027"), Ent("AMOUNT", "40 000 €")],
    ),
    Example(  # NEW
        "frm-neurodege-2028", "test",
        "https://www.frm.org/appels/neurodegeneratif-2028",
"""\
Fondation pour la Recherche Médicale - Appel à projets : Maladies neurodégénératives 2028

La FRM lance l'appel à projets Maladies neurodégénératives 2028.

Ce programme finance la recherche sur Alzheimer, Parkinson et la sclérose en plaques.

Date limite : 30 avril 2028
Ouverture : 30 janvier 2028
Montant maximal : 260 000 €
Durée maximale : 36 mois

Éligibilité : Neurologues, neurobiologistes, chercheurs.
Institutions : universités, Inserm, CNRS, hôpitaux.

Thématiques : Alzheimer, Parkinson, sclérose en plaques, protéines mal repliées, neuroinflammation.

Contact : neuro@frm.org""",
        {
            "title": "Maladies neurodégénératives 2028",
            "organisation": "FRM",
            "deadline": "2028-04-30",
            "opening_date": "2028-01-30",
            "amount_max": 260000,
            "currency": "EUR",
            "eligibility": "Neurologues, neurobiologistes, chercheurs.",
            "eligible_applicants": ["universités", "Inserm", "CNRS", "hôpitaux"],
            "research_topics": ["Alzheimer", "Parkinson", "sclérose en plaques", "protéines mal repliées", "neuroinflammation"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "30 avril 2028"), Ent("OPENING_DATE", "30 janvier 2028"), Ent("AMOUNT", "260 000 €")],
    ),
    Example(  # NEW
        "anr-culture-2027", "train",
        "https://anr.fr/fr/les-appels-a-projets/cultures-2027.html",
"""\
Appel à projets : AAP Cultures et sociétés 2027

L'ANR lance l'appel à projets Cultures et sociétés 2027.

Ce programme finance la recherche en sciences humaines et sociales sur les cultures.

Date limite : 1er novembre 2027
Ouverture : 1er juillet 2027
Montant maximal : 180 000 €
Durée maximale : 36 mois

Éligibilité : Chercheurs en sciences humaines et sociales.
Institutions : universités, CNRS, musées, archives.

Thématiques : patrimoine, littérature, arts, histoire, anthropologie.

Contact : cultures@anr.fr""",
        {
            "title": "AAP Cultures et sociétés 2027",
            "organisation": "ANR",
            "deadline": "2027-11-01",
            "opening_date": "2027-07-01",
            "amount_max": 180000,
            "currency": "EUR",
            "eligibility": "Chercheurs en sciences humaines et sociales.",
            "eligible_applicants": ["universités", "CNRS", "musées", "archives"],
            "research_topics": ["patrimoine", "littérature", "arts", "histoire", "anthropologie"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "1er novembre 2027"), Ent("OPENING_DATE", "1er juillet 2027"), Ent("AMOUNT", "180 000 €")],
    ),
    Example(  # NEW
        "ars-idf-sommeil-2028", "train",
        "https://www.ars-idf.sante.fr/aaps/sommeil-2028",
"""\
ARS Île-de-France - Appel à projets : Sommeil et santé 2028

L'ARS Île-de-France lance l'appel à projets Sommeil et santé 2028.

Ce programme finance la recherche sur les troubles du sommeil et leurs impacts.

Date limite : 30 mai 2028
Ouverture : 1er mars 2028
Montant maximal : 55 000 €
Durée maximale : 18 mois

Éligibilité : Médecins du sommeil, neurologues, psychologues.
Institutions : hôpitaux, centres du sommeil, universités.

Thématiques : insomnie, apnée du sommeil, rythmes circadiens, sommeil et travail posté.

Contact : sommeil@ars-idf.fr""",
        {
            "title": "Sommeil et santé 2028",
            "organisation": "ARS Île-de-France",
            "deadline": "2028-05-30",
            "opening_date": "2028-03-01",
            "amount_max": 55000,
            "currency": "EUR",
            "eligibility": "Médecins du sommeil, neurologues, psychologues.",
            "eligible_applicants": ["hôpitaux", "centres du sommeil", "universités"],
            "research_topics": ["insomnie", "apnée du sommeil", "rythmes circadiens", "sommeil et travail posté"],
            "geographical_scope": "Île-de-France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "30 mai 2028"), Ent("OPENING_DATE", "1er mars 2028"), Ent("AMOUNT", "55 000 €")],
    ),
    Example(  # NEW
        "horizon-europe-education-2027", "test",
        "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic/details/EDU-2027",
"""\
Horizon Europe - Appel à projets : Éducation et compétences 2027

La Commission européenne lance l'appel EDU-2027.

Recherche sur l'éducation, les compétences et l'apprentissage tout au long de la vie.

Date limite : 1er mars 2027
Ouverture : 1er novembre 2026
Montant maximal : 1 500 000 €
Durée maximale : 36 mois

Éligibilité : Consortium d'au moins 2 organisations de 2 pays européens.
Institutions : universités, écoles, ONG, instituts de recherche.

Thématiques : compétences numériques, formation professionnelle, apprentissage des langues, égalité des chances.

Contact : edu@ec.europa.eu""",
        {
            "title": "EDU-2027",
            "organisation": "Commission européenne",
            "deadline": "2027-03-01",
            "opening_date": "2026-11-01",
            "amount_max": 1500000,
            "currency": "EUR",
            "eligibility": "Consortium d'au moins 2 organisations de 2 pays européens.",
            "eligible_applicants": ["universités", "écoles", "ONG", "instituts de recherche"],
            "research_topics": ["compétences numériques", "formation professionnelle", "apprentissage des langues", "égalité des chances"],
            "geographical_scope": "Europe",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "1er mars 2027"), Ent("OPENING_DATE", "1er novembre 2026"), Ent("AMOUNT", "1 500 000 €")],
    ),
    Example(  # NEW
        "inserm-infectio-2027", "train",
        "https://www.inserm.fr/appels-a-projets/infectio2027",
"""\
Inserm - Appel à projets : Maladies infectieuses 2027

L'Inserm lance l'appel à projets Maladies infectieuses 2027.

Ce programme finance la recherche sur les agents infectieux et leur impact sanitaire.

Date limite : 15 juin 2027
Ouverture : 15 mars 2027
Montant maximal : 300 000 €
Durée maximale : 36 mois

Éligibilité : Microbiologistes, virologues, immunologistes, cliniciens.
Institutions : unités Inserm, CNRS, Pasteur, CHU.

Thématiques : bactéries, virus, champignons, antibiorésistance, zoonoses, vaccins.

Contact : infectio@inserm.fr""",
        {
            "title": "Maladies infectieuses 2027",
            "organisation": "Inserm",
            "deadline": "2027-06-15",
            "opening_date": "2027-03-15",
            "amount_max": 300000,
            "currency": "EUR",
            "eligibility": "Microbiologistes, virologues, immunologistes, cliniciens.",
            "eligible_applicants": ["unités Inserm", "CNRS", "Pasteur", "CHU"],
            "research_topics": ["bactéries", "virus", "champignons", "antibiorésistance", "zoonoses", "vaccins"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 juin 2027"), Ent("OPENING_DATE", "15 mars 2027"), Ent("AMOUNT", "300 000 €")],
    ),
    Example(  # NEW
        "anr-chimie-2028", "test",
        "https://anr.fr/fr/les-appels-a-projets/chimie-2028.html",
"""\
Appel à projets : AAP Chimie verte 2028

L'ANR lance l'appel à projets Chimie verte 2028.

Ce programme finance la recherche en chimie durable et éco-conception.

Date limite : 15 novembre 2028
Ouverture : 15 juin 2028
Montant maximal : 320 000 €
Durée maximale : 36 mois

Éligibilité : Chimistes, ingénieurs, biologistes.
Institutions : universités, CNRS, écoles d'ingénieurs, CEA.

Thématiques : chimie verte, catalyse, chimie biosourcée, recyclage, chimie de l'eau.

Contact : chimie@anr.fr""",
        {
            "title": "AAP Chimie verte 2028",
            "organisation": "ANR",
            "deadline": "2028-11-15",
            "opening_date": "2028-06-15",
            "amount_max": 320000,
            "currency": "EUR",
            "eligibility": "Chimistes, ingénieurs, biologistes.",
            "eligible_applicants": ["universités", "CNRS", "écoles d'ingénieurs", "CEA"],
            "research_topics": ["chimie verte", "catalyse", "chimie biosourcée", "recyclage", "chimie de l'eau"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 novembre 2028"), Ent("OPENING_DATE", "15 juin 2028"), Ent("AMOUNT", "320 000 €")],
    ),
    Example(  # NEW
        "cnrs-materiaux-2027", "train",
        "https://www.cnrs.fr/appels-a-projets/materiaux2027",
"""\
CNRS - Appel à projets : Matériaux du futur 2027

Le CNRS lance l'appel à projets Matériaux du futur 2027.

Ce programme finance la recherche sur les nouveaux matériaux à haute performance.

Date limite : 30 novembre 2027
Ouverture : 1er août 2027
Montant maximal : 200 000 €
Durée maximale : 36 mois

Éligibilité : Chimistes des matériaux, physiciens, ingénieurs.
Institutions : instituts CNRS, universités, CEA, écoles d'ingénieurs.

Thématiques : matériaux composites, céramiques, alliages, matériaux bio-inspirés, impression 3D.

Contact : materiaux@cnrs.fr""",
        {
            "title": "Matériaux du futur 2027",
            "organisation": "CNRS",
            "deadline": "2027-11-30",
            "opening_date": "2027-08-01",
            "amount_max": 200000,
            "currency": "EUR",
            "eligibility": "Chimistes des matériaux, physiciens, ingénieurs.",
            "eligible_applicants": ["instituts CNRS", "universités", "CEA", "écoles d'ingénieurs"],
            "research_topics": ["matériaux composites", "céramiques", "alliages", "matériaux bio-inspirés", "impression 3D"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "30 novembre 2027"), Ent("OPENING_DATE", "1er août 2027"), Ent("AMOUNT", "200 000 €")],
    ),
    Example(  # NEW
        "inserm-epigenetique-cancer-2028", "test",
        "https://www.inserm.fr/appels-a-projets/epigenetique-2028",
"""\
Inserm - Appel à projets : Épigénétique et santé 2028

L'Inserm lance l'appel à projets Épigénétique et santé 2028.

Ce programme finance la recherche sur les mécanismes épigénétiques et leurs implications cliniques.

Date limite : 30 septembre 2028
Ouverture : 1er mai 2028
Montant maximal : 280 000 €
Durée maximale : 36 mois

Éligibilité : Biologistes moléculaires, généticiens, cliniciens.
Institutions : unités Inserm, CHU, universités.

Thématiques : méthylation, histones, microARN, épigénétique des maladies chroniques.

Contact : epigenetique@inserm.fr""",
        {
            "title": "Épigénétique et santé 2028",
            "organisation": "Inserm",
            "deadline": "2028-09-30",
            "opening_date": "2028-05-01",
            "amount_max": 280000,
            "currency": "EUR",
            "eligibility": "Biologistes moléculaires, généticiens, cliniciens.",
            "eligible_applicants": ["unités Inserm", "CHU", "universités"],
            "research_topics": ["méthylation", "histones", "microARN", "épigénétique des maladies chroniques"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "30 septembre 2028"), Ent("OPENING_DATE", "1er mai 2028"), Ent("AMOUNT", "280 000 €")],
    ),
    Example(  # NEW
        "ars-nouvelle-aquitaine-2028", "test",
        "https://www.ars-nouvelle-aquitaine.sante.fr/aaps/reco256",
"""\
ARS Nouvelle-Aquitaine - Appel à projets : Santé bucco-dentaire 2028

L'ARS Nouvelle-Aquitaine lance l'appel à projets Santé bucco-dentaire 2028.

Ce programme finance des projets de recherche sur la prévention en santé orale.

Date limite : 15 juillet 2028
Ouverture : 15 avril 2028
Montant maximal : 40 000 €
Durée maximale : 12 mois

Éligibilité : Dentistes, chirurgiens-dentistes, professionnels de santé scolaire.
Institutions : CHU, universités, associations.

Thématiques : santé bucco-dentaire, prévention, hygiène buccale, accès aux soins dentaires.

Contact : buccodentaire@ars-na.fr""",
        {
            "title": "Santé bucco-dentaire 2028",
            "organisation": "ARS Nouvelle-Aquitaine",
            "deadline": "2028-07-15",
            "opening_date": "2028-04-15",
            "amount_max": 40000,
            "currency": "EUR",
            "eligibility": "Dentistes, chirurgiens-dentistes, professionnels de santé scolaire.",
            "eligible_applicants": ["CHU", "universités", "associations"],
            "research_topics": ["santé bucco-dentaire", "prévention", "hygiène buccale", "accès aux soins dentaires"],
            "geographical_scope": "Nouvelle-Aquitaine",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 juillet 2028"), Ent("OPENING_DATE", "15 avril 2028"), Ent("AMOUNT", "40 000 €")],
    ),
    Example(  # NEW
        "fondation-arc-immuno-2028", "train",
        "https://www.fondation-arc.org/appel-a-projets/immunotherapie-2028",
"""\
Fondation ARC - Appel à projets : Immunothérapie des cancers 2028

La Fondation ARC finance la recherche en immunothérapie des cancers.

Ce programme porte sur le développement de nouvelles immunothérapies.

Date limite : 20 octobre 2028
Ouverture : 20 juin 2028
Montant maximal : 300 000 €
Durée maximale : 36 mois

Éligibilité : Immunologistes, oncologues, biotechnologistes.
Institutions : centres de recherche, hôpitaux, universités.

Thématiques : CAR-T cells, anticorps, microbiote et immunothérapie, biomarqueurs de réponse.

Contact : immunotherapie@fondation-arc.org""",
        {
            "title": "Immunothérapie des cancers 2028",
            "organisation": "Fondation ARC",
            "deadline": "2028-10-20",
            "opening_date": "2028-06-20",
            "amount_max": 300000,
            "currency": "EUR",
            "eligibility": "Immunologistes, oncologues, biotechnologistes.",
            "eligible_applicants": ["centres de recherche", "hôpitaux", "universités"],
            "research_topics": ["CAR-T cells", "anticorps", "microbiote et immunothérapie", "biomarqueurs de réponse"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "20 octobre 2028"), Ent("OPENING_DATE", "20 juin 2028"), Ent("AMOUNT", "300 000 €")],
    ),
    Example(  # NEW
        "ligue-cancer-leucemie-2027", "train",
        "https://www.ligue-cancer.net/appel-a-projets/leucemie-2027",
"""\
Ligue contre le Cancer - Appel à projets : Leucémie lymphoïde chronique 2027

La Ligue contre le Cancer lance l'appel à projets Leucémie lymphoïde chronique 2027.

Ce programme soutient la recherche sur les leucémies de l'adulte.

Date limite : 30 novembre 2027
Ouverture : 1er septembre 2027
Montant maximal : 190 000 €
Durée maximale : 36 mois

Éligibilité : Hématologues, oncologues, cytogénéticiens.
Institutions : centres de recherche, hôpitaux, universités.

Thématiques : leucémie lymphoïde chronique, cytogénétique, thérapies ciblées, minirésidu moléculaire.

Contact : leucemie@ligue-cancer.net""",
        {
            "title": "Leucémie lymphoïde chronique 2027",
            "organisation": "Ligue contre le Cancer",
            "deadline": "2027-11-30",
            "opening_date": "2027-09-01",
            "amount_max": 190000,
            "currency": "EUR",
            "eligibility": "Hématologues, oncologues, cytogénéticiens.",
            "eligible_applicants": ["centres de recherche", "hôpitaux", "universités"],
            "research_topics": ["leucémie lymphoïde chronique", "cytogénétique", "thérapies ciblées", "minirésidu moléculaire"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "30 novembre 2027"), Ent("OPENING_DATE", "1er septembre 2027"), Ent("AMOUNT", "190 000 €")],
    ),
    Example(  # NEW
        "frm-diabette-2027", "train",
        "https://www.frm.org/appels/diabete-2027",
"""\
Fondation pour la Recherche Médicale - Appel à projets : Diabète 2027

La FRM lance l'appel à projets Diabète 2027.

Ce programme finance la recherche sur le diabète et les complications associées.

Date limite : 30 juin 2027
Ouverture : 1er avril 2027
Montant maximal : 240 000 €
Durée maximale : 36 mois

Éligibilité : Diabétologues, endocrinologues, chercheurs en métabolisme.
Institutions : universités, Inserm, CHU.

Thématiques : diabète de type 1, diabète de type 2, insuline, complications diabétiques, pancréas artificiel.

Contact : diabete@frm.org""",
        {
            "title": "Diabète 2027",
            "organisation": "FRM",
            "deadline": "2027-06-30",
            "opening_date": "2027-04-01",
            "amount_max": 240000,
            "currency": "EUR",
            "eligibility": "Diabétologues, endocrinologues, chercheurs en métabolisme.",
            "eligible_applicants": ["universités", "Inserm", "CHU"],
            "research_topics": ["diabète de type 1", "diabète de type 2", "insuline", "complications diabétiques", "pancréas artificiel"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "30 juin 2027"), Ent("OPENING_DATE", "1er avril 2027"), Ent("AMOUNT", "240 000 €")],
    ),
    Example(  # NEW
        "fondation-france-climat-2028", "train",
        "https://www.fondationdefrance.org/appels/climat-2028",
"""\
Fondation de France - Recherche sur le climat 2028

La Fondation de France lance l'appel à projets Recherche sur le climat 2028.

Ce programme finance des projets de recherche sur les impacts locaux du changement climatique.

Date limite : 1er novembre 2028
Ouverture : 1er juillet 2028
Montant maximal : 60 000 €
Durée maximale : 18 mois

Éligibilité : Climatologues, géographes, économistes, sociologues.
Institutions : universités, CNRS, associations.

Thématiques : impacts locaux, adaptation, résilience territoriale, îlots de chaleur, littoral.

Contact : climat@fondationdefrance.org""",
        {
            "title": "Recherche sur le climat 2028",
            "organisation": "Fondation de France",
            "deadline": "2028-11-01",
            "opening_date": "2028-07-01",
            "amount_max": 60000,
            "currency": "EUR",
            "eligibility": "Climatologues, géographes, économistes, sociologues.",
            "eligible_applicants": ["universités", "CNRS", "associations"],
            "research_topics": ["impacts locaux", "adaptation", "résilience territoriale", "îlots de chaleur", "littoral"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "1er novembre 2028"), Ent("OPENING_DATE", "1er juillet 2028"), Ent("AMOUNT", "60 000 €")],
    ),
    Example(  # NEW
        "anr-agroecologie-2027", "train",
        "https://anr.fr/fr/les-appels-a-projets/agroecologie-2027.html",
"""\
Appel à projets : AAP Agroécologie 2027

L'ANR lance l'appel à projets Agroécologie 2027.

Ce programme finance la recherche sur la transition agroécologique des systèmes agricoles.

Date limite : 1er mai 2027
Ouverture : 1er février 2027
Montant maximal : 260 000 €
Durée maximale : 48 mois

Éligibilité : Agronomes, écologues, économistes agricoles.
Institutions : universités, INRAE, CNRS, Chambres d'agriculture.

Thématiques : agroécologie, agrobiodiversité, sols vivants, systèmes de culture, élevage durable.

Contact : agro@anr.fr""",
        {
            "title": "AAP Agroécologie 2027",
            "organisation": "ANR",
            "deadline": "2027-05-01",
            "opening_date": "2027-02-01",
            "amount_max": 260000,
            "currency": "EUR",
            "eligibility": "Agronomes, écologues, économistes agricoles.",
            "eligible_applicants": ["universités", "INRAE", "CNRS", "Chambres d'agriculture"],
            "research_topics": ["agroécologie", "agrobiodiversité", "sols vivants", "systèmes de culture", "élevage durable"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "1er mai 2027"), Ent("OPENING_DATE", "1er février 2027"), Ent("AMOUNT", "260 000 €")],
    ),
    Example(  # NEW
        "ctu-grenoble-2028", "test",
        "https://www.chu-grenoble.fr/appels-a-projets/telemedecine-2028",
"""\
CHU Grenoble Alpes - Appel à projets : Télémédecine 2028

Le CHU Grenoble Alpes lance l'appel à projets Télémédecine 2028.

Ce programme finance la recherche sur la télésanté et les objets connectés en santé.

Date limite : 15 juin 2028
Ouverture : 15 mars 2028
Montant maximal : 60 000 €
Durée maximale : 24 mois

Éligibilité : Médecins, ingénieurs, informaticiens, soignants.
Institutions : CHU, universités, instituts de recherche.

Thématiques : télémédecine, téléconsultation, objets connectés, e-santé, données de santé.

Contact : telemedecine@chu-grenoble.fr""",
        {
            "title": "Télémédecine 2028",
            "organisation": "CHU Grenoble Alpes",
            "deadline": "2028-06-15",
            "opening_date": "2028-03-15",
            "amount_max": 60000,
            "currency": "EUR",
            "eligibility": "Médecins, ingénieurs, informaticiens, soignants.",
            "eligible_applicants": ["CHU", "universités", "instituts de recherche"],
            "research_topics": ["télémédecine", "téléconsultation", "objets connectés", "e-santé", "données de santé"],
            "geographical_scope": "Auvergne-Rhône-Alpes",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 juin 2028"), Ent("OPENING_DATE", "15 mars 2028"), Ent("AMOUNT", "60 000 €")],
    ),
    Example(  # NEW
        "horizon-europe-espace-2027", "test",
        "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic/details/SPACE-2027",
"""\
Horizon Europe - Appel à projets : Espace et observation de la Terre 2027

La Commission européenne lance l'appel SPACE-2027 dans le cadre d'Horizon Europe.

Recherche sur l'observation de la Terre et les applications spatiales.

Date limite : 15 juillet 2027
Ouverture : 15 mars 2027
Montant maximal : 2 200 000 €
Durée maximale : 48 mois

Éligibilité : Consortium d'au moins 3 organisations de 3 pays européens.
Institutions : agences spatiales, universités, entreprises.

Thématiques : observation de la Terre, Copernicus, satellites, données spatiales, changement climatique.

Contact : space@ec.europa.eu""",
        {
            "title": "SPACE-2027",
            "organisation": "Commission européenne",
            "deadline": "2027-07-15",
            "opening_date": "2027-03-15",
            "amount_max": 2200000,
            "currency": "EUR",
            "eligibility": "Consortium d'au moins 3 organisations de 3 pays européens.",
            "eligible_applicants": ["agences spatiales", "universités", "entreprises"],
            "research_topics": ["observation de la Terre", "Copernicus", "satellites", "données spatiales", "changement climatique"],
            "geographical_scope": "Europe",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 juillet 2027"), Ent("OPENING_DATE", "15 mars 2027"), Ent("AMOUNT", "2 200 000 €")],
    ),
    Example(  # NEW
        "inca-reinsertion-2028", "train",
        "https://www.e-cancer.fr/Institut-national-du-cancer/Appels-a-projets/reinsertion-2028",
"""\
INCa - Appel à projets : Retour à la vie après cancer 2028

L'INCa lance l'appel à projets Retour à la vie après cancer 2028.

Ce programme finance la recherche sur la qualité de vie et la réinsertion des patients.

Date limite : 30 avril 2028
Ouverture : 1er janvier 2028
Montant maximal : 130 000 €
Durée maximale : 24 mois

Éligibilité : Chercheurs en santé publique, psychologues, sociologues.
Institutions : centres de recherche, CHU, associations.

Thématiques : qualité de vie, réinsertion professionnelle, fatigue, soutien social, suivi post-cancer.

Contact : reinsertion@e-cancer.fr""",
        {
            "title": "Retour à la vie après cancer 2028",
            "organisation": "INCa",
            "deadline": "2028-04-30",
            "opening_date": "2028-01-01",
            "amount_max": 130000,
            "currency": "EUR",
            "eligibility": "Chercheurs en santé publique, psychologues, sociologues.",
            "eligible_applicants": ["centres de recherche", "CHU", "associations"],
            "research_topics": ["qualité de vie", "réinsertion professionnelle", "fatigue", "soutien social", "suivi post-cancer"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "30 avril 2028"), Ent("OPENING_DATE", "1er janvier 2028"), Ent("AMOUNT", "130 000 €")],
    ),
    Example(  # NEW
        "cnrs-robotique-2027", "test",
        "https://www.cnrs.fr/appels-a-projets/robotique2027",
"""\
CNRS - Appel à projets : Robotique et automatique 2027

Le CNRS lance l'appel à projets Robotique et automatique 2027.

Ce programme finance la recherche en robotique de service et industrielle.

Date limite : 30 mars 2027
Ouverture : 30 novembre 2026
Montant maximal : 220 000 €
Durée maximale : 36 mois

Éligibilité : Roboticiens, automaticiens, informaticiens.
Institutions : instituts CNRS, INRIA, écoles d'ingénieurs, universités.

Thématiques : robotique de service, cobotique, perception, planification, robotique adaptative.

Contact : robotique@cnrs.fr""",
        {
            "title": "Robotique et automatique 2027",
            "organisation": "CNRS",
            "deadline": "2027-03-30",
            "opening_date": "2026-11-30",
            "amount_max": 220000,
            "currency": "EUR",
            "eligibility": "Roboticiens, automaticiens, informaticiens.",
            "eligible_applicants": ["instituts CNRS", "INRIA", "écoles d'ingénieurs", "universités"],
            "research_topics": ["robotique de service", "cobotique", "perception", "planification", "robotique adaptative"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "30 mars 2027"), Ent("OPENING_DATE", "30 novembre 2026"), Ent("AMOUNT", "220 000 €")],
    ),
    Example(  # NEW
        "ars-guadeloupe-2028", "test",
        "https://www.ars-guadeloupe.sante.fr/aaps/dengue-2028",
"""\
ARS Guadeloupe - Appel à projets : Maladies vectorielles 2028

L'ARS Guadeloupe lance l'appel à projets Maladies vectorielles 2028.

Ce programme finance la recherche sur les maladies transmises par les moustiques.

Date limite : 15 août 2028
Ouverture : 15 mai 2028
Montant maximal : 45 000 €
Durée maximale : 18 mois

Éligibilité : Entomologistes, virologues, épidémiologistes.
Institutions : instituts de recherche, CHU, universités, associations.

Thématiques : dengue, chikungunya, zika, lutte antivectorielle, moustiques.

Contact : vectorielle@ars-guadeloupe.fr""",
        {
            "title": "Maladies vectorielles 2028",
            "organisation": "ARS Guadeloupe",
            "deadline": "2028-08-15",
            "opening_date": "2028-05-15",
            "amount_max": 45000,
            "currency": "EUR",
            "eligibility": "Entomologistes, virologues, épidémiologistes.",
            "eligible_applicants": ["instituts de recherche", "CHU", "universités", "associations"],
            "research_topics": ["dengue", "chikungunya", "zika", "lutte antivectorielle", "moustiques"],
            "geographical_scope": "Guadeloupe",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "15 août 2028"), Ent("OPENING_DATE", "15 mai 2028"), Ent("AMOUNT", "45 000 €")],
    ),
    Example(  # NEW
        "inserm-cardiologie-2028", "train",
        "https://www.inserm.fr/appels-a-projets/cardiologie2028",
"""\
Inserm - Appel à projets : Cardiologie fondamentale 2028

L'Inserm lance l'appel à projets Cardiologie fondamentale 2028.

Ce programme finance la recherche sur les mécanismes des maladies cardiaques.

Date limite : 30 octobre 2028
Ouverture : 1er juillet 2028
Montant maximal : 300 000 €
Durée maximale : 36 mois

Éligibilité : Cardiologues, biophysiciens, généticiens.
Institutions : unités Inserm, CHU, universités.

Thématiques : cardiomyopathies, canaux ioniques, régénération cardiaque, imagerie cardiaque.

Contact : cardio@inserm.fr""",
        {
            "title": "Cardiologie fondamentale 2028",
            "organisation": "Inserm",
            "deadline": "2028-10-30",
            "opening_date": "2028-07-01",
            "amount_max": 300000,
            "currency": "EUR",
            "eligibility": "Cardiologues, biophysiciens, généticiens.",
            "eligible_applicants": ["unités Inserm", "CHU", "universités"],
            "research_topics": ["cardiomyopathies", "canaux ioniques", "régénération cardiaque", "imagerie cardiaque"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "30 octobre 2028"), Ent("OPENING_DATE", "1er juillet 2028"), Ent("AMOUNT", "300 000 €")],
    ),
    Example(  # NEW
        "fondation-arc-prison-2027", "train",
        "https://www.fondation-arc.org/appel-a-projets/solidarite-2027",
"""\
Fondation ARC - Appel à projets : Cancérologie et précarité 2027

La Fondation ARC lance l'appel à projets Cancérologie et précarité 2027.

Ce programme finance la recherche sur l'accès aux soins des personnes précaires.

Date limite : 1er avril 2027
Ouverture : 1er janvier 2027
Montant maximal : 90 000 €
Durée maximale : 24 mois

Éligibilité : Épidémiologistes sociaux, psychologues, sociologues.
Institutions : centres de recherche, CHU, associations.

Thématiques : inégalités d'accès, précarité, littératie en santé, dépistage, populations vulnérables.

Contact : precarite@fondation-arc.org""",
        {
            "title": "Cancérologie et précarité 2027",
            "organisation": "Fondation ARC",
            "deadline": "2027-04-01",
            "opening_date": "2027-01-01",
            "amount_max": 90000,
            "currency": "EUR",
            "eligibility": "Épidémiologistes sociaux, psychologues, sociologues.",
            "eligible_applicants": ["centres de recherche", "CHU", "associations"],
            "research_topics": ["inégalités d'accès", "précarité", "littératie en santé", "dépistage", "populations vulnérables"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "1er avril 2027"), Ent("OPENING_DATE", "1er janvier 2027"), Ent("AMOUNT", "90 000 €")],
    ),
    Example(  # NEW
        "anr-relance-2027", "test",
        "https://anr.fr/fr/les-appels-a-projets/compactage-2027.html",
"""\
Appel à projets : AAP Entreprises et territoires 2027

L'ANR lance l'appel à projets Entreprises et territoires 2027.

Ce programme finance la recherche sur les dynamiques entrepreneuriales et territoriales.

Date limite : 10 avril 2027
Ouverture : 10 janvier 2027
Montant maximal : 200 000 €
Durée maximale : 36 mois

Éligibilité : Économistes, gestionnaires, géographes.
Institutions : universités, écoles de commerce, CNRS.

Thématiques : écosystèmes d'innovation, entrepreneuriat, PME, territoires, relocalisation.

Contact : entreprise@anr.fr""",
        {
            "title": "AAP Entreprises et territoires 2027",
            "organisation": "ANR",
            "deadline": "2027-04-10",
            "opening_date": "2027-01-10",
            "amount_max": 200000,
            "currency": "EUR",
            "eligibility": "Économistes, gestionnaires, géographes.",
            "eligible_applicants": ["universités", "écoles de commerce", "CNRS"],
            "research_topics": ["écosystèmes d'innovation", "entrepreneuriat", "PME", "territoires", "relocalisation"],
            "geographical_scope": "France",
            "funding_type": "subvention",
        },
        [Ent("DEADLINE", "10 avril 2027"), Ent("OPENING_DATE", "10 janvier 2027"), Ent("AMOUNT", "200 000 €")],
    ),
]


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        for ex in EXAMPLES:
            fh.write(json.dumps(ex.to_dict(), ensure_ascii=False))
            fh.write("\n")

    # Validation: every entity span must be found exactly at its computed offset.
    missing = []
    for ex in EXAMPLES:
        for ent in ex.entity_annotations:
            span = ex.text[ent["start"]:ent["end"]]
            if span != ent["text"]:
                missing.append((ex.id, ent["label"], ent["text"], span))
    if missing:
        raise SystemExit(f"Entity offset mismatch:\n{missing}")

    ids = [ex.id for ex in EXAMPLES]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        raise SystemExit(f"Duplicate ids: {dup}")

    print(f"Wrote {len(EXAMPLES)} examples to {OUT}")
    print("  split test:", sum(1 for e in EXAMPLES if e.split == "test"))
    print("  split train:", sum(1 for e in EXAMPLES if e.split == "train"))


if __name__ == "__main__":
    main()
