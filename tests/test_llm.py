"""Tests for the LLM structured extractor (mocked — no network).

The OpenAI client is mocked so tests stay fast and offline, consistent with
the repository's test conventions.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from aap_watcher.extraction.base import Document
from aap_watcher.extraction.llm import LLMExtractor

MOCK_RESPONSE_JSON = {
    "title": "Programme Cancer 2027",
    "organisation": "ANR",
    "amount_max": 500000,
    "currency": "EUR",
    "deadline": "2026-10-15",
    "eligibility": "universités, laboratoires",
    "research_topics": ["cancérologie"],
    "funding_type": "subvention",
}

MOCK_NULL_RESPONSE_JSON = {
    "title": "Appel unclear",
    "organisation": None,
    "amount_max": None,
    "currency": None,
    "deadline": None,
    "eligibility": None,
    "research_topics": [],
    "funding_type": None,
}


def _make_mock_client(response_json: dict) -> MagicMock:
    """Create a mock OpenAI client whose chat.completions.create returns the given JSON."""
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = json.dumps(response_json)
    mock_resp.model = "test-model"
    client = MagicMock()
    client.chat.completions.create.return_value = mock_resp
    return client


DOC = Document(
    text="Appel à projets : Programme Cancer 2027\nDate limite : 15 octobre 2026\nMontant maximum : 500 000 €\nL'ANR lance un appel.",
    source_url="https://anr.fr/AAP/1",
)


@patch("aap_watcher.extraction.llm.OpenAI", autospec=True)
def test_llm_extracts_structured_fields(mock_openai_cls):
    client = _make_mock_client(MOCK_RESPONSE_JSON)
    mock_openai_cls.return_value = client

    ext = LLMExtractor(model="test", api_key="fake", base_url="http://localhost")
    ex = ext.extract(DOC)

    assert ex.title == "Programme Cancer 2027"
    assert ex.organisation == "ANR"
    assert ex.amount_max == 500000
    assert ex.currency == "EUR"
    assert ex.deadline == "2026-10-15"
    assert ex.eligibility and "universités" in ex.eligibility
    assert "cancérologie" in ex.research_topics
    assert ex.funding_type == "subvention"
    assert ex.extraction_method == "llm"
    # Provenance carries model version
    assert ex.provenance.model_version == "test"
    assert ex.provenance.prompt_version == "aap-json-v2"


@patch("aap_watcher.extraction.llm.OpenAI", autospec=True)
def test_llm_handles_null_fields(mock_openai_cls):
    client = _make_mock_client(MOCK_NULL_RESPONSE_JSON)
    mock_openai_cls.return_value = client

    ext = LLMExtractor(model="test", api_key="fake", base_url="http://localhost")
    ex = ext.extract(DOC)

    assert ex.title == "Appel unclear"
    assert ex.organisation is None
    assert ex.amount_max is None
    assert ex.deadline is None
    assert ex.eligibility is None
    assert ex.research_topics == []
    assert ex.funding_type is None


@patch("aap_watcher.extraction.llm.OpenAI", autospec=True)
def test_llm_passes_correct_model_and_endpoint(mock_openai_cls):
    client = _make_mock_client(MOCK_RESPONSE_JSON)
    mock_openai_cls.return_value = client

    ext = LLMExtractor(model="qwen3:8b", api_key="ollama", base_url="http://localhost:11434/v1")
    ext.extract(DOC)

    call_kwargs = client.chat.completions.create.call_args
    assert call_kwargs.kwargs["model"] == "qwen3:8b"
    assert call_kwargs.kwargs["response_format"] == {"type": "json_object"}


@patch("aap_watcher.extraction.llm.OpenAI")
def test_llm_env_defaults(mock_openai_cls, monkeypatch):
    """Model and base_url resolve from env vars when not passed explicitly."""
    monkeypatch.setenv("AAP_LLM_MODEL", "gemma3:latest")
    monkeypatch.setenv("AAP_LLM_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    mock_client = _make_mock_client(MOCK_RESPONSE_JSON)
    mock_openai_cls.return_value = mock_client

    ext = LLMExtractor()
    assert ext.model == "gemma3:latest"
    ext.extract(DOC)
    call_kwargs = mock_client.chat.completions.create.call_args
    assert call_kwargs.kwargs["model"] == "gemma3:latest"


@patch("aap_watcher.extraction.llm.OpenAI")
def test_llm_coerces_list_eligibility(mock_openai_cls):
    """Models sometimes return eligibility as a list; the schema wants a string."""
    resp = {**MOCK_RESPONSE_JSON, "eligibility": ["Agronomes", "Écologues"], "status": "open"}
    client = _make_mock_client(resp)
    mock_openai_cls.return_value = client

    ext = LLMExtractor(model="test", api_key="fake", base_url="http://localhost")
    ex = ext.extract(DOC)

    assert "Agronomes" in ex.eligibility
    assert ex.status.value == "open"


def test_llm_importable_when_openai_missing(monkeypatch):
    """LLMExtractor class is importable regardless of openai availability."""
    # Even if AVAILABLE were False, the class itself should be importable
    # (the error is raised at __init__, not at class definition time).
    from aap_watcher.extraction.llm import LLMExtractor as Cls
    assert hasattr(Cls, "extract")
