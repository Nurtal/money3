"""Field-level benchmark metrics.

For each (example, field) pair we compute an exact match and a normalised
match. Extractor performance is aggregated micro-averaged across fields and
examples into precision / recall / F1, plus per-field match rates. All numbers
are produced by running the benchmark — never hand-estimated (README: no
manually estimated scores).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .normalisation import normalize_value

_COMPARED_FIELDS = (
    "title",
    "organisation",
    "amount_min",
    "amount_max",
    "currency",
    "deadline",
    "opening_date",
    "eligibility",
    "eligible_applicants",
    "research_topics",
    "geographical_scope",
    "funding_type",
    "status",
)


@dataclass
class FieldResult:
    exact_matches: int = 0
    normalised_matches: int = 0
    present_in_gold: int = 0
    present_in_pred: int = 0


@dataclass
class ExtractorResult:
    extractor: str
    field_results: dict[str, FieldResult] = field(default_factory=dict)
    tp: int = 0
    fp: int = 0
    fn: int = 0
    latency_ms: float = 0.0
    memory_mb: float = 0.0
    cost_eur: float = 0.0

    @property
    def precision(self) -> float:
        denom = self.tp + self.fp
        return self.tp / denom if denom else 0.0

    @property
    def recall(self) -> float:
        denom = self.tp + self.fn
        return self.tp / denom if denom else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0

    @property
    def exact_match_rate(self) -> float:
        total = sum(fr.present_in_gold for fr in self.field_results.values())
        matched = sum(fr.exact_matches for fr in self.field_results.values())
        return matched / total if total else 0.0

    @property
    def normalised_match_rate(self) -> float:
        total = sum(fr.present_in_gold for fr in self.field_results.values())
        matched = sum(fr.normalised_matches for fr in self.field_results.values())
        return matched / total if total else 0.0


def _field_match(field: str, gold_val, pred_val) -> tuple[bool, bool]:
    g = normalize_value(field, gold_val)
    p = normalize_value(field, pred_val)
    exact = g == p
    norm = g == p  # normalise already applied; equality is the normalised test
    return exact, norm


def evaluate_extractor(
    extractor_name: str,
    predictions: list[dict],
    golds: list[dict],
) -> ExtractorResult:
    """Compare predicted field dicts against gold field dicts."""
    result = ExtractorResult(extractor=extractor_name)
    for gold, pred in zip(golds, predictions):
        for f in _COMPARED_FIELDS:
            fr = result.field_results.setdefault(f, FieldResult())
            g_has = gold.get(f) not in (None, "", [], {})
            p_has = pred.get(f) not in (None, "", [], {})
            if g_has:
                fr.present_in_gold += 1
            if p_has:
                fr.present_in_pred += 1
            if g_has and p_has:
                exact, norm = _field_match(f, gold.get(f), pred.get(f))
                if exact:
                    fr.exact_matches += 1
                    result.tp += 1
                else:
                    result.fp += 1
                    result.fn += 1
                if norm:
                    fr.normalised_matches += 1
            elif g_has and not p_has:
                result.fn += 1
            elif (not g_has) and p_has:
                result.fp += 1
    return result
