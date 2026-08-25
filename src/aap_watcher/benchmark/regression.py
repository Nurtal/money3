"""Benchmark regression tracking (Phase 5).

CI should catch when a new extractor version degrades quality or speed. The
README specifies thresholds: F1 down >2%, recall down >3%, latency up >20%.
Results are persisted as JSON so a later run can be compared against a baseline.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

F1_DROP = 0.02
RECALL_DROP = 0.03
LATENCY_INCREASE = 0.20


@dataclass
class Regression:
    extractor: str
    metric: str
    before: float
    after: float
    delta: float


def result_to_dict(result) -> dict:
    return {
        "n_examples": result.n_examples,
        "extractors": [
            {
                "name": r.extractor,
                "f1": r.f1,
                "precision": r.precision,
                "recall": r.recall,
                "latency_ms": r.latency_ms,
                "memory_mb": r.memory_mb,
                "cost_eur": r.cost_eur,
            }
            for r in result.results
        ],
    }


def save_results(result, path: str | Path) -> None:
    Path(path).write_text(json.dumps(result_to_dict(result), indent=2), encoding="utf-8")


def load_results(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _index(d: dict) -> dict:
    return {e["name"]: e for e in d["extractors"]}


def detect_regressions(before: dict, after: dict) -> list[Regression]:
    regressions: list[Regression] = []
    b = _index(before)
    a = _index(after)
    for name, after_e in a.items():
        if name not in b:
            continue
        before_e = b[name]
        f1_b, f1_a = before_e["f1"], after_e["f1"]
        if f1_b - f1_a > F1_DROP:
            regressions.append(Regression(name, "f1", f1_b, f1_a, f1_a - f1_b))
        r_b, r_a = before_e["recall"], after_e["recall"]
        if r_b - r_a > RECALL_DROP:
            regressions.append(Regression(name, "recall", r_b, r_a, r_a - r_b))
        l_b, l_a = before_e["latency_ms"], after_e["latency_ms"]
        if l_b > 0 and (l_a - l_b) / l_b > LATENCY_INCREASE:
            regressions.append(Regression(name, "latency_ms", l_b, l_a, l_a - l_b))
    return regressions
