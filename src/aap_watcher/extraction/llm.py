"""LLM structured extractor (Phase 3 baseline, optional dependency).

LLMs are one candidate extraction technology among others — they must be
benchmarked, not assumed superior (README: strategy 7). This extractor calls an
OpenAI-compatible chat API (hosted or local, e.g. Ollama) and enforces the
canonical schema: never invent missing values, return ``null`` when
unavailable, preserve source text, and record model + prompt versions. Requires
the ``llm`` extra.

Model and endpoint resolve, in order of precedence, from constructor args, then
``AAP_LLM_MODEL`` / ``AAP_LLM_BASE_URL`` env vars, then the hosted defaults — so
the benchmark can run a local small model (``AAP_LLM_BASE_URL=http://localhost:11434/v1``)
without any code change.

Cost is tracked per call so the benchmark can compare €/document across
strategies.
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from ..schema import AAPExtraction, AAPStatus, Provenance
from ..benchmark.normalisation import normalize_amount, normalize_date
from .base import Document

try:
    from openai import OpenAI  # noqa: F401

    AVAILABLE = True
except ImportError:  # pragma: no cover
    OpenAI = None
    AVAILABLE = False

_PROMPT_VERSION = "aap-json-v2"

_SCHEMA_HINT = (
    "Extract information from the French funding call (AAP) text into strict JSON. "
    "Return a single JSON object with exactly these keys:\n"
    "  title (string), organisation (string), amount_min (int or null), "
    "amount_max (int or null), currency (string), opening_date (ISO YYYY-MM-DD or null), "
    "deadline (ISO YYYY-MM-DD or null), eligibility (string or null), "
    "eligible_applicants (list of strings), research_topics (list of strings), "
    "geographical_scope (string or null), funding_type (string or null), "
    "status (one of \"upcoming\", \"open\", \"closing_soon\", \"closed\", \"cancelled\", "
    "\"archived\" or null).\n"
    "Never invent values; use null (or empty list) when unknown. Amounts are integers in EUR. "
    "Dates are ISO 8601 (YYYY-MM-DD)."
)

_STATUS_ALIASES = {
    "à venir": AAPStatus.UPCOMING,
    "prochain": AAPStatus.UPCOMING,
    "upcoming": AAPStatus.UPCOMING,
    "ouvert": AAPStatus.OPEN,
    "open": AAPStatus.OPEN,
    "en cours": AAPStatus.OPEN,
    "se clôture": AAPStatus.CLOSING_SOON,
    "closing soon": AAPStatus.CLOSING_SOON,
    "clôturé": AAPStatus.CLOSED,
    "closed": AAPStatus.CLOSED,
    "annulé": AAPStatus.CANCELLED,
    "cancelled": AAPStatus.CANCELLED,
    "archivé": AAPStatus.ARCHIVED,
    "archived": AAPStatus.ARCHIVED,
}


def _as_str(value: Any) -> Optional[str]:
    """Coerce a model value to a single string or None."""
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        return s or None
    if isinstance(value, list):
        # e.g. eligibility returned as a list of sentences -> join into prose.
        s = "; ".join(str(x) for x in value if x).strip()
        return s or None
    if isinstance(value, (int, float)):
        return str(value)
    return str(value).strip()  # dict → JSON string as a last resort


def _as_str_list(value: Any) -> list[str]:
    """Coerce a model value to a list of strings."""
    if value is None:
        return []
    if isinstance(value, str):
        parts = [p.strip() for p in value.split(",")]
        return [p for p in parts if p]
    if isinstance(value, list):
        out: list[str] = []
        for x in value:
            if isinstance(x, str) and x.strip():
                out.append(x.strip())
            elif isinstance(x, (int, float)):
                out.append(str(x))
        return out
    return []


def _as_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return normalize_amount(value)
    except (TypeError, ValueError):
        return None


def _as_status(value: Any) -> AAPStatus:
    raw = _as_str(value)
    if raw is None:
        return AAPStatus.UNKNOWN
    return _STATUS_ALIASES.get(raw.strip().lower(), AAPStatus.UNKNOWN)


class LLMExtractor:
    name = "llm"

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        cost_per_doc: float = 0.0,
    ):
        if not AVAILABLE:
            raise RuntimeError("openai package not installed. Add the 'llm' extra.")
        # Model/endpoint resolve from env so the benchmark can run a local model
        # (e.g. Ollama on :11434) without changing code: AAP_LLM_MODEL /
        # AAP_LLM_BASE_URL, falling back to the hosted defaults.
        model = model or os.environ.get("AAP_LLM_MODEL", "gpt-4o-mini")
        base_url = base_url or os.environ.get("AAP_LLM_BASE_URL")
        self.model = model
        self.cost_per_doc = cost_per_doc
        self._client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"), base_url=base_url)

    def extract(self, document: Document) -> AAPExtraction:
        messages = [
            {"role": "system", "content": _SCHEMA_HINT},
            {"role": "user", "content": document.text or ""},
        ]
        resp = self._client.chat.completions.create(
            model=self.model, messages=messages, response_format={"type": "json_object"}
        )
        raw = json.loads(resp.choices[0].message.content)
        raw = raw if isinstance(raw, dict) else {}
        prov = Provenance(
            source_url=document.source_url,
            source_text=document.text[:500],
            extraction_method=self.name,
            model_version=self.model,
            prompt_version=_PROMPT_VERSION,
            confidence_score=0.9,
        )
        return AAPExtraction(
            title=_as_str(raw.get("title")),
            organisation=_as_str(raw.get("organisation")),
            amount_min=_as_int(raw.get("amount_min")),
            amount_max=_as_int(raw.get("amount_max")),
            currency=_as_str(raw.get("currency")),
            opening_date=normalize_date(raw.get("opening_date")) if raw.get("opening_date") else None,
            deadline=normalize_date(raw.get("deadline")) if raw.get("deadline") else None,
            eligibility=_as_str(raw.get("eligibility")),
            eligible_applicants=_as_str_list(raw.get("eligible_applicants")),
            research_topics=_as_str_list(raw.get("research_topics")),
            geographical_scope=_as_str(raw.get("geographical_scope")),
            funding_type=_as_str(raw.get("funding_type")),
            status=_as_status(raw.get("status")),
            source_url=document.source_url,
            extraction_method=self.name,
            provenance=prov,
        )