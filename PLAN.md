# Session Plan: AAP Watcher Development

## Tasks (in order)

### 1. Install spaCy + Real NER Extractor
- Add `spacy>=3.7` to optional deps in `pyproject.toml`
- Download `fr_core_news_md` French NER model
- Replace `src/aap_watcher/extraction/spacy_ner.py` stub with real implementation:
  - Use `fr_core_news_md` for ORG, DATE, MONEY, PER entities
  - Map spaCy labels to AAP schema fields
  - Maintain `Extractor` Protocol compliance
- Add test in `tests/test_extractors.py`
- Run `uv run aap-watcher benchmark` to compare against existing extractors

### 2. Add PDF Parsing Capability
- Add `PyMuPDF>=1.24` to core dependencies (or optional `[pdf]` extra)
- Create `src/aap_watcher/scrapers/pdf_parser.py` utility module:
  - `extract_text_from_pdf(pdf_bytes) -> str`
  - Handle multi-page documents, tables, metadata
- Extend `Document` model in `extraction/base.py` with optional `content_type` field
- Integrate into pipeline: auto-detect `.pdf` URLs in scrapers
- Add tests with synthetic PDF fixtures

### 3. Per-field Benchmark Matrix
- Extend `src/aap_watcher/benchmark/reports.py`:
  - New function `render_field_matrix(results) -> str`
  - Shows precision/recall/F1 per field per extractor
- Add `--format matrix` option to `cli.py` benchmark command
- Output as markdown table and optional JSON

### 4. Create Docs + Configs
- Create `docs/architecture/adr/` directory
- Write 6 ADRs per README spec:
  - 0001-python.md (Python + Pydantic)
  - 0002-sqlite.md (SQLite for dev)
  - 0003-httpx-scraping.md (httpx + robots.txt)
  - 0004-benchmark.md (benchmark-first extraction)
  - 0005-extraction-strategies.md (competing strategies)
  - 0006-postgresql.md (production DB target)
- Create `configs/sources.yaml` (20 source configs)
- Create `configs/extractors.yaml` (extractor registry config)

### 5. Grow Gold Corpus to 500 Examples
- Extend `scripts/build_gold_corpus.py` to generate 500 examples
- Add text generation for missing sources: Inserm, CNRS, Inria, Inrae, Bettencourt, BPI, Horizon Europe
- Ensure entity annotation coverage for all fields
- Run `uv run python scripts/build_gold_corpus.py` to regenerate

### 6. Build Train/Val/Test Splits
- Restructure gold corpus into proper splits:
  - `data/benchmark/gold/train.jsonl` (70% = 350)
  - `data/benchmark/gold/val.jsonl` (15% = 75)
  - `data/benchmark/gold/test.jsonl` (15% = 75)
- Update `benchmark/datasets.py` to load splits properly
- Update benchmark CLI to accept `--split {train,val,test,all}`

## Verification
- Run `uv run pytest` after each task
- Run `uv run aap-watcher benchmark` after tasks 1, 3, 5
- Check `uv run aap-watcher serve` starts without errors after tasks 1-4
