# ADR-0002: Source Adapter Architecture

## Status

Accepted (implemented, 25 source adapters).

## Context

AAP Watcher aggregates calls from many independent funding organisations (ANR, INCa, ARS, FRM, Fondation ARC, Horizon Europe, …). Each site publishes content in different markup and under its own robots.txt / ToS. We need one uniform downstream interface regardless of source, and a way to add new sources without touching the extraction or storage layers.

## Decision

Introduce a **source adapter** abstraction:

- A `BaseScraper` abstract base that centralises the *polite crawling* concerns (robots.txt respect, rate limiting, cache, descriptive User-Agent) and provides an HTML-to-text helper.
- A `GenericSourceScraper` subclass that handles the common "list of entry blocks" layout via a configurable `entry_block` regex; concrete sources only set `source_name`, `listing_url` and the block delimiter.
- A **registry** (`sources.py` → `sources_catalog.py`) mapping string keys to adapter classes, so the CLI/pipeline can scrape one source or all.
- Each adapter exposes `discover(html) -> Iterator[Document]`, yielding normalised `Document` objects (text, source_url, html, metadata).

Every source gets a corresponding offline HTML fixture and test, so the whole suite runs without network access (see AGENTS.md).

## Alternatives considered

- One monolithic scraper with per-site `if/else`: rejected — couples all sources, easy to break.
- XPath/CSS selectors via BeautifulSoup/selectolax per source: still adapter-per-source but heavier dependency; regex keeps the dependency surface minimal for the entry-block shape most sites share.
- Headless browser (Playwright) for JS-rendered pages: deferred; current sources render entry lists server-side. Revisit only for sources that genuinely require it.

## Consequences

- Adding a source = subclass + register + fixture + test; no changes to extraction/storage.
- Polite-crawling guarantees are enforced once in the base rather than per adapter.
- Regex-based block extraction is brittle to layout changes but simple and dependency-light; tests pin the current real markup.
- PDF attachments are handled by a shared parser (`scrapers/pdf_parser.py`) rather than duplicated per source.
