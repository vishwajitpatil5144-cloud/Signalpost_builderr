# Signalpost — Hackathon Context

**Purpose of this file:** everything an agent needs to know about this hackathon
in one place, so it doesn't need to re-read seven separate source documents to
understand what is being built and why. This is a faithful consolidation of
Builderr's own published materials (links at the bottom), current as of
**19 September 2026**. Where Builderr's own docs disagree slightly in wording
(they do, in a couple of places), this file notes both versions rather than
silently picking one.

---

## 1. What this is, in one paragraph

Builderr is running a paid challenge called **Signalpost**: build an agent
that, given a Norwegian company's organisation number, searches permitted
public sources, produces a company profile (identity, financials, leadership,
website, hiring, public activity), cites a source and date for every fact,
clearly marks what it couldn't find, and can be re-run later to detect real
changes without duplicating or fabricating them. Every entrant is tested on
the **same 100 randomly selected companies every day**, drawn from a public
list of 411,160 eligible companies — including company numbers the agent has
never seen before.

**Prize:** $2,500 in final rewards (see §8 for the exact breakdown — there is
a minor inconsistency in Builderr's own totals).
**Closes:** 21 October 2026. Daily random evaluation has been running since
24 August 2026.
**Qualification bar:** 65/100 or higher on an official run.
**Current public standings** (reviewed 16 September 2026, from a shared
100-company cohort): 10 submissions, 10 assessed, 7 qualified. Top scores:
Anmol 76.71, Ajai 70.32, digikuo/Harsh/Rakesh 66.92, Sanjai 65.92,
Karthik/AAFA 65.19 (qualified); Sudhir 62.92, Hardik 57.16, Dhanush 54.92
(not qualified). No winner declared yet. A new 100-company cohort is added
every other day and scores update as the checked collection grows.

---

## 2. What to build

Build a company research agent that, from an organisation number alone:

1. **Collects company details, people, locations, financial results, jobs
   and public activity** where available, from permitted public sources
   (company websites, official registries, other permitted sources).
2. **Checks each fact belongs to the right company**, links it to its source
   and date, and clearly marks anything it could not find.
3. **Keeps profiles current**: re-checks sources, shows what changed, and
   preserves the earlier evidence rather than overwriting it.

The product should help someone understand a company before they apply,
sell, partner, or invest: what it does, who leads it, where it operates, how
its latest filed numbers look, whether it appears to be hiring, and what
dated public activity the checked sources reveal.

The agent must work from a bare company number, **including companies it has
not researched before** — daily test batches can and do include company
numbers outside whatever 1,000+ you submitted.

---

## 3. Universe and corpus

- **Universe definition:** Norway-registered entities with observed official
  annual-account records, frozen to the **2025-filer snapshot**.
- **Public universe size:** 411,160 eligible organisation numbers.
- **Full company list file:** `signalpost-company-universe-2025.jsonl.gz`
  - Uncompressed content SHA-256: `b82d6a3e7231d1759a958c282bc4366b80ec2fab8095053d8ed7fa9cd01bc838`
  - Download archive SHA-256: `1c89710e5b01f8617e86d09fbdff4a52f2f8dbbba297e74f7164b5984f5a0384`
  - Row count when decompressed: 411,160 (verified against this project's
    copy — see §11).
- **Public product sample:** 100 profiles hosted at `builderr.ai/signalpost`
  — a demo/reference implementation, not a live production dataset. Its
  website-coverage rate (looked artificially high, ~60/100 in the fixture)
  is **not representative** of the real universe — a genuine random draw
  from the real registry shows real-world website coverage closer to
  **~14–15%**, since most randomly drawn entities are holding companies or
  property entities with no public website at all.

---

## 4. What to submit

- **At least 1,000 completed company profiles**, plus the exact list
  (manifest) of organisation numbers used. Larger submissions (10,000, or
  the full universe) are allowed but **not directly rewarded** — the source
  policy explicitly states the competition does not reward request count,
  pages downloaded, or raw records collected; it rewards exact-company,
  decision-useful coverage with valid evidence.
- **Repository link and exact commit hash.**
- **One command to run the agent.**
- **Disclosure**: models/APIs/licences used, expected cost per 100-company
  run, and contact details for results.
- Choose companies from the supplied universe list; include sources and
  dates in every profile; make missing information explicit rather than
  guessed or zeroed.

**Submission channel:** email `submit@builderr.ai` with: agent name,
repository URL, exact commit hash, completed-profiles path (≥1,000),
organisation-number manifest path, **terminal result envelopes path**,
machine-readable run report path, refresh/change evidence path, one-command
run instruction, models/APIs/licences, expected cost per 100-company run,
and contact for results.

**Versioning:** your first submission is version 1. You may submit up to
**four revised commit hashes** before **18 October 2026**, for five versions
total. Each revision is frozen before its next daily run and applies only to
batches after that point — it never retroactively changes earlier batch
results.

---

## 5. How daily testing works

- Every entered agent is run on the **same 100 randomly selected companies
  each day**, chosen fresh after a daily cutoff from the full 411,160-company
  list. This batch can include companies outside your submitted 1,000 —
  generalization is being tested, not memorization of a fixed set.
- **Locked evaluator budget, per 100-company daily batch:**
  - 100 input organisation numbers
  - 45 minutes wall clock
  - 8 vCPU, 16 GB RAM, 10 GB temporary disk
  - **2,000 outbound requests max**, including redirects and retries
    (cache hits are free; Builderr-supplied official snapshots don't count
    toward third-party spend)
  - **$10 maximum declared third-party API spend**
- Builderr supplies the organisation numbers, the cutoff, and the output
  contract — not the companies' official sites or social identities; those
  are what your agent has to find.
- **Ranking method:** final ranking is the **mean score across every
  scheduled daily batch** while your frozen version is active — not your
  single best run. An entrant-caused failure or missed batch (after Builderr
  reproduces it in a clean evaluator run) scores **zero** for that batch. A
  failure caused by Builderr's own harness, infrastructure, or a shared
  source is **voided and rerun** for every affected entrant on the same
  frozen code.

---

## 6. Required output contract (the terminal envelope)

**Exactly one terminal envelope per input organisation number**, even when
sources are missing or blocked — never skip a company, never silently turn
absence into zero.

**Required sections in every envelope:**
1. Legal identity and public brand
2. Latest annual accounts and available history
3. Leadership and registered workplaces
4. Verified official website and company-owned profiles
5. Hiring and dated public activity from permitted sources
6. Claim-level evidence and availability state
7. Refresh metadata and material changes since the previous run

**The exact six valid availability states** — use these and only these:
`available`, `not_available`, `blocked`, `not_applicable`, `ambiguous`,
`failed`. (Builderr's short participant brief calls these "explicit states
such as..." while the formal evaluation contract calls them "valid states
are..." with the same six — treat the list as exact and closed, not
illustrative.)

**Reference shape** (from this project's `OUTPUT_CONTRACT.md`, itself a
transcription of the evaluation contract's requirements):
```json
{
  "organisation_number": "123456789",
  "run": {
    "run_id": "2026-08-24-a",
    "started_at": "2026-08-24T06:00:00Z",
    "completed_at": "2026-08-24T06:00:08Z",
    "terminal_status": "completed"
  },
  "claims": [
    {
      "field": "official_website",
      "value": "https://example.no/",
      "availability": "available",
      "confidence": 0.99,
      "evidence_ids": ["ev-1"]
    }
  ],
  "evidence": [
    {
      "id": "ev-1",
      "source_url": "https://example.no/",
      "source_class": "company_owned",
      "retrieved_at": "2026-08-24T06:00:04Z",
      "content_sha256": "...",
      "claim_span": "Example AS, organisation number 123 456 789"
    }
  ],
  "changes": [],
  "errors": [],
  "operations": {
    "requests": 4,
    "runtime_ms": 8120,
    "third_party_cost_usd": 0
  }
}
```
A checked source that returned zero jobs or zero locations is a **different,
distinguishable state** from a source that was never checked at all — don't
collapse the two.

**Critical judgment call embedded in this contract:** a website (or other
fact) that was *fetched successfully* but could **not be confirmed to belong
to the exact legal entity** must be reported as `ambiguous`, not `available`.
Reporting an unverified match as available is a step toward exactly the
"material wrong-company publication" that blocks qualification. *"It is
better to miss some information than publish it under the wrong company."*
(direct quote, repeated near-verbatim in three of the source documents).

---

## 7. Scoring — 100 points total

| # | Category | Points | What it measures |
|---|---|---|---|
| 1 | Coverage and source discovery | 35 | How much checked information you found |
| 2 | Accuracy, exact identity and evidence | 30 | Whether each fact belongs to the right company, with valid source and date |
| 3 | Refresh and extensibility | 20 | Whether reruns show real changes, preserve evidence, avoid duplicates/false changes |
| 4 | Decision-useful synthesis | 10 | Whether the profile explains the company, what changed, and what's unknown — without unsupported claims |
| 5 | UX and interaction | 5 | Whether a user can find, compare and verify information on desktop and mobile |

### Coverage scoring formula (the 35-point category)
For each information type (field family): **70% of its score is company
recall, 30% is individual-claim recall**, both measured against a shared,
independently verified reference collection (see §7a).

**Worked example from the official docs:** the checked collection has 50 job
postings across 20 companies. You find 30 postings across 15 of those
companies → 60% of postings, 75% of companies →
`70% × 75% + 30% × 60% = 70.5%` for that information type. This is one
field's contribution to the 35 coverage points, not your total score —
different information types carry different weights within the 35.

### 7a. The shared, growing reference collection
Builderr combines **independently checked findings from every submission
plus Builderr's own crawlers** into one pooled reference collection.
Duplicate facts and wrong-company matches are removed from the pool. New
verified findings **update the collection, and every entrant is rescored
against the new version** — each addition is hashed and versioned. **This is
the checked information found so far, not a claim of finding everything
online.** The union freezes only after all eligible final submissions have
been verified. Practical implication: finding something nobody else found
(and getting it verified) raises the bar for everyone, including future
rescoring of your own earlier work.

### 7b. What to optimize, in order
1. **First**, make sure every fact belongs to the right company and has
   evidence — a high score cannot make up for a material wrong-company
   match.
2. **Then**, increase how much checked information you find.

---

## 8. Qualification and official-run rules

- **Qualification = an official run scoring ≥65/100 overall.**
- Coverage, recall, accuracy, refresh, synthesis and usability are **scored
  dimensions of that one number**, not separate pass/fail thresholds on
  their own (stated three times across the sources, worded slightly
  differently each time, always meaning the same thing).
- **Sparse-data escape hatch:** if the verified pool has fewer than 15
  positive company-field opportunities across at least three external field
  families, recall for that batch is reported as **"not measured"** rather
  than scored as 0%. This is a scored observation, not a qualification gate.
- **Your score and your qualification are separate things.** A small factual
  mistake only lowers accuracy. A **material wrong-company match** is worse
  — it can put an entire website, brand, and set of facts under the wrong
  profile — so your score stays visible, but the run **cannot become
  official** until the match is corrected.

### Official-run checklist (all must hold)
- Submitted public artifact has ≥1,000 completed profiles and its exact
  organisation-number manifest.
- Exactly 100 terminal envelopes produced for every daily batch.
- No fabricated financial values, no material wrong-company publication.
- Claim-level source, retrieval time, and reporting period recorded where
  relevant.
- Honest availability states (never silently converting missing to zero).
- Idempotent refresh — re-running the same source snapshot must not create
  duplicate records or false changes; earlier evidence must be preserved.
- Reproducible setup: pinned dependencies, one evaluator command.
- Source rights, server-side secrets, and safe outbound-URL handling are
  documented.
- Unsafe source/secret handling, fabricated claims, compromised evidence, or
  evaluator failures are investigated with named ownership — **unless** the
  failure is Builderr's own harness/infrastructure/shared-source issue, in
  which case it's rerun and not attributed to the builder.

### Tiebreaks (in exact order)
1. Fewer wrong-company publications
2. Higher weighted company recall
3. Lower declared third-party API cost

---

## 9. Source policy — what you can and can't use

### Preferred, in priority order (the "source ladder")
1. **Official registers and annual accounts** — Brønnøysundregistrene
   Enhetsregisteret (bulk data + entity API) for identity, legal form,
   address, industry, registered employee count; Regnskapsregisteret API for
   filed financial data and history; official roles and subunit endpoints.
   *This is the identity anchor — it does not, by itself, identify the
   public brand or website.*
2. **Verified company-owned sources** — the company's own verified website,
   sitemap, news/investor/careers/location/contact pages, structured data
   the company embeds, and social/video profiles **linked from the verified
   company site** (subject to that destination platform's own terms).
3. **Official or licensed platform APIs.**
4. **Permitted public pages** whose terms and robots policy allow the
   submitted access pattern (licensed news, review, jobs, traffic, or
   company-data feeds).
5. **Search/discovery providers — for candidate generation only, never as
   evidence itself.**

### Publication rules
- Search results generate *candidates*; they are never claim evidence on
  their own.
- A profile or domain must resolve to the **exact legal entity** before its
  facts are published — parent, subsidiary, franchise, and public-brand
  relationships must be **labelled, not collapsed** into the entity being
  profiled.
- Every claim needs: source URL/identifier, retrieval time,
  effective/reporting date where relevant, content hash, and extraction
  method.
- Missing, blocked, and ambiguous are explicit, first-class states — not
  omissions.
- Company-owned promotional copy can describe the business but **cannot
  serve as independent sentiment evidence**.

### Restricted platforms — the non-negotiable limitation
**LinkedIn, Meta, Glassdoor, Indeed, and similar platforms have access
restrictions.** Use only official, licensed, or otherwise permitted access.
- An unofficial/open-source client for these platforms is **not made
  acceptable just because code for it exists on GitHub.**
- Such a connector **may be tested privately** as a candidate-discovery
  experiment, but for competition scoring the entrant must (a) declare the
  connector, (b) demonstrate permitted access, and (c) **independently
  verify any published claim from a durable permitted source** — the
  unofficial connector can never be the *sole* support for a published
  claim.

### Evidence beats volume
Direct quote: **"The competition does not reward request count, pages
downloaded or raw posts collected."** It rewards exact-company,
decision-useful coverage with valid evidence and reproducible refresh
behavior.

---

## 10. Agent playbook — recommended architecture (not mandated)

Builderr is explicit that this is a *reference* architecture: "keep any
component only when a blind evaluation shows that it improves coverage
without increasing wrong-company or unsupported-claim rates."

1. **Start with authoritative identity.** Seed every run with organisation
   number, legal name, legal form, registered address, industry, and latest
   filing year from Brønnøysundregistrene. The organisation number is the
   stable key; a brand/domain/handle is only a *candidate* until tied back
   to the exact entity.

2. **Resolve public identity as an evidence graph**, not name-similarity
   matching:
   `legal entity → official site candidate → public brand/aliases → leaders/founders → company profile candidate → reverse proof`
   Useful proof: the organisation number appearing on the site, or a strong
   combination of legal name + address + phone + leadership + independent
   official evidence. Parent brands, franchises, sister companies, and
   portfolio pages are **not** exact matches.
   *Leader-bridging is sanctioned*: find a verified role in the official
   register → locate that person's public profile via a permitted source →
   confirm it resolves back to the same entity. This only **generates
   candidates** — it never replaces exact-entity verification.

3. **Crawl deterministically first**, escalate only when needed:
   - Scrapy (queues/throttling/retry/dedup/per-domain budgets)
   - Sitemap + static HTML before browser rendering
   - extruct (JSON-LD/OpenGraph/microdata)
   - Trafilatura (readable text)
   - Playwright **only** after a deterministic check confirms a JS shell
   - Pydantic (or equivalent) validation before publication
   - Plain PDF text extraction first; layout/OCR only for difficult reports
   - Priority paths: `/about`, `/om-oss`, `/contact`, `/kontakt`,
     `/leadership`, `/ledelse`, `/locations`, `/careers`, `/jobs`, `/news`,
     `/investor`

4. **Never use search rank or an unofficial scraper response as evidence
   itself** — always re-fetch the underlying permitted source and preserve
   it.

5. **Preserve evidence before extraction.** Store immutable raw snapshots
   with: requested + final URL, redirect chain + response status, retrieval
   timestamp, relevant effective/reporting date, content hash, parser +
   extractor version, source class + access policy. Every published claim
   should point to a snapshot plus a selector/character span/table
   cell/PDF page.

6. **Extract in layers, in this order**: structured data → DOM attributes →
   clean text → deterministic role/location rules → **model extraction
   last**. Validate every output. Retain conflicting candidates rather than
   silently picking one. *An LLM may summarise supported claims or propose
   candidates. It must not decide exact identity, invent a missing field, or
   silently override deterministic evidence.*

7. **Refresh as a diff**, using stable claim keys + immutable snapshots +
   idempotent upserts. A refresh should output: current supported value,
   previous supported value, first/last observed timestamps, change type +
   materiality, sources supporting both sides. Re-crawl by source
   volatility (annual accounts: slowly; jobs/news: frequently). **A failed
   refresh must keep the last known supported value and expose the
   failure** — never erase it.

8. **Evaluate as a control loop.** Freeze dev/validation/final sets with no
   organisation or host overlap. Hand-label exact identity, claim support,
   expected availability. Tune only on dev, set thresholds once on
   validation, run final once. Track: exact-company precision + wrong-company
   publications, field precision/recall/coverage, evidence-span validity,
   static vs. browser-rendered crawl success, refresh correctness +
   false-change rate, cost/requests/p50/p95 time per company. **Abstention
   is allowed and must be reported — it cannot hide low coverage.**

9. **Suggested repo files:** `README.md`, `AGENT.md` (research/abstention
   policy), `CRAWLERS.md` (connectors/budgets/fallbacks), `IDENTITY_RESOLUTION.md`
   (candidate + publication gates), `DATA_SCHEMA.md` (envelopes/claims/
   evidence), `REFRESH.md` (scheduling/snapshots/diffs), `EVAL.md` (corpus
   split/metrics/thresholds), `LIMITATIONS.md` (known gaps/licences/
   source restrictions).

---

## 11. Learning harness — how to iterate safely

Core loop: **try a strategy → preserve the attempt → score it → compare it
→ promote or reject it.** Public development data is training ground;
hidden companies are the exam.

1. **Strategy registry** — every discovery/extraction route gets a stable
   name + version (e.g. `registry-provided website`, `sitemap and robots
   discovery`, `static homepage crawl`, targeted-path crawl, `JSON-LD/
   OpenGraph extraction`, `search-provider candidate discovery`,
   `leader/founder bridge`, `browser-rendered fallback`, `annual-account
   PDF fallback`). New strategies enter the registry and face the same
   tests as the current winner — the agent must never silently invent and
   deploy new production code.

2. **Save every attempt**: strategy name+version, input org number,
   requested URLs + redirect chain, raw snapshot hashes, candidate
   domains/profiles/claims, accepted **and rejected** claims with reasons,
   exact-identity evidence, runtime/requests/cost, errors + availability
   states. This makes failures diagnosable (found nothing vs. wrong company
   vs. bad extraction vs. too expensive).

3. **Score in strict priority order:**
   1. Wrong-company publications — must not increase
   2. Supported-claim precision — must not fall
   3. Evidence validity — every accepted claim points to the right source span
   4. Coverage and recall — useful supported fields added
   5. Refresh correctness
   6. Runtime, requests, cost
   *"A strategy that finds more data about the wrong company loses."*

4. **Strict promotion rule** — promote a challenger only when **all** hold:
   zero new material wrong-company publications; no meaningful precision
   drop; 100% evidence completeness on published material claims; useful
   coverage/recall improves by a declared minimum; runtime/cost stay in
   budget. Keep the previous strategy available for rollback; store the
   decision + exact evaluation report.
   *For v1, use a decision table, not reinforcement learning* (e.g. static
   HTML first, browser render only after a JS-shell test, PDF layout
   parsing only when plain text fails). A learned router is optional later.

5. **Learning ≠ refresh.** Learning picks better strategies; refresh
   revisits evidence with the chosen frozen strategies. Refresh should emit
   a typed change like `new_role`, `closed_job`, `new_location`,
   `new_filing`, `changed_description`. A failed refresh must not erase the
   last supported value.

6. **Freeze before each daily evaluation**: code + dependency lockfile,
   strategy versions + routing table, prompts/models/model versions,
   thresholds + publication gates, source allowlist + budgets. Hidden
   scores/labels must never tune the running submission.

### Recommended open-source stack (all free)
- **Crawl/extraction:** Scrapy, scrapy-playwright, extruct, Trafilatura,
  Pydantic
- **Identity/normalization:** RapidFuzz, tldextract, phonenumbers
- **Documents:** pypdf (first pass), Docling (tables/layout), Tesseract OCR
  (scanned pages only)
- **Eval/storage:** pytest, DuckDB + Parquet, OpenTelemetry Python
- **Optional connector experiments:** JobSpy (job-discovery benchmarking),
  yt-dlp (public video metadata) — *"these are experiments, not automatic
  permission to collect. The submitted access method must comply with
  source terms and applicable law."*

### Suggested minimal repo layout
```text
strategies/
  registry_site.py
  sitemap_static.py
  search_candidates.py
  browser_fallback.py
  pdf_fallback.py
eval/
  gold_companies.jsonl
  score_attempts.py
  promotion_gate.py
snapshots/
claims/
reports/
```
One command should run the public loop and produce a comparison report:
```bash
python -m eval.run --corpus eval/gold_companies.jsonl --challenger browser_fallback_v2
```

---

## 12. Measurement Builderr reports on every run

Exact-company precision, wrong-company publications, per-field
precision/recall/coverage, evidence-span validity, crawl completion, refresh
correctness, false-change rate, cost per company, request count, and
p50/p95 runtime. **Abstention is reported separately and cannot satisfy
coverage.**

---

## 13. Rewards

- **Main challenge pool — $2,000:** $1,200 / $500 / $300 for 1st / 2nd / 3rd.
- **Separate JBOX bonus pool — $500:** $250 / $150 / $100 for qualifying
  agents built with JBOX.
- **Community-vote awards — $100 × 4**, on 6 September, 20 September,
  4 October, and 18 October 2026. **Public voting never changes the
  technical ranking.**
- *(Note: the challenge page's headline figure says "$2,500 final rewards,"
  which matches main pool + JBOX bonus ($2,000 + $500); the four $100
  community awards ($400 total) appear to be additional to that headline
  figure, not included in it. Transcribed as published — Builderr's own
  numbers don't fully reconcile here.)*
- Only **technically qualified** entries enter the hosted Builderr gallery.
  Builderr covers hosting during the competition.
- **Beyond the prize:** the winning builder gets the opportunity to partner
  with Håvard Liltved Dalen (CPO at Fronted, co-founder of JBOX) to launch
  Signalpost in Norway.

---

## 14. This project's current compliance status (as of last audit)

This repo (`signal_scrape`) implements the pipeline as: registry identity →
registry-listed website → free domain-guess discovery → deterministic
synthesis → **export to the terminal-envelope format** described in §6.

Known-resolved gap: the internal pipeline originally used a non-conforming
status vocabulary (`not_found`/`not_fetched`/`source_error`) and labelled
identity-unverified website matches as `available`. `scripts/
export_terminal_envelopes.py` now translates internal statuses into the
required six-state vocabulary and — critically — maps a fetched-but-
unverified website to `ambiguous` rather than `available`, in line with §6's
core rule and the repeated instruction across every source document that
"it is better to miss some information than publish it under the wrong
company." Validated against the current 100-company live rerun in
`signal_scrape/out/rerun-100-20260919/`: 100 terminal envelopes, 1,296
claims, 8 `ambiguous` claims, 1 `blocked` claim, 2 `failed` claims, and no
invalid availability states. The rerun used 562 official requests plus 241
free-discovery requests, for 803 outbound requests total.

Known-restricted-by-design: LinkedIn/Meta/Indeed connectors are present in
the original starter kit but quarantined to `scripts/experimental_restricted/`
and excluded from the default pipeline, per §9's non-negotiable platform
restriction.

Verified in the current 100-company rerun: every exported envelope has
nonzero `operations.requests` and `operations.runtime_ms`, derived from the
batch runner's per-profile `run_metrics`. The exporter also accepts
`--previous` and computes tracked-field refresh events into `changes[]`.
The live diff found 3 changes for 1 company and `idempotent_rerun: true`.

The project currently has 107 passing tests. The rerun artifacts are kept in
`signal_scrape/out/rerun-100-20260919/` and are intentionally separate from
the existing 1,000-company outputs.

---

## 15. Source documents (all fetched and confirmed accessible 19 Sep 2026)

- Challenge page (incl. scoring section): https://builderr.ai/challenges/signalpost
- Participant brief: https://builderr.ai/starter-briefs/signalpost.md
- Agent playbook: https://builderr.ai/starter-briefs/signalpost-agent-playbook.md
- Learning harness: https://builderr.ai/starter-briefs/signalpost-learning-harness.md
- Source policy: https://builderr.ai/starter-briefs/signalpost-sources.md
- Evaluation contract: https://builderr.ai/docs/signalpost-evaluation-harness.md
- Public 100-company sample: https://builderr.ai/signalpost
- Starter kit download: https://builderr.ai/signalpost-starter-kit.zip
- Full universe download: https://builderr.ai/signalpost-company-universe-2025.jsonl.gz
- Submission email: submit@builderr.ai

---

## 16. Required update command after every change

After every code, pipeline, schema, or documentation change, run this single
PowerShell command from `D:\signal_scrape\signal_scrape`:

```powershell
..\.venv\Scripts\python.exe -m pytest; if ($LASTEXITCODE -eq 0) { git diff --check; git status --short }
```

Do not treat a change as complete until the tests pass and the resulting Git
status has been reviewed. For pipeline changes, also rerun the smallest
relevant smoke or live command and record its output in the work log or
session summary.

## 17. v4 connector validation (20 September 2026)

The v4 implementation adds three bounded company-site outputs to the default
pipeline: `public_activity`, company-owned news activity, and `hiring_signal`.
The hiring signal reports only verified careers/jobs-page existence and hiring
language; it never asserts a job count. Career paths are included in the
crawler priority list, without adding a separate request budget.

Fresh validation artifacts are in
`signal_scrape/out/rerun-100-v4-20260920/`. The run produced 100 terminal
envelopes and 1,596 claims: 20 `public_activity` claims, 3 company-news
observations, 1 `hiring_signal` claim, and 7 `ambiguous` website claims. All
100 envelopes had nonzero operations metrics and all claims used valid
availability states.

## 18. v5 retry validation (20 September 2026)

V5 adds bounded retries to website fetching: transient server errors,
network errors, and unexpected fetch errors receive up to two retries, while
404/410 remain terminal `not_available` outcomes. This improves resilience
without changing the identity gate or claiming unavailable data.

Fresh artifacts are in `signal_scrape/out/rerun-100-v5-20260920/`. The 100-
company run emitted 100 envelopes and 1,596 claims. It used 570 official
requests and 347 discovery requests, for 917 outbound requests total, below
the 2,000-request budget. The distributions were 20 `public_activity`, 3
company-news observations, 1 bounded `hiring_signal`, and 7 `ambiguous`
website claims. All envelopes had nonzero operations metrics and valid states.

## 19. v6 external footprint & multi-connector validation (20 September 2026)

V6 implements the external footprint schema and multi-connector expansion
strictly conforming to AGENT_MISSION.md §0 rules:

1. **Signal-bucketed link selection & career discovery fix**:
   Refactored `_priority_links()` in `website.py` into signal buckets (`career`,
   `news`, `identity`, `contact`, `leadership`, `locations`) with round-robin
   interleaved candidate selection. This prevents common product phrases (e.g.
   "management") from crowding out careers and news. Expanded `CAREER_PATH` and
   added `CAREER_TITLE` matching in `extract_company_hiring_signal.py`.

2. **Wikidata connector (`official_api`, free, approved)**:
   `scripts/run_wikidata_connector.py` queries Wikidata SPARQL for exact
   Norwegian organisation numbers (property P2333). Batches 100 org numbers in
   1 SPARQL request. Emits `company_profile` with exact identity proof.

3. **OpenStreetMap / Nominatim location verification connector**:
   `scripts/run_nominatim_connector.py` cross-verifies registered business
   addresses from Brreg against OpenStreetMap. Adheres strictly to Nominatim
   Usage Policy: rate-limited to >= 1.1s intervals (<= 1 req/s) with on-disk
   caching in `out/cache/nominatim/`. Verified 80/100 companies in the benchmark
   batch with exact coordinates and OSM place IDs (80/80 publishable observations,
   0 errors). Emits `place_summary` claims.

4. **Google Places & YouTube API connectors (§0 Rule 4)**:
   Implemented `scripts/run_google_places_connector.py` and
   `scripts/run_youtube_api_connector.py` behind `SIGNAL_SCRAPE_GOOGLE_PLACES_API_KEY`
   and `SIGNAL_SCRAPE_YOUTUBE_API_KEY`. When keys are unset, both report cleanly
   as inactive pending operator keys without failing the run.

5. **Terminal envelope exporter & pipeline synchronization**:
   `scripts/export_terminal_envelopes.py` accepts `--wikidata` and `--nominatim`
   and emits `company_profile` and `place_summary` claims with full six-state
   vocabulary compliance. Both `run_full_pipeline.ps1` and `run_full_pipeline.sh`
   are synchronized with the new stages. Fresh export on the 100-company rerun
   contains 1,796 claims (1,187 available, 7 ambiguous, 3 failed, 1 blocked,
   598 not_available) with zero invalid states and zero dangling evidence references.

6. **Self-audit tooling & tests**:
   Created `scripts/audit_published_claims.py` for human review. Test suite
   expanded from 110 to 114 tests, all passing in 2.9 seconds. Total requests:
   1,012 / 2,000 budget, $0 cost.

## 20. v7 Prototype Showcase and Deterministic Synthesis (20 September 2026)

V7 folds the external footprint into the decision-useful synthesis and browsable
showcase UI:
1. `generate_synthesis.py` ingests `--activity`, `--news`, `--hiring`, `--wikidata`,
   and `--nominatim` to enrich deterministic summaries with verified geo-coordinates
   and Wikidata descriptions without LLM hallucinations.
2. `build_prototype.py` showcases verified OpenStreetMap locations, Wikidata entity
   links, updated stats counters, and intelligent Q&A routing in the Research Agent.
3. Test suite expanded to 116 tests passing.

## 21. v8 NAV Arbeidsplassen Vacancy Connector & Backlog Resolution (20 September 2026)

V8 addresses the remaining backlog items from AGENT_MISSION.md §3:
1. **NAV Arbeidsplassen Vacancy Connector (`official_api`, free, approved)**:
   Built `scripts/run_nav_arbeidsplassen_connector.py`. Authenticates via Norway Labour
   and Welfare Administration's official public JWT (`pam-stilling-feed.nav.no/api/publicToken`)
   and streams 1,000-item vacancy pages. Emits `job_posting` observations passing
   `external_footprint.validate_observation` with exact businessName and municipality
   identity verification. Wired into `export_terminal_envelopes.py` via `--nav`,
   `generate_synthesis.py`, and both `run_full_pipeline.ps1` and `run_full_pipeline.sh`.
2. **Google News RSS Connector Compliance Audit**:
   Empirical check of `news.google.com/robots.txt` confirmed that `/rss/search` is
   explicitly disallowed under `User-agent: * Disallow: /`. Documented in `OPEN_QUESTIONS.md`
   under §0 Rule 3 & Rule 9; kept quarantined to prevent rights violations.
3. **Fagfolkguiden Reviews Connector**:
   Moved to `scripts/experimental_restricted/` per mission instructions because review
   ratings are syndicated from Google Local rather than native, and directory coverage
   on general companies is negligible.
4. **Sentiment Model Evidence Gating**:
   Verified that `src/signal_scrape_core/external_footprint.py` strictly abstains
   (`status: "abstain"`, `score: None`) until the required threshold of >=10
   independent observations across >=2 distinct hosts is reached (§0 Rule 2 compliant).
5. **Playwright Feasibility Evaluation**:
   Empirically confirmed that headless Chromium browser binaries are absent in the local
   environment and spawning heavyweight browser engines risks blowing the 45-minute
   evaluator budget. Static link extraction + round-robin priority interleaving captures
   career pages deterministically without browser overhead.
6. **Operations Telemetry & Budget Verification**:
   Verified that every envelope contains real per-company request and runtime measurements
   (averaging 5–7 requests/co, total 570 requests on 100-company rerun, well within the
   2,000 budget cap; $0 third-party cost).
7. **Test Suite Expansion**:
   Added `NAVArbeidsplassenConnectorTests` with 4 test cases; 120/120 tests passing in 2.87s.

