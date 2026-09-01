# ADR-0003: Canonical AAP Schema

## Status

Accepted (implemented in `src/aap_watcher/schema.py`).

## Context

Every extractor strategy (regex, dictionary, classical NLP, spaCy, transformers, LLM, hybrid) must produce comparable outputs so the benchmark can score them identically. If strategies emitted bespoke dicts with inconsistent field names and formats, evaluation (and the monitor, and the API) would each need to understand every strategy's quirks.

## Decision

Define a single **canonical `AAPExtraction`** Pydantic model in `schema.py` that mirrors the README field table:

- Scalar fields (`title`, `organisation`, `deadline`, `amount_max`, `currency`, `eligibility`, `geographical_scope`, `funding_type`, …) default to `None`.
- List fields (`eligible_applicants`, `research_topics`, `documents`) default to empty lists.
- Lifecycle via the `AAPStatus` enum (`upcoming/open/closing_soon/closed/cancelled/archived/unknown`) using README names exactly.
- Every extraction carries `Provenance` (source url/text, method, model + prompt version, timestamp, confidence) so each value is traceable — a hard project constraint.
- `dedupe_key()` provides a stable key for basic deduplication.

This schema is the **single source of truth**. The benchmark `normalisation.py` helpers define how raw values (French dates, amounts) are compared, keeping extractor output and evaluation consistent.

## Alternatives considered

- Shared duck-typed dict contract: rejected — no validation, no documentation, easy to drift.
- No canonical schema (each strategy its own shape): rejected — breaks the benchmark's core comparability guarantee.
- Different schema for ML/LLM strategies: rejected — the whole point is identical inputs/outputs across all strategies.

## Consequences

- All extractors implement the `Extractor` protocol (`extract(Document) -> AAPExtraction`).
- Modifying this schema is a significant act: per project conventions it requires an explicit ADR.
- JSON serialization and DB persistence map directly onto the model.
- The benchmark compares only the fields in `_COMPARED_FIELDS`, a stable subset.
