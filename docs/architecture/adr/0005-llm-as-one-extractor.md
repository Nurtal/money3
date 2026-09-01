# ADR-0005: LLM as One Extractor Among Many

## Status

Accepted (LLM extractor is a stub behind the optional `llm` extra).

## Context

LLM-based extraction is compelling for free-text, semantic fields. But LLMs add per-call cost and latency, and their accuracy on this domain is unproven relative to cheap deterministic strategies. The project must not silently become an LLM pipeline.

## Decision

Treat the **LLM as one extractor among many** in the benchmark — never as the default pipeline:

- Implement the LLM extractor behind the optional `llm` extra (`openai`), returning a normalised `AAPExtraction` via a shared prompt, with the prompt version recorded in `Provenance`.
- It is benchmarked like every other strategy: `run_benchmark` measures its F1/precision/recall, latency and cost (€/doc) against the same gold corpus and the same fields.
- The LLM may only be adopted for fields (or documents) where it measurably beats simpler strategies at an acceptable cost — per ADR-0004, no technology wins without benchmark evidence.

## Alternatives considered

- Make the LLM the sole/default extractor: accepted rationale in README is explicitly rejected — contradicts the benchmark-first principle and the "no winner before benchmarking" rule.
- Use the LLM only as a hybrid "last resort" for fields the determinists leave empty: reasonable future extension, but only where it wins on cost-adjusted accuracy; not the default.

## Consequences

- `hybrid.py` remains deterministic (regex + dictionary + classical NLP) unless an ADR extends it with an LLM merger that is first benchmarked.
- Cost and latency are first-class metrics, so an LLM's accuracy gain can be weighed against its price.
- The LLM extractor surfaces provenance (model + prompt version) for traceability.
- No prompt or model change silently changes behaviour without being re-benchmarked.
