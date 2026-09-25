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
  .\run_full_pipeline.ps1 -Organisations "out/full-1000-run-20260921/companies.jsonl" -Bulk "brreg-enheter.csv" -ExpectedCount 1000 -RunId "eval-1000" -OutDir "out/eval-1000-run"
  ```
* **Bash (Linux / macOS / Git Bash):**
  ```bash
  ./run_full_pipeline.sh out/full-1000-run-20260921/companies.jsonl brreg-enheter.csv 1000 eval-1000 out/eval-1000-run
  ```

### Fast 100-Company Evaluation Check (~5 Minutes)
For quick budget-friendly evaluation (<600 HTTP requests, completed in minutes):
* **PowerShell (Windows):**
  ```powershell
  .\run_full_pipeline.ps1 -Organisations "out/fresh-100-run-20260921/companies.jsonl" -Bulk "brreg-enheter.csv" -ExpectedCount 100 -RunId "eval-100" -OutDir "out/eval-100-run"
  ```
* **Bash (Linux / macOS / Git Bash):**
  ```bash
  ./run_full_pipeline.sh out/fresh-100-run-20260921/companies.jsonl brreg-enheter.csv 100 eval-100 out/eval-100-run
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

### 1. Offline Unit Test Suite (120 Tests)
Run the full test suite validating all schemas, connectors, identity gates, priority interleaving, and envelope exporters:
```bash
uv run --with pytest pytest -q
```
*Expected Result:* `120 passed, 5 subtests passed in ~3s`.

### 2. Idempotency & Diff Engine Fixture Check
Verify the refresh engine on the evaluator-provided old/new snapshot fixture:
```bash
python first_run.py
```
*Expected Result:* `Signalpost starter: SUCCESS` (2 expected changes found, 0 false positives, `idempotent_rerun: true`).

### 3. Interactive Showcase UI
Open the browsable, zero-dependency 1,000-entity showcase site directly in your browser:
* Local Path: `out/full-1000-run-20260921/showcase.html`
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
│   ├── signalpost-company-universe-2025.jsonl.gz  # Hash-verified official universe file
│   └── universe-metadata.json                     # Official universe schema and metadata
│
├── out/
│   ├── full-1000-run-20260921/   # Definitive 1,000-company submission dataset
│   │   ├── terminal-envelopes.jsonl      # 1,000 contract terminal envelopes
│   │   ├── profiles-with-discovery.jsonl # 1,000 enriched company profiles
│   │   ├── manifest-1000.txt             # 1,000 organisation numbers
│   │   ├── run-report.json               # Execution metrics & request logs
│   │   ├── refresh-check.json            # 1,000-entity idempotency audit report
│   │   ├── showcase.html                 # Enhanced 6.25 MB browsable UI
│   │   ├── nominatim.jsonl               # 830 OSM geocoded places
│   │   ├── wikidata.jsonl                # 7 exact P2333 entity matches
│   │   ├── companies.jsonl               # Seed organisations input
│   │   └── synthesis.jsonl               # Decision-useful summaries
│   └── fresh-100-run-20260921/   # Evaluation 100-company cohort (0 overlap)
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
    ├── test_poc.py               # 120 automated unit and regression tests
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

### 1. Zero-Cost Website Discovery Engine
Rather than relying on expensive search APIs (such as Brave or Google Custom Search), `scripts/run_free_domain_discovery.py` generates normalized domain permutations derived from Norwegian corporate naming rules (handling AS/ASA stripping, Norwegian vowels `æ/ø/å` transliteration, compound hyphenation, and `.no/.com/.org` TLDs). 
* Every candidate must pass an independent **Exact-Entity Identity Gate**: the target site must contain either the company's 9-digit organisation number or an exact match of the registered legal name in title, OpenGraph tags, schema.org JSON-LD, or imprint.
* In the 1,000-company cohort, this discovered and verified **79 new legitimate corporate websites** at $0 cost.

### 2. Honest Abstention & Six-State Vocabulary
The pipeline never guesses when evidence is missing:
* Unreported employee counts in registry filings are emitted as `not_available` with note `"Not reported by the registry; not interpreted as zero."`
* Candidate websites that respond over HTTP but fail exact identity verification are emitted as `ambiguous` with note `"Fetched successfully but exact-entity identity verification did not pass."` They are never promoted to `available`.
* Zero dangling evidence IDs: every `claim.evidence_ids` links directly to an item in `envelope.evidence[]`.

### 3. OpenStreetMap Nominatim Connector
`scripts/run_nominatim_connector.py` extracts official business addresses (`forretningsadresse` or `postadresse`) from the registry, parses postal codes and municipalities, queries Nominatim, and cross-verifies matched street numbers. In the 1,000 run, **830 entities** were geocoded with physical coordinates and verified OpenStreetMap place nodes.

### 4. Leadership & Auditor Separation
`scripts/build_prototype.py` was specifically enhanced to categorize leadership roles:
* **Executive Leadership & Board Members** (daglig leder, styreleder, styremedlem) are presented prominently as company directors.
* **Corporate Auditors & Accounting Firms** (revisor, regnskapsfører) are cleanly separated into a secondary "External Auditors & Corporate Services" panel to avoid misrepresenting external accounting firms as corporate officers.

---

## Submitted Deliverables Matrix

All deliverables for the full 1,000-company cohort are pre-generated, verified, and staged in `out/full-1000-run-20260921/`. A fresh 100-company validation cohort is also provided in `out/fresh-100-run-20260921/`.

| Deliverable | Path | Description / Verification Metrics |
|---|---|---|
| **Terminal Envelopes (≥1,000)** | [`out/full-1000-run-20260921/terminal-envelopes.jsonl`](out/full-1000-run-20260921/terminal-envelopes.jsonl) | 1,000 completed terminal envelopes; 100% valid six-state vocabulary; 0 dangling evidence IDs |
| **Organisation Manifest** | [`out/full-1000-run-20260921/manifest-1000.txt`](out/full-1000-run-20260921/manifest-1000.txt) | 1,000 unique organisation numbers matching universe seeds |
| **Completed Profiles** | [`out/full-1000-run-20260921/profiles-with-discovery.jsonl`](out/full-1000-run-20260921/profiles-with-discovery.jsonl) | 1,000 structured profiles including 79 newly discovered & verified websites |
| **Machine Run Report** | [`out/full-1000-run-20260921/run-report.json`](out/full-1000-run-20260921/run-report.json) | 5,674 requests, 61.2 MB data transferred, 0 unhandled failures, `$0.00` third-party cost |
| **Refresh Audit Evidence** | [`out/full-1000-run-20260921/refresh-check.json`](out/full-1000-run-20260921/refresh-check.json) | 1,000 profiles compared against baseline; 0 false changes; `idempotent_rerun: true` |
| **Interactive Showcase** | [`out/full-1000-run-20260921/showcase.html`](out/full-1000-run-20260921/showcase.html) | Standalone browsable UX (6.25 MB) with verified map coordinates and separated leadership |
| **Fresh 100 Cohort** | [`out/fresh-100-run-20260921/`](out/fresh-100-run-20260921/) | Complete 6-stage run on 100 fresh companies (0 overlap with initial cohort) |

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

### Source Policy Compliance & Quarantined Platforms
Per competition rules, high-friction and restricted scrapers (LinkedIn, Meta/Facebook, Indeed, Glassdoor) are strictly excluded from the production pipeline. Experimental evaluation harnesses are quarantined in [`scripts/experimental_restricted/`](scripts/experimental_restricted/) and are never invoked during standard pipeline runs.

---

## Contact & Candidate Details
* **Candidate**: Vishwajit Patil
* **Email**: `vishwajitpatil5144@gmail.com`
* **Repository**: `https://github.com/vishwajitpatil5144-cloud/Signalpost_builderr.git`
* **Submission Target**: `submit@builderr.ai`
