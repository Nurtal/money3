"""Registry of source adapters.

Returns every available source adapter so the pipeline/CLI can scrape one or
all of them. New sources are registered here (see ``sources_catalog.py``).
"""

from __future__ import annotations

from .anr import ANRScraper
from .sources_catalog import (
    ARSScraper,
    FRMScraper,
    FondationARCScraper,
    FondationDeFranceScraper,
    INCaScraper,
    LigueContreLeCancerScraper,
)

SOURCES = {
    "anr": ANRScraper,
    "inca": INCaScraper,
    "ars": ARSScraper,
    "fondation_arc": FondationARCScraper,
    "frm": FRMScraper,
    "ligue_cancer": LigueContreLeCancerScraper,
    "fondation_france": FondationDeFranceScraper,
}


def available_sources() -> list[str]:
    return list(SOURCES.keys())


def get_source(name: str):
    if name not in SOURCES:
        raise KeyError(f"Unknown source '{name}'. Available: {available_sources()}")
    return SOURCES[name]()
