# ADR-0001: Python

## Status

Accepted (early-development scaffold).

## Context

AAP Watcher must monitor funding calls, extract structured data from heterogeneous French/EC sources and benchmark multiple extraction strategies. The choice of implementation language and core data tooling shapes every later decision.

## Decision

Use **Python (>=3.12)** as the sole implementation language, with:

- **Pydantic v2** for the canonical AAP schema and validation.
- **SQLAlchemy 2.0** (ORM + Core) for storage, on SQLite locally and PostgreSQL in production (see ADR-0006).
- **httpx** for HTTP scraping.
- **`uv`** + `pyproject.toml` (`src/` layout) for packaging, dependency and environment management.

Python is chosen because the target ecosystem — NLP/ML (spaCy, transformers, scikit-learn), web scraping (httpx, BeautifulSoup) and rapid iteration of a benchmark harness — is strongest there, and because the benchmark-first goal needs a scripting language where many extraction strategies can be prototyped and compared cheaply.

## Alternatives considered

- **Rust/Go**: better raw performance but a far weaker ML/NLP ecosystem; would require re-implementing most extraction tooling in a second language.
- **TypeScript/Node**: reasonable scraping story but weak French NLP/ML support.
- **Java/Kotlin**: heavyweight; academic research ecosystem is Python-first.

## Consequences

- Strong NLP/ML library availability makes the multi-strategy benchmark the intended scope of the project.
- Pydantic gives validated, documented schemas that are easy to serialize to JSON and persist.
- Python is not the fastest option; latency is measured by the benchmark (see ADR-0004) and only matters where it measurably hurts accuracy/cost.
- Optional extras (`spacy`, `transformers`, `llm`, `api`, `pdf`) keep the core install lightweight while allowing capabilities to be added.
