import pytest

from aap_watcher.schema import AAPExtraction, AAPStatus


def test_dedupe_key_uses_source_url():
    a = AAPExtraction(title="X", source_url="https://anr.fr/AAP/1/")
    b = AAPExtraction(title="X", source_url="https://anr.fr/AAP/1")
    assert a.dedupe_key() == b.dedupe_key()


def test_dedupe_key_falls_back_to_title_org():
    a = AAPExtraction(title="Programme X", organisation="ANR")
    assert a.dedupe_key() == "anr|programme x"


def test_status_default_unknown():
    assert AAPExtraction().status == AAPStatus.UNKNOWN
