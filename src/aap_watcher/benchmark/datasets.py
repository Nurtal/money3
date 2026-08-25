"""Annotation schema and gold-standard corpus loader.

Two annotation levels are required (README: annotation):
  * entity level  — raw text spans with labels, for NER evaluation
  * structured level — normalised field values, for final extraction evaluation

Gold examples are stored as JSONL. The test split must stay isolated from model
development; never hand-edit expected values to flatter a favourite extractor.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class EntityAnnotation:
    text: str
    label: str
    start: int
    end: int


@dataclass
class GoldExample:
    id: str
    source_url: str
    text: str
    expected: dict
    split: str = "test"
    entities: list[EntityAnnotation] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "GoldExample":
        ents = [
            EntityAnnotation(
                text=e["text"], label=e["label"], start=e["start"], end=e["end"]
            )
            for e in d.get("entities", [])
        ]
        return cls(
            id=d["id"],
            source_url=d.get("source_url", ""),
            text=d["text"],
            expected=d.get("expected", {}),
            split=d.get("split", "test"),
            entities=ents,
        )


def load_corpus(path: str | Path) -> list[GoldExample]:
    """Load a JSONL gold-standard corpus."""
    path = Path(path)
    examples: list[GoldExample] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            examples.append(GoldExample.from_dict(json.loads(line)))
    return examples


def corpus_by_split(examples: list[GoldExample]) -> dict[str, list[GoldExample]]:
    out: dict[str, list[GoldExample]] = {}
    for ex in examples:
        out.setdefault(ex.split, []).append(ex)
    return out
