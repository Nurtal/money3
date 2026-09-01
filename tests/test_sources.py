from aap_watcher.scrapers.sources import available_sources, get_source
from aap_watcher.scrapers.sources_catalog import (
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

# Each fixture reproduces the *real* markup of the corresponding listing page
# (corrected August 2026). `link_in_block` signals whether the detail <a> sits
# inside the entry block (heading tags carrying their own link for INCa/ARS/…).

FIXTURES = {
    "anr": dict(
        scraper=ANRScraper,
        link_in_block=True,
        html="""
        <html><body>
        <h2><a href="https://anr.fr/fr/detail/call/aapg-appel-a-projets-generique-2027/">
          AAPG - Appel à projets générique 2027</a></h2>
        <h2><a href="https://anr.fr/fr/detail/call/labcom-2026/">LabCom 2026</a></h2>
        </body></html>
        """,
        expect=["AAPG", "LabCom"],
    ),
    "inca": dict(
        scraper=INCaScraper,
        link_in_block=True,
        html="""
        <html><body>
        <div class="card">
          <h2 class="card-title">
            <a href="/professionnels/.../prt-k27">Appel à projets Programme de
            recherche translationnelle en cancérologie PRT-K 2026-2027</a>
          </h2>
        </div>
        <div class="card">
          <h2 class="card-title">
            <a href="/professionnels/.../plbio26">Appel à projets PLBIO - Biologie
            et Sciences du Cancer</a>
          </h2>
        </div>
        </body></html>
        """,
        expect=["PRT-K", "PLBIO"],
    ),
    "ars": dict(
        scraper=ARSScraper,
        link_in_block=True,
        html="""
        <html><body>
        <div class="accueil-appels-projets--item">
          <h3 class="accueil-appels-projets--item-titre">
            <a href="//www.pays-de-la-loire.ars.sante.fr/appel-projet-ehpad"
               target="_blank">Création d'un EHPAD - Nord Sarthe</a>
          </h3>
        </div>
        <div class="accueil-appels-projets--item">
          <h3 class="accueil-appels-projets--item-titre">
            <a href="//www.pays-de-la-loire.ars.sante.fr/prevention-chutes"
               target="_blank">prévention des chutes des personnes âgées</a>
          </h3>
        </div>
        </body></html>
        """,
        expect=["EHPAD", "chutes"],
    ),
    "fondation_arc": dict(
        scraper=FondationARCScraper,
        link_in_block=True,
        html="""
        <html><body>
        <div class="card">
          <h2><a href="https://www.fondation-arc.org/appels-a-projets/pancreas-2026/">
            PANCRÉAS 2026 : cancer du pancréas</a></h2>
        </div>
        <div class="card">
          <h2><a href="https://www.fondation-arc.org/appels-a-projets/passerelle/">
            Passerelle</a></h2>
        </div>
        </body></html>
        """,
        expect=["PANCRÉAS", "Passerelle"],
    ),
    "frm": dict(
        scraper=FRMScraper,
        link_in_block=False,
        html="""
        <html><body>
        <details>
          <summary class="Program_summary"><h3 class="Program_title">Amorçage de
            jeunes équipes 2026 - Session 2</h3>
            <p class="Program_date">Date de clôture : 04 septembre 2026</p>
          </summary>
        </details>
        <details>
          <summary class="Program_summary"><h3 class="Program_title">Prématuration
            de projets FRM 2026</h3>
            <p class="Program_date">Date de clôture : 30 avril 2026</p>
          </summary>
        </details>
        </body></html>
        """,
        expect=["Amorçage", "Prématuration"],
    ),
    "ligue_cancer": dict(
        scraper=LigueContreLeCancerScraper,
        link_in_block=True,
        html="""
        <html><body>
        <article>
          <h2>Subvention colloque (session 2)</h2>
          <p>En cours 12/05/2026 - 04/09/2026</p>
          <a href="https://www.ligue-cancer.net/colloque-s2">Détails</a>
        </article>
        <article>
          <h2>Allocations doctorales (3 ans)</h2>
          <p>National</p>
          <a href="https://www.ligue-cancer.net/doc3">Détails</a>
        </article>
        </body></html>
        """,
        expect=["colloque", "doctorales"],
    ),
    "fondation_france": dict(
        scraper=FondationDeFranceScraper,
        link_in_block=True,
        html="""
        <html><body>
        <div class="aap">
          <h2><a href="https://www.fondationdefrance.org/fr/appels-a-projets/neuro">
            Recherche sur les maladies neurodégénératives</a></h2>
        </div>
        <div class="aap">
          <h2><a href="https://www.fondationdefrance.org/fr/appels-a-projets/cardio">
            Recherche sur les maladies cardiovasculaires</a></h2>
        </div>
        </body></html>
        """,
        expect=["neurodégénératives", "cardiovasculaires"],
    ),
    "inserm": dict(
        scraper=InsermScraper,
        link_in_block=True,
        html="""
        <html><body>
        <ul>
          <li><a href="https://pro.inserm.fr/rubriques/appels-a-projets/mcmp">
            Exploration fonctionnelle du microenvironnement des cancers (MCMP)</a></li>
          <li><a href="https://pro.inserm.fr/rubriques/appels-a-projets/psci">
            Apports de la physique à l'oncologie (PCSI)</a></li>
        </ul>
        </body></html>
        """,
        expect=["MCMP", "PCSI"],
    ),
    "cnrs": dict(
        scraper=CNRSScraper,
        link_in_block=True,
        html="""
        <html><body>
        <div class="appel">
          <h3><a href="https://miti.cnrs.fr/appels-a-projets/ecoconception/">
            Appel à projets : Ecoconception</a></h3>
        </div>
        <div class="appel">
          <h3><a href="https://miti.cnrs.fr/appels-a-projets/biologie-numerique/">
            Biologie numérique : AMI</a></h3>
        </div>
        </body></html>
        """,
        expect=["Ecoconception", "Biologie"],
    ),
    "inria": dict(
        scraper=InriaScraper,
        link_in_block=True,
        html="""
        <html><body>
        <li><a href="https://www.inria.fr/fr/equipes-associees-2027">
            Appel à candidature Équipes Associées 2027</a></li>
        <li><a href="https://www.inria.fr/fr/chaires-internationales-2027">
            Appel à candidature Chaires internationales 2027</a></li>
        </body></html>
        """,
        expect=["Équipes Associées", "Chaires"],
    ),
    "inrae": dict(
        scraper=InraeScraper,
        link_in_block=True,
        html="""
        <html><body>
        <div class="appel">
          <h3><a href="https://explorae.inrae.fr/fr/challenges">Appel à idées
            EXPLORATION</a></h3>
        </div>
        <div class="appel">
          <h3><a href="https://better.hub.inrae.fr/ami-2027">AMI 2027 -
            Métaprogramme BETTER</a></h3>
        </div>
        </body></html>
        """,
        expect=["EXPLORATION", "BETTER"],
    ),
    "bettencourt": dict(
        scraper=BettencourtScraper,
        link_in_block=False,
        html="""
        <html><body>
        <div class="prix">
          <h2>Prix Liliane Bettencourt pour les sciences du vivant</h2>
          <p>Attribué à un chercheur de moins de 45 ans</p>
        </div>
        <div class="prix">
          <h2>Impulscience</h2>
          <p>7 soutiens de 2,3 M€ sur 5 ans</p>
        </div>
        </body></html>
        """,
        expect=["sciences du vivant", "Impulscience"],
    ),
    "bpi": dict(
        scraper=BPIScraper,
        link_in_block=False,
        html="""
        <html><body>
        <ul class="listing-block">
          <li>
            <div class="article-card">
              <h3><a href="/nos-appels-a-projets-concours/appel-a-projets-ast">
                Appel à projets : PIIEC sur les semiconducteurs</a></h3>
            </div>
          </li>
          <li>
            <div class="article-card">
              <h3><a href="/nos-appels-a-projets-concours/appel-a-projets-bio">
                Appel à Projets Innovations en biothérapies</a></h3>
            </div>
          </li>
        </ul>
        </body></html>
        """,
        expect=["semiconducteurs", "biothérapies"],
    ),
    "appel_projet_recherche": dict(
        scraper=AppelsProjetsRechercheScraper,
        link_in_block=True,
        html="""
        <html><body>
        <div class="position-relative card border-0 bg-reversed h-100">
          <h5>Pré-annonce : Appel à projets Transnational Conjoint 2026</h5>
          <a href="/appel/1-anr-1988" class="btn">Lire la suite</a>
        </div>
        <div class="position-relative card border-0 bg-reversed h-100">
          <h5>Appel à candidatures ANR 2027</h5>
          <a href="/appel/1-anr-1994" class="btn">Lire la suite</a>
        </div>
        </body></html>
        """,
        expect=["Transnational Conjoint", "ANR 2027"],
    ),
    "tete_cou": dict(
        scraper=TeteCouScraper,
        link_in_block=True,
        html="""
        <html><body>
        <h2>en cours</h2>
        <h3><a href="https://www.tete-cou.fr/recherche/appels-a-projets/fondation">
          Fondation Maladies Rares</a></h3>
        <h3><a href="https://www.tete-cou.fr/recherche/appels-a-projets/erc">
          European Research Council (ERC)</a></h3>
        </body></html>
        """,
        expect=["Maladies Rares", "ERC"],
    ),
    "research_connect": dict(
        scraper=ResearchConnectScraper,
        link_in_block=True,
        html="""
        <html><body>
        <article>
          <h2><a href="https://myresearchconnect.com/news/epilepsy-2026/">
            Epilepsy Research Institute UK Awards Open for 2026</a></h2>
        </article>
        <article>
          <h2><a href="https://myresearchconnect.com/news/st-andrews-env-prize/">
            Launch of 2026-2027 St Andrews Environment Prize</a></h2>
        </article>
        </body></html>
        """,
        expect=["Epilepsy", "St Andrews"],
    ),
    "bzh": dict(
        scraper=BZHScraper,
        link_in_block=True,
        html="""
        <html><body>
        <h2><a href="https://www.bretagne.bzh/aides/langue-bretonne-aroad/">
          Langue bretonne – Arload – Création de ressources numériques</a></h2>
        <h2><a href="https://www.bretagne.bzh/aides/langue-bretonne-stlenn/">
          Langue bretonne – Stlenn – Traduction de ressources numériques</a></h2>
        </body></html>
        """,
        expect=["Arload", "Stlenn"],
    ),
    "girci_go": dict(
        scraper=GirciGoScraper,
        link_in_block=True,
        html="""
        <html><body>
        <article>
          <h2><a href="https://www.chu-hugo.fr/appels-a-projets/2027">
            Appels à projets 2027 du GIRCI Grand Ouest</a></h2>
        </article>
        <article>
          <h2><a href="https://www.chu-hugo.fr/appels-a-projets/laureats/">
            Lauréats des appels à projets du GIRCI Grand Ouest</a></h2>
        </article>
        </body></html>
        """,
        expect=["GIRCI Grand Ouest", "Lauréats"],
    ),
    "europe": dict(
        scraper=HorizonEuropeScraper,
        link_in_block=True,
        html="""
        <html><body>
        <article>
          <h2><a href="https://www.horizon-europe.gouv.fr/meetup-greentech-2026">
            Meet'Up Greentech 2026</a></h2>
        </article>
        <article>
          <h2><a href="https://www.horizon-europe.gouv.fr/webinaire-eic-transition">
            Webinaire checklist EIC Transition 2026</a></h2>
        </article>
        </body></html>
        """,
        expect=["Greentech", "EIC Transition"],
    ),
    "thesaurus": dict(
        scraper=ThesaurusScraper,
        link_in_block=True,
        html="""
        <html><body>
        <table>
          <tr><td><b>DGRINES : PHRC-N 2026/2027</b></td>
              <td><a href="/thesaurus/financement/5766">Détail</a></td></tr>
          <tr><td><b>PHRIP 2027</b></td>
              <td><a href="/thesaurus/financement/5657">Détail</a></td></tr>
        </table>
        </body></html>
        """,
        expect=["PHRC-N", "PHRIP"],
    ),
    "pasteur": dict(
        scraper=PasteurScraper,
        link_in_block=True,
        html="""
        <html><body>
        <div class="aap">
          <h3><a href="https://research.pasteur.fr/fr/appels-a-projets/antimicrobial/">
            Appel à projets : Recherche sur la résistance antimicrobienne</a></h3>
        </div>
        <div class="aap">
          <h3><a href="https://research.pasteur.fr/fr/appels-a-projets/emerging-viruses/">
            Appel à projets : Virus émergents et pandémies</a></h3>
        </div>
        </body></html>
        """,
        expect=["Antimicrobienne", "Virus émergents"],
    ),
    "ademe": dict(
        scraper=AdemeScraper,
        link_in_block=True,
        html="""
        <html><body>
        <div class="position-relative card border-0">
          <h5><a href="https://agirpourlatransition.ademe.fr/entreprises/appel-projets-decarbonation">
            Appel à projets : Décarbonation de l'industrie</a></h5>
        </div>
        <div class="position-relative card border-0">
          <h5><a href="https://agirpourlatransition.ademe.fr/entreprises/appel-projets-vehicules">
            Appel à projets : Véhicules du futur</a></h5>
        </div>
        </body></html>
        """,
        expect=["Décarbonation", "Véhicules"],
    ),
    "afm": dict(
        scraper=AFMTéléthonScraper,
        link_in_block=True,
        html="""
        <html><body>
        <div class="aap">
          <h2><a href="https://www.afm-telethon.fr/recherche/appel-projets-myopathies">
            Appel à projets : Myopathies et dystrophies musculaires</a></h2>
        </div>
        <div class="aap">
          <h2><a href="https://www.afm-telethon.fr/recherche/appel-projets-gene-therapy">
            Appel à projets : Thérapie génique des maladies rares</a></h2>
        </div>
        </body></html>
        """,
        expect=["Myopathies", "Thérapie génique"],
    ),
    "ansm": dict(
        scraper=ANSMScraper,
        link_in_block=True,
        html="""
        <html><body>
        <div class="appel">
          <h3><a href="https://ansm.sante.fr/appels-a-projets/pharmacovigilance">
            Appel à projets : Pharmacovigilance et sécurité des médicaments</a></h3>
        </div>
        <div class="appel">
          <h3><a href="https://ansm.sante.fr/appels-a-projets/essais-cliniques">
            Appel à projets : Essais cliniques et biomédicaux</a></h3>
        </div>
        </body></html>
        """,
        expect=["Pharmacovigilance", "Essais cliniques"],
    ),
    "alzheimer": dict(
        scraper=AlzheimerScraper,
        link_in_block=True,
        html="""
        <html><body>
        <div class="aap">
          <h2><a href="https://www.fondation-alzheimer.org/appels-a-projets/neuroproteomique">
            Appel à projets : Neuroprotéomique de la maladie d'Alzheimer</a></h2>
        </div>
        <div class="aap">
          <h2><a href="https://www.fondation-alzheimer.org/appels-a-projets/accompagnement">
            Appel à projets : Recherche sur l'accompagnement et les aidants</a></h2>
        </div>
        </body></html>
        """,
        expect=["Neuroprotéomique", "aidants"],
    ),
}

SOURCES_UNDER_TEST = {
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


def test_registry_contains_all_sources():
    names = available_sources()
    for key in SOURCES_UNDER_TEST:
        assert key in names


def test_each_source_discovers_documents_offline():
    for key, spec in FIXTURES.items():
        docs = list(spec["scraper"]().discover(spec["html"]))
        assert len(docs) == len(spec["expect"]), key
        assert spec["expect"][0].lower() in docs[0].text.lower(), f"{key}: {docs[0].text}"
        if spec["link_in_block"]:
            assert docs[0].source_url.startswith("http"), key
        else:
            # No link inside the block -> fall back to the listing URL.
            assert docs[0].source_url == spec["scraper"].listing_url, key


def test_get_source_returns_configured_adapter():
    scraper = get_source("inca")
    assert isinstance(scraper, INCaScraper)
    assert scraper.source_name == "inca"
