from aap_watcher.scrapers.anr import ANRScraper

ANR_FIXTURE = """
<html><body>
<article>
  <h2>Appel à projets : Programme Cancer 2027</h2>
  <p>Date limite : 15 octobre 2026. Montant maximum : 500 000 €.</p>
  <a href="https://anr.fr/AAP/cancer-2027">Détails</a>
</article>
<article>
  <h2>Appel à projets : IA en santé 2028</h2>
  <p>Date limite : 03 mai 2028.</p>
  <a href="https://anr.fr/AAP/ia-sante-2028">Détails</a>
</article>
</body></html>
"""


def test_discovers_one_document_per_article():
    docs = list(ANRScraper().discover(html=ANR_FIXTURE))
    assert len(docs) == 2
    assert docs[0].source_url == "https://anr.fr/AAP/cancer-2027"
    assert "Programme Cancer 2027" in docs[0].text
