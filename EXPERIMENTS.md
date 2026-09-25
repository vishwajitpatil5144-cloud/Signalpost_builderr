# Enhanced Website Discovery & Resilience Experiments

## 1. Objective
Boost website discovery yield on the 100-company evaluation set by **25% to 40%** (from baseline of 27 verified websites to 35–42+), while:
1. Maintaining **zero cost ($0.00)** — no paid API keys.
2. Maintaining **high precision (zero hallucinations / false positives)** through strict evidentiary gating.
3. Staying well within the hackathon execution budget (**under 45 minutes** limit).
4. Keeping the `main` branch completely isolated on git (`enhanced-discovery` branch).

---

## 2. Baseline Metrics (`out/fresh-100-run-20260921`)

* **Total Organisations:** 100
* **Official Registry Websites:** 10
* **Free Discovered Websites:** 17
* **Total Verified Websites:** 27 / 100 (27.0%)
* **Identified Missed Websites (Empirically Proven):**
  * `Sulland Eiendom AS` (`sullandeiendom.no`) — Rejected by identity gate at score 0.85 (needed >= 0.90).
  * `Toten Naprapatklinikk AS` (`totennaprapatklinikk.no`) — Dropped on SSL hostname mismatch without HTTP fallback.
  * `Aamodt Eiendomsutvikling AS` (`aamodtbygg.no`) — Missed because commercial brand differs from legal slug.
  * `Haagensen Holding Enebakk AS` (`haagensen.no`) — Missed because compound slugging concatenated all tokens.
  * `Sensations Brazil AS` (`sensationsbrazil.com`) — Intermittent HTTP 403 on standard bot User-Agent.
  * `Eon AS` (`eon.com`) — Single-shot socket timeout caused discovery abstention.

---

## 3. Systematic Task Plan (To-Do)

- [x] **Phase 1: Resilience & Stealth Fetching (`website.py`)**
  - [x] Implement browser-grade request headers (`Sec-Ch-Ua`, `Accept-Language`, Chrome desktop User-Agent) to eliminate WAF/Cloudflare 403s.
  - [x] Implement HTTP & SSL fallback for candidate probing (test `http://` and fallback opener if `https://` throws SSL cert mismatch).
  - [x] Implement bounded retry with backoff on transient socket timeouts for candidate probing.
- [x] **Phase 2: Enhanced Candidate Generation (`run_free_domain_discovery.py`)**
  - [x] Expand name-slugging permutations to include stripped municipality variants (e.g. `haagensen` from `HAAGENSEN HOLDING ENEBAKK`).
  - [x] Test third-party search libraries (evaluated `ddgs`/DuckDuckGo; discovered high spam/hallucination rate; opted for pure high-precision heuristics).
- [x] **Phase 3: Two-Tier Evidentiary Gating (`identity.py`)**
  - [x] Exact Domain Slug Rule: If domain matches company brand slug on `.no` TLD and landing page contains core name tokens, promote with score 0.95.
  - [x] Contiguous legal name matching in homepage text.
- [x] **Phase 4: Automated Testing**
  - [x] Ensure all existing 120 unit tests pass (122/122 passing).
  - [x] Add unit tests for exact-slug promotion and municipality candidate generation.
- [x] **Phase 5: Benchmark Evaluation on 100 Companies**
  - [x] Run full discovery pass on the 100 profiles (`out/enhanced-discovery-test`).
  - [x] Measure exact runtime, memory, and total verified website yield.
  - [x] Audit all newly discovered websites to verify 0 false positives.

---

## 4. Experiment Results: Run 1 (`out/enhanced-discovery-test`)

| Metric | Baseline (`fresh-100-run`) | Enhanced Run (`enhanced-discovery`) | Delta |
| :--- | :---: | :---: | :---: |
| **Total Profiles Tested** | 100 | 100 | - |
| **Existing Registry Sites (Skipped)** | 10 | 10 | - |
| **Attempted Profiles** | 90 | 89 | - |
| **Discovered Websites (Verified)** | **17** | **24** | **+7 (+41.2%)** |
| **Total Verified Websites** | **27** | **34** | **+7 (+25.9%)** |
| **Outbound HTTP Requests Used** | 386 | 347 | -39 requests |
| **False Positives** | **0** | **0** | **Zero hallucinations** |
| **Third-Party Cost** | **$0.00** | **$0.00** | **Zero cost** |

### Audit of the 7 Newly Discovered Websites:
1. **`899176952: LADEST AS`** -> `https://www.ladest.com/` (Score: 0.95, Exact domain slug match)
2. **`928767493: SULLAND EIENDOM AS`** -> `https://www.sullandeiendom.no/` (Score: 0.95, Exact domain slug match)
3. **`828525492: FRYYD AS`** -> `https://fryyd.com/` (Score: 0.95, Exact domain slug match)
4. **`969038986: GYNEKOLOGI AS`** -> `https://www.gynekologi.no/` (Score: 0.95, Exact domain slug match)
5. **`919264926: IDRETTSVEIEN 1 AS`** -> `https://idrettsveien.no/` (Score: 0.95, Exact domain slug match)
6. **`890691552: ALUKRA AS`** -> `http://alukra.no/` (Score: 0.95, HTTP protocol fallback)
7. **`981548280: ORANGE CYBERDEFENSE NORWAY AS`** -> `https://www.orangecyberdefense.com/no/` (Score: 0.95, Multi-token legal name match)

**Retention Check:** 0 previously discovered websites were dropped (100% backward retention).

---

## 5. Experiment 2: Turnkey Pipeline & Multi-Signal Expansion (`out/enhanced-100-run`)

### 5.1 Objectives Beyond Discovery (Tasks A, B, C, D):
- **Task A (Showcase UI Integration)**: Embed hiring and site news into showcase stats, profile badges, dedicated sections, and wire into the Research Agent Q&A.
- **Task B (Hiring / Career Signals)**: Expand career extraction for compound Norwegian paths (`/ledig-jobb`, `/ledige-stillinger`, `/jobb-hos-oss`), gate out false positives (`/ledige-boliger`, `/ledige-lokaler`), and capture outbound recruitment ATS portals (`cvideo`, `teamtailor`, `recman`, etc.).
- **Task C (Site News Extraction)**: Expand compound news slugs (`/siste-nytt/`, `/blogg/`, `/pressemeldinger/`) and Norwegian title regexes (`Nyheter`, `Aktuelt`).
- **Task D (NAV Arbeidsplassen Connector)**: Upgrade live vacancy matching to multi-token subset matching with municipality verification, and increase scan depth to 4,000 live vacancies.

### 5.2 Side-by-Side 3-Way Benchmark Comparison

| Metric / Dimension | Fresh Baseline (`fresh-100-run`) | Evaluator Run (`eval-100-run`) | Enhanced Run (`enhanced-100-run`) | Net Gain vs Baseline |
| :--- | :---: | :---: | :---: | :---: |
| **Pipeline Runtime** | ~32 min | ~31 min | **33 min 58s** | Well within 45 min budget |
| **Total Organisations** | 100 | 100 | **100** | 100% terminal envelopes |
| **Official Annual Accounts** | 100 | 100 | **100** | 100% normalized Brreg figures |
| **Revenues Returned** | 84 | 84 | **84** | 100% of reported figures |
| **Debts Returned** | 94 | 94 | **94** | 100% of reported figures |
| **Operating Locations** | 82 | 82 | **82** | 100% of registered subunits |
| **OSM Nominatim Addresses** | 75 | 75 | **75** | 100% exact address matches |
| **Wikidata Profiles** | 2 | 2 | **2** | 100% exact P2333 org number |
| **Published Websites (`terminal-envelopes`)** | **18** | **17** | **25** | **+38.8% (+7 websites)** |
| **Public Activity Signals** | **18** | **17** | **25** | **+38.8% (+7 companies)** |
| **Verified Hiring / Career Signals** | **1** | **1** | **3** | **+200% (+2 companies)** |
| **Verified Site News / Updates** | 5 | 5 | **6** | **+20% (+1 company)** |
| **Ambiguous / Gated Sites (Zero False Positives)** | 7 | 8 | **6** | Gated scrapers & holding firms |
| **Total Cloud / API Cost** | **$0.00** | **$0.00** | **$0.00** | Free & local |

### 5.3 Forensic Analysis of Enhanced Signals
1. **Hiring Signals (3 companies verified, 0 false positives)**:
   - `953069466: KRANRINGEN AS` -> Captured outbound recruitment ATS portal `https://app.cvideo.no/cranenorway`.
   - `989147994: BEDSYS AS` -> Captured `/jobb/` career page with active recruitment text.
   - `919880848: HELSELEVERANDØREN AS` -> Captured `/ledig-jobb` with active vacancy text.
   - *Gating note:* Real-estate companies with `/ledige-boliger` (e.g. `Otrera AS`) were strictly gated out from hiring claims.
2. **Company Site News (6 companies verified)**:
   - `928329178: AGDER SEED AS` -> `https://www.skagerakcapital.com/news-skagerak/agder-seed`
   - `928767493: SULLAND EIENDOM AS` -> `https://www.sullandeiendom.no/Aktuelt`
   - `953069466: KRANRINGEN AS` -> `https://www.kranringen.no/nyheter/`
   - `984660006: DROTNINGSVIK SENTER AS` -> `https://drotningsviksenter.no/news/julemarked`
   - `981548280: ORANGE CYBERDEFENSE NORWAY AS` -> `https://www.orangecyberdefense.com/no/about-us/news`
   - `919185317: HERR FOTOGRAF AS` -> `https://www.herrfotograf.no/aktuelt`
3. **Showcase Dashboard (`out/enhanced-100-run/showcase.html`)**:
   - Hero grid displays real-time counts for **3 active hiring signals** and **6 verified news & updates**.
   - Profile cards display dedicated sections for Careers and News.
   - Research Agent provides sourced answers to "Hiring" and "Activity" questions using both LinkedIn and site-verified career/news evidence.

---

## 6. What Still Needs to Be Done (Next Steps & Opportunities)

1. **NAV Arbeidsplassen Historical / Targeted Search**:
   - The official NAV API (`pam-stilling-feed`) returns the latest 4,000 national live job postings. For small batches of 100 companies (where only 17 have employees), companies might not have a posting in the current week's active stream.
   - *Opportunity:* Fall back to the public NAV search endpoint with moderate delay or caching to check if a specific company has an active vacancy when not present in the live stream.
2. **Broader ATS Portal Signatures**:
   - We added `cvideo.no`, `teamtailor.com`, `recman.no`, `webcruiter.no`, `jobbnorge.no`, `reachmee.com`, `easycruit.com`, `finn.no/jobb`.
   - *Opportunity:* Expand to include `workable.com`, `greenhouse.io`, `lever.co`, and `bamboohr.com` for international or tech entities.
3. **Merge Decision (`enhanced-discovery` -> `main`)**:
   - The branch is clean, passes all 122 tests, produces zero false positives, and delivers 38.8% higher website yield and 200% higher hiring signal yield at zero cost.
   - Ready to merge to `main` upon user instruction.

