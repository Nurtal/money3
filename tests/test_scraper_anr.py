from aap_watcher.scrapers.anr import ANRScraper

ANR_FIXTURE = """
<html><body>
<h2>
  <a href="https://anr.fr/fr/detail/call/aapg-appel-a-projets-generique-2027/">
    AAPG - Appel à projets générique 2027</a>
</h2>
<h2>
  <a href="https://anr.fr/fr/detail/call/ia-sante-2028/">IA en santé 2028</a>
</h2>
</body></html>
"""


def test_discovers_one_document_per_header():
    docs = list(ANRScraper().discover(html=ANR_FIXTURE))
    assert len(docs) == 2
    assert docs[0].source_url == "https://anr.fr/fr/detail/call/aapg-appel-a-projets-generique-2027/"
    assert "Appel à projets générique 2027" in docs[0].text
