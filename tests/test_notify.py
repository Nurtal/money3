import smtplib
from email.message import EmailMessage
from typing import ClassVar

import pytest

from aap_watcher.database.models import make_session_factory
from aap_watcher.database.repository import Repository
from aap_watcher.notify.base import ChangeNotice
from aap_watcher.notify.email import EmailNotifier
from aap_watcher.schema import AAPExtraction, AAPStatus, Provenance


def _plain_text(msg):
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            return part.get_payload(decode=True).decode()
    return ""


class FakeSMTP:
    """In-memory SMTP double that records the last sent message."""

    sent: ClassVar[list[EmailMessage]] = []
    instances: ClassVar[int] = 0

    def __init__(self, host, port=None, *args, **kwargs):
        self.host = host
        self.port = port
        FakeSMTP.instances += 1
        self.ehlo_called = False
        self._closed = False

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def ehlo(self):
        self.ehlo_called = True

    def starttls(self):
        self.ehlo_called = True

    def login(self, user, password):
        pass

    def send_message(self, msg):
        FakeSMTP.sent.append(msg)

    def close(self):
        self._closed = True


def _notice(**kw):
    defaults = {
        "type": "new", "key": "https://anr.fr/aap/x", "version": 1,
        "title": "Cancer X", "organisation": "ANR", "deadline": "2026-10-15",
        "application_url": "https://anr.fr/aap/x", "source_url": "https://anr.fr/aap/x",
        "status": "open",
    }
    defaults.update(kw)
    return ChangeNotice(**defaults)


def _notifier(**kw):
    defaults = {"host": "smtp.test", "port": 587, "user": "user", "password": "pw",
                "from_addr": "noreply@test", "to_addrs": ["me@test"]}
    defaults.update(kw)
    return EmailNotifier(**defaults)


@pytest.fixture(autouse=True)
def _reset_fake():
    FakeSMTP.sent = []
    FakeSMTP.instances = 0
    yield


def test_send_builds_and_delivers_email(monkeypatch):
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    n = _notifier(starttls=True)
    n.send([_notice()])
    assert len(FakeSMTP.sent) == 1
    msg = FakeSMTP.sent[0]
    assert msg["From"] == "noreply@test"
    assert msg["To"] == "me@test"
    assert "Cancer X" in _plain_text(msg)


def test_send_multiple_change_types(monkeypatch):
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    n = _notifier()
    n.send([_notice(type="new"), _notice(type="deadline_changed", title="Cancer Y")])
    body = _plain_text(FakeSMTP.sent[0])
    assert "Nouvel appel" in body
    assert "Date limite modifiée" in body
    assert "Cancer Y" in body


def test_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv("AAP_SMTP_HOST", "smtp.example")
    monkeypatch.setenv("AAP_SMTP_PORT", "2525")
    monkeypatch.setenv("AAP_SMTP_USER", "u")
    monkeypatch.setenv("AAP_SMTP_PASSWORD", "p")
    monkeypatch.setenv("AAP_SMTP_FROM", "from@x")
    monkeypatch.setenv("AAP_NOTIFY_TO", "a@x,b@x")
    n = EmailNotifier.from_env()
    assert n.host == "smtp.example"
    assert n.port == 2525
    assert n.to_addrs == ["a@x", "b@x"]


def test_from_env_requires_host_and_to(monkeypatch):
    for var in ("AAP_SMTP_HOST", "AAP_SMTP_USER", "AAP_SMTP_PASSWORD",
                "AAP_SMTP_FROM", "AAP_NOTIFY_TO"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(ValueError):
        EmailNotifier.from_env()


def _ext(**kw):
    prov = Provenance(source_url="https://anr.fr/AAP/x", extraction_method="regex")
    defaults = {
        "title": "Cancer X", "organisation": "ANR", "deadline": "2026-10-15",
        "amount_max": 500000, "currency": "EUR", "status": AAPStatus.OPEN,
        "source_url": "https://anr.fr/AAP/x", "provenance": prov,
    }
    defaults.update(kw)
    return AAPExtraction(**defaults)


@pytest.fixture
def repo(tmp_path):
    from sqlalchemy import create_engine

    db = create_engine(f"sqlite:///{tmp_path/'n.db'}")
    sf = make_session_factory(db)
    r = Repository(sf)
    r.init_db(db)
    return r


def test_notification_dedup(repo):
    ev = repo.save_aap(_ext())
    assert ev.type == "new"
    assert not repo.was_notified(ev.key, ev.version)
    repo.mark_notified(ev.key, ev.version)
    assert repo.was_notified(ev.key, ev.version)


def test_repository_notification_roundtrip(repo):
    ev1 = repo.save_aap(_ext())
    repo.save_aap(_ext())
    ev3 = repo.save_aap(_ext(deadline="2026-12-01"))
    assert ev3.type == "deadline_changed"
    repo.mark_notified(ev1.key, ev1.version)
    assert repo.was_notified(ev1.key, ev1.version)
    assert not repo.was_notified(ev3.key, ev3.version)


def test_notifier_and_repo_integration(repo, monkeypatch):
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    ev = repo.save_aap(_ext())
    rec = repo.latest(ev.key)
    n = _notifier()
    notice = ChangeNotice(
        type=ev.type, key=ev.key, version=ev.version,
        title=rec.title, organisation=rec.organisation, deadline=rec.deadline,
        status=rec.status, application_url=rec.application_url, source_url=rec.source_url,
    )
    n.send([notice])
    assert len(FakeSMTP.sent) == 1
    body = _plain_text(FakeSMTP.sent[0])
    assert notice.title and notice.title in body
    repo.mark_notified(ev.key, ev.version, ev.type)
    assert repo.was_notified(ev.key, ev.version)
