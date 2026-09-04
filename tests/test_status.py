from aap_watcher.extraction._status import detect_status
from aap_watcher.schema import AAPStatus


def test_detect_open():
    assert detect_status("Appel ouvert.") == AAPStatus.OPEN


def test_detect_open_variant():
    assert detect_status("Candidatures ouvertes.") == AAPStatus.OPEN


def test_detect_upcoming():
    assert detect_status("Appel à venir, ouverture prévue prochainement.") == AAPStatus.UPCOMING


def test_detect_closed():
    assert detect_status("Ce appel est clôturé.") == AAPStatus.CLOSED


def test_detect_closed_variant():
    assert detect_status("Candidatures closes.") == AAPStatus.CLOSED


def test_detect_cancelled():
    assert detect_status("Appel annulé.") == AAPStatus.CANCELLED


def test_detect_cancelled_variant():
    assert detect_status("Appel à projets annulé par l'organisme.") == AAPStatus.CANCELLED


def test_detect_closing_soon():
    assert detect_status("Clôture prochaine, date limite imminente.") == AAPStatus.CLOSING_SOON


def test_detect_unknown_when_no_marker():
    assert detect_status("L'appel finance la recherche.") == AAPStatus.UNKNOWN


def test_detect_unknown_empty():
    assert detect_status("") == AAPStatus.UNKNOWN


def test_case_insensitive():
    assert detect_status("APPEL OUVERT.") == AAPStatus.OPEN
