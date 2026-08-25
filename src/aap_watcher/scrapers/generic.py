"""Generic source adapter.

Most AAP listing pages share a shape: a list of entry blocks (``<article>`` or
``<li>``) each linking to a detail page. This base covers that common case so
concrete sources (INCa, ARS, foundations…) stay thin and independent. Each
source only overrides its ``source_name`` and ``listing_url``. Live fetching
respects robots.txt via :class:`BaseScraper`; tests inject raw HTML.
"""

from __future__ import annotations

import re
from typing import Iterator, Optional

from ..extraction.base import Document
from .base import BaseScraper, LINK_RE

_BLOCK_RE = re.compile(r"<(?P<tag>article|li)[^>]*>(?P<body>.*?)</(?P=tag)>", re.IGNORECASE | re.DOTALL)


class GenericSourceScraper(BaseScraper):
    source_name = "generic"
    listing_url = ""

    def discover(self, html: Optional[str] = None) -> Iterator[Document]:
        html = self.fetch(self.listing_url, html=html)
        for match in _BLOCK_RE.finditer(html):
            body = match.group("body")
            text = self.html_to_text(body)
            if not text.strip():
                continue
            link = LINK_RE.search(body)
            source_url = link.group("url") if link else self.listing_url
            yield Document(
                text=text, source_url=source_url, html=body,
                metadata={"source": self.source_name},
            )
