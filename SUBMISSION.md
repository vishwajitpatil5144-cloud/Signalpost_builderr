# Signalpost Hackathon — Submission Manifest

Submit via email to: **`submit@builderr.ai`**

---

### Submission Email Content

**Subject:** Signalpost Submission — signal_scrape

**Body:**

1. **Agent Name:** `signal_scrape`
2. **Repository URL:** `https://github.com/vishwajitpatil5144-cloud/Signalpost_builderr.git`
3. **Commit Hash:** `fabba58c386a6cb51b7be4903a738bc3bfa9025b` (or latest HEAD on `main`)
4. **Completed Profiles Path (≥1,000):** `out/profiles-with-discovery.jsonl`
5. **Organisation-Number Manifest Path:** `out/manifest-1000.txt`
6. **Terminal Result Envelopes Path:** `out/terminal-envelopes-1000.jsonl`
7. **Machine-Readable Run Report Path:** `out/run-report.json` and `out/rerun-100-v8-20260921/run-report.json`
8. **Refresh / Change Evidence Path:** `out/rerun-100-v8-20260921/refresh-check.json` (idempotent rerun verified, 0 false changes)
9. **One-Command Run Instruction:**
   * PowerShell: `.\run_full_pipeline.ps1 -Organisations "out/iter-companies.jsonl" -Bulk "brreg-enheter.csv" -ExpectedCount 100 -RunId "daily-run"`
   * Bash: `./run_full_pipeline.sh out/iter-companies.jsonl brreg-enheter.csv 100 daily-run`
10. **Models, APIs, and Licences Used:**
    * Brønnøysundregistrene Enhetsregisteret & Regnskapsregisteret official bulk and open REST APIs (NLOD - Norwegian Licence for Open Government Data)
    * Free deterministic domain discovery & direct HTTP crawling with robots.txt compliance
    * Wikidata official SPARQL API (property P2333 exact orgnr matching, CC0)
    * OpenStreetMap Nominatim official API (ODbL, rate-limited to <= 1 req/s with on-disk caching)
    * NAV Arbeidsplassen official public vacancy feed (`pam-stilling-feed.nav.no`, NLOD)
    * No restricted scraping (LinkedIn, Meta, Glassdoor quarantined)
11. **Expected Cost per 100-Company Run:** `$0.00` (zero third-party paid API dependencies)
12. **Contact Details for Results:** Vishwajit Patil (vishwajitpatil5144@gmail.com)

---

### Verification Summary

* **Total Envelopes:** 1,000 completed terminal envelopes in `out/terminal-envelopes-1000.jsonl`
* **Six-State Vocabulary:** 100% compliant (`available`, `not_available`, `blocked`, `not_applicable`, `ambiguous`, `failed`)
* **Evidence References:** 0 dangling evidence IDs
* **Test Suite:** 120/120 tests passing in `tests/test_poc.py`
* **Evaluator Budget:** 570 requests on 100-company cohort (cap: 2,000 requests, 45 min wall clock)
