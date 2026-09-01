"""Benchmark report rendering (markdown tables)."""

from __future__ import annotations

from .metrics import _COMPARED_FIELDS


def render_report(result) -> str:
    lines = [
        "AAP Extraction Benchmark",
        "=========================",
        "",
        f"Documents: {result.n_examples}",
        "",
        f"{'Extractor':<16}{'F1':>8}{'Prec':>8}{'Rec':>8}"
        f"{'Exact%':>9}{'Norm%':>9}{'Lat(ms)':>10}{'Cost€':>9}",
        "-" * 77,
    ]
    for r in result.results:
        lines.append(
            f"{r.extractor:<16}{r.f1:>8.2f}{r.precision:>8.2f}{r.recall:>8.2f}"
            f"{r.exact_match_rate * 100:>9.1f}{r.normalised_match_rate * 100:>9.1f}"
            f"{r.latency_ms:>10.2f}{r.cost_eur:>9.2f}"
        )
    return "\n".join(lines)


def _field_stats(fr):
    """Derive micro TP/FP/FN for a single FieldResult (normalised match)."""
    tp = fr.normalised_matches
    fp = fr.present_in_pred - fr.normalised_matches
    fn = fr.present_in_gold - fr.normalised_matches
    return tp, fp, fn


def render_field_matrix(result) -> str:
    """Per-extractor, per-field normalised precision/recall/F1 markdown matrix.

    Each cell shows ``F1`` with ``P/R`` beneath. This exposes *where* each
    strategy wins and loses (dates/amounts vs topics/eligibility) instead of a
    single aggregate score.
    """
    extractors = [r.extractor for r in result.results]
    header = f"{'Field':<18}" + "".join(f"{name:>22}" for name in extractors)
    lines = [
        "Per-field match matrix (normalised micro P/R/F1)",
        "==================================================",
        "",
        header,
        "-" * len(header),
    ]
    for field in _COMPARED_FIELDS:
        # Skip fields absent from every extractor to keep the table readable.
        if all(field not in r.field_results for r in result.results):
            continue
        parts = [f"{field:<18}"]
        for r in result.results:
            fr = r.field_results.get(field)
            if fr is None or (fr.present_in_gold == 0 and fr.present_in_pred == 0):
                cells = "-"
            else:
                tp, fp, fn = _field_stats(fr)
                p = tp / (tp + fp) if (tp + fp) else 0.0
                rec = tp / (tp + fn) if (tp + fn) else 0.0
                f1 = 2 * p * rec / (p + rec) if (p + rec) else 0.0
                cells = f"{f1:.2f} ({p:.2f}/{rec:.2f})"
            parts.append(f"{cells:>22}")
        lines.append("".join(parts))
    return "\n".join(lines)
