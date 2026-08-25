# AAP Watcher

Automated monitoring, extraction and benchmarking of **Appels à Projets (AAP)** from French and European research, healthcare and funding organisations.

AAP Watcher continuously monitors websites publishing funding opportunities, discovers candidate AAPs, extracts their content, normalises it into a common schema and stores it in a searchable, historical database.

The project is deliberately designed as an **information-extraction benchmark platform**: multiple extraction technologies are implemented and evaluated on the exact same corpus.

---

## 🎯 Objectives

Funding opportunities are highly fragmented across:

- Institutional websites
- HTML pages
- PDFs
- News pages
- Dedicated application platforms
- Archives
- Regional websites
- Foundation websites
- European funding portals

AAP Watcher aims to transform this fragmented information into a structured, machine-readable database.

For every AAP, the system should attempt to extract:

| Field | Description |
|---|---|
| `title` | Name of the call for projects |
| `organisation` | Funding organisation |
| `description` | Description of the opportunity |
| `amount_min` | Minimum funding |
| `amount_max` | Maximum funding |
| `currency` | Currency |
| `opening_date` | Opening date |
| `deadline` | Submission deadline |
| `eligibility` | Eligibility conditions |
| `eligible_applicants` | Who can apply |
| `research_topics` | Scientific/thematic areas |
| `geographical_scope` | Geographic eligibility |
| `project_duration` | Maximum project duration |
| `funding_type` | Grant, fellowship, equipment, infrastructure, etc. |
| `application_url` | Official application page |
| `source_url` | Original source |
| `documents` | Associated documents |
| `contact` | Contact information |
| `status` | Upcoming / open / closed / archived |
| `last_updated` | Last detected modification |
| `scraped_at` | Extraction timestamp |
| `extraction_method` | Technology used |
| `confidence_score` | Extraction confidence |

The project has two complementary objectives:

1. Build a useful and continuously updated funding-opportunity database.
2. **Benchmark different information-extraction strategies on the exact same task and corpus.**

---

# 🎯 Target sources

Initial targets include:

- ANR — Agence Nationale de la Recherche
- ARS — Agences Régionales de Santé
- INCa — Institut National du Cancer
- Fondation ARC
- Fondation pour la Recherche Médicale
- Ligue contre le cancer
- Fondation de France
- Inserm
- CNRS
- Universities
- CHU / hospital foundations
- Disease-specific foundations
- Regional funding organisations
- European funding organisations
- Horizon Europe
- Other public and private research funders

The architecture must make it easy to add new sources through independent source adapters.

---

# 🧠 Core idea: extraction as a benchmark

The project must **not assume that an LLM is the best extraction technology**.

Instead, the extraction layer is designed as a pluggable system where multiple approaches compete on the same dataset.

Initial benchmark:

    Regex / Rules
         │
         ├── Dictionaries / Gazetteers
         │
         ├── Classical NLP
         │
         ├── spaCy NER
         │
         ├── BERT / CamemBERT
         │
         ├── Other Transformers
         │
         ├── LLM
         │
         └── Hybrid approaches

The benchmark evaluates:

- Precision
- Recall
- F1-score
- Exact match
- Normalised match
- Robustness
- Latency
- Memory consumption
- Computational cost
- API cost
- Reproducibility
- Maintenance complexity

The goal is not to determine which technology is universally "best".

The goal is to determine:

> Which extraction strategy provides the best trade-off between accuracy, robustness, cost and complexity for each type of AAP information?

---

# 🔬 Extraction strategies

## 1. Regex / rule-based extraction

The simplest baseline.

Regex is particularly appropriate for highly structured information such as:

- Dates
- Amounts
- Percentages
- Durations
- Email addresses
- URLs
- Explicit labels
- Application identifiers

Example:

    Date limite : 15 octobre 2026
    Montant maximum : 500 000 €
    Financement jusqu'à 250k€

### Advantages

- Extremely fast
- Deterministic
- Very cheap
- Easy to understand
- Easy to debug
- No training required

### Weaknesses

- Brittle
- Difficult to maintain for heterogeneous sources
- Poor semantic understanding
- Weak for complex eligibility criteria

Regex serves as an important baseline.

---

# 2. Dictionary / gazetteer-based extraction

Use curated vocabularies for concepts such as:

### Applicant types

- University
- Hospital
- Inserm
- CNRS
- SME
- Association
- Foundation
- Research organisation
- Public institution

### Research topics

- Cancer
- Immunology
- Rare diseases
- AI
- Machine learning
- Digital health
- Public health
- Clinical research

This approach can be combined with contextual rules.

### Advantages

- Simple
- Fast
- Explainable
- Easy to update
- Excellent for controlled vocabularies

### Weaknesses

- Vocabulary coverage
- Synonyms
- Ambiguity
- Poor generalisation

---

# 3. Classical NLP

Traditional NLP methods provide another baseline before moving to neural models.

Potential techniques:

- Tokenisation
- Sentence segmentation
- Lemmatization
- POS tagging
- Dependency parsing
- TF-IDF
- n-grams
- Keyword extraction
- Text classification
- CRF
- Logistic Regression
- SVM

Potential tools:

- spaCy
- scikit-learn
- NLTK

Possible tasks:

- AAP detection
- Topic classification
- Funding type classification
- Eligibility classification
- Applicant classification

Example:

    Document
       ↓
    TF-IDF
       ↓
    Classifier
       ↓
    AAP / NOT_AAP

---

# 4. spaCy NER

A custom Named Entity Recognition model can be trained specifically for AAP documents.

Possible entities:

    AAP_TITLE
    ORGANISATION
    AMOUNT
    CURRENCY
    DATE
    DEADLINE
    ELIGIBILITY
    APPLICANT_TYPE
    RESEARCH_TOPIC
    DURATION
    GEOGRAPHIC_SCOPE
    FUNDING_TYPE

Example:

    Les projets doivent être soumis avant le 15 octobre 2026.

                                          └──────────────┘
                                              DEADLINE

Benchmark variants:

    spaCy generic NER
            vs
    spaCy custom NER

---

# 5. BERT / Transformer token classification

The extraction problem can be formulated as token classification.

Example:

    Les        O
    projets    O
    doivent    O
    être       O
    soumis     O
    avant      O
    le         O
    15         B-DEADLINE
    octobre    I-DEADLINE
    2026       I-DEADLINE

Potential models:

- BERT
- RoBERTa
- DistilBERT
- CamemBERT
- French-specific transformers
- Domain-specific transformers

For French AAPs, **CamemBERT and other French-language transformers should be explicitly benchmarked**.

---

# 6. Transformer classification

Not every extraction problem needs NER.

Some fields are better treated as classification tasks.

Example:

    Does this AAP concern cancer?

    YES / NO

Funding type:

    GRANT
    FELLOWSHIP
    EQUIPMENT
    TRAINING
    INFRASTRUCTURE
    OTHER

Applicant:

    UNIVERSITY
    HOSPITAL
    RESEARCH_ORGANISATION
    SME
    ASSOCIATION
    OTHER

This enables specialised models for individual extraction tasks.

---

# 7. LLM structured extraction

LLMs represent another candidate extraction technology.

The document is provided to a model together with a strict schema.

Example JSON:

    {
      "title": "Programme X 2027",
      "amount_min": null,
      "amount_max": 500000,
      "currency": "EUR",
      "deadline": "2026-10-15",
      "eligible_applicants": [
        "Universities",
        "Public research organisations"
      ],
      "research_topics": [
        "Cancer",
        "Immunology"
      ]
    }

The LLM must follow strict rules:

- Never invent missing information.
- Return `null` when information is unavailable.
- Preserve original source text.
- Produce schema-valid output.
- Record model version.
- Record prompt version.
- Record extraction timestamp.

---

# 8. Local LLM vs API LLM

The benchmark should distinguish:

- Local small models
- Local medium models
- Local large models
- External API models

Relevant dimensions:

- Accuracy
- Latency
- Cost
- Hardware requirements
- Privacy
- Reproducibility
- Availability

Potential local inference backends:

- Ollama
- LM Studio
- llama.cpp
- vLLM
- Other OpenAI-compatible local servers

---

# 9. Hybrid extraction

Hybrid approaches combine multiple technologies.

Example:

    RAW DOCUMENT
         │
         ▼
    ┌───────────────┐
    │ Regex / Rules │
    └───────┬───────┘
            │
       Dates / Amounts
            │
            ▼
    ┌───────────────┐
    │    spaCy      │
    └───────┬───────┘
            │
    Organisations
    Applicant types
            │
            ▼
    ┌───────────────┐
    │  Transformer  │
    └───────┬───────┘
            │
       Topics / NER
            │
            ▼
    ┌───────────────┐
    │      LLM      │
    └───────┬───────┘
            │
    Complex eligibility
            │
            ▼
       FINAL AAP OBJECT

A hybrid pipeline may provide a better accuracy/cost trade-off than an LLM-only architecture.

This must be tested rather than assumed.

---

# 🏆 Benchmark architecture

Every extractor must implement the same interface.

    class Extractor(Protocol):

        def extract(
            self,
            document: Document
        ) -> AAPExtraction:
            ...

Implementations:

    extractors/
    ├── base.py
    ├── regex.py
    ├── dictionary.py
    ├── classical_nlp.py
    ├── spacy_ner.py
    ├── bert_ner.py
    ├── transformer_classifier.py
    ├── llm.py
    └── hybrid.py

This guarantees that all methods receive identical inputs and produce comparable outputs.

---

# 📊 Benchmark dataset

A manually annotated **gold-standard corpus** is required.

Initial target:

    500–1,000 AAP documents

The corpus should contain:

- ANR AAPs
- ARS AAPs
- INCa AAPs
- Foundation AAPs
- HTML pages
- PDFs
- Short documents
- Long documents
- Simple AAPs
- Complex AAPs
- Different years
- Different funding amounts
- Different deadline formats
- Different eligibility structures

Dataset split:

    TRAIN
    VALIDATION
    TEST

The test set must remain isolated from model development.

---

# 🏷️ Annotation

Annotations should exist at two levels.

## Entity level

    {
      "text": "15 octobre 2026",
      "label": "DEADLINE",
      "start": 1823,
      "end": 1839
    }

## Structured level

    {
      "deadline": "2026-10-15",
      "amount_max": 500000,
      "currency": "EUR"
    }

This allows the benchmark to distinguish:

- NER performance
- Final structured extraction performance

---

# 📏 Evaluation metrics

## Entity extraction

Calculate:

- Precision
- Recall
- F1
- Exact Match
- Partial Match

Example:

Gold:

    15 octobre 2026

Prediction:

    15/10/2026

Raw string:

    Exact Match = 0

After normalisation:

    Normalised Match = 1

Both metrics should therefore be reported.

---

# 🧮 Field-level evaluation

Every field gets an independent score.

Fields:

- title
- organisation
- amount
- deadline
- eligibility
- eligible_applicants
- research_topics
- duration
- geographical_scope
- funding_type

Example:

| Field | Regex | spaCy | CamemBERT | LLM | Hybrid |
|---|---:|---:|---:|---:|---:|
| Title | — | — | — | — | — |
| Organisation | — | — | — | — | — |
| Amount | — | — | — | — | — |
| Deadline | — | — | — | — | — |
| Eligibility | — | — | — | — | — |
| Topics | — | — | — | — | — |
| Duration | — | — | — | — | — |

Values will be populated by actual benchmark runs.

**No manually estimated scores should be included in the repository.**

---

# ⚡ Performance benchmark

Accuracy is only one dimension.

Every benchmark run should measure:

## Latency

- Documents / second
- Milliseconds / document

## Memory

- RAM
- GPU VRAM

## Compute

- CPU utilisation
- GPU utilisation

## Cost

For API models:

- €/1,000 documents
- €/10,000 documents
- €/1M tokens

For local models:

- Inference time
- Hardware requirements
- Energy consumption when measurable

---

# ⚖️ Benchmark dimensions

The benchmark should ultimately produce a matrix such as:

| Technology | F1 | Recall | Precision | Latency | Cost | RAM | Training |
|---|---:|---:|---:|---:|---:|---:|---|
| Regex | | | | | | | No |
| Dictionary | | | | | | | No |
| Classical NLP | | | | | | | Optional |
| spaCy NER | | | | | | | Yes |
| BERT | | | | | | | Yes |
| CamemBERT | | | | | | | Yes |
| LLM | | | | | | | No |
| Hybrid | | | | | | | Mixed |

---

# 🧪 Benchmark experiments

The project should explicitly test the following hypotheses.

## H1 — Rules are sufficient for simple fields

Compare:

    Regex
    vs
    ML / LLM

For:

- Dates
- Amounts
- URLs

## H2 — Classical NLP improves semantic extraction

Compare:

    Regex
    vs
    Regex + Classical NLP

## H3 — Domain-specific NER improves extraction

Compare:

    spaCy generic
    vs
    spaCy custom NER

## H4 — Transformers outperform classical NLP

Compare:

    spaCy
    vs
    BERT
    vs
    CamemBERT

## H5 — LLMs improve complex semantic extraction

Especially for:

- Eligibility
- Applicant requirements
- Project constraints
- Funding conditions

## H6 — Hybrid systems provide the best trade-off

Compare:

    Regex
    +
    spaCy
    +
    Transformer
    +
    LLM

versus:

    LLM only

---

# 🧪 Reproducible benchmark CLI

Example:

    aap-benchmark run \
        --dataset benchmark-v1 \
        --extractors regex dictionary spacy bert camembert llm hybrid

Generate a report:

    aap-benchmark report \
        --input results/benchmark-v1

Example output:

    AAP Extraction Benchmark
    =========================

    Dataset: benchmark-v1
    Documents: 1,000

                             F1       Latency       Cost
    -------------------------------------------------------
    Regex                   0.71       1 ms        €0.00
    Dictionary              0.75       1 ms        €0.00
    spaCy                   0.79       8 ms        €0.00
    CamemBERT               0.89      42 ms        €0.03
    LLM                     0.93     820 ms        €1.87
    Hybrid                  0.95      61 ms        €0.21

The values above are **illustrative only**.

Actual benchmark results must be generated automatically.

---

# 📈 Benchmark visualisations

The benchmark should automatically generate:

- F1 by extraction technology
- Accuracy vs latency
- Accuracy vs cost
- Precision / recall curves
- Field-level performance
- Error distributions
- Confusion matrices
- Pareto frontiers

The benchmark should make it easy to answer questions such as:

- Is an LLM actually better than regex for deadlines?
- Does CamemBERT outperform spaCy for eligibility?
- Is the LLM worth its additional computational cost?
- Which extractor performs best on PDFs?
- Which approach is most robust across organisations?
- Which fields require semantic models?
- Which fields can be extracted reliably with deterministic rules?
- Does a hybrid approach outperform a single model?

---

# 🔄 Regression benchmarking

Every new extractor version should be benchmarked against the previous version.

Example:

    CamemBERT v1
           ↓
    CamemBERT v2
           ↓
        Compare

The CI pipeline should be able to detect:

    F1 decreased > 2%
    Recall decreased > 3%
    Latency increased > 20%

and flag a regression.

---

# 🧠 Error analysis

The benchmark should not stop at aggregate metrics.

For each extractor, store examples of:

## False positives

    Predicted:
    AMOUNT = 2026

    Actual:
    No funding amount

## False negatives

    Gold:
    500 000 €

    Prediction:
    null

## Semantic errors

    Gold:
    Hospitals may apply.

    Prediction:
    Hospitals are excluded.

## Normalisation errors

    Gold:
    15 octobre 2026

    Prediction:
    15/10/2027

This allows targeted improvement of individual extraction strategies.

---

# 🧬 Provenance

Every important extracted value should be traceable to the source.

Example:

    {
      "deadline": {
        "value": "2026-10-15",
        "source_text": "Les dossiers doivent être soumis avant le 15 octobre 2026",
        "source_url": "https://...",
        "confidence": 0.99
      }
    }

For PDFs, preserve whenever possible:

- Document
- Page
- Section
- Text span
- Source URL
- Extraction method
- Model version
- Extraction timestamp

This is critical for:

- Debugging
- Validation
- Human review
- Benchmark evaluation
- Auditability

---

# 🔍 Human validation

Low-confidence extractions should be routed to human review.

    Extraction confidence < 0.80
                 │
                 ▼
           Human validation
                 │
           ┌─────┴─────┐
           ▼           ▼
        Correct      Reject
           │           │
           └─────┬─────┘
                 ▼
          Gold dataset

Human corrections can eventually become new training data.

Iterative loop:

    Scraping
       ↓
    Extraction
       ↓
    Human validation
       ↓
    Gold dataset
       ↓
    Model training
       ↓
    Benchmark
       ↓
    Improved extraction

---

# 🏗️ Complete architecture

                         ┌─────────────────┐
                         │     SOURCES     │
                         │                 │
                         │ ANR / ARS / INCa│
                         │ Foundations / EU│
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │    DISCOVERY    │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │     SCRAPING    │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ RAW DOCUMENTS   │
                         │ HTML / PDF / OCR│
                         └────────┬────────┘
                                  │
                                  ▼
                ┌─────────────────────────────────┐
                │       EXTRACTION ENGINE         │
                │                                 │
                │ Regex                           │
                │ Dictionaries                    │
                │ Classical NLP                   │
                │ spaCy                           │
                │ BERT / CamemBERT                │
                │ Transformers                    │
                │ LLM                             │
                │ Hybrid                          │
                └────────────────┬────────────────┘
                                 │
                                 ▼
                         ┌─────────────────┐
                         │  NORMALISATION  │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │   VALIDATION    │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ DEDUPLICATION   │
                         └────────┬────────┘
                                  │
                     ┌────────────┴────────────┐
                     ▼                         ▼
              ┌─────────────┐          ┌─────────────┐
              │  DATABASE   │          │  BENCHMARK  │
              └──────┬──────┘          └──────┬──────┘
                     │                        │
                     ▼                        ▼
              Search / API             Metrics / Reports
                     │
                     ▼
               Web interface

---

# 📁 Project structure

    aap-watcher/
    │
    ├── README.md
    ├── pyproject.toml
    ├── uv.lock
    │
    ├── src/
    │   └── aap_watcher/
    │       │
    │       ├── scrapers/
    │       │   ├── base.py
    │       │   ├── anr.py
    │       │   ├── ars.py
    │       │   ├── inca.py
    │       │   └── ...
    │       │
    │       ├── extraction/
    │       │   ├── base.py
    │       │   ├── regex.py
    │       │   ├── dictionary.py
    │       │   ├── classical_nlp.py
    │       │   ├── spacy_ner.py
    │       │   ├── bert_ner.py
    │       │   ├── transformer_classifier.py
    │       │   ├── llm.py
    │       │   └── hybrid.py
    │       │
    │       ├── normalization/
    │       │   ├── dates.py
    │       │   ├── amounts.py
    │       │   ├── organisations.py
    │       │   └── topics.py
    │       │
    │       ├── validation/
    │       │   ├── schema.py
    │       │   ├── confidence.py
    │       │   └── deduplication.py
    │       │
    │       ├── database/
    │       │   ├── models.py
    │       │   ├── repository.py
    │       │   └── migrations/
    │       │
    │       ├── benchmark/
    │       │   ├── datasets.py
    │       │   ├── evaluator.py
    │       │   ├── metrics.py
    │       │   ├── runner.py
    │       │   ├── error_analysis.py
    │       │   └── reports.py
    │       │
    │       ├── pipeline/
    │       │   ├── discover.py
    │       │   ├── scrape.py
    │       │   ├── extract.py
    │       │   ├── normalize.py
    │       │   └── run.py
    │       │
    │       ├── cli.py
    │       └── config.py
    │
    ├── tests/
    │   ├── scrapers/
    │   ├── extraction/
    │   ├── normalization/
    │   └── benchmark/
    │
    ├── configs/
    │   ├── sources.yaml
    │   └── extractors.yaml
    │
    ├── data/
    │   ├── raw/
    │   ├── processed/
    │   └── benchmark/
    │
    ├── results/
    │   └── benchmarks/
    │
    └── docs/
        ├── architecture/
        │   └── adr/
        └── sources/

---

# 🗄️ Database

SQLite can be used for local development.

PostgreSQL is recommended for production.

Main entities:

    organisations
          │
          └──< aaps
                  │
                  ├──< documents
                  ├──< topics
                  ├──< eligibility_rules
                  ├──< extraction_runs
                  └──< aap_versions

The database should preserve historical versions rather than simply overwriting existing AAPs.

---

# 📜 Extraction history

The system should never overwrite extraction results without preserving history.

Example:

    AAP
     │
     ├── Regex extraction
     ├── spaCy extraction
     ├── CamemBERT extraction
     ├── LLM extraction
     └── Hybrid extraction

This makes it possible to compare extraction technologies retrospectively.

---

# 🔄 AAP lifecycle

    DISCOVERED
        │
        ▼
      OPEN
        │
        ▼
    CLOSING_SOON
        │
        ▼
      CLOSED
        │
        ▼
     ARCHIVED

Possible states:

- upcoming
- open
- closing_soon
- closed
- cancelled
- archived
- unknown

---

# 🔔 Notifications

Once the database is operational:

    New AAP detected
           ↓
    Matches user profile
           ↓
       Notification

Possible channels:

- Email
- Slack
- Teams
- Discord
- RSS
- Web notifications
- API
- Daily digest

---

# 🔎 Search API

Example endpoint:

    GET /api/aaps

Possible filters:

    organisation=ANR
    status=open
    topic=cancer
    deadline_before=2026-12-31
    amount_min=100000

Additional future filters:

- Applicant type
- Region
- Country
- Funding type
- Research topic
- Deadline range
- Amount range
- Organisation
- Open/closed status

---

# 🖥️ Web interface

The interface should eventually provide:

- Search
- Organisation filter
- Topic filter
- Funding amount filter
- Deadline filter
- Applicant type filter
- Status filter
- Sorting by deadline
- Sorting by funding amount
- Source link
- Full extraction provenance

Example:

    ┌──────────────────────────────────────────────┐
    │ AAP Watcher                                  │
    ├──────────────────────────────────────────────┤
    │ Search: [ cancer AI                  ] 🔍    │
    │                                              │
    │ Filters                                      │
    │ Organisation     [ All ]                     │
    │ Deadline         [ Next 12 months ]          │
    │ Funding          [ > €100k ]                 │
    │                                              │
    ├──────────────────────────────────────────────┤
    │ ANR — Programme X                             │
    │ €300k · Deadline 15/10/2026                  │
    │ Cancer · AI                                  │
    │                                              │
    │ INCa — Programme Y                            │
    │ €500k · Deadline 30/11/2026                  │
    │ Cancer                                       │
    └──────────────────────────────────────────────┘

---

# 🛡️ Scraping ethics

AAP Watcher should be a polite crawler.

The project must:

- Respect `robots.txt`
- Respect website terms of service
- Rate-limit requests
- Cache downloaded content
- Avoid unnecessary requests
- Use a descriptive User-Agent
- Retry responsibly
- Handle HTTP errors
- Never bypass authentication
- Never bypass technical restrictions
- Avoid collecting unnecessary personal data

Example configuration:

    crawler:
      requests_per_second: 0.5
      timeout: 30
      retries: 3
      respect_robots_txt: true

---

# 📦 Technology stack

## Scraping

- Python
- httpx
- BeautifulSoup
- selectolax
- Playwright when JavaScript rendering is required

## Documents

- PyMuPDF
- pdfplumber
- OCR when necessary

## Classical NLP

- spaCy
- scikit-learn
- NLTK
- regex

## Machine Learning

- PyTorch
- Transformers
- BERT
- CamemBERT
- RoBERTa
- Domain-specific models

## LLM

Potential backends:

- Ollama
- LM Studio
- OpenAI-compatible APIs
- Other local or hosted models

## Database

- PostgreSQL
- SQLAlchemy
- Alembic

## API

- FastAPI

## Search

Potential options:

- PostgreSQL full-text search
- OpenSearch
- Elasticsearch
- Meilisearch

## Scheduling

Potential options:

- cron
- APScheduler
- Dagster
- Prefect

---

# 📝 Architectural Decision Records

Architecture decisions should be documented through ADRs.

Directory:

    docs/
    └── architecture/
        └── adr/
            ├── 0001-python.md
            ├── 0002-source-adapter-architecture.md
            ├── 0003-canonical-schema.md
            ├── 0004-extraction-benchmark.md
            ├── 0005-llm-as-one-extractor.md
            └── 0006-postgresql.md

Important architectural principle:

> **No extraction technology is considered the winner before benchmarking.**

Every significant architectural choice should be documented with:

- Context
- Decision
- Alternatives considered
- Consequences
- Status

---

# 🗺️ Roadmap

## Phase 1 — Proof of Concept

- [ ] Define canonical AAP schema
- [ ] Implement database
- [ ] Implement generic scraper
- [ ] Implement first source
- [ ] Extract title
- [ ] Extract amount
- [ ] Extract deadline
- [ ] Extract eligibility
- [ ] Store raw source
- [ ] Basic deduplication

## Phase 2 — Benchmark infrastructure

- [ ] Define annotation schema
- [ ] Create gold-standard corpus
- [ ] Build annotation tooling
- [ ] Implement benchmark runner
- [ ] Implement field-level metrics
- [ ] Implement normalised matching
- [ ] Implement latency benchmark
- [ ] Implement memory benchmark
- [ ] Implement cost tracking
- [ ] Implement error analysis

## Phase 3 — Extraction baselines

- [ ] Regex
- [ ] Dictionaries
- [ ] Classical NLP
- [ ] spaCy generic NER
- [ ] spaCy custom NER
- [ ] BERT NER
- [ ] CamemBERT NER
- [ ] Transformer classification
- [ ] LLM structured extraction
- [ ] Hybrid extraction

## Phase 4 — Multi-source ingestion

- [ ] ANR
- [ ] INCa
- [ ] ARS
- [ ] Fondation ARC
- [ ] Fondation pour la Recherche Médicale
- [ ] Ligue contre le cancer
- [ ] Fondation de France
- [ ] Other foundations
- [ ] Regional organisations
- [ ] European organisations

Target:

    10+ sources
    1,000+ AAPs

## Phase 5 — Production monitoring

- [ ] Scheduled scraping
- [ ] Detect new AAPs
- [ ] Detect modified AAPs
- [ ] Detect deadline changes
- [ ] Detect cancelled calls
- [ ] Historical versions
- [ ] Extraction regression tests
- [ ] Benchmark regression tracking

## Phase 6 — Search & API

- [ ] REST API
- [ ] Full-text search
- [ ] Advanced filters
- [ ] Similar AAP detection
- [ ] Public API documentation
- [ ] Web interface

## Phase 7 — Personalised funding discovery

Users could define:

    Research areas:
        Cancer
        Immunology
        Rare diseases

    Technologies:
        AI
        Machine Learning

    Funding:
        > €100k

    Geography:
        France
        Europe

The system could then rank opportunities:

    AAP #123

    Relevance: 94%

    ✓ Cancer
    ✓ Immunology
    ✓ AI
    ✓ France
    ✓ Funding > €100k

---

# 📈 Long-term vision

Once enough historical data has been collected, AAP Watcher becomes more than a scraper.

It can support:

## Funding landscape analysis

- Funding by organisation
- Funding by topic
- Funding by year
- Funding by region
- Funding by applicant type
- Funding by funding mechanism

## Funding-cycle analysis

Questions that could eventually be answered:

- Which AAPs recur every year?
- When do they usually open?
- How long are submission windows?
- Which organisations fund specific research topics?
- How have funding amounts evolved?
- Which AAPs are persistent over time?

## Funding opportunity prediction

Example:

    Organisation X usually opens this programme
    between September and October.

The system could use historical observations to identify likely future opportunities.

## Personalised funding assistant

    Research profile
           ↓
    AAP knowledge base
           ↓
    Eligibility filtering
           ↓
    Semantic matching
           ↓
    Ranked opportunities

---

# 🚀 Vision

    Thousands of websites
            ↓
    Millions of documents
            ↓
       AAP detection
            ↓
    Information extraction
            ↓
       Benchmarking
            ↓
        Validation
            ↓
    Structured knowledge
            ↓
    Historical database
            ↓
    Personalised funding opportunities

The central question of AAP Watcher is not simply:

> "Can we extract AAPs?"

but:

> **"What is the most accurate, robust, reproducible and cost-efficient way to extract structured funding opportunities from heterogeneous real-world documents?"**

Regex, classical NLP, spaCy, BERT/CamemBERT, other transformers, LLMs and hybrid systems are therefore treated as **competing extraction strategies**, evaluated on the same corpus and using the same metrics.

---

# 🤝 Contributing

Contributions are welcome.

## Add a new source

1. Implement a source adapter.
2. Add fixtures.
3. Add tests.
4. Document the source.
5. Verify scraping behaviour.
6. Open a Pull Request.

## Add a new extractor

1. Implement the `Extractor` interface.
2. Add unit tests.
3. Run the benchmark.
4. Add benchmark results.
5. Analyse errors.
6. Document limitations.
7. Open a Pull Request.

New extractors must not modify the benchmark protocol or canonical schema without an explicit architectural decision.

---

# 🧪 Development principles

The project follows several principles.

### Reproducibility

The same input and configuration should produce reproducible extraction results whenever technically possible.

### Modularity

Scraping, extraction, normalisation, validation, storage and benchmarking must remain independent components.

### Provenance

Every extracted value should be traceable to its source.

### Benchmark first

No extraction technology should be adopted simply because it is fashionable or powerful.

### Human-readable

Results and errors should remain understandable to developers and domain experts.

### Replaceability

Any extraction technology should be replaceable without rewriting the rest of the pipeline.

### No unnecessary LLM usage

LLMs should only be used where they provide a measurable advantage over simpler approaches.

---

# ⚖️ Disclaimer

AAP Watcher is an aggregation and information tool.

The official funding organisation and its published documentation remain authoritative.

Users should always verify the following on the official source before submitting an application:

- Eligibility
- Funding amount
- Submission deadline
- Required documents
- Application procedure
- Specific funding rules
- Any amendments or updates to the call

AAP Watcher must not be considered an authoritative source for funding decisions.

---

# 📜 License

License to be defined.

The final license should take into account:

- Source website terms of use
- Scraped-content redistribution restrictions
- Database rights
- Software licensing
- Model licensing
- Training dataset licensing

The project should clearly distinguish between:

1. The software code.
2. Scraped source documents.
3. Extracted structured data.
4. Benchmark datasets.
5. Trained models.

These components may require different licensing conditions.

---

# 🔐 Data and privacy

The project should minimise personal data collection.

AAP Watcher primarily targets publicly available information concerning funding opportunities.

If contact information is extracted from AAP pages, the system should:

- Store only information relevant to the AAP
- Avoid unnecessary personal data
- Preserve source provenance
- Respect applicable legal requirements
- Avoid creating unnecessary personal profiles

---

# 📌 Project status

Status: **Early development**

The current priority is to establish:

1. A robust scraping architecture.
2. A canonical AAP schema.
3. A gold-standard benchmark dataset.
4. Multiple independent extraction strategies.
5. A reproducible benchmark framework.

The first major milestone is not a production web interface.

It is a reliable answer to:

> **Which extraction architecture actually works best for extracting structured information from French AAPs?**
