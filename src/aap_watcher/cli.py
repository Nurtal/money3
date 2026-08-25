"""CLI entrypoint."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .benchmark import load_corpus, render_report, run_benchmark
from .benchmark.regression import detect_regressions, load_results, save_results
from .database.models import make_engine, make_session_factory
from .database.repository import Repository
from .extraction.regex import RegexExtractor
from .extraction.registry import available_extractors
from .pipeline.run import run_once
from .scrapers.sources import available_sources, get_source

_DEFAULT_CORPUS = "data/benchmark/gold/v1.jsonl"


def cmd_run(args) -> int:
    engine = make_engine(args.db)
    sf = make_session_factory(engine)
    repo = Repository(sf)
    repo.init_db(engine)

    extractor = RegexExtractor()
    names = available_sources() if args.source == "all" else [args.source]
    total = {"processed": 0, "new": 0, "modified": 0, "deadline_changed": 0, "cancelled": 0}
    for name in names:
        scraper = get_source(name)
        try:
            summary = run_once(scraper, extractor, repo)
        except Exception as exc:  # noqa: BLE001 - one bad source must not abort the run
            print(f"[warn] source '{name}' failed: {exc}")
            scraper.close()
            continue
        scraper.close()
        for k in total:
            total[k] += summary.get(k, 0)
        print(f"[{name}] {summary}")
    print(f"Total: {total}")
    return 0


def cmd_monitor(args) -> int:
    """One monitoring pass over all sources; reports new/changed/cancelled."""
    engine = make_engine(args.db)
    sf = make_session_factory(engine)
    repo = Repository(sf)
    repo.init_db(engine)

    extractor = RegexExtractor()
    total = {"processed": 0, "new": 0, "modified": 0, "deadline_changed": 0, "cancelled": 0}
    for name in available_sources():
        scraper = get_source(name)
        try:
            summary = run_once(scraper, extractor, repo)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] source '{name}' failed: {exc}")
            scraper.close()
            continue
        scraper.close()
        for k in total:
            total[k] += summary.get(k, 0)
        if any(summary.get(k, 0) for k in ("new", "modified", "deadline_changed", "cancelled")):
            print(f"[{name}] changes: {summary}")
    print(f"Monitor pass complete: {total}")
    return 0


def cmd_benchmark(args) -> int:
    corpus_path = args.corpus or _DEFAULT_CORPUS
    examples = load_corpus(corpus_path)
    if args.split:
        examples = [e for e in examples if e.split == args.split]
    if not examples:
        print(f"No gold examples found at {corpus_path}")
        return 1
    extractors = available_extractors()
    result = run_benchmark(examples, extractors)
    print(render_report(result))
    if args.save:
        save_results(result, args.save)
        print(f"Saved results to {args.save}")
    return 0


def cmd_regression(args) -> int:
    before = load_results(args.before)
    after = load_results(args.after)
    regs = detect_regressions(before, after)
    if not regs:
        print("No regressions detected.")
        return 0
    print("Regressions detected:")
    for r in regs:
        print(f"  - {r.extractor}: {r.metric} {r.before:.3f} -> {r.after:.3f} (Δ{r.delta:+.3f})")
    return 1


def cmd_serve(args) -> int:
    import uvicorn

    from .api import create_app

    app = create_app(args.db)
    uvicorn.run(app, host=args.host, port=args.port)  # noqa: S104
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aap-watcher", description="AAP Watcher")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="Scrape + extract + store")
    p_run.add_argument("--db", default="sqlite:///aap_watcher.db")
    p_run.add_argument("--source", default="anr", choices=["all", *available_sources()])
    p_run.set_defaults(func=cmd_run)

    p_mon = sub.add_parser("monitor", help="Monitoring pass over all sources (detect new/changed/cancelled)")
    p_mon.add_argument("--db", default="sqlite:///aap_watcher.db")
    p_mon.set_defaults(func=cmd_monitor)

    p_bench = sub.add_parser("benchmark", help="Run extraction benchmark on gold corpus")
    p_bench.add_argument("--corpus", default=None, help=f"JSONL gold corpus (default: {_DEFAULT_CORPUS})")
    p_bench.add_argument("--split", default=None, help="Restrict to a split (train/val/test)")
    p_bench.add_argument("--save", default=None, help="Persist results JSON for regression tracking")
    p_bench.set_defaults(func=cmd_benchmark)

    p_reg = sub.add_parser("regression", help="Compare two saved benchmark results")
    p_reg.add_argument("--before", required=True)
    p_reg.add_argument("--after", required=True)
    p_reg.set_defaults(func=cmd_regression)

    p_serve = sub.add_parser("serve", help="Serve the REST API + web UI (FastAPI/uvicorn)")
    p_serve.add_argument("--db", default="sqlite:///aap_watcher.db")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.set_defaults(func=cmd_serve)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
