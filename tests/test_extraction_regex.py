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
