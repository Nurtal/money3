import pytest
from sqlalchemy import create_engine

from aap_watcher.database.models import Base, make_session_factory
from aap_watcher.database.repository import Repository
from aap_watcher.extraction.base import Document
from aap_watcher.extraction.regex import RegexExtractor
from aap_watcher.pipeline.run import run_once
from aap_watcher.scrapers.anr import ANRScraper


@pytest.fixture
def repo(tmp_path):
    db = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db}")
    sf = make_session_factory(engine)
    r = Repository(sf)
    r.init_db(engine)
    return r


def test_deduplication_on_repeat_run(repo):
    html = """
    <h2><a href="https://anr.fr/AAP/unique">Appel à projets : Unique 2027</a></h2>
    <p>Date limite : 15 octobre 2026. Montant maximum : 100 000 €.</p>
    """
    scraper = ANRScraper()
    extractor = RegexExtractor()

    first = run_once(scraper, extractor, repo, html=html)
    second = run_once(scraper, extractor, repo, html=html)

    assert first["new"] == 1
    assert second["new"] == 0
    assert repo.exists("https://anr.fr/aap/unique")


def test_raw_source_stored(repo):
    html = """
    <h2><a href="https://anr.fr/AAP/unique">Appel à projets : Unique 2027</a></h2>
    <p>Date limite : 15 octobre 2026.</p>
    """
    run_once(ANRScraper(), RegexExtractor(), repo, html=html)
    from aap_watcher.database.models import RawDocument
    from sqlalchemy import select

    with repo._sf() as s:
        rows = s.scalars(select(RawDocument)).all()
    assert len(rows) == 1
    assert "Unique 2027" in rows[0].body
