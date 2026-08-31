from aap_watcher.extraction.base import Document
from aap_watcher.extraction.regex import RegexExtractor

TEXT = """
Appel à projets : Programme Cancer 2027

Date limite : 15 octobre 2026
Montant maximum : 500 000 €

Candidats éligibles : Les universités, les laboratoires et les CHU peuvent candidater.
"""


def test_extracts_title():
    ex = RegexExtractor().extract(Document(text=TEXT, source_url="https://anr.fr/1"))
    assert ex.title == "Programme Cancer 2027"


def test_extracts_french_deadline():
    ex = RegexExtractor().extract(Document(text=TEXT))
    assert ex.deadline == "2026-10-15"


def test_extracts_amount_and_currency():
    ex = RegexExtractor().extract(Document(text=TEXT))
    assert ex.amount_max == 500000
    assert ex.currency == "EUR"


def test_extracts_eligibility():
    ex = RegexExtractor().extract(Document(text=TEXT))
    assert ex.eligibility
    assert "universités" in ex.eligibility


def test_provenance_recorded():
    ex = RegexExtractor().extract(Document(text=TEXT, source_url="https://anr.fr/1"))
    assert ex.provenance is not None
    assert ex.provenance.extraction_method == "regex"
    assert ex.provenance.source_url == "https://anr.fr/1"


ANR_ANNONCER = """
Appel à projets : AAP Matière condensée 2027

L'Agence nationale de la recherche finance la recherche en physique de la matière condensée.

Éligibilité : Physiciens, chimistes des matériaux.
Institutions éligibles : universités, CNRS, CEA, écoles d'ingénieurs.
"""


def test_org_prefers_announcer_over_partner_in_eligibility():
    ex = RegexExtractor().extract(Document(text=ANR_ANNONCER))
    # The issuing org (full name in the opening sentence) wins over CNRS which
    # only appears in the eligibility line.
    assert ex.organisation == "ANR"


FRM_ANNONCER = """
Fondation pour la Recherche Médicale - Appel à projets : Recherche fondamentale 2028

La FRM lance l'appel à projets Recherche fondamentale 2028.

Institutions : universités, INSERM, CNRS, hôpitaux.
"""


def test_org_prefers_announcer_abbreviation():
    ex = RegexExtractor().extract(Document(text=FRM_ANNONCER))
    assert ex.organisation == "FRM"


ARS_PACA = """
ARS PACA - Appel à projets : Antibiorésistance 2028

L'ARS PACA lance un appel à projets sur l'antibiorésistance.
"""


def test_org_keeps_regional_qualifier_paca():
    ex = RegexExtractor().extract(Document(text=ARS_PACA))
    assert ex.organisation == "ARS PACA"


DISTRACTOR_AMOUNT = """
Appel à projets : Énergie solaire 2029

Un appel voisin (2026) finançait à hauteur de 150 000 €.

Montant maximal : EUR 350 000

L'appel parallèle octroyait 150 000 €.
"""


def test_amount_prefers_value_right_after_label_over_distractor():
    ex = RegexExtractor().extract(Document(text=DISTRACTOR_AMOUNT))
    assert ex.amount_max == 350000


RECURRING_AMOUNT = """
INCa - Bourses de thèse 2027

L'INCa offre des bourses de thèse en cancérologie.

Montant : 22 000 € par an pendant 3 ans
"""


def test_amount_sums_annual_grant_over_duration():
    ex = RegexExtractor().extract(Document(text=RECURRING_AMOUNT))
    assert ex.amount_max == 66000


CHU_LYON = """
CHU de Lyon - Appel à projets : Recherche en soins 2027

Le CHU de Lyon lance un appel à projets de recherche paramédicale.
"""

ARS_PROVENCE = """
ARS Provence-Alpes-Côte d'Azur - Appel à projets : Antibiorésistance 2028

L'ARS PACA lance un appel à projets sur l'antibiorésistance.
"""


def test_scope_derived_from_regional_ars():
    ex = RegexExtractor().extract(Document(text=ARS_PROVENCE))
    # The announcer sentence names "ARS PACA", which the gold scopes to PACA.
    assert ex.geographical_scope == "PACA"


def test_scope_defaults_to_france_for_national_org():
    ex = RegexExtractor().extract(Document(text=RECURRING_AMOUNT))
    assert ex.geographical_scope == "France"


def test_chu_defaults_to_france_scope():
    ex = RegexExtractor().extract(Document(text=CHU_LYON))
    assert ex.geographical_scope == "France"


HORIZON_CODE = """
Horizon Europe - Appel à projets : Santé 2028

La Commission européenne lance l'appel à projets HEALTH-2028 dans le cadre d'Horizon Europe.
"""


def test_title_prefers_official_call_code():
    ex = RegexExtractor().extract(Document(text=HORIZON_CODE))
    assert ex.title == "HEALTH-2028"





