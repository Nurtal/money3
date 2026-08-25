from aap_watcher.scrapers.sources import available_sources, get_source
from aap_watcher.scrapers.sources_catalog import (
    ARSScraper,
    FRMScraper,
    FondationARCScraper,
    FondationDeFranceScraper,
    INCaScraper,
    LigueContreLeCancerScraper,
)

_BLOCK = """
<html><body>
<article>
  <h2>Appel à projets : {name} 2027</h2>
  <p>Date limite : 15 octobre 2026. Montant maximum : 200 000 €.</p>
  <a href="https://example.org/{key}/details">Détails</a>
</article>
<article>
  <h2>Appel à projets : {name} santé 2028</h2>
  <p>Date limite : 03 mai 2028.</p>
  <a href="https://example.org/{key}/sante-2028">Détails</a>
</article>
</body></html>
"""

SOURCES_UNDER_TEST = {
    "inca": (INCaScraper, "INCa"),
    "ars": (ARSScraper, "ARS"),
    "fondation_arc": (FondationARCScraper, "ARC"),
    "frm": (FRMScraper, "FRM"),
    "ligue_cancer": (LigueContreLeCancerScraper, "Ligue"),
    "fondation_france": (FondationDeFranceScraper, "Fondation de France"),
}


def test_registry_contains_all_sources():
    names = available_sources()
    for key in SOURCES_UNDER_TEST:
        assert key in names
    assert "anr" in names


def test_each_source_discovers_documents_offline():
    for key, (scraper_cls, label) in SOURCES_UNDER_TEST.items():
        html = _BLOCK.format(name=label, key=key)
        docs = list(scraper_cls().discover(html=html))
        assert len(docs) == 2, key
        assert docs[0].source_url.endswith("/details"), key
        assert label in docs[0].text, key


def test_get_source_returns_configured_adapter():
    scraper = get_source("inca")
    assert isinstance(scraper, INCaScraper)
    assert scraper.source_name == "inca"
