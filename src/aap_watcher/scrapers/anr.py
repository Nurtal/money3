"""ANR (Agence Nationale de la Recherche) source adapter.

This is the first source adapter (README: Phase 1 — "Implement first source").
It parses a simple AAP listing page into one Document per candidate call and
leaves field extraction to the extraction layer.

To keep tests offline and deterministic, ``discover`` accepts raw ``html``.
"""

from __future__ import annotations

import re
from typing import Iterator, Optional

from ..extraction.base import Document
from .base import BaseScraper

_LISTING_URL = "https://anr.fr/fr/appels-a-projets/"

# The ANR listing page wraps the whole page in one <article>; each call is a
# dedicated <h2> carrying its own detail link.
_ENTRY_RE = re.compile(
    r"<h2[^>]*>(?P<body>.*?)</h2>", re.IGNORECASE | re.DOTALL
)
_LINK_RE = re.compile(r'href="(?P<url>https?://[^"]+)"', re.IGNORECASE)


class ANRScraper(BaseScraper):
    source_name = "anr"
    listing_url = _LISTING_URL

    def discover(self, html: Optional[str] = None) -> Iterator[Document]:
        html = self.fetch(self.listing_url, html=html)
        for match in _ENTRY_RE.finditer(html):
            body = match.group("body")
            text = self.html_to_text(body)
            if not text:
                continue
            link = _LINK_RE.search(body)
            source_url = link.group("url") if link else self.listing_url
            yield Document(text=text, source_url=source_url, html=body, metadata={"source": "anr"})
