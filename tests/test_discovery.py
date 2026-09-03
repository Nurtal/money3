import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from aap_watcher.api import create_app
from aap_watcher.database.models import make_session_factory
from aap_watcher.database.repository import Repository
from aap_watcher.discovery.scoring import Matchable, rank, score
from aap_watcher.schema import AAPExtraction, AAPStatus, Provenance


def _prov(url):
    return Provenance(source_url=url, extraction_method="regex")


def _matchable(title="X", topics=("cancer",), amount_max=500000, geo="France"):
    return Matchable(
        title=title, topics=list(topics), amount_max=amount_max,
        geographical_scope=geo, status=AAPStatus.OPEN.value,
    )


def test_score_perfect_match_is_high():
    s = score(research_topics=["cancer", "immunology"], geographies=["France"], amount_min=100000,
              item=_matchable(topics=["cancer", "immunology"], amount_max=500000, geo="France"))
    assert s >= 90


def test_score_wrong_topic_is_low():
    s = score(research_topics=["immunology"], geographies=["France"], amount_min=100000,
              item=_matchable(topics=["cancer"], amount_max=500000, geo="France"))
    assert s < 50


def test_amount_bonus():
    s_big = score(research_topics=["cancer"], geographies=[], amount_min=400000,
                  item=_matchable(amount_max=500000))
    s_small = score(research_topics=["cancer"], geographies=[], amount_min=400000,
                    item=_matchable(amount_max=50000))
    assert s_big > s_small


def test_geography_contributes():
    s_match = score(research_topics=["cancer"], geographies=["France"], amount_min=None,
                    item=_matchable(geo="France, Europe"))
    s_miss = score(research_topics=["cancer"], geographies=["France"], amount_min=None,
                   item=_matchable(geo="Europe"))
    assert s_match > s_miss


def test_rank_orders_by_score_desc():
    items = [_matchable(title="Low", topics=["theology"]),
             _matchable(title="High", topics=["cancer"])]
    ranked = rank(research_topics=["cancer"], item_pool=items)
    assert ranked[0][1] >= ranked[1][1]
    assert ranked[0][0].title == "High"


def test_case_insensitive_topics():
    upper = score(research_topics=["Cancer"], item=_matchable(topics=["cancer"]))
    lower = score(research_topics=["cancer"], item=_matchable(topics=["cancer"]))
    assert upper == lower
    assert upper > 50


def _seed(tmp_path):
    db = tmp_path / "d.db"
    url = f"sqlite:///{db}"
    engine = create_engine(url)
    sf = make_session_factory(engine)
    repo = Repository(sf)
    repo.init_db(engine)
    repo.save_aap(AAPExtraction(
        title="Cancer AI", organisation="ANR", research_topics=["cancer", "ai"],
        amount_max=500000, currency="EUR", geographical_scope="France",
        status=AAPStatus.OPEN, source_url="u1", provenance=_prov("u1")))
    repo.save_aap(AAPExtraction(
        title="Theology", organisation="CNRS", research_topics=["theology"],
        amount_max=50000, currency="EUR", geographical_scope="Germany",
        status=AAPStatus.OPEN, source_url="u2", provenance=_prov("u2")))
    return url


@pytest.fixture
def client(tmp_path):
    app = create_app(_seed(tmp_path))
    with TestClient(app) as c:
        yield c


def test_profile_matches_endpoint(client):
    r = client.get("/api/profile/matches", params={"topics": "cancer,ai", "amount_min": 100000})
    assert r.status_code == 200
    items = r.json()["items"]
    assert items[0]["title"] == "Cancer AI"
    assert items[0]["relevance"] > items[1]["relevance"]


def test_profile_matches_respects_geography(client):
    r = client.get("/api/profile/matches", params={"topics": "cancer", "geographies": "france"})
    assert r.status_code == 200
    assert r.json()["items"][0]["title"] == "Cancer AI"
