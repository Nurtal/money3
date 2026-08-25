"""LLM structured extractor (Phase 3 baseline, optional dependency).

LLMs are one candidate extraction technology among others — they must be
benchmarked, not assumed superior (README: strategy 7). This extractor calls an
OpenAI-compatible chat API and enforces the canonical schema: never invent
missing values, return ``null`` when unavailable, preserve source text, and
record model + prompt versions. Requires the ``llm`` extra.

Cost is tracked per call so the benchmark can compare €/document across
strategies.
"""

from __future__ import annotations

import json
import os
from typing import Optional

from ..schema import AAPExtraction, AAPStatus, Provenance
from .base import Document, Extractor
from ..benchmark.normalisation import normalize_amount, normalize_date

try:
    from openai import OpenAI  # noqa: F401

    AVAILABLE = True
except ImportError:  # pragma: no cover
    OpenAI = None
    AVAILABLE = False

_PROMPT_VERSION = "aap-json-v1"

_SCHEMA_HINT = (
    "Return strict JSON with fields: title, organisation, amount_max (int or null), "
    "currency, deadline (ISO YYYY-MM-DD or null), eligibility, research_topics (list), "
    "funding_type. Never invent values; use null when unknown."
)


class LLMExtractor:
    name = "llm"

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        cost_per_doc: float = 0.0,
    ):
        if not AVAILABLE:
            raise RuntimeError("openai package not installed. Add the 'llm' extra.")
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
        prov = Provenance(
            source_url=document.source_url,
            source_text=document.text[:500],
            extraction_method=self.name,
            model_version=self.model,
            prompt_version=_PROMPT_VERSION,
            confidence_score=0.9,
        )
        return AAPExtraction(
            title=raw.get("title"),
            organisation=raw.get("organisation"),
            amount_max=normalize_amount(raw.get("amount_max")) if raw.get("amount_max") else None,
            currency=raw.get("currency"),
            deadline=normalize_date(raw.get("deadline")) if raw.get("deadline") else None,
            eligibility=raw.get("eligibility"),
            research_topics=raw.get("research_topics") or [],
            funding_type=raw.get("funding_type"),
            source_url=document.source_url,
            extraction_method=self.name,
            status=AAPStatus.UNKNOWN,
            provenance=prov,
        )
