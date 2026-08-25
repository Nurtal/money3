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
