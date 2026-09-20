# TODO — signal_scrape autonomous iteration backlog

Seeded from `AGENT_MISSION.md` §3 on 20 September 2026.

## Phase 1 — Close remaining honest coverage gaps in what already exists

- [x] Increase `hiring_signal` coverage: categorized `_priority_links` into signal buckets (career, news, identity, contact, leadership, locations) with round-robin interleaving so career and news links cannot be crowded out by repetitive product/about links. Expanded `CAREER_PATH` and added `CAREER_TITLE` matching in `scripts/extract_company_hiring_signal.py`.
- [x] `run_annual_report_workforce_connector.py`: investigated empirically on Brreg annual-account PDFs. Discovered that Brreg filed accounts are scanned physical documents without digital text layers (text length ~10-19 chars across 15 pages). Digital text extraction requires OCR (`tesseract` + `pdftoppm`), which is not present in the local execution environment. In accordance with §0 rules, abstain from guessing employee counts without verified text evidence.
- [ ] Consider Playwright escalation (`scrapy-playwright`, already an
  optional dependency in `pyproject.toml`) for JS-shell career pages —
  but only as a bounded escalation after a deterministic check confirms a
  JS shell, per the agent playbook's own rule, and only if it doesn't
  blow the 45-minute/2,000-request budget at 100-company scale. Measure
  before and after on a real run.

## Phase 2 — Port the real external-footprint schema, then build connectors against it (highest leverage remaining work)

- [x] Port `norway_company_agent/external_footprint.py`'s `PLATFORMS`,
  `SIGNAL_TYPES`, `PUBLISHABLE_ACQUISITION_MODES`, `validate_observation`,
  `publishable_observation`, and `aggregate_footprint` into
  `src/signal_scrape_core/external_footprint.py`, faithfully.
  **Done:** Ported and verified.
- [x] Wikidata / Wikipedia: free, no key, `official_api`. `platform="wikidata"`, `signal_type="company_profile"`.
  **Done:** Built `scripts/run_wikidata_connector.py` querying Wikidata SPARQL on exact P2333 (organisasjonsnummer). 1 SPARQL query batches all 100 companies (1 HTTP request total). Wired into `export_terminal_envelopes.py` via `--wikidata` emitting `company_profile` claim. Wired into `run_full_pipeline.ps1` and `run_full_pipeline.sh`.
- [x] OpenStreetMap / Nominatim: free, no key, `official_api`.
  **Done:** Built `scripts/run_nominatim_connector.py`. Strictly rate-limited (1.1s intervals, <= 1 req/s per usage policy), with on-disk caching in `out/cache/nominatim`. Cross-verifies registered business address from Brreg against OpenStreetMap. Verified 80/100 companies in the benchmark batch with exact OSM IDs and coordinates. Emits `platform="openstreetmap"`, `signal_type="place_summary"`, `acquisition_mode="official_api"`, `rights_status="approved"`. Wired into `export_terminal_envelopes.py` via `--nominatim` emitting `place_summary` claim. Wired into `run_full_pipeline.ps1` and `run_full_pipeline.sh`.
- [x] Google Places API, YouTube Data API: implement the connector code and wire it in behind an environment variable (`SIGNAL_SCRAPE_GOOGLE_PLACES_API_KEY`, `SIGNAL_SCRAPE_YOUTUBE_API_KEY`), default off. Do not attempt to obtain a key yourself.
  **Done:** Built `scripts/run_google_places_connector.py` and `scripts/run_youtube_api_connector.py`. Both check their respective environment variable, log inactive status cleanly without error when unset, and process active official API responses when provided by an operator (§0 Rule 4 compliant).
- [x] Update `export_terminal_envelopes.py` to read the new `external_footprint` observations and emit them as additional claims (`company_profile`, `place_summary`) using the same six-state vocabulary.
  **Done:** Added `--wikidata` and `--nominatim` flags. Verified with 100% compliant claim generation (available / not_available states, exact identity proofs, mapped evidence IDs).
- [ ] NAV's public job vacancy feed: sequential chronological event feed of all Norway vacancies.
- [ ] `run_google_news_rss_connector.py`: Google News search blocks automated crawling in robots.txt (`rights_status: review_required`).
- [ ] `run_fagfolkguiden_reviews_connector.py`: verify robots.txt and exact entity attribution before considering publishable.
- [ ] Sentiment (`run_sentiment_model.py`): only activate once at least 10 independently-sourced observations across 2+ distinct hosts exist for a given company.

## Phase 3 — Precision, robustness, and self-audit tooling

- [x] Build a lightweight internal audit helper: given a sample of N published claims (start with N=20-30), print each claim plus its evidence source URL and span in a format a human can quickly eyeball.
  **Done:** Built `scripts/audit_published_claims.py`. Supports sampling, field filtering, and reproducible seed. Displays claim value, availability, confidence, note, source URL, source class, retrieved_at, and claim span.
- [x] Unit test suite expansion: added 4 new unit test suites in `tests/test_poc.py` (total 114 tests passing in ~2.9s), validating Wikidata observations, Nominatim address extraction and verification, envelope export with new external claims, and priority bucket interleaving.
- [ ] Re-run the retry/backoff logic under load: confirm on a real 100-company run that request count stays comfortably under 2,000 and wall-clock stays comfortably under 45 minutes even with every new connector active.
- [ ] Confirm `operations.requests` / `operations.runtime_ms` in the terminal envelope are populated from real per-company measurements.

## Phase 4 — Polish (do last, only if Phase 1-3 are genuinely exhausted)

- [ ] Synthesis quality pass on `generate_synthesis.py` — fold real hiring/activity/location language into the generated summary honestly.
- [ ] Showcase UX (`build_prototype.py`): surface the new external footprint data in the browsable site.

---

## Completed items log

| Item | Result | Date |
|------|--------|------|
| Port external_footprint.py schema | Verified faithful port in `src/signal_scrape_core/external_footprint.py` | 2026-09-20 |
| Priority links bucketed interleaving | Prevented career/news pages being crowded out by repetitive links | 2026-09-20 |
| Wikidata connector | `scripts/run_wikidata_connector.py` query by exact P2333 org number via official SPARQL API | 2026-09-20 |
| Nominatim connector | `scripts/run_nominatim_connector.py` cross-verifying registered business addresses against OpenStreetMap (80/100 verified) | 2026-09-20 |
| Google Places & YouTube API connectors | Implemented behind `SIGNAL_SCRAPE_GOOGLE_PLACES_API_KEY` and `SIGNAL_SCRAPE_YOUTUBE_API_KEY` (§0 Rule 4 compliant) | 2026-09-20 |
| Export terminal envelopes | Added `--wikidata` and `--nominatim` flags emitting `company_profile` and `place_summary` claims | 2026-09-20 |
| Pipeline scripts synchronization | Updated `run_full_pipeline.ps1` and `run_full_pipeline.sh` with Wikidata and Nominatim stages | 2026-09-20 |
| Audit helper tool | `scripts/audit_published_claims.py` for human eyeball audit of claims and evidence | 2026-09-20 |
| Test suite expansion | 114 tests passing in `tests/test_poc.py` | 2026-09-20 |
