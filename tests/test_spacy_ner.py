import pytest

from aap_watcher.extraction.base import Document
from aap_watcher.extraction.registry import available_extractor_names, available_extractors

try:
    from aap_watcher.extraction.spacy_ner import SpacyNerExtractor

    SPACY_AVAILABLE = True
except Exception:  # noqa: BLE001 - exercised only when spacy missing  # pragma: no cover
    SPACY_AVAILABLE = False


TEXT = """
Appel à projets : Programme Intelligence Artificielle 2027

L'ANR lance l'appel à projets dédié à l'intelligence artificielle.
Ce programme vise à soutenir la recherche en IA.
Date limite : 15 octobre 2026
Montant maximum : 500 000 €
Candidats éligibles : Les universités et les laboratoires peuvent candidater.
"""

pytestmark = pytest.mark.skipif(
    not SPACY_AVAILABLE, reason="spaCy not installed"
)


def _doc():
    return Document(text=TEXT, source_url="https://anr.fr/AAP/1")


def test_spacy_extracts_organisation_and_deadline():
    ex = SpacyNerExtractor().extract(_doc())
    # Organisation comes from the shared gazetteer (announcer detection).
    assert ex.organisation == "ANR"
    # Deadline falls back to the shared regex date strategies when NER misses it.
    assert ex.deadline == "2026-10-15"


def test_spacy_registered_when_available():
    names = available_extractor_names()
    assert "spacy_ner" in names


def test_spacy_in_benchmark_without_crash():
    extractors = available_extractors()
    spacy_ex = [e for e in extractors if getattr(e, "name", "") == "spacy_ner"]
    assert len(spacy_ex) == 1
    from aap_watcher.schema import AAPExtraction

    out = spacy_ex[0].extract(_doc())
    assert isinstance(out, AAPExtraction)
    assert out.extraction_method == "spacy_ner"
