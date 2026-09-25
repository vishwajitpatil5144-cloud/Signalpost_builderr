# signal_scrape — Norwegian Company Intelligence & Verification Pipeline

> **Submission for the Builderr Signalpost Challenge**  
> **Evaluator Quick Access:** See [SUBMISSION.md](SUBMISSION.md) for the formal email submission manifest and pre-verified artifact paths.

---

## One-Command Turnkey Pipeline Execution

The pipeline is packaged into a unified multi-stage launcher available for both PowerShell and Bash environments.

### General Command (Any Custom Cohort, Path, or Batch Size)
The launcher accepts custom organisation inputs from any directory (supporting `.jsonl`, `.txt` with one 9-digit orgnr per line, or `.json`), any expected count, and outputs all 6-stage artifacts to your designated output folder:
* **PowerShell (Windows):**
  ```powershell
  .\run_full_pipeline.ps1 -Organisations "<path_to_organisations_file>" -Bulk "brreg-enheter.csv" -ExpectedCount <count> -RunId "<run_id>" -OutDir "<path_to_output_dir>"
  ```
* **Bash (Linux / macOS / Git Bash):**
  ```bash
  ./run_full_pipeline.sh <path_to_organisations_file> brreg-enheter.csv <count> <run_id> <path_to_output_dir>
  ```

### Full 1,000-Company Submission Reproduction
Reproduces the complete 1,000-company submission dataset from scratch:
* **PowerShell (Windows):**
  ```powershell
  .\run_full_pipeline.ps1 -Organisations "data/companies-1000.jsonl" -Bulk "brreg-enheter.csv" -ExpectedCount 1000 -RunId "submission-1000" -OutDir "out/submission-1000-run"
  ```
* **Bash (Linux / macOS / Git Bash):**
  ```bash
  ./run_full_pipeline.sh data/companies-1000.jsonl brreg-enheter.csv 1000 submission-1000 out/submission-1000-run
  ```

### Fast 100-Company Evaluation Check (~13 Minutes)
For quick budget-friendly evaluation (<600 HTTP requests, completed in minutes):
* **PowerShell (Windows):**
  ```powershell
  .\run_full_pipeline.ps1 -Organisations "data/companies-100.jsonl" -Bulk "brreg-enheter.csv" -ExpectedCount 100 -RunId "benchmark-100" -OutDir "out/benchmark-100-run"
  ```
* **Bash (Linux / macOS / Git Bash):**
  ```bash
  ./run_full_pipeline.sh data/companies-100.jsonl brreg-enheter.csv 100 benchmark-100 out/benchmark-100-run
  ```

### Automated Pipeline Stages
Both launchers automatically execute the 6-stage workflow end-to-end:
1. **Official Registry Batch**: Queries Brønnøysundregistrene bulk CSV and live REST APIs (Enhetsregisteret, Regnskapsregisteret, Roller, Underenheter, Konsernstruktur).
2. **Free Domain Discovery**: For companies without a registry-listed website, generates deterministic domain permutations and verifies candidates via exact identity gates ($0 cost, no search APIs).
3. **External Footprint Connectors**:
   * *OpenStreetMap / Nominatim*: Validates registered addresses, resolves physical coordinates, and records OSM place nodes.
   * *Wikidata SPARQL*: Queries official property P2333 for exact entity matches, multi-lingual descriptions, and inception dates.
   * *NAV Arbeidsplassen*: Cross-references active public vacancy feeds (`pam-stilling-feed.nav.no`) for authentic hiring events.
   * *Company Site Signals*: Crawls priority bucketed pages (careers, news, leadership) with strict `robots.txt` adherence.
4. **Deterministic Synthesis**: Emits readable decision summaries using evidence-backed templates without generative model hallucination.
5. **Showcase UI Build**: Compiles all verified claims, coordinates, and observations into the standalone HTML interface.
6. **Terminal Envelope Export**: Maps internal profile claims into contract-compliant terminal envelopes with full six-state availability mapping.

---

## Evaluator Quick Verification (Under 2 Minutes)

### 1. Offline Unit Test Suite (129 Tests)
Run the full test suite validating all schemas, connectors, identity gates, priority interleaving, and envelope exporters:
```bash
uv run python -m unittest discover tests
```
*Expected Result:* `Ran 129 tests in ~1s, OK`.

### 2. Idempotency & Diff Engine Fixture Check
Verify the refresh engine on the evaluator-provided old/new snapshot fixture:
```bash
python first_run.py
```
*Expected Result:* `Signalpost starter: SUCCESS` (2 expected changes found, 0 false positives, `idempotent_rerun: true`).

### 3. Interactive Showcase UI
Open the browsable, zero-dependency 1,000-entity showcase site directly in your browser:
* Local Path: `out/submission-1000-run/showcase.html`
* Features: Instant client-side search, prominent verified website action buttons, leadership hierarchy separated from corporate auditors/accountants, interactive OpenStreetMap location pins, and evidence-bounded research agent Q&A.

---

## Repository Structure

```text
signal_scrape/
├── brreg-enheter.csv             # Bundled BRREG official bulk registry file (~154 MB)
├── first_run.py                  # Starter qualification check (offline snapshot replay)
├── pyproject.toml                # Standard uv/pip project configuration
├── run_full_pipeline.ps1         # Unified one-command PowerShell runner
├── run_full_pipeline.sh          # Unified one-command POSIX/Bash runner
├── select_entry_batch.py         # Deterministic batch sampler from universe
├── SUBMISSION.md                 # Official submission manifest for submit@builderr.ai
│
├── data/
│   ├── companies-1000.jsonl                      # 1,000-company submission input cohort
│   ├── manifest-1000.txt                         # 1,000 organisation numbers
│   ├── companies-100.jsonl                       # 100-company benchmark input cohort
│   ├── signalpost-company-universe-2025.jsonl.gz # Hash-verified official universe file
│   └── universe-metadata.json                    # Official universe schema and metadata
│
├── out/
│   ├── submission-1000-run/      # Definitive 1,000-company submission dataset
│   │   ├── terminal-envelopes.jsonl      # 1,000 contract terminal envelopes
│   │   ├── profiles-with-discovery.jsonl # 1,000 enriched company profiles
│   │   ├── manifest-1000.txt             # 1,000 organisation numbers
│   │   ├── run-report.json               # Execution metrics & request logs
│   │   ├── refresh-check.json            # 1,000-entity idempotency audit report
│   │   ├── showcase.html                 # Enhanced 6.38 MB browsable UI
│   │   ├── nominatim.jsonl               # 831 OSM geocoded places
│   │   ├── wikidata.jsonl                # 8 exact P2333 entity matches
│   │   ├── companies.jsonl               # Seed organisations input
│   │   └── synthesis.jsonl               # Decision-useful summaries
│   ├── benchmark-100-run/        # Evaluation 100-company cohort
│   │   ├── terminal-envelopes.jsonl      # 100 contract terminal envelopes
│   │   ├── profiles-with-discovery.jsonl # 100 enriched company profiles
│   │   ├── run-report.json               # Execution metrics (572 requests, ~13 min)
│   │   ├── refresh-check.json            # 100-entity idempotency audit report
│   │   ├── showcase.html                 # Standalone browsable UI
│   │   └── synthesis.jsonl               # Decision-useful summaries
│   └── cache/                    # Nominatim on-disk geocoding cache
│
├── scripts/                      # Core pipeline processing & connector scripts
│   ├── run_competition_batch.py
│   ├── run_free_domain_discovery.py
│   ├── run_nominatim_connector.py
│   ├── run_wikidata_connector.py
│   ├── run_nav_arbeidsplassen_connector.py
│   ├── extract_company_site_activity.py
│   ├── extract_company_hiring_signal.py
│   ├── generate_synthesis.py
│   ├── build_prototype.py
│   ├── export_terminal_envelopes.py
│   ├── diff_live_runs.py
│   └── experimental_restricted/  # Quarantined non-compliant platform scripts
│
├── src/signal_scrape_core/       # Modular core package
│   ├── identity.py               # Exact-entity verification & normalization
│   ├── discovery.py              # Domain permutation generator
│   ├── official.py               # BRREG bulk & REST parser
│   ├── external_footprint.py     # Schema contracts for Nominatim, Wikidata, NAV
│   ├── refresh.py                # Dataset diff engine & change detector
│   └── evidence.py               # Cryptographic SHA-256 evidence builder
│
└── tests/
    ├── test_poc.py               # 129 automated unit and regression tests
    └── fixtures/                 # Offline test fixtures and snapshot manifests
```

---

## Executive Summary

`signal_scrape` is an autonomous, production-grade intelligence pipeline designed to ingest Norwegian organisation numbers, resolve their legal identities against official state registers, discover and verify digital footprints without paid third-party search APIs, extract verified operational signals, and emit contract-compliant terminal envelopes with provable provenance.

### Core Architectural Guarantees
* **$0 Operational Cost**: 100% free and open data sources. Zero paid third-party search or LLM APIs required.
* **Deterministic Accuracy**: Grounded exclusively in primary registers and exact-identity verified web surfaces. Zero hallucinated claims.
* **Strict Six-State Vocabulary**: Every claim complies with the competition contract (`available`, `not_available`, `blocked`, `not_applicable`, `ambiguous`, `failed`). Unverified candidate sites are strictly marked `ambiguous`, never `available`.
* **Zero Dangling Evidence**: 100% of emitted claims reference verified evidence items with cryptographic SHA-256 provenance and timestamped source URLs.
* **Idempotent Refresh Engine**: Rerunning the pipeline on unchanged companies yields exactly 0 false changes, while real historical changes are detected with 100% precision and recall.

---

## Technical Implementations & Design Highlights

### 1. Zero-Cost Website Discovery & Exact-Entity Identity Gating
Rather than relying on expensive search APIs (such as Brave or Google Custom Search), `scripts/run_free_domain_discovery.py` generates normalized domain permutations derived from Norwegian corporate naming rules (handling AS/ASA stripping, Norwegian vowels `æ/ø/å` transliteration, compound hyphenation, and `.no/.com/.org` TLDs). 
* Every candidate must pass an independent **Exact-Entity Identity Gate**: the target site must contain either the company's 9-digit organisation number or an exact match of the registered legal name in title, OpenGraph tags, schema.org JSON-LD, or imprint.
* In the 1,000-company cohort, this discovered and verified **97 new legitimate corporate websites** at $0 cost.

### 2. Multi-Layer Site Liveness & Anti-Parking Classifier
Reachable HTTP 200 responses do not necessarily represent active company websites. `src/signal_scrape_core/identity.py` features a dedicated **Site Liveness Classifier** (`classify_site_liveness`) that inspects HTTP headers, page titles, body text, and frame sources:
* **Registrar Placeholders & Parked Domains**: Intercepts registrar parking markers (Domainnameshop, GoDaddy, Sedo, Dan.com, Afternic, STRATO, WebIT) and for-sale landers (e.g. `alukra.no`, `fryyd.com`).
* **Under Construction & Empty Stubs**: Quarantines placeholder pages containing "under construction", "coming soon", "nettside under utvikling", or empty body stubs (e.g. `idrettsveien.no`).
* **Frameset Cloaking**: Inspects HTML `<frame>` and `<iframe>` elements to detect parked redirect frames (e.g. `parkert-su.webit.no` on `gynekologi.no`).
* **Server Error Dumps**: Rejects pages returning unhandled PHP/database fatal error dumps while emitting HTTP 200 (e.g. `folkestadkraftverk.no`).

### 3. Acronym Collision & Foreign Grounding Guards
To guarantee zero false-positive entity attributions:
* **Short Acronym Guard**: Norwegian companies frequently share short 2–3 letter names (e.g. `VTO AS`). Matching the letters alone in a domain (e.g. `vto.no`) is not treated as evidence, as it may belong to an unrelated company (*Virkestransport Øst AS* in Elverum vs *VTO AS* in Bergen). Candidate domains for short-acronym entities require explicit corroboration against the registered organization number, municipality, or board leadership.
* **Foreign Grounding Guard**: For non-`.no` TLDs (`.com`, `.net`, `.org`), candidate domains must exhibit explicit Norwegian grounding (Norwegian org number, Norwegian phone/address, municipality, or `/no/` locale subpath) to eliminate foreign name collisions (e.g. *LADEST AS* vs Louisiana Destination Imagination on `ladest.com`).

### 4. Fast DNS & TCP Socket Pre-Probing (Sub-Millisecond Rejection)
On Windows and UNIX systems, connecting to unreachable or non-existent hosts can stall the kernel network stack for 21 to 63 seconds per dead host due to TCP SYN retries:
* **Fast DNS Pre-Check (`socket.gethostbyname`)**: Immediately discards non-existent hostnames (NXDOMAIN) in ~10ms.
* **1.5-Second TCP Socket Pre-Probe (`socket.create_connection`)**: Actively tests TCP port 80/443 with a strict 1.5s timeout before invoking full HTTP parsers.
* **Global Socket Timeout (`socket.setdefaulttimeout(15.0)`)**: Guarantees no low-level socket or SSL handshake can hang indefinitely.
* **Impact**: Reduced 100-company discovery probe time from >1 hour to **under 8 minutes**.

### 5. Honest Abstention & Six-State Vocabulary
The pipeline never guesses when evidence is missing:
* Unreported employee counts in registry filings are emitted as `not_available` with note `"Not reported by the registry; not interpreted as zero."`
* Candidate websites that respond over HTTP but fail exact identity verification or liveness checks are emitted as `ambiguous` with note `"Fetched successfully but exact-entity identity verification did not pass."` They are never promoted to `available`.
* Zero dangling evidence IDs: every `claim.evidence_ids` links directly to an item in `envelope.evidence[]`.

### 6. External Footprint & Verified Signals
* **OpenStreetMap / Nominatim Connector**: Extracts official business addresses (`forretningsadresse` or `postadresse`) from the registry, parses postal codes and municipalities, queries Nominatim, and cross-verifies matched street numbers. In the 1,000 run, **831 entities** were geocoded with physical coordinates and verified OpenStreetMap place nodes.
* **Wikidata SPARQL Connector**: Queries official property P2333 for exact entity matches, multi-lingual descriptions, and inception dates.
* **NAV Arbeidsplassen Connector**: Cross-references active public vacancy feeds (`pam-stilling-feed.nav.no`) for authentic hiring events.
* **Direct Site Signals**: Crawls priority bucketed pages (careers, news, leadership) with strict `robots.txt` adherence.

### 7. Leadership & Auditor Separation
`scripts/build_prototype.py` was specifically enhanced to categorize leadership roles:
* **Executive Leadership & Board Members** (daglig leder, styreleder, styremedlem) are presented prominently as company directors.
* **Corporate Auditors & Accounting Firms** (revisor, regnskapsfører) are cleanly separated into a secondary "External Auditors & Corporate Services" panel to avoid misrepresenting external accounting firms as corporate officers.

---

## Submitted Deliverables Matrix

All deliverables for the full 1,000-company cohort are pre-generated, verified, and staged in `out/submission-1000-run/`. A fresh 100-company validation cohort is also provided in `out/benchmark-100-run/`.

| Deliverable | Path | Description / Verification Metrics |
|---|---|---|
| **Terminal Envelopes (≥1,000)** | [`out/submission-1000-run/terminal-envelopes.jsonl`](out/submission-1000-run/terminal-envelopes.jsonl) | 1,000 completed terminal envelopes; 100% valid six-state vocabulary; 0 dangling evidence IDs |
| **Organisation Manifest** | [`out/submission-1000-run/manifest-1000.txt`](out/submission-1000-run/manifest-1000.txt) | 1,000 unique organisation numbers matching universe seeds |
| **Completed Profiles** | [`out/submission-1000-run/profiles-with-discovery.jsonl`](out/submission-1000-run/profiles-with-discovery.jsonl) | 1,000 structured profiles including 97 newly discovered & verified websites |
| **Machine Run Report** | [`out/submission-1000-run/run-report.json`](out/submission-1000-run/run-report.json) | 5,660 requests, 0 unhandled failures, `$0.00` third-party cost |
| **Refresh Audit Evidence** | [`out/submission-1000-run/refresh-check.json`](out/submission-1000-run/refresh-check.json) | 1,000 profiles compared against baseline; 0 false changes; `idempotent_rerun: true` |
| **Interactive Showcase** | [`out/submission-1000-run/showcase.html`](out/submission-1000-run/showcase.html) | Standalone browsable UX (6.38 MB) with verified map coordinates and separated leadership |
| **Benchmark 100 Cohort** | [`out/benchmark-100-run/`](out/benchmark-100-run/) | Complete 6-stage run on 100 fresh benchmark companies (572 requests, ~13 min) |

---

## External Data Sources & Compliance Declaration

| Source / Platform | Acquisition Mode | Protocol / Endpoint | Licence / Terms | Usage in Pipeline |
|---|---|---|---|---|
| **Brønnøysundregistrene (BRREG)** | Official Bulk CSV & REST API | `data.brreg.no/enhetsregisteret/api` | NLOD (Norwegian Licence for Open Government Data) | Primary identity anchor: legal name, status, accounts, roles, subunits |
| **Regnskapsregisteret** | Official REST API | `data.brreg.no/regnskapsregisteret/regnskap` | NLOD | Financial performance: revenue, operating results, annual result, assets, debt |
| **OpenStreetMap / Nominatim** | Official API | `nominatim.openstreetmap.org/search` | ODbL (Open Database Licence) | Business address geocoding, node verification, physical map coordinates (rate-limited <= 1 req/s, on-disk cache) |
| **Wikidata** | Official SPARQL API | `query.wikidata.org/sparql` | CC0 Public Domain | Exact P2333 organisation number resolution, knowledge graph entities |
| **NAV Arbeidsplassen** | Official Public API | `pam-stilling-feed.nav.no/api/v1` | NLOD | Public job vacancies verified against Norwegian employer registry |
| **Direct Company Websites** | Direct HTTP Crawling | Direct GET with `robots.txt` check | Public Web (robots.txt compliant) | Verified company activity, careers/hiring detection, social link normalization |
| **DNS & Port Pre-Check** | Socket Pre-Probe | RFC 1035 DNS & TCP port 80/443 | Open Internet Protocol | Sub-millisecond dead IP and non-resolving candidate domain rejection |

### Source Policy Compliance & Quarantined Platforms
* **Zero Generative LLM Dependency**: All entity parsing, liveness classification, and synthesis summaries are 100% deterministic to mathematically eliminate hallucination, ensure zero inference latency, and guarantee `$0.00` marginal cost.
* **Restricted Scrapers Quarantined**: Per competition rules, high-friction and restricted scrapers (LinkedIn, Meta/Facebook, Indeed, Glassdoor) are strictly excluded from the production pipeline. Experimental evaluation harnesses are quarantined in [`scripts/experimental_restricted/`](scripts/experimental_restricted/) and are never invoked during standard pipeline runs.

---

## Contact & Candidate Details
* **Candidate**: Vishwajit Patil
* **Email**: `vishwajitpatil5144@gmail.com`
* **Repository**: `https://github.com/vishwajitpatil5144-cloud/Signalpost_builderr.git`
* **Submission Target**: `submit@builderr.ai`
