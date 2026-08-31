"""Generic source adapter.

Most AAP listing pages share a shape: a list of entry blocks, each linking to a
detail page. Entries may be marked up as ``<article>``/``<li>`` (the default)
but real sites frequently use a heading tag (``<h2>``/``<h3>``) per entry,
sometimes carrying the ``<a href>`` itself (INCa, ARS, ANR, Fondation de
France…). This base stays thin: each concrete source only overrides
``source_name``, ``listing_url`` and optionally ``entry_block`` (a regex whose
named group ``body`` delimits one entry). Live fetching respects robots.txt via
:class:`BaseScraper`; tests inject raw HTML.
"""

from __future__ import annotations

import re
from typing import Iterator, Optional

from ..extraction.base import Document
from .base import BaseScraper, LINK_RE


class GenericSourceScraper(BaseScraper):
    source_name = "generic"
    listing_url = ""
    #: Regex (with a named group ``body``) delimiting a single AAP entry.
    entry_block: str = r"<(?P<tag>article|li)[^>]*>(?P<body>.*?)</(?P=tag)>"

    def discover(self, html: Optional[str] = None) -> Iterator[Document]:
        html = self.fetch(self.listing_url, html=html)
        block_re = re.compile(self.entry_block, re.IGNORECASE | re.DOTALL)
        for match in block_re.finditer(html):
            body = match.groupdict().get("body")
            if body is None:
                body = match.group(0)
            text = self.html_to_text(body)
            if not text.strip():
                continue
            link = LINK_RE.search(body)
            source_url = link.group("url") if link else self.listing_url
            yield Document(
                text=text, source_url=source_url, html=body,
                metadata={"source": self.source_name},
            )
