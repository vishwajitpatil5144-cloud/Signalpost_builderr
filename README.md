# signal_scrape

A $0, fully open-source pipeline for the Builderr Signalpost challenge: given a
Norwegian organisation number, produce a source-cited company profile, mark
what's genuinely unknown, and detect real changes on rerun.

This is the official starter kit, renamed and extended:

- Internal package renamed `norway_company_agent` → `signal_scrape_core`.
- **New:** `scripts/run_free_domain_discovery.py` — a $0, no-API-key website
  discovery connector (deterministic domain guessing + independent fetch
  verification) that replaces the paid `run_brave_discovery.py` path.
- **New:** `scripts/generate_synthesis.py` — a deterministic, LLM-free
  decision-useful-summary generator (no model call, so it cannot hallucinate
  a fact or an identity match).
- **Quarantined:** the three LinkedIn-touching scripts were moved to
  `scripts/experimental_restricted/` and are excluded from every command
  below. See that folder's README for why.
- The competition universe file you uploaded is already verified and staged
  at `data/signalpost-company-universe-2025.jsonl.gz` (SHA-256 checked against
  Builderr's published hash — see step 1).
- The original starter-kit README is kept at `README.original.md` for
  reference.

Every dependency used below is free and open-source (Scrapy, BeautifulSoup,
Trafilatura, extruct, Pydantic, tldextract, pypdf, pytest — no paid API key
required anywhere in this pipeline).

---

## Step 0 — Install `uv` and sync dependencies

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # skip if you already have uv
cd signal_scrape
uv sync
```

## Step 1 — Verify the universe file (already done for you, but confirm it)

```bash
sha256sum data/signalpost-company-universe-2025.jsonl.gz
# must print: 1c89710e5b01f8617e86d09fbdff4a52f2f8dbbba297e74f7164b5984f5a0384

zcat data/signalpost-company-universe-2025.jsonl.gz | sha256sum
# must print: b82d6a3e7231d1759a958c282bc4366b80ec2fab8095053d8ed7fa9cd01bc838

zcat data/signalpost-company-universe-2025.jsonl.gz | wc -l
# must print: 411160
```
I already ran this check on the file you uploaded — both hashes match and the
row count is exactly 411,160, so it's the genuine, unmodified competition
universe.

## Step 2 — Sanity check with saved fixtures (no network, no API key)

```bash
python3 first_run.py
```
Expected: `Signalpost starter: SUCCESS` — it replays a saved refresh scenario
and confirms the diff engine finds exactly the expected changes with no false
positives. This proves the refresh/idempotency logic works before you spend
any real requests.

Then run the full offline test suite:
```bash
uv run --with pytest pytest -q
```
Expected: `104 passed, 5 subtests passed`.

## Step 3 — Download the one thing not provided: the BRREG bulk registry CSV

This is Builderr's official identity anchor. It's free and requires no key,
but it's ~200MB+ and refreshes, so it isn't bundled — pull it fresh:
```bash
curl -L 'https://data.brreg.no/enhetsregisteret/api/enheter/lastned/csv' -o brreg-enheter.csv
```

## Step 4 — Select your entry batch from the real universe

```bash
uv run python select_entry_batch.py \
  --universe data/signalpost-company-universe-2025.jsonl.gz \
  --count 1000 \
  --output out/entry-companies.jsonl

head -n 10 out/entry-companies.jsonl > out/smoke-companies.jsonl
```
I already generated both of these files for you in this delivered project
(`out/entry-companies.jsonl`, `out/smoke-companies.jsonl`) using seed
`20260823`, so this step is reproducible and optional to rerun.

## Step 5 — Smoke test: 10 live companies, registry + registry-website only

```bash
uv run python scripts/run_competition_batch.py \
  --organisations out/smoke-companies.jsonl \
  --bulk brreg-enheter.csv \
  --profiles-output out/smoke-profiles.jsonl \
  --output out/smoke-envelopes.jsonl \
  --report out/smoke-report.json \
  --run-id smoke-001 \
  --expected-count 10
```
Inspect `out/smoke-report.json` for request count, latency, and any errors
before scaling up.

## Step 6 — Free website discovery (the $0 connector) on the smoke batch

Only companies with no registry-listed website are attempted; every
candidate still has to pass the same exact-entity identity gate the registry
path uses, so nothing gets published on a guess alone.

```bash
uv run python scripts/run_free_domain_discovery.py \
  --input out/smoke-profiles.jsonl \
  --output out/smoke-profiles-with-discovery.jsonl \
  --report out/smoke-discovery-report.json \
  --promote-verified
```

## Step 7 — Deterministic synthesis (decision-useful summary, $0, no LLM)

```bash
uv run python scripts/generate_synthesis.py \
  --input out/smoke-profiles-with-discovery.jsonl \
  --output out/smoke-synthesis.jsonl
```
Open `out/smoke-synthesis.jsonl` — one readable paragraph per company, built
only from fields that already passed verification, with an explicit
"not established in this run" line for anything missing.

## Step 8 — If the smoke batch looks right, run the full 1,000-company entry

```bash
uv run python scripts/run_competition_batch.py \
  --organisations out/entry-companies.jsonl \
  --bulk brreg-enheter.csv \
  --profiles-output out/profiles.jsonl \
  --output out/envelopes.jsonl \
  --report out/run-report.json \
  --run-id local-001 \
  --expected-count 1000

uv run python scripts/run_free_domain_discovery.py \
  --input out/profiles.jsonl \
  --output out/profiles-with-discovery.jsonl \
  --report out/discovery-report.json \
  --promote-verified

uv run python scripts/generate_synthesis.py \
  --input out/profiles-with-discovery.jsonl \
  --output out/synthesis.jsonl
```

## Step 9 — Refresh check (proves rerun correctness — 20 of 100 points)

Two ways to check this:

**A. Fixture replay** (what Step 2 already ran) uses `run_refresh_replay.py`
with a hand-built old/new snapshot manifest — good for regression-testing your
diff logic against known expected changes:
```bash
uv run python scripts/run_refresh_replay.py \
  --manifest tests/fixtures/refresh-snapshots.json \
  --output out/refresh-demo.json
```

**B. Live rerun diff** (new script, `diff_live_runs.py`) — re-run Step 8 later
(a day, a week) into new output files, then diff the two real runs directly:
```bash
uv run python scripts/diff_live_runs.py \
  --previous out/profiles-with-discovery.jsonl \
  --current out/profiles-with-discovery-rerun.jsonl \
  --output out/live-refresh-report.json
```
Check `out/live-refresh-report.json` for real changes with `idempotent_rerun:
true` (diffing the current run against itself must yield zero changes).

## Step 10 — Build the browsable showcase site (UX points, 5 of 100)

```bash
uv run python scripts/build_prototype.py \
  --input out/envelopes.jsonl \
  --output out/showcase.html
```
Open `out/showcase.html` locally — searchable index, per-company profile
view, and the evidence-bounded research-agent widget, all reading directly
from your generated JSONL (no server, no API key).

## Step 11 — Export the submission envelopes

The pipeline keeps its internal `out/envelopes.jsonl` shape separate from the
submission contract. Export the contract-facing file after discovery and before
submission:

```bash
uv run python scripts/export_terminal_envelopes.py \
  --input out/profiles-with-discovery.jsonl \
  --output out/terminal-envelopes.jsonl \
  --run-id local-001
```

For a refresh rerun, add `--previous` with the prior profile JSONL. The
exporter then computes the tracked-field diff and carries the resulting
evidence-backed events into each envelope's `changes[]` array:

```bash
uv run python scripts/export_terminal_envelopes.py \
  --input out/profiles-with-discovery-rerun.jsonl \
  --previous out/profiles-with-discovery.jsonl \
  --output out/terminal-envelopes-rerun.jsonl \
  --run-id rerun-001
```

The exporter translates internal statuses into the six contract states and
marks fetched but identity-unverified websites as `ambiguous`, not
`available`. This distinction prevents a plausible wrong-company match from
being published as a confirmed company website.

On Windows, use `run_full_pipeline.ps1` for the same five stages. The existing
`.sh` launcher remains available for Git Bash and other POSIX-compatible shells.

## Step 12 — Run the local competition checks

```bash
uv run --with pytest pytest -q
npm run check:signalpost 2>/dev/null || true
```
(The `npm run` checks are Builderr's own harness scripts if present in your
environment; they're optional locally but worth running before you submit.)

## Step 13 — Submit

Email `submit@builderr.ai` with:
- your repository URL and exact commit hash
- `out/terminal-envelopes.jsonl` profile count (must be ≥1,000) and `out/entry-companies.jsonl` as the manifest
- one run command (Step 8 plus Step 11 as a single script — see `run_full_pipeline.ps1` or `run_full_pipeline.sh`)
- declared models/APIs: **none** — registry APIs, direct HTTP fetches, and local deterministic code only
- expected cost per 100-company batch: **$0**

---

## What's intentionally NOT in the default pipeline

- **No LinkedIn/Meta/Indeed scraping** — quarantined in
  `scripts/experimental_restricted/`, per the source policy's restricted-
  platform rule.
- **No paid search API** — `run_brave_discovery.py` is left in the repo for
  reference but `run_free_domain_discovery.py` is what the pipeline above
  actually uses.
- **No LLM calls** — synthesis is templated and deterministic, which also
  means it can never be the thing that costs you accuracy points.

## Files this project adds on top of the original starter kit

| File | Purpose |
|---|---|
| `scripts/run_free_domain_discovery.py` | $0 website discovery, no API key |
| `scripts/generate_synthesis.py` | $0 deterministic decision-useful summary |
| `scripts/experimental_restricted/` | quarantined LinkedIn scripts, excluded by default |
| `data/signalpost-company-universe-2025.jsonl.gz` | your uploaded, hash-verified universe file |
| `out/entry-companies.jsonl`, `out/smoke-companies.jsonl` | pre-generated entry batch and smoke subset |
