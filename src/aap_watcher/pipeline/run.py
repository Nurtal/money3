"""Pipeline orchestration (Phase 1 slice).

Flow: scraper.discover -> extractor.extract -> repository.save. This is the
thin orchestration layer; scraping, extraction and storage stay independent
components (README: development principles).
"""

from __future__ import annotations

from typing import Optional

from ..database.repository import Repository
from ..extraction.base import Document, Extractor
from ..scrapers.base import BaseScraper


def run_once(
    scraper: BaseScraper,
    extractor: Extractor,
    repository: Repository,
    html: Optional[str] = None,
) -> dict:
    """Run one scrape+extract+store pass. Returns summary counts.

    The repository preserves history and returns a :class:`ChangeEvent` per AAP;
    we tally new vs modified so the monitor can report what changed.
    """
    counts = {"processed": 0, "new": 0, "modified": 0, "deadline_changed": 0, "cancelled": 0}
    events = []
    for doc in scraper.discover(html=html):
        assert isinstance(doc, Document)
        extraction = extractor.extract(doc)
        repository.save_raw(
            source_url=extraction.source_url or doc.source_url or "",
            body=doc.text,
            content_type="text/plain",
        )
        event = repository.save_aap(extraction)
        counts["processed"] += 1
        if event.type in counts:
            counts[event.type] += 1
        if event.type != "unchanged":
            events.append(event)
    counts["events"] = events
    return counts
