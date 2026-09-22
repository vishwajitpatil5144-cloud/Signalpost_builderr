# Signalpost Hackathon — Submission Manifest

Submit via email to: **`submit@builderr.ai`**

---

### Submission Email Content

**Subject:** Signalpost Submission — signal_scrape

**Body:**

1. **Agent Name:** `signal_scrape`
2. **Repository URL:** `https://github.com/vishwajitpatil5144-cloud/Signalpost_builderr.git`
3. **Commit Hash:** `182198f131d1a68a4edfb2e58be3f4c99225a429`
4. **Completed Profiles Path (≥1,000):** `out/full-1000-run-20260921/profiles-with-discovery.jsonl`
5. **Organisation-Number Manifest Path:** `out/full-1000-run-20260921/manifest-1000.txt`
6. **Terminal Result Envelopes Path:** `out/full-1000-run-20260921/terminal-envelopes.jsonl`
7. **Machine-Readable Run Report Path:** `out/full-1000-run-20260921/run-report.json`
8. **Refresh / Change Evidence Path:** `out/full-1000-run-20260921/refresh-check.json` (idempotent rerun verified, 0 false changes across 1,000 entities)
9. **Interactive Showcase (1,000 entities):** `out/full-1000-run-20260921/showcase.html`
10. **One-Command Run Instruction:**
   * **Full 1,000-Company Submission Reproduction:**
     * PowerShell: `.\run_full_pipeline.ps1 -Organisations "out/full-1000-run-20260921/companies.jsonl" -Bulk "brreg-enheter.csv" -ExpectedCount 1000 -RunId "eval-1000" -OutDir "out/eval-1000-run"`
     * Bash: `./run_full_pipeline.sh out/full-1000-run-20260921/companies.jsonl brreg-enheter.csv 1000 eval-1000 out/eval-1000-run`
   * **Fast 100-Company Evaluation Check (~5 min budget check):**
     * PowerShell: `.\run_full_pipeline.ps1 -Organisations "out/fresh-100-run-20260921/companies.jsonl" -Bulk "brreg-enheter.csv" -ExpectedCount 100 -RunId "eval-100" -OutDir "out/eval-100-run"`
     * Bash: `./run_full_pipeline.sh out/fresh-100-run-20260921/companies.jsonl brreg-enheter.csv 100 eval-100 out/eval-100-run`
11. **Models, APIs, and Licences Used:**
    * Brønnøysundregistrene Enhetsregisteret & Regnskapsregisteret official bulk and open REST APIs (NLOD - Norwegian Licence for Open Government Data)
    * Free deterministic domain discovery & direct HTTP crawling with robots.txt compliance
    * Wikidata official SPARQL API (property P2333 exact orgnr matching, CC0)
    * OpenStreetMap Nominatim official API (ODbL, rate-limited to <= 1 req/s with on-disk caching)
    * NAV Arbeidsplassen official public vacancy feed (`pam-stilling-feed.nav.no`, NLOD)
    * No restricted scraping (LinkedIn, Meta, Glassdoor quarantined)
12. **Expected Cost per 100-Company Run:** `$0.00` (zero third-party paid API dependencies)
13. **Contact Details for Results:** Vishwajit Patil (vishwajitpatil5144@gmail.com)

---

### Verification Summary

* **Total Envelopes:** 1,000 completed terminal envelopes in `out/full-1000-run-20260921/terminal-envelopes.jsonl`
* **Six-State Vocabulary:** 100% compliant (`available`, `not_available`, `blocked`, `not_applicable`, `ambiguous`, `failed`)
* **Evidence References:** 0 dangling evidence IDs
* **Test Suite:** 120/120 tests passing in `tests/test_poc.py`
* **Evaluator Budget:** 570 requests on 100-company cohort (cap: 2,000 requests, 45 min wall clock)
