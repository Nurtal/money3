from pathlib import Path

from aap_watcher.benchmark import (
    analyse,
    load_corpus,
    normalize_amount,
    normalize_date,
    normalize_text,
    render_report,
    run_benchmark,
)
from aap_watcher.extraction.regex import RegexExtractor

CORPUS = Path("data/benchmark/gold/v1.jsonl")


def test_load_corpus_and_split():
    examples = load_corpus(CORPUS)
    assert len(examples) >= 3
    test_split = [e for e in examples if e.split == "test"]
    train_split = [e for e in examples if e.split == "train"]
    assert len(test_split) > 0
    assert len(train_split) > 0
    # Every example must be unique.
    assert len({e.id for e in examples}) == len(examples)
    # The test split must stay isolated from model development: all ids unique.
    assert set(e.id for e in test_split).isdisjoint(e.id for e in train_split)


def test_corpus_entity_offsets_match_text():
    examples = load_corpus(CORPUS)
    for ex in examples:
        for ent in ex.entities:
            assert ex.text[ent.start:ent.end] == ent.text, (
                f"[{ex.id}] span {ent.text!r} != text[{ent.start}:{ent.end}]"
            )


def test_normalisation():
    assert normalize_date("15 octobre 2026") == "2026-10-15"
    assert normalize_date("15/10/2026") == "2026-10-15"
    assert normalize_amount("500 000 €") == 500000
    assert normalize_text("  Programme  Cancer! ") == "programme cancer"


def test_benchmark_runs_and_measures():
    examples = load_corpus(CORPUS)
    result = run_benchmark(examples, [RegexExtractor()])
    r = result.results[0]
    assert result.n_examples == len(examples)
    assert 0.0 <= r.f1 <= 1.0
    assert r.latency_ms > 0.0
    assert r.cost_eur == 0.0


def test_benchmark_reports_nonempty():
    examples = load_corpus(CORPUS)
    result = run_benchmark(examples, [RegexExtractor()])
    out = render_report(result)
    assert "regex" in out
    assert "F1" in out


def test_error_analysis_collects_mismatches():
    from aap_watcher.extraction.base import Document

    ex = load_corpus(CORPUS)[0]
    # Force a wrong prediction by dropping the title to manufacture a false negative.
    pred = RegexExtractor().extract(Document(text=ex.text, source_url=ex.source_url)).model_dump()
    pred["title"] = None
    report = analyse("regex", [pred], [ex.expected], [ex.id])
    assert any(c.kind == "false_negative" and c.field == "title" for c in report.cases)
