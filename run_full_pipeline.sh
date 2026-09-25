#!/usr/bin/env bash
# signal_scrape — one-command pipeline.
#
# Usage:
#   ./run_full_pipeline.sh <organisations.jsonl> <bulk_csv> <expected_count> <run_id>
#
# Example (full 1,000-company entry):
#   ./run_full_pipeline.sh out/entry-companies.jsonl brreg-enheter.csv 1000 local-001
#
# Example (10-company smoke test):
#   ./run_full_pipeline.sh out/smoke-companies.jsonl brreg-enheter.csv 10 smoke-001
set -euo pipefail

ORGANISATIONS="${1:?Usage: $0 <organisations.jsonl> <bulk_csv> <expected_count> <run_id>}"
BULK="${2:?bulk CSV path required}"
EXPECTED_COUNT="${3:?expected count required}"
RUN_ID="${4:?run id required}"

OUT_DIR="${5:-out}"
mkdir -p "$OUT_DIR"

echo "== [1/5] Registry + registry-website batch =="
uv run python scripts/run_competition_batch.py \
  --organisations "$ORGANISATIONS" \
  --bulk "$BULK" \
  --profiles-output "$OUT_DIR/profiles.jsonl" \
  --output "$OUT_DIR/envelopes.jsonl" \
  --report "$OUT_DIR/run-report.json" \
  --run-id "$RUN_ID" \
  --expected-count "$EXPECTED_COUNT"

echo "== [2/5] Free ($0, no API key) website discovery for the rest =="
uv run python scripts/run_free_domain_discovery.py \
  --input "$OUT_DIR/profiles.jsonl" \
  --output "$OUT_DIR/profiles-with-discovery.jsonl" \
  --report "$OUT_DIR/discovery-report.json" \
  --promote-verified

echo "== [3/6] External footprint & signal connectors =="
uv run python scripts/extract_company_site_activity.py \
  --profiles "$OUT_DIR/profiles-with-discovery.jsonl" \
  --output "$OUT_DIR/activity.jsonl" \
  --report "$OUT_DIR/activity-report.json"
uv run python scripts/extract_company_site_news.py \
  --profiles "$OUT_DIR/profiles-with-discovery.jsonl" \
  --output "$OUT_DIR/news.jsonl" \
  --report "$OUT_DIR/news-report.json"
uv run python scripts/extract_company_hiring_signal.py \
  --profiles "$OUT_DIR/profiles-with-discovery.jsonl" \
  --output "$OUT_DIR/hiring.jsonl" \
  --report "$OUT_DIR/hiring-report.json"
uv run python scripts/run_wikidata_connector.py \
  --profiles "$OUT_DIR/profiles-with-discovery.jsonl" \
  --output "$OUT_DIR/wikidata.jsonl" \
  --report "$OUT_DIR/wikidata-report.json"
uv run python scripts/run_nominatim_connector.py \
  --profiles "$OUT_DIR/profiles-with-discovery.jsonl" \
  --output "$OUT_DIR/nominatim.jsonl" \
  --report "$OUT_DIR/nominatim-report.json"
uv run python scripts/run_nav_arbeidsplassen_connector.py \
  --profiles "$OUT_DIR/profiles-with-discovery.jsonl" \
  --output "$OUT_DIR/nav.jsonl" \
  --report "$OUT_DIR/nav-report.json"

echo "== [4/6] Deterministic, $0 decision-useful synthesis =="
uv run python scripts/generate_synthesis.py \
  --input "$OUT_DIR/profiles-with-discovery.jsonl" \
  --output "$OUT_DIR/synthesis.jsonl" \
  --activity "$OUT_DIR/activity.jsonl" \
  --news "$OUT_DIR/news.jsonl" \
  --hiring "$OUT_DIR/hiring.jsonl" \
  --wikidata "$OUT_DIR/wikidata.jsonl" \
  --nominatim "$OUT_DIR/nominatim.jsonl" \
  --nav "$OUT_DIR/nav.jsonl"

echo "== [5/6] Browsable showcase site =="
uv run python scripts/build_prototype.py \
  --input "$OUT_DIR/profiles-with-discovery.jsonl" \
  --external-observations \
    "$OUT_DIR/activity.jsonl" \
    "$OUT_DIR/news.jsonl" \
    "$OUT_DIR/hiring.jsonl" \
    "$OUT_DIR/wikidata.jsonl" \
    "$OUT_DIR/nominatim.jsonl" \
    "$OUT_DIR/nav.jsonl" \
  --output "$OUT_DIR/showcase.html" || echo "(showcase build skipped/failed — check scripts/build_prototype.py --help)"

echo "== [6/6] Export contract-compliant terminal envelopes =="
uv run python scripts/export_terminal_envelopes.py \
  --input "$OUT_DIR/profiles-with-discovery.jsonl" \
  --output "$OUT_DIR/terminal-envelopes.jsonl" \
  --run-id "$RUN_ID" \
  --activity "$OUT_DIR/activity.jsonl" \
  --news "$OUT_DIR/news.jsonl" \
  --hiring "$OUT_DIR/hiring.jsonl" \
  --wikidata "$OUT_DIR/wikidata.jsonl" \
  --nominatim "$OUT_DIR/nominatim.jsonl" \
  --nav "$OUT_DIR/nav.jsonl"

echo
echo "Done. Key outputs:"
echo "  $OUT_DIR/terminal-envelopes.jsonl   (submission artifact)"
echo "  $OUT_DIR/envelopes.jsonl            (internal envelope shape)"
echo "  $OUT_DIR/profiles-with-discovery.jsonl"
echo "  $OUT_DIR/synthesis.jsonl            (decision-useful summaries)"
echo "  $OUT_DIR/showcase.html              (browsable UI)"
echo "  $OUT_DIR/run-report.json, $OUT_DIR/discovery-report.json  (cost/request accounting — declare these)"
