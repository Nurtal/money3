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
