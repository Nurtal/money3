"""Extraction layer.

Every extraction strategy (regex, dictionary, spaCy, BERT/CamemBERT, LLM,
hybrid) MUST implement the ``Extractor`` interface so all strategies receive
identical inputs and produce comparable ``AAPExtraction`` outputs. This is a
hard project constraint: do not special-case inputs/outputs per strategy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol

from ..schema import AAPExtraction


@dataclass
class Document:
    """Normalised input passed to every extractor.

    ``text`` is the plain-text content to extract from; ``html`` is kept for
    source adapters that need structure; ``source_url`` enables provenance.
    """

    text: str
    source_url: Optional[str] = None
    html: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class Extractor(Protocol):
    """Common interface implemented by all extraction strategies."""

    name: str

    def extract(self, document: Document) -> AAPExtraction:
        """Extract a normalised AAP from ``document``."""
        ...
