import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from aap_watcher.api import create_app
from aap_watcher.database.models import make_session_factory
from aap_watcher.database.repository import Repository
from aap_watcher.schema import AAPExtraction, AAPStatus, Provenance


def _prov(url):
    return Provenance(source_url=url, extraction_method="regex")


def _seed(tmp_path):
    db = tmp_path / "api.db"
    url = f"sqlite:///{db}"
    engine = create_engine(url)
    sf = make_session_factory(engine)
    repo = Repository(sf)
    repo.init_db(engine)
    repo.save_aap(AAPExtraction(
        title="Cancer X", organisation="ANR", research_topics=["cancer"],
        deadline="2026-10-15", amount_max=500000, amount_min=100000, currency="EUR",
        funding_type="grant", eligible_applicants=["Universities"],
        geographical_scope="France", status=AAPStatus.OPEN,
        source_url="u1", provenance=_prov("u1")))
    repo.save_aap(AAPExtraction(
        title="Cancer Y", organisation="ANR", research_topics=["cancer", "immunology"],
        deadline="2026-11-01", amount_max=300000, amount_min=50000, currency="EUR",
        funding_type="fellowship", eligible_applicants=["SMEs", "Universities"],
        geographical_scope="Europe", status=AAPStatus.OPEN,
        source_url="u2", provenance=_prov("u2")))
    return url


@pytest.fixture
def client(tmp_path):
    url = _seed(tmp_path)
    app = create_app(url)
    with TestClient(app) as c:
        yield c


def test_full_text_search(client):
    r = client.get("/api/aaps", params={"q": "cancer"})
    assert r.status_code == 200
    assert r.json()["total"] == 2


def test_topic_filter(client):
    r = client.get("/api/aaps", params={"topic": "immunology"})
    assert r.json()["total"] == 1


def test_deadline_filter(client):
    r = client.get("/api/aaps", params={"deadline_before": "2026-10-20"})
    assert r.json()["total"] == 1


def test_amount_filter(client):
    r = client.get("/api/aaps", params={"amount_min": 400000})
    assert r.json()["total"] == 1


def test_status_filter(client):
    r = client.get("/api/aaps", params={"status": "open"})
    assert r.json()["total"] == 2


def test_get_by_id(client):
    r = client.get("/api/aaps/1")
    assert r.status_code == 200
    assert r.json()["title"] == "Cancer X"


def test_get_missing_returns_404(client):
    assert client.get("/api/aaps/999").status_code == 404


def test_similar_endpoint(client):
    r = client.get("/api/aaps/1/similar")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1
    assert items[0]["title"] == "Cancer Y"
    assert items[0]["similarity"] > 0


def test_sources_endpoint(client):
    r = client.get("/api/sources")
    assert "anr" in r.json()


def test_root_serves_html(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "AAP Watcher" in r.text


def test_pagination_metadata(client):
    r = client.get("/api/aaps", params={"limit": 1, "offset": 0})
    j = r.json()
    assert j["total"] == 2
    assert j["limit"] == 1
    assert j["offset"] == 0
    assert len(j["items"]) == 1


def test_multi_term_search_is_and(client):
    r = client.get("/api/aaps", params={"q": "cancer immunology"})
    assert r.json()["total"] == 1

    r = client.get("/api/aaps", params={"q": "cancer"})
    assert r.json()["total"] == 2


def test_funding_type_filter(client):
    r = client.get("/api/aaps", params={"funding_type": "fellowship"})
    assert r.json()["total"] == 1


def test_eligible_applicants_filter(client):
    r = client.get("/api/aaps", params={"eligible_applicants": "sme"})
    assert r.json()["total"] == 1


def test_geographical_scope_filter(client):
    r = client.get("/api/aaps", params={"geographical_scope": "France"})
    assert r.json()["total"] == 1


def test_deadline_after_filter(client):
    r = client.get("/api/aaps", params={"deadline_after": "2026-10-20"})
    assert r.json()["total"] == 1


def test_amount_max_filter(client):
    r = client.get("/api/aaps", params={"amount_max": 75000})
    assert r.json()["total"] == 1


def test_sort_deadline_desc(client):
    r = client.get("/api/aaps", params={"sort": "deadline_desc"})
    items = r.json()["items"]
    assert items[0]["title"] == "Cancer Y"


def test_sort_amount_desc(client):
    r = client.get("/api/aaps", params={"sort": "amount_desc"})
    items = r.json()["items"]
    assert items[0]["title"] == "Cancer X"


def test_disclaimer_present(client):
    assert "disclaimer" in client.get("/api/aaps/1").json()
    assert "disclaimer" in client.get("/api/aaps", params={"q": "cancer"}).json()["items"][0]
