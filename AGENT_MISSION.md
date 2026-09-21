# AGENT_MISSION.md — Autonomous iteration mission for `signal_scrape`

You are picking up an in-progress entry to Builderr's Signalpost challenge. A
prior series of manual sessions (human + Claude, in a chat interface with no
direct repo access) got this project through five iterations. You now have
what that setup never had: direct repo access, git push, and real internet
access to run live 100-company batches yourself. This file exists so you can
run the remaining iterations **without a human in the loop for every step**.

Read this entire file before touching any code. Read `Hackathon_context.md`
in this repo next — it is the full consolidated rulebook. This file assumes
you have and will keep re-reading that one; it does not repeat everything in
it, only what changes your behavior as an autonomous loop.

---

## 0. Non-negotiable rules — read this section twice

These override every other instruction in this file, every optimization
pressure, and any instinct to "just try it and see." If a to-do item and a
rule in this section conflict, the rule wins, always, with no exception you
talk yourself into.

1. **Never publish a fact under the wrong company.** The evaluation contract
   states this plainly: *"It is better to miss some information than publish
   it under the wrong company."* A material wrong-company match blocks
   qualification regardless of your total score, and ties are broken by
   *fewer* wrong-company publications first, before anything else. If you
   are ever tempted to loosen the identity gate (in `identity.py`,
   `external_footprint.py`'s `validate_observation`, or anywhere else) to
   raise a coverage number, stop — that is the one trade that cannot be
   worth it, by the competition's own stated rules.
2. **Never fabricate a claim, a source, a hash, or a label.** Every claim
   needs a real `source_url`, a real `retrieved_at`, and a real
   `content_sha256` computed from content you actually fetched. Every
   external-footprint observation needs real `identity_proof`. If you
   cannot get real evidence for something, the correct claim is
   `not_available` or `ambiguous`, not an invented one.
3. **Never scrape a restricted platform outside an approved
   `acquisition_mode`.** LinkedIn, Facebook, Instagram, X, TikTok,
   Glassdoor, Indeed: only `official_api`, `licensed_api`,
   `company_authorized_export`, or `permitted_public_page` acquisition
   modes are publishable (see `src/signal_scrape_core_footprint`
   validation logic you will build in Phase 2 — modelled exactly on the
   starter kit's `external_footprint.py::validate_observation`). An
   unofficial scraper for these platforms is not made acceptable by being
   open source, by working technically, or by "everyone doing it." The
   three quarantined scripts in `scripts/experimental_restricted/` stay
   quarantined. Do not un-quarantine them. Do not write new ones for the
   same platforms.
4. **$0 real cost, always.** Every connector you add must run with no paid
   API key. Free-tier-with-signup services (Google Places API, YouTube
   Data API) need a human to create the API key and billing-safe project —
   you cannot do that yourself. Treat those as **blocked, not skipped**:
   implement the connector code and wire it in behind a config flag /
   environment variable, leave it off by default, and log clearly in
   `Hackathon_context.md` and your PR/commit message that it is
   implemented-but-inactive pending a human-provided key. Never hardcode a
   key, never guess one, never fall back to scraping the same data
   unofficially "since we don't have the key."
5. **Stay inside the locked evaluator budget on every batch you run**: 100
   companies, 45 minutes, ≤2,000 outbound requests, ≤$10 declared
   third-party cost (which should be $0 given rule 4). Redirects and
   retries count as requests. If a change risks this budget, add an
   explicit per-company or per-run cap before deploying it, and verify the
   cap holds on a real run before considering the item done.
6. **Every terminal envelope claim uses exactly one of the six valid
   states**: `available`, `not_available`, `blocked`, `not_applicable`,
   `ambiguous`, `failed`. No other string, ever, in
   `scripts/export_terminal_envelopes.py` or anywhere claims are emitted.
7. **A failed refetch must never erase a previously known value.** This was
   a real bug, already fixed once in `refresh.py` (`_FAILED_REFETCH_STATUSES`
   handling). If you touch refresh logic again, re-verify this property
   holds with a real test before moving on (see §4).
8. **Precision before coverage, in that literal order, every time you have
   to choose.** This is not a vibe — it's the competition's documented
   optimization order and its tiebreak order. When two ideas compete for
   your next iteration and one raises coverage while the other tightens
   precision or fixes a validity bug, do the precision/validity one first.
9. **When genuinely uncertain whether an action crosses one of rules 1-4,
   don't proceed on a guess.** Write the uncertainty into
   `OPEN_QUESTIONS.md` (create it if it doesn't exist) with enough detail
   for a human to resolve in one read, skip that specific item, and move to
   the next backlog item. Do not block the whole loop on one uncertain
   item.

---

## 1. Where things stand at handoff

Read these in order before your first iteration:

- `Hackathon_context.md` — full rulebook, scoring, source policy, agent
  playbook, learning harness, current leaderboard snapshot (may be stale —
  re-fetch the challenge page yourself early in your first session and
  update it).
- `README.md` — the pipeline as it exists today, step by step.
- `run_full_pipeline.sh` — the single command that runs the whole thing.

**What already works, verified against real live 100-company runs** (do not
re-litigate these unless a real run shows a regression):
- Registry identity, roles, locations, financials: near-100% coverage,
  high confidence, stable across runs.
- Free domain-guess website discovery (`run_free_domain_discovery.py`):
  no API key, ~17-21% real verified-website coverage, matches independent
  real-world benchmarks.
- Identity gate correctly withholds unverified website matches as
  `ambiguous` rather than publishing them — this is load-bearing, protect
  it.
- `export_terminal_envelopes.py`: correctly maps internal statuses to the
  six required states; validated field-for-field against real data.
- `refresh.py`: failed refetches no longer erase last-known values
  (fixed and tested).
- `website.py::fetch_website`: has a bounded retry (2 attempts) on
  transient failures; confirmed it engages, confirmed some failures are
  genuine site downtime that retries can't fix (that's fine — real,
  honest `source_error`, not a bug to keep chasing).
- `group_structure` claim: official BRREG subsidiary data, previously
  fetched but silently dropped, now exported (free — no new requests).
- `public_activity` and `hiring_signal` claims: newly wired from
  `extract_company_site_activity.py`, `extract_company_site_news.py`,
  `extract_company_hiring_signal.py` — all identity-gated, zero new
  requests (derived from pages already fetched). `hiring_signal` coverage
  is currently very low (~1%) because career/job paths were only just
  added to the crawler's priority-path list — a fresh full run should show
  more once the crawler actually visits those pages at scale.

**What is unused and is your primary backlog** (see §3): `run_google_news_rss_connector.py`,
`run_fagfolkguiden_reviews_connector.py`, `run_youtube_search_connector.py`,
`normalize_google_maps_results.py`, `run_annual_report_workforce_connector.py`,
`run_scrapy_websites.py`, `run_sentiment_model.py`, `apply_verified_site_seeds.py`,
`build_verified_observations.py`, `score_company_completeness.py`,
`score_competition_v3.py`, `evaluate_external_footprint.py`.

**The most important structural finding from the starter kit that hasn't been
acted on yet**: `norway_company_agent/external_footprint.py` (in the
original starter kit, not yet ported into `signal_scrape_core`) defines a
real, strict schema for "external footprint" observations — platform,
signal_type, acquisition_mode, rights_status, identity_proof, etc. — with a
validator (`validate_observation`) that is the actual gate for whether an
external fact (a job posting, a review, a news mention, a place listing) is
publishable. This schema is **not currently ported into `signal_scrape_core`
at all.** Porting it faithfully and building every new external connector to
satisfy it from day one is the single highest-leverage piece of unfinished
work — see Phase 2 in §3.

---

## 2. Your operating loop

Repeat this loop. Each pass through it is "one iteration." Budget your own
time per iteration reasonably (a single well-tested change plus a real
verification run, not a huge multi-feature batch — smaller iterations are
easier to bisect if something regresses).

1. **Pick the single highest-leverage item** from the current
   `TODO.md` (see §3 for how to seed and maintain it). Highest-leverage
   means: closes a currently-zero required section > fixes a precision/
   validity bug > adds real coverage to an existing weak field > polish.
2. **Implement it.** Follow the existing code's patterns (identity gating,
   evidence dataclass shape, `$0`/no-restricted-platform constraints from
   §0). If it's a new external-footprint connector, it MUST emit
   observations conforming to the ported `external_footprint.py` schema
   (see Phase 2, §3) from the start — do not build a connector now and
   retrofit the schema later.
3. **Verify offline first**:
   ```bash
   python3 -m py_compile $(git diff --name-only -- '*.py')
   uv run --with pytest pytest -q
   python3 first_run.py
   ```
   All must pass before you proceed. If tests fail, fix before continuing
   — never commit on a red test suite.
4. **Run a real live batch.** You have real internet access; use it. Run
   the full pipeline on a genuine 100-company sample (reuse the same
   `companies.jsonl` across iterations where possible so results are
   comparable; regenerate from the universe file only when you want to
   check generalization to unseen companies, matching how Builderr's
   actual daily test works):
   ```bash
   uv run python select_entry_batch.py --universe data/signalpost-company-universe-2025.jsonl.gz --count 100 --output out/iter-companies.jsonl
   ./run_full_pipeline.sh out/iter-companies.jsonl brreg-enheter.csv 100 iter-$(date +%Y%m%d-%H%M%S)
   ```
5. **Score it with the two proxy scorers**, treating their numbers as
   directional signal, not ground truth (they say so themselves —
   `"Optimization proxy. Final score requires the organiser's frozen
   hidden companies and independent labels."`):
   ```bash
   uv run python scripts/score_company_completeness.py --profiles out/profiles-with-discovery.jsonl --results out/<external-observations>.jsonl --output out/completeness-report.json
   ```
   For `score_competition_v3.py` and `evaluate_external_footprint.py`: they
   require a `--labels` file with hand-audited ground truth you do not
   have. Do not fabricate labels to make these run "clean." Either skip
   the audit-gated report and rely on the non-audit-dependent parts
   (`batch_valid`, `refresh_valid`, `connector_policy`,
   `official_identity_complete` — all computable from your own pipeline
   output honestly), or run them with an empty/zero-row labels file and
   read only the coverage/gate fields that don't depend on labels, noting
   in your commit message exactly which parts you could and couldn't
   verify this way.
6. **Diff against the previous iteration's real run.** Same method used
   throughout this project's history: compare per-company field-level
   classifications between this run and the last one you committed, not
   just aggregate percentages — aggregate deltas hide which specific
   companies moved and why, and that's where real bugs (like the retry
   fix, the schema-mismatch bug, the refresh false-change bug) were
   actually found. Concretely:
   ```bash
   python3 -c "
   import json
   def load(path):
       return {json.loads(l)['organisation_number']: json.loads(l) for l in open(path)}
   old = load('out/<previous-iteration>/terminal-envelopes.jsonl')
   new = load('out/terminal-envelopes.jsonl')
   for org, new_env in new.items():
       old_env = old.get(org)
       if not old_env: continue
       old_claims = {c['field']: c['availability'] for c in old_env['claims']}
       new_claims = {c['field']: c['availability'] for c in new_env['claims']}
       for field in new_claims:
           if old_claims.get(field) != new_claims.get(field):
               print(org, field, old_claims.get(field), '->', new_claims.get(field))
   "
   ```
   If anything moved in a direction you can't explain, investigate before
   committing — do not commit an unexplained regression.
7. **Update `TODO.md`**: mark the item done with a one-line real result
   (e.g. "hiring_signal: 1/100 -> 9/100 after career-path crawl fix,
   verified real run 2026-09-2x"), and add any new backlog items you
   discovered while doing this one.
8. **Update `Hackathon_context.md`** §14 ("current compliance status") with
   what changed, honestly — including anything that *didn't* work or that
   you deliberately chose not to do and why (§0 rule 9 territory).
9. **Commit and tag.** See §5.
10. **Check the stopping condition (§7).** If not met, go back to step 1.

---

## 3. Prioritized backlog (seed `TODO.md` with this, then keep it current)

Copy this into `TODO.md` at the start of your first iteration, formatted as
checkboxes, and maintain it from there — this section of this file does not
get edited again; `TODO.md` is the living document.

### Phase 1 — Close remaining honest coverage gaps in what already exists
- [ ] Increase `hiring_signal` coverage: confirm the career/job priority-path
  crawl fix from the previous session is actually firing at scale on a
  fresh 100-company run (last check showed only 1/100 — verify whether
  that's realistic (most Norwegian SMEs genuinely lack a dedicated careers
  page) or whether more crawl depth / more path variants would find more
  real ones, without inventing signal that isn't there).
- [ ] `run_annual_report_workforce_connector.py`: wire in. This targets the
  weak `employees` field (currently ~17%) via PDF annual-report parsing
  (pypdf first, escalate only if needed). Zero new external cost beyond
  fetching PDFs already linked from filings you have access to.
- [ ] Consider Playwright escalation (`scrapy-playwright`, already an
  optional dependency in `pyproject.toml`) for JS-shell career pages —
  but only as a bounded escalation after a deterministic check confirms a
  JS shell, per the agent playbook's own rule, and only if it doesn't
  blow the 45-minute/2,000-request budget at 100-company scale. Measure
  before and after on a real run.

### Phase 2 — Port the real external-footprint schema, then build connectors against it (highest leverage remaining work)
- [ ] Port `norway_company_agent/external_footprint.py`'s `PLATFORMS`,
  `SIGNAL_TYPES`, `PUBLISHABLE_ACQUISITION_MODES`, `validate_observation`,
  `publishable_observation`, and `aggregate_footprint` into
  `src/signal_scrape_core/external_footprint.py`, faithfully — this is the
  real gate every new external connector below must satisfy to be
  publishable, not just runnable.
- [ ] `run_google_news_rss_connector.py`: wire in as a genuine
  `acquisition_mode="permitted_public_page"`, `platform="news"`,
  `signal_type="public_mention"` source. Free, no key, already exists.
- [ ] NAV's public job vacancy feed (build a new connector if one doesn't
  exist yet — check `run_fagfolkguiden_reviews_connector.py` and the
  existing scripts list first for anything already pointed at NAV):
  `platform="job_board"`, `signal_type="job_posting"`,
  `acquisition_mode="official_api"`. This is Norway's own government job
  board — free, official, and directly closes the "jobs" part of the
  required "hiring and dated public activity" section with real listings
  (not just "a careers page exists," which is all the current
  `hiring_signal` claim can honestly say).
- [ ] OpenStreetMap / Nominatim: free, no key, `official_api`. Useful for
  cross-verifying `operating_locations` addresses independently of the
  registry — a second independent source for the same fact raises
  confidence without raising risk.
- [ ] Wikidata / Wikipedia: free, no key, `official_api`. `platform`
  can map to `wikidata`/`wikipedia`, `signal_type="company_profile"`.
  Only publish when the Wikidata/Wikipedia entity's official registry
  identifier (Norwegian organisation number, if present as a Wikidata
  property) matches exactly — do not match on name similarity alone.
- [ ] `run_fagfolkguiden_reviews_connector.py`: before wiring in, verify
  its acquisition method is genuinely `permitted_public_page` (check
  robots.txt and terms, same standard the rest of the crawler already
  holds itself to) and that review content is attributed to the exact
  company, not a category/directory page. If it can't clear that bar
  cleanly, leave it in `experimental_restricted/` instead and say so in
  `TODO.md`.
- [ ] Google Places API, YouTube Data API: implement the connector code
  and wire it in behind an environment variable
  (`SIGNAL_SCRAPE_GOOGLE_PLACES_API_KEY`, `SIGNAL_SCRAPE_YOUTUBE_API_KEY`),
  default off. Do not attempt to obtain a key yourself. Document clearly
  in `TODO.md` and `Hackathon_context.md` that these are implemented but
  inactive pending a human-provided key (§0 rule 4).
- [ ] Sentiment (`run_sentiment_model.py`): only activate once at least 10
  independently-sourced observations across 2+ distinct hosts exist for a
  given company (`aggregate_footprint`'s own `sentiment_ready` gate) —
  do not report a sentiment score below that threshold, it's explicitly
  designed to abstain until then.
- [ ] Update `export_terminal_envelopes.py` to read the new
  `external_footprint` observations and emit them as additional claims
  (e.g. `job_postings`, `place_listing`, `news_mentions`,
  `independent_sentiment`) using the same six-state vocabulary, with the
  same care taken for `official_website`'s available-vs-ambiguous
  distinction — an external observation that fetched fine but failed
  `validate_observation` should not silently vanish; decide honestly
  whether that maps to `ambiguous` or `not_available` for that claim and
  say why in a code comment.

### Phase 3 — Precision, robustness, and self-audit tooling
- [ ] Build a lightweight internal audit helper: given a sample of N
  published claims (start with N=20-30, not the full 100 the real
  `evaluate_external_footprint.py` wants), print each claim plus its
  evidence source URL and span in a format a human can quickly eyeball
  and label — this doesn't solve the "needs human judgment" boundary
  (§0), but it makes the human's job fast when they do sit down to do it,
  and gives you (the agent) a cheap self-check: if your own eyeballing of
  a small sample turns up an obvious wrong-entity match, that's a signal
  to tighten the identity gate before doing anything else.
- [ ] Re-run the retry/backoff logic under load: confirm on a real 100-
  company run that request count stays comfortably under 2,000 and
  wall-clock stays comfortably under 45 minutes even with every new
  connector active. If not, prioritize trimming before adding more.
- [ ] Confirm `operations.requests` / `operations.runtime_ms` in the
  terminal envelope are populated from real per-company measurements, not
  placeholders, once new connectors are contributing to per-company cost
  — this was flagged once before as worth re-checking and was resolved,
  but every new connector is a new place this could silently regress.

### Phase 4 — Polish (do last, only if Phase 1-3 are genuinely exhausted)
- [ ] Synthesis quality pass on `generate_synthesis.py` now that
  `public_activity`, `hiring_signal`, and (once built) the external
  observations exist — fold real hiring/activity language into the
  generated summary honestly (only state what's actually available).
- [ ] Showcase UX (`build_prototype.py`): surface the new external
  footprint data in the browsable site if it doesn't already render
  gracefully with the new claim fields.

---

## 4. Verification protocol (run this exact sequence before every commit)

```bash
# 1. Every changed file compiles
python3 -m py_compile $(git diff --name-only --diff-filter=ACM -- '*.py')

# 2. Full offline suite
uv run --with pytest pytest -q
# Expect: all tests pass, count should only ever grow as you add coverage
# for new connectors, never shrink.

# 3. Fixture sanity check
python3 first_run.py
# Expect: "Signalpost starter: SUCCESS"

# 4. Every claim in the fresh export uses a valid state
python3 -c "
import json
valid = {'available','not_available','blocked','not_applicable','ambiguous','failed'}
n = 0
for line in open('out/terminal-envelopes.jsonl'):
    env = json.loads(line)
    for c in env['claims']:
        assert c['availability'] in valid, f'INVALID STATE: {c}'
        n += 1
print(f'PASS: {n} claims, all valid')
"

# 5. Zero-fabrication spot check: every 'available' claim has real evidence
python3 -c "
import json
bad = 0
for line in open('out/terminal-envelopes.jsonl'):
    env = json.loads(line)
    ev_ids = {e['id'] for e in env['evidence']}
    for c in env['claims']:
        if c['availability'] == 'available' and c['evidence_ids']:
            for eid in c['evidence_ids']:
                if eid not in ev_ids:
                    print('DANGLING EVIDENCE REF:', env['organisation_number'], c['field'], eid)
                    bad += 1
print('PASS: no dangling evidence refs' if bad == 0 else f'FAIL: {bad} dangling refs')
"

# 6. Refresh integrity: a failed refetch must never erase a known value
uv run python scripts/diff_live_runs.py --previous out/<prior>/profiles-with-discovery.jsonl --current out/profiles-with-discovery.jsonl --output out/refresh-check.json
python3 -c "
import json
d = json.load(open('out/refresh-check.json'))
for e in d['events']:
    if e['status'] == 'refresh_check_failed':
        assert e['old_value'] == e['new_value'], f'FAIL: refresh erased a value: {e}'
print('PASS: no failed refetch erased a known value')
print('idempotent_rerun:', d.get('idempotent_rerun'))
"

# 7. Budget check on the real run's report
python3 -c "
import json
d = json.load(open('out/run-report.json'))
requests = d.get('operations', {}).get('requests') or d.get('requests', 0)
print('requests used:', requests, '/ 2000 budget')
assert requests < 2000, 'OVER BUDGET'
"
```

Only commit if every one of these passes. If step 6 or 5 ever fails, that is
a precision/integrity bug — stop the loop, fix it as the very next
iteration regardless of what else was planned, per §0 rule 8.

---

## 5. Git and versioning protocol

- One commit per completed backlog item (step 9 of the loop), not one giant
  commit per session. Small, bisectable commits.
- Commit message format:
  ```
  [signal_scrape] <short summary>

  What: <one or two sentences>
  Why: <which backlog item / which real problem this addresses>
  Verified: <one line — e.g. "104->108 tests pass, real 100-co run: hiring_signal 1->9, requests 247/2000, no regressions in field-diff vs previous run">
  ```
- Tag every commit that completes a full loop iteration (after §2 step 9)
  as `v6`, `v7`, `v8`, ... continuing the existing sequence from this
  project's history (last known tag context: `v5`). Use
  `git tag -a v6 -m "<one-line summary of what changed this iteration>"`
  then push tags: `git push origin main --tags`.
- Push after every commit, not batched at the end — the repo is the source
  of truth now, there is no more zip-file handoff step.
- Never force-push. Never rewrite history that's already pushed.

---

## 6. Updating `Hackathon_context.md`

This file is the shared rulebook for any agent (human or AI) that picks
this project up next. Keep §14 ("current compliance status") current every
iteration: what's implemented, what's verified against real data, what's
blocked pending a human (API keys, the audit-label gap), and what's
deliberately not done and why (restricted platforms, unverifiable claims).

Additionally, **re-fetch the three source documents yourself** at least
once per session (`https://builderr.ai/challenges/signalpost`,
`https://builderr.ai/docs/signalpost-evaluation-harness.md`, and the other
starter-brief docs linked in §15 of that file) — rules, the leaderboard, and
scoring details can change, and the whole point of this file existing is
that a human isn't re-checking this for you each time. If anything material
changed, update `Hackathon_context.md` accordingly and note the change date.

---

## 7. Stopping condition — what "ceiling" means here

Stop the autonomous loop (and write a clear summary in `TODO.md` and
`Hackathon_context.md` for the human) when **any** of these is true:

1. **The entire Phase 1-3 backlog in §3 is done**, verified against real
   runs, with nothing left except Phase 4 polish or items blocked on a
   human (API keys, the hand-labeled audit).
2. **Three consecutive iterations produce no measurable real-data
   improvement** in either coverage (field-availability percentages on a
   fresh real run) or a fixed bug, after genuinely trying non-trivial
   ideas each time — this means you've hit diminishing returns with the
   free/permitted/$0 tools available, which is a legitimate, honest
   ceiling, not a failure.
3. **You hit a wall that requires violating §0** to progress further (e.g.,
   the only way to gain more coverage is to scrape a restricted platform,
   or fabricate a signal, or spend money). Stop there — do not cross it.
   Log exactly what the wall was.
4. **A hard safety cap of 25 iterations** is reached, regardless of the
   above, as a backstop against an unbounded loop burning time/tokens on
   marginal gains. If you hit this before 1 or 2, that itself is useful
   information — say so plainly rather than padding remaining iterations
   with busywork.

When you stop, produce one final summary commit whose message states: what
the honest current state is, what's blocked and on what, and — being
explicit about the limits of your own visibility — that no one, including
you, has ever seen Builderr's real internal score, so all coverage numbers
in this project are proxy signals verified against real live data, not a
confirmed final score.

---

## 8. Things you cannot do autonomously — surface these, don't route around them

- **The ≥100-observation hand-labeled audit** that `evaluate_external_footprint.py`
  and `score_competition_v3.py` require for their qualification-gate
  computation. This needs a human's judgment call on "is this really the
  exact company" and "is this metric correct" per sample. Do not fabricate
  these labels to make the script run clean.
- **Google Places / YouTube API keys** (§0 rule 4, §3 Phase 2).
- **The actual Builderr submission** (`submit@builderr.ai`) — that's the
  human's call on timing, not something to trigger automatically even if
  you believe the ceiling has been reached.
- **Anything §0 rule 9 sent to `OPEN_QUESTIONS.md`.**

---

## 9. Quick reference: key files

| File | Role |
|---|---|
| `Hackathon_context.md` | Full rulebook — read first, keep current |
| `README.md` | Current pipeline, step by step |
| `run_full_pipeline.sh` | Single-command full run |
| `TODO.md` | Living backlog — seed from §3, maintain from there |
| `OPEN_QUESTIONS.md` | Things you deliberately did not resolve alone |
| `scripts/export_terminal_envelopes.py` | Internal schema → required output contract |
| `src/signal_scrape_core/website.py` | Fetch/crawl/identity-gate core |
| `src/signal_scrape_core/refresh.py` | Refresh diff engine (failed-refetch-safe) |
| `src/signal_scrape_core/external_footprint.py` | To be created in Phase 2 — the real publishability gate for external connectors |
| `scripts/experimental_restricted/` | Quarantined — never reactivate |
