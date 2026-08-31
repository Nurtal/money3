"""Concrete source adapters (Phase 4 — multi-source ingestion).

Each is an independent adapter implementing the shared scraper interface. Add a
new source by subclassing :class:`GenericSourceScraper` (or ``BaseScraper`` for
non-standard layouts), then register it in ``sources.py`` and add a fixture +
test (README: contributing → add a source).
"""

from __future__ import annotations

from .generic import GenericSourceScraper


class INCaScraper(GenericSourceScraper):
    source_name = "inca"
    listing_url = "https://www.e-cancer.fr/Professionnels-de-sante/Appels-a-projets"


class ARSScraper(GenericSourceScraper):
    source_name = "ars"
    listing_url = "https://www.ars.sante.fr/appels-a-projets"


class FondationARCScraper(GenericSourceScraper):
    source_name = "fondation_arc"
    listing_url = "https://www.fondation-arc.org/nos-aides-et-subventions"


class FRMScraper(GenericSourceScraper):
    source_name = "frm"
    listing_url = "https://www.frm.org/appels-a-projets"


class LigueContreLeCancerScraper(GenericSourceScraper):
    source_name = "ligue_cancer"
    listing_url = "https://www.ligue-cancer.net/Appels_a_projets"


class FondationDeFranceScraper(GenericSourceScraper):
    source_name = "fondation_france"
    listing_url = "https://www.fondationdefrance.org/fr/appels-a-projets"


class InsermScraper(GenericSourceScraper):
    source_name = "inserm"
    listing_url = "https://www.inserm.fr/financer-votre-projet/appels-a-projets/"


class CNRSScraper(GenericSourceScraper):
    source_name = "cnrs"
    listing_url = "https://www.cnrs.fr/fr/appels-a-projets-et-candidatures"


class InriaScraper(GenericSourceScraper):
    source_name = "inria"
    listing_url = "https://www.inria.fr/fr/appels-a-propositions-et-a-candidatures"


class InraeScraper(GenericSourceScraper):
    source_name = "inrae"
    listing_url = "https://www.inrae.fr/appels-projets"


class BettencourtScraper(GenericSourceScraper):
    source_name = "bettencourt"
    listing_url = "https://www.fondationbs.org/fr/nos-appels-a-projets"
