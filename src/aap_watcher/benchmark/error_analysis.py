"""Error analysis.

Collects, per extractor, the mismatch cases the README calls for: false
positives, false negatives, normalisation errors and semantic (value) errors.
Used for targeted improvement of individual extraction strategies.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .metrics import _COMPARED_FIELDS
from .normalisation import normalize_value


@dataclass
class ErrorCase:
    example_id: str
    field: str
    kind: str
    gold: object
    predicted: object


@dataclass
class ErrorReport:
    cases: list[ErrorCase] = field(default_factory=list)

    def by_kind(self, kind: str) -> list[ErrorCase]:
        return [c for c in self.cases if c.kind == kind]


def analyse(
    extractor_name: str,
    predictions: list[dict],
    golds: list[dict],
    example_ids: list[str],
) -> ErrorReport:
    report = ErrorReport()
    for ex_id, gold, pred in zip(example_ids, golds, predictions):
        for f in _COMPARED_FIELDS:
            g_has = gold.get(f) not in (None, "", [], {})
            p_has = pred.get(f) not in (None, "", [], {})
            if g_has and not p_has:
                report.cases.append(ErrorCase(ex_id, f, "false_negative", gold.get(f), pred.get(f)))
            elif p_has and not g_has:
                report.cases.append(ErrorCase(ex_id, f, "false_positive", gold.get(f), pred.get(f)))
            elif g_has and p_has:
                g = normalize_value(f, gold.get(f))
                p = normalize_value(f, pred.get(f))
                if g != p:
                    raw_g = normalize_value("title", gold.get(f))
                    raw_p = normalize_value("title", pred.get(f))
                    kind = "normalisation_error" if raw_g == raw_p else "semantic_error"
                    report.cases.append(ErrorCase(ex_id, f, kind, gold.get(f), pred.get(f)))
    return report
