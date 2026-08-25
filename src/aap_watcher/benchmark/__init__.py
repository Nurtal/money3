"""Benchmark package exports."""

from __future__ import annotations

from .datasets import EntityAnnotation, GoldExample, corpus_by_split, load_corpus
from .error_analysis import ErrorCase, ErrorReport, analyse
from .metrics import ExtractorResult, evaluate_extractor
from .normalisation import normalize_amount, normalize_date, normalize_text, normalize_value
from .reports import render_report
from .runner import BenchmarkResult, run_benchmark

__all__ = [
    "EntityAnnotation",
    "GoldExample",
    "load_corpus",
    "corpus_by_split",
    "normalize_text",
    "normalize_date",
    "normalize_amount",
    "normalize_value",
    "ExtractorResult",
    "evaluate_extractor",
    "run_benchmark",
    "BenchmarkResult",
    "ErrorCase",
    "ErrorReport",
    "analyse",
    "render_report",
]
