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

OUT_DIR="out"
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

echo "== [3/5] Deterministic, $0 decision-useful synthesis =="
uv run python scripts/generate_synthesis.py \
  --input "$OUT_DIR/profiles-with-discovery.jsonl" \
  --output "$OUT_DIR/synthesis.jsonl"

echo "== [4/5] Browsable showcase site =="
uv run python scripts/build_prototype.py \
  --input "$OUT_DIR/envelopes.jsonl" \
  --output "$OUT_DIR/showcase.html" || echo "(showcase build skipped/failed — check scripts/build_prototype.py --help)"

# Keep this translation step separate from the internal envelope output: the
# terminal-envelope file is the contract-facing artifact used for submission.
echo "== [5/5] Export contract-compliant terminal envelopes =="
uv run python scripts/export_terminal_envelopes.py \
  --input "$OUT_DIR/profiles-with-discovery.jsonl" \
  --output "$OUT_DIR/terminal-envelopes.jsonl" \
  --run-id "$RUN_ID"

echo
echo "Done. Key outputs:"
echo "  $OUT_DIR/terminal-envelopes.jsonl   (submission artifact)"
echo "  $OUT_DIR/envelopes.jsonl            (internal envelope shape)"
echo "  $OUT_DIR/profiles-with-discovery.jsonl"
echo "  $OUT_DIR/synthesis.jsonl            (decision-useful summaries)"
echo "  $OUT_DIR/showcase.html              (browsable UI)"
echo "  $OUT_DIR/run-report.json, $OUT_DIR/discovery-report.json  (cost/request accounting — declare these)"
