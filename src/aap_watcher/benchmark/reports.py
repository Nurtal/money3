"""Benchmark report rendering (markdown table)."""

from __future__ import annotations


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
