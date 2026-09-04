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


# The 9 source organisations added to broaden the corpus must be recognised by
# the regex extractor (abbreviation or full name), and scope to France.
_NEW_ORGS = [
    ("Inria", "L'Inria lance un appel à projets sur l'apprentissage."),
    ("Inrae", "L'Inrae lance un appel à projets en agroécologie."),
    ("Bettencourt", "La Fondation Bettencourt Schueller soutient un prix."),
    ("BPI", "Bpifrance lance un appel à projets deep tech."),
    ("Institut Pasteur", "L'Institut Pasteur lance un appel sur la microbiologie."),
    ("ADEME", "L'ADEME lance un appel à projets sur la décarbonation."),
    ("AFM-Téléthon", "L'AFM-Téléthon lance un appel sur les maladies rares."),
    ("ANSM", "L'ANSM lance un appel à projets en pharmacovigilance."),
    ("Fondation pour la Recherche sur Alzheimer", "La Fondation pour la Recherche sur Alzheimer lance un appel."),
]


def test_new_orgs_detected_and_scope_france():
    for expected, body in _NEW_ORGS:
        ex = RegexExtractor().extract(Document(text=body))
        assert ex.organisation == expected, f"{expected}: got {ex.organisation!r}"
        assert ex.geographical_scope == "France", expected


HORIZON_CODE = """
Horizon Europe - Appel à projets : Santé 2028

La Commission européenne lance l'appel à projets HEALTH-2028 dans le cadre d'Horizon Europe.
"""


def test_title_prefers_official_call_code():
    ex = RegexExtractor().extract(Document(text=HORIZON_CODE))
    assert ex.title == "HEALTH-2028"


# ---------------------------------------------------------------------------
# amount_min: range parsing
# ---------------------------------------------------------------------------

AMOUNT_RANGE_DE_A = """
Appel à projets : Matériaux 2029

Budget : De 50 000 € à 400 000 €.
"""


def test_amount_min_from_de_a_range():
    ex = RegexExtractor().extract(Document(text=AMOUNT_RANGE_DE_A))
    assert ex.amount_min == 50000
    assert ex.amount_max == 400000


AMOUNT_RANGE_ENTRE = """
Appel à projets : Énergie 2029

Financement : Entre 100 000 et 500 000 EUR.
"""


def test_amount_min_from_entre_et_range():
    ex = RegexExtractor().extract(Document(text=AMOUNT_RANGE_ENTRE))
    assert ex.amount_min == 100000
    assert ex.amount_max == 500000


AMOUNT_RANGE_MONTANT = """
Appel à projets : Climat 2029

Montant : 3 000 000 à 5 000 000 €.
"""


def test_amount_min_from_montant_a_range():
    ex = RegexExtractor().extract(Document(text=AMOUNT_RANGE_MONTANT))
    assert ex.amount_min == 3000000
    assert ex.amount_max == 5000000


AMOUNT_NO_MIN = """
Appel à projets : Santé 2029

Montant maximal : 200 000 €.
"""


def test_amount_min_none_when_no_range():
    ex = RegexExtractor().extract(Document(text=AMOUNT_NO_MIN))
    assert ex.amount_min is None


# ---------------------------------------------------------------------------
# status detection integration
# ---------------------------------------------------------------------------


def test_regex_detects_status_open():
    ex = RegexExtractor().extract(Document(text="Appel ouvert. Montant : 100 000 €."))
    assert ex.status == "open"


def test_regex_detects_status_closed():
    ex = RegexExtractor().extract(Document(text="Ce appel est clôturé."))
    assert ex.status == "closed"


def test_regex_detects_status_cancelled():
    ex = RegexExtractor().extract(Document(text="Appel annulé par l'organisme."))
    assert ex.status == "cancelled"


def test_regex_status_unknown_when_no_marker():
    ex = RegexExtractor().extract(Document(text="L'appel finance la recherche en physique."))
    assert ex.status == "unknown"



