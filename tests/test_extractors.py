from aap_watcher.extraction.base import Document
from aap_watcher.extraction.classical_nlp import ClassicalNLPExtractor
from aap_watcher.extraction.dictionary import DictionaryExtractor
from aap_watcher.extraction.hybrid import HybridExtractor
from aap_watcher.extraction.regex import RegexExtractor
from aap_watcher.extraction.registry import available_extractors, available_extractor_names

TEXT = """
Appel à projets : Programme Cancer 2027

Date limite : 15 octobre 2026
Montant maximum : 500 000 €

Cet appel est publié par l'ANR.
Candidats éligibles : Les universités, les laboratoires et les CHU peuvent candidater.
"""


def _doc():
    return Document(text=TEXT, source_url="https://anr.fr/AAP/1")


def test_dictionary_extracts_organisation_and_topics():
    ex = DictionaryExtractor().extract(_doc())
    assert ex.organisation in ("ANR", "Agence Nationale de la Recherche")
    assert "cancer" in ex.research_topics
    assert "universités" in ex.eligible_applicants
    assert ex.amount_max is None  # dictionary does not do amounts


_DICT_NEW_ORGS = [
    ("Inria", "Appel à projets Inria sur l'apprentissage."),
    ("Inrae", "Appel à projets Inrae en agroécologie."),
    ("Bettencourt", "Appel à projets Fondation Bettencourt Schueller."),
    ("BPI", "Appel à projets Bpifrance deep tech."),
    ("Institut Pasteur", "Appel à projets Institut Pasteur microbiologie."),
    ("ADEME", "Appel à projets ADEME décarbonation."),
    ("AFM-Téléthon", "Appel à projets AFM-Téléthon maladies rares."),
    ("ANSM", "Appel à projets ANSM pharmacovigilance."),
    ("Fondation pour la Recherche sur Alzheimer", "Appel à projets Fondation pour la Recherche sur Alzheimer."),
]


def test_dictionary_detects_new_orgs():
    for expected, body in _DICT_NEW_ORGS:
        ex = DictionaryExtractor().extract(Document(text=body))
        assert ex.organisation == expected, f"{expected}: got {ex.organisation!r}"


def test_classical_nlp_extracts_title_and_eligibility_sentence():
    ex = ClassicalNLPExtractor().extract(_doc())
    assert ex.title == "Programme Cancer 2027"
    assert ex.eligibility and "universités" in ex.eligibility


def test_hybrid_merges_strategies():
    ex = HybridExtractor().extract(_doc())
    # regex contributes dates/amounts, dictionary contributes topics/org
    assert ex.deadline == "2026-10-15"
    assert ex.amount_max == 500000
    assert "cancer" in ex.research_topics
    assert ex.organisation in ("ANR", "Agence Nationale de la Recherche")
    assert ex.extraction_method == "hybrid"


def test_registry_includes_core_extractors():
    names = available_extractor_names()
    assert {"regex", "dictionary", "classical_nlp", "hybrid"}.issubset(set(names))


def test_registry_skips_unavailable_deps():
    # Optional (spaCy/transformers/llm) may be absent; registry must not crash.
    extractors = available_extractors()
    assert len(extractors) >= 4
    for e in extractors:
        assert hasattr(e, "extract")


def test_dictionary_detects_status_open():
    ex = DictionaryExtractor().extract(Document(text="Appel ouvert. Candidatures ouvertes."))
    assert ex.status == "open"


def test_dictionary_detects_status_closed():
    ex = DictionaryExtractor().extract(Document(text="Ce appel est clôturé."))
    assert ex.status == "closed"


def test_dictionary_status_unknown_when_no_marker():
    ex = DictionaryExtractor().extract(Document(text="Financement recherche."))
    assert ex.status == "unknown"


def test_dictionary_expanded_topics():
    text = "Thématiques : biologie cellulaire, agronomie, cybersécurité."
    ex = DictionaryExtractor().extract(Document(text=text))
    topics = [t.lower() for t in ex.research_topics]
    assert "biologie cellulaire" in topics
    assert "agronomie" in topics
    assert "cybersécurité" in topics


def test_dictionary_expanded_applicants():
    text = "Candidats : CEA, MNHN, postdocs, organismes publics, hôpitaux universitaires."
    ex = DictionaryExtractor().extract(Document(text=text))
    applicants = [a.lower() for a in ex.eligible_applicants]
    assert "cea" in applicants
    assert "mnhn" in applicants
    assert "postdocs" in applicants
    assert "hôpitaux universitaires" in applicants
