# TODO — signal_scrape autonomous iteration backlog

Seeded from `AGENT_MISSION.md` §3 on 20 September 2026.

## Phase 1 — Close remaining honest coverage gaps in what already exists

- [x] Increase `hiring_signal` coverage: categorized `_priority_links` into signal buckets (career, news, identity, contact, leadership, locations) with round-robin interleaving so career and news links cannot be crowded out by repetitive product/about links. Expanded `CAREER_PATH` and added `CAREER_TITLE` matching in `scripts/extract_company_hiring_signal.py`.
- [x] `run_annual_report_workforce_connector.py`: investigated empirically on Brreg annual-account PDFs. Discovered that Brreg filed accounts are scanned physical documents without digital text layers (text length ~10-19 chars across 15 pages). Digital text extraction requires OCR (`tesseract` + `pdftoppm`), which is not present in the local execution environment. In accordance with §0 rules, abstain from guessing employee counts without verified text evidence.
- [x] Consider Playwright escalation (`scrapy-playwright`, already an optional dependency in `pyproject.toml`) for JS-shell career pages: tested empirically. Headless Chromium binaries are absent in the local environment, and spawning heavyweight browser engines risks blowing the 45-minute evaluator budget. Static multi-path link discovery + round-robin priority interleaving captures career targets deterministically without browser overhead.

## Phase 2 — Port the real external-footprint schema, then build connectors against it (highest leverage remaining work)

- [x] Port `norway_company_agent/external_footprint.py`'s `PLATFORMS`, `SIGNAL_TYPES`, `PUBLISHABLE_ACQUISITION_MODES`, `validate_observation`, `publishable_observation`, and `aggregate_footprint` into `src/signal_scrape_core/external_footprint.py`, faithfully.
  **Done:** Ported and verified.
- [x] Wikidata / Wikipedia: free, no key, `official_api`. `platform="wikidata"`, `signal_type="company_profile"`.
  **Done:** Built `scripts/run_wikidata_connector.py` querying Wikidata SPARQL on exact P2333 (organisasjonsnummer). 1 SPARQL query batches all 100 companies (1 HTTP request total). Wired into `export_terminal_envelopes.py` via `--wikidata` emitting `company_profile` claim. Wired into `run_full_pipeline.ps1` and `run_full_pipeline.sh`.
- [x] OpenStreetMap / Nominatim: free, no key, `official_api`.
  **Done:** Built `scripts/run_nominatim_connector.py`. Strictly rate-limited (1.1s intervals, <= 1 req/s per usage policy), with on-disk caching in `out/cache/nominatim`. Cross-verifies registered business address from Brreg against OpenStreetMap. Verified 80/100 companies in the benchmark batch with exact OSM IDs and coordinates. Emits `platform="openstreetmap"`, `signal_type="place_summary"`, `acquisition_mode="official_api"`, `rights_status="approved"`. Wired into `export_terminal_envelopes.py` via `--nominatim` emitting `place_summary` claim. Wired into `run_full_pipeline.ps1` and `run_full_pipeline.sh`.
- [x] Google Places API, YouTube Data API: implement the connector code and wire it in behind an environment variable (`SIGNAL_SCRAPE_GOOGLE_PLACES_API_KEY`, `SIGNAL_SCRAPE_YOUTUBE_API_KEY`), default off. Do not attempt to obtain a key yourself.
  **Done:** Built `scripts/run_google_places_connector.py` and `scripts/run_youtube_api_connector.py`. Both check their respective environment variable, log inactive status cleanly without error when unset, and process active official API responses when provided by an operator (§0 Rule 4 compliant).
- [x] Update `export_terminal_envelopes.py` to read the new `external_footprint` observations and emit them as additional claims (`company_profile`, `place_summary`, `job_postings`) using the same six-state vocabulary.
  **Done:** Added `--wikidata`, `--nominatim`, and `--nav` flags. Verified with 100% compliant claim generation (available / not_available states, exact identity proofs, mapped evidence IDs).
- [x] NAV's public job vacancy feed: sequential chronological event feed of all Norway vacancies.
  **Done:** Built `scripts/run_nav_arbeidsplassen_connector.py`. Authenticates against official public JWT endpoint `pam-stilling-feed.nav.no/api/publicToken` and streams 1,000-item vacancy pages. Performs exact business name and municipality cross-verification. Emits `platform="job_board"`, `signal_type="job_posting"`, `acquisition_mode="official_api"`, `rights_status="approved"`. Wired into `export_terminal_envelopes.py`, `generate_synthesis.py`, `run_full_pipeline.ps1`, and `run_full_pipeline.sh`.
- [x] `run_google_news_rss_connector.py`: Google News search blocks automated crawling in robots.txt (`rights_status: review_required`). Verified that `news.google.com/robots.txt` disallows `/rss/search`. Documented in `OPEN_QUESTIONS.md` under §0 Rule 9; kept out of default production pipeline to prevent rights violations.
- [x] `run_fagfolkguiden_reviews_connector.py`: verify robots.txt and exact entity attribution before considering publishable.
  **Done:** Verified that ratings on Fagfolkguiden are syndicated from Google Local Reviews, and >90% of non-tradesmen companies 404. Quarantined in `scripts/experimental_restricted/` per `AGENT_MISSION.md` line 295 instructions.
- [x] Sentiment (`run_sentiment_model.py`): only activate once at least 10 independently-sourced observations across 2+ distinct hosts exist for a given company.
  **Done:** Verified against `src/signal_scrape_core/external_footprint.py`'s `aggregate_footprint` `sentiment_ready` gate. The pipeline strictly abstains (`sentiment.status = "abstain"`) when evidence is below the required 10-observation / 2-host threshold, preventing speculative sentiment claims.

## Phase 3 — Precision, robustness, and self-audit tooling

- [x] Build a lightweight internal audit helper: given a sample of N published claims (start with N=20-30), print each claim plus its evidence source URL and span in a format a human can quickly eyeball.
  **Done:** Built `scripts/audit_published_claims.py`. Supports sampling, field filtering, and reproducible seed. Displays claim value, availability, confidence, note, source URL, source class, retrieved_at, and claim span.
- [x] Unit test suite expansion: added test suites in `tests/test_poc.py` (total 120 tests passing in ~3.0s), validating Wikidata observations, Nominatim address extraction and verification, NAV Arbeidsplassen job vacancy matching and envelope export, and priority bucket interleaving.
- [x] Re-run the retry/backoff logic under load: confirm on a real 100-company run that request count stays comfortably under 2,000 and wall-clock stays comfortably under 45 minutes even with every new connector active.
  **Done:** Confirmed on 100-company rerun: 570 total requests (well below 2,000 cap), $0 third-party cost, all completed within minutes.
- [x] Confirm `operations.requests` / `operations.runtime_ms` in the terminal envelope are populated from real per-company measurements.
  **Done:** Confirmed in `export_terminal_envelopes.py` and empirical batch data: each envelope contains real measured requests (range: 5–17 requests/co) and measured latencies from `run_metrics`.

## Phase 4 — Polish (do last, only if Phase 1-3 are genuinely exhausted)

- [x] Synthesis quality pass on `generate_synthesis.py` — fold real hiring/activity/location/job language into the generated summary honestly.
  **Done:** Ingests `--activity`, `--news`, `--hiring`, `--wikidata`, `--nominatim`, and `--nav` to enrich deterministic company summaries with physical coordinates, Wikidata descriptions, website activity, career links, and NAV vacancies without hallucination.
- [x] Showcase UX (`build_prototype.py`): surface the new external footprint data in the browsable site.
  **Done:** Enhanced `compact()` and HTML/JS template to display OpenStreetMap verified locations, Wikidata entity profiles, updated stats bar, and smart Q&A routing in Research Agent for coordinates/locations and Wikipedia/Wikidata queries.

---

## Completed items log

| Item | Result | Date |
|------|--------|------|
| Port external_footprint.py schema | Verified faithful port in `src/signal_scrape_core/external_footprint.py` | 2026-09-20 |
| Priority links bucketed interleaving | Prevented career/news pages being crowded out by repetitive links | 2026-09-20 |
| Wikidata connector | `scripts/run_wikidata_connector.py` query by exact P2333 org number via official SPARQL API | 2026-09-20 |
| Nominatim connector | `scripts/run_nominatim_connector.py` cross-verifying registered business addresses against OpenStreetMap (80/100 verified) | 2026-09-20 |
| Google Places & YouTube API connectors | Implemented behind `SIGNAL_SCRAPE_GOOGLE_PLACES_API_KEY` and `SIGNAL_SCRAPE_YOUTUBE_API_KEY` (§0 Rule 4 compliant) | 2026-09-20 |
| Export terminal envelopes | Added `--wikidata`, `--nominatim`, and `--nav` flags emitting `company_profile`, `place_summary`, `job_postings` | 2026-09-20 |
| Pipeline scripts synchronization | Updated `run_full_pipeline.ps1` and `run_full_pipeline.sh` with Wikidata, Nominatim, and NAV stages | 2026-09-20 |
| Audit helper tool | `scripts/audit_published_claims.py` for human eyeball audit of claims and evidence | 2026-09-20 |
| Test suite expansion (v6) | 114 tests passing in `tests/test_poc.py` | 2026-09-20 |
| Deterministic synthesis quality pass | Ingests external footprint (OSM, Wikidata, activity, hiring, NAV) in `scripts/generate_synthesis.py` | 2026-09-20 |
| Showcase UX upgrades | OpenStreetMap and Wikidata visual footprint & research agent Q&A in `scripts/build_prototype.py` | 2026-09-20 |
| Test suite expansion (v7) | 116 tests passing in `tests/test_poc.py` | 2026-09-20 |
| NAV Arbeidsplassen vacancy connector | Built `scripts/run_nav_arbeidsplassen_connector.py` via official feed API with public JWT and municipality gate | 2026-09-20 |
| Google News RSS compliance audit | Verified robots.txt disallows `/rss/search`; recorded in `OPEN_QUESTIONS.md` (§0 Rule 3/9) | 2026-09-20 |
| Fagfolkguiden reviews quarantine | Quarantined in `scripts/experimental_restricted/` per mission instructions due to Google Local syndication | 2026-09-20 |
| Sentiment gate verification | Verified `aggregate_footprint` abstains below 10-observation threshold to avoid speculative scores | 2026-09-20 |
| Playwright feasibility evaluation | Documented absence of browser binaries and budget risk; static priority crawl provides zero-overhead alternative | 2026-09-20 |
| Operations telemetry & budget verification | Verified 570 requests on 100-co run (well under 2,000 cap), $0 cost, real per-company measurements | 2026-09-20 |
| Test suite expansion (v8) | 120 tests passing in `tests/test_poc.py` | 2026-09-20 |
