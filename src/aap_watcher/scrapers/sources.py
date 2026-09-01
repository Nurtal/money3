"""Registry of source adapters.

Returns every available source adapter so the pipeline/CLI can scrape one or
all of them. New sources are registered here (see ``sources_catalog.py``).
"""

from __future__ import annotations

from .sources_catalog import (
    AFMTéléthonScraper,
    ANSMScraper,
    ANRScraper,
    ARSScraper,
    AdemeScraper,
    AlzheimerScraper,
    AppelsProjetsRechercheScraper,
    BPIScraper,
    BZHScraper,
    BettencourtScraper,
    CNRSScraper,
    FRMScraper,
    FondationARCScraper,
    FondationDeFranceScraper,
    GirciGoScraper,
    HorizonEuropeScraper,
    INCaScraper,
    InraeScraper,
    InriaScraper,
    InsermScraper,
    LigueContreLeCancerScraper,
    PasteurScraper,
    ResearchConnectScraper,
    TeteCouScraper,
    ThesaurusScraper,
)

SOURCES = {
    "anr": ANRScraper,
    "inca": INCaScraper,
    "ars": ARSScraper,
    "fondation_arc": FondationARCScraper,
    "frm": FRMScraper,
    "ligue_cancer": LigueContreLeCancerScraper,
    "fondation_france": FondationDeFranceScraper,
    "inserm": InsermScraper,
    "cnrs": CNRSScraper,
    "inria": InriaScraper,
    "inrae": InraeScraper,
    "bettencourt": BettencourtScraper,
    "thesaurus": ThesaurusScraper,
    "bpi": BPIScraper,
    "appel_projet_recherche": AppelsProjetsRechercheScraper,
    "tete_cou": TeteCouScraper,
    "research_connect": ResearchConnectScraper,
    "bzh": BZHScraper,
    "girci_go": GirciGoScraper,
    "europe": HorizonEuropeScraper,
    "pasteur": PasteurScraper,
    "ademe": AdemeScraper,
    "afm": AFMTéléthonScraper,
    "ansm": ANSMScraper,
    "alzheimer": AlzheimerScraper,
}


def available_sources() -> list[str]:
    return list(SOURCES.keys())


def get_source(name: str):
    if name not in SOURCES:
        raise KeyError(f"Unknown source '{name}'. Available: {available_sources()}")
    return SOURCES[name]()
