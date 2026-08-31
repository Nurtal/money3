"""Concrete source adapters (Phase 4 — multi-source ingestion).

Each is an independent adapter implementing the shared scraper interface. Add a
new source by subclassing :class:`GenericSourceScraper` (or ``BaseScraper`` for
non-standard layouts), then register it in ``sources.py`` and add a fixture +
test (README: contributing → add a source).

``entry_block`` is a regex whose named group ``body`` delimits a single AAP
entry. Real listing pages rarely use per-entry ``<article>``/``<li>``; most put
each title (and often its link) inside a heading tag, so we override the block
delimiter per source. ``listing_url`` values were validated against the live
sites (corrected 2026-08).
"""

from __future__ import annotations

from .generic import GenericSourceScraper

#: Entry is a single ``<h2>`` (title + possibly the detail link inside it).
_H2_BLOCK = r"<h2[^>]*>(?P<body>.*?)</h2>"

#: Entry is a single ``<h3>`` (ARS/FRM/CNRS style heading entries).
_H3_BLOCK = r"<h3[^>]*>(?P<body>.*?)</h3>"


class ANRScraper(GenericSourceScraper):
    source_name = "anr"
    listing_url = "https://anr.fr/fr/appels-a-projets/"
    entry_block = _H2_BLOCK


class INCaScraper(GenericSourceScraper):
    source_name = "inca"
    listing_url = (
        "https://www.cancer.fr/professionnels-de-la-recherche/"
        "appels-a-projets-et-a-candidatures/nos-appels-a-projets"
    )
    entry_block = _H2_BLOCK


class ARSScraper(GenericSourceScraper):
    source_name = "ars"
    listing_url = "https://www.ars.sante.fr/liste-appels-projet-candidature-nationale"
    entry_block = _H3_BLOCK


class FondationARCScraper(GenericSourceScraper):
    source_name = "fondation_arc"
    listing_url = "https://www.fondation-arc.org/appels-a-projets/"
    entry_block = _H2_BLOCK


class FRMScraper(GenericSourceScraper):
    source_name = "frm"
    listing_url = "https://www.frm.org/fr/programmes"
    entry_block = _H3_BLOCK


class LigueContreLeCancerScraper(GenericSourceScraper):
    source_name = "ligue_cancer"
    listing_url = "https://www.ligue-cancer.net/espace-chercheur"


class FondationDeFranceScraper(GenericSourceScraper):
    source_name = "fondation_france"
    listing_url = "https://www.fondationdefrance.org/fr/appels-a-projets"
    entry_block = _H2_BLOCK


class InsermScraper(GenericSourceScraper):
    source_name = "inserm"
    listing_url = "https://pro.inserm.fr/appels-a-projets"


class CNRSScraper(GenericSourceScraper):
    source_name = "cnrs"
    listing_url = "https://miti.cnrs.fr/appels-a-projets/"
    entry_block = _H3_BLOCK


class InriaScraper(GenericSourceScraper):
    source_name = "inria"
    listing_url = "https://www.inria.fr/fr/appels-a-propositions-et-a-candidatures"


class InraeScraper(GenericSourceScraper):
    source_name = "inrae"
    listing_url = "https://explorae.inrae.fr/fr"
    entry_block = _H3_BLOCK


class BettencourtScraper(GenericSourceScraper):
    source_name = "bettencourt"
    listing_url = "https://www.fondationbs.org/candidater-un-prix"
    entry_block = _H2_BLOCK
