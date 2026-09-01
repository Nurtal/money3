import pytest

from aap_watcher.scrapers.base import BaseScraper
from aap_watcher.scrapers.pdf_parser import extract_pdf_text


class _PdfScraper(BaseScraper):
    source_name = "pdf_test"

    def discover(self, html=None):
        return iter(())


def _make_pdf_bytes(text: str) -> bytes:
    from tests.test_pdf_parser import _make_pdf_bytes as make

    return make(text)


class _FakeClient:
    """Minimal stand-in for httpx.Client with a .get() returning bytes content."""

    def __init__(self, body: bytes):
        self._body = body

    def get(self, url):
        class _Resp:
            def __init__(self, body):
                self.content = body
                self.text = body.decode("latin-1", errors="replace")

            def raise_for_status(self):
                return None

        return _Resp(self._body)


def test_fetch_parses_pdf_url_when_content_is_pdf(monkeypatch):
    scraper = _PdfScraper()
    pdf = _make_pdf_bytes("Appel à projets PDF 2026")
    monkeypatch.setattr(scraper, "_client", _FakeClient(pdf))
    monkeypatch.setattr(scraper, "_robots_allows", lambda url: True)
    monkeypatch.setattr(scraper, "_rate_limit", lambda: None)
    out = scraper.fetch("https://example.org/aap.pdf")
    assert "PDF" in out


def test_fetch_returns_html_for_html_url(monkeypatch):
    scraper = _PdfScraper()
    monkeypatch.setattr(
        scraper, "_client", _FakeClient(b"<html><body><p>hi</p></body></html>")
    )
    monkeypatch.setattr(scraper, "_robots_allows", lambda url: True)
    monkeypatch.setattr(scraper, "_rate_limit", lambda: None)
    out = scraper.fetch("https://example.org/aap.html")
    assert "<html>" in out
