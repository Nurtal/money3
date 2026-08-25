import pytest
from sqlalchemy import create_engine

from aap_watcher.benchmark.regression import detect_regressions, result_to_dict, save_results, load_results
from aap_watcher.database.models import Base, make_session_factory
from aap_watcher.database.repository import Repository
from aap_watcher.schema import AAPExtraction, AAPStatus, Provenance


def _ext(title="X", deadline=None, amount=100000, text="", status=AAPStatus.UNKNOWN):
    prov = Provenance(source_url="https://anr.fr/AAP/x", source_text=text, extraction_method="regex")
    return AAPExtraction(title=title, deadline=deadline, amount_max=amount,
                         currency="EUR", status=status, source_url="https://anr.fr/AAP/x",
                         provenance=prov)


@pytest.fixture
def repo(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path/'m.db'}")
    sf = make_session_factory(engine)
    r = Repository(sf)
    r.init_db(engine)
    return r


def test_new_then_unchanged(repo):
    ev1 = repo.save_aap(_ext(deadline="2026-10-15"))
    assert ev1.type == "new" and ev1.version == 1
    ev2 = repo.save_aap(_ext(deadline="2026-10-15"))
    assert ev2.type == "unchanged"


def test_deadline_change_detected(repo):
    repo.save_aap(_ext(deadline="2026-10-15"))
    ev = repo.save_aap(_ext(deadline="2026-12-01"))
    assert ev.type == "deadline_changed"
    assert ev.version == 2


def test_modified_detected(repo):
    repo.save_aap(_ext(title="A", deadline="2026-10-15"))
    ev = repo.save_aap(_ext(title="B", deadline="2026-10-15"))
    assert ev.type == "modified"
    assert ev.version == 2


def test_cancelled_detected(repo):
    repo.save_aap(_ext(title="A", deadline="2026-10-15"))
    ev = repo.save_aap(_ext(title="A", deadline="2026-10-15", text="Cet appel est annule."))
    assert ev.type == "cancelled"
    hist = repo.history("https://anr.fr/aap/x")
    assert hist[-1].status == "cancelled"


def test_history_preserved(repo):
    repo.save_aap(_ext(deadline="2026-10-15"))
    repo.save_aap(_ext(deadline="2026-12-01"))
    assert len(repo.history("https://anr.fr/aap/x")) == 2


def test_regression_detection():
    before = {"extractors": [{"name": "regex", "f1": 0.90, "recall": 0.90, "latency_ms": 1.0}]}
    after = {"extractors": [{"name": "regex", "f1": 0.85, "recall": 0.80, "latency_ms": 1.5}]}
    regs = detect_regressions(before, after)
    kinds = {r.metric for r in regs}
    assert "f1" in kinds
    assert "recall" in kinds
    assert "latency_ms" in kinds


def test_no_regression_when_stable():
    d = {"extractors": [{"name": "regex", "f1": 0.90, "recall": 0.90, "latency_ms": 1.0}]}
    assert detect_regressions(d, d) == []


def test_serialization_roundtrip(tmp_path):
    class FakeResult:
        n_examples = 2
        results = []

    save_results(FakeResult(), tmp_path / "r.json")
    loaded = load_results(tmp_path / "r.json")
    assert loaded["n_examples"] == 2
