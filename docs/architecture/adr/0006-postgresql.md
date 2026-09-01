# ADR-0006: PostgreSQL for Production

## Status

Accepted (future direction; SQLite is the current dev backend).

## Context

Local development and the offline test suite use SQLite. For a continuously updated funding database with full-text search, concurrent writes from scheduling, and the potential to scale, SQLite is not the production target.

## Decision

Use **PostgreSQL in production**, with SQLite retained for local development and tests:

- Storage layer is written against SQLAlchemy 2.0 so the backend can be switched by changing the database URL (SQLite `sqlite:///…` → PostgreSQL `postgresql://…`).
- The schema (see `models.py`) is backend-agnostic; no SQLite-only features are relied upon.
- Full-text search in production uses PostgreSQL full-text search (or an external search engine — OpenSearch/Elasticsearch/Meilisearch are noted as options in the README).
- Object-relation mapping and repository patterns (`repository.py`) isolate the chosen backend.

## Consequences

- Swapping the backend is a DSN change plus migrations, not a rewrite.
- PostgreSQL enables production full-text search, better concurrency and stronger data integrity for the historical versioning model (multiple `aap_versions` per AAP).
- Migration tooling (e.g. Alembic) should be introduced before production adoption so schema changes are versioned (not yet set up — see AGENTS.md toolchain gaps).
- The canonical schema and change detection are backend-independent, so benchmarks and behaviour are identical across SQLite and PostgreSQL.
