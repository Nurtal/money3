# ADR-0004: Extraction Benchmark

## Status

Accepted (implemented in `src/aap_watcher/benchmark/`).

## Context

The project's central hypothesis (README) is that **no extraction technology is the winner before it is benchmarked**. Regex, gazetteers, classical NLP, spaCy NER, transformers/CamemBERT and LLMs all have different accuracy, latency and cost profiles, and the "best" choice depends on the actual corpus. Hand-estimated scores are explicitly forbidden.

## Decision

Frame extraction as a **benchmark over competing strategies on a shared gold corpus**:

- A canonical gold corpus (JSONL, split into train/val/test) of hand-annotated AAP documents with entity span offsets.
- Each strategy implements the shared `Extractor` interface and runs over the same `Document` inputs.
- Field-level evaluation (`metrics.py`): exact and normalised match → precision / recall / F1 per extractor, plus per-field breakdown for the match matrix.
- The runner (`runner.py`) measures **latency (ms/doc)**, **memory (MB)** and **cost (€/doc)** using execution, not estimates.
- A **regression detector** (`regression.py`) flags F1↓>2%, recall↓>3%, latency↑>20% between saved benchmark runs (README thresholds).
- Reports render as markdown (`reports.py`), including the per-field matrix (`render_field_matrix`).
- All scores are produced by running the benchmark — never committed by hand.

## Alternatives considered

- Assume an LLM is best and adopt it directly as the extractor: rejected — this is the core anti-hypothesis the project exists to test (see ADR-0005).
- Anecdotal qualitative comparison: rejected — not reproducible, cannot track regressions.
- Single "accuracy" number without field/latency/cost granularity: rejected — hides where strategies win/lose and obscures cost/latency tradeoffs.

## Consequences

- Extraction improvement is measured, not asserted; a strategy only earns its place by scoring well.
- The gold corpus must be maintained and grown for results to remain meaningful (see task: grow to 500+).
- Results serialize to JSON so regression detection works across runs.
- New extractors plug in via `registry.py` and are automatically benchmarked.
