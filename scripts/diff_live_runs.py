#!/usr/bin/env python3
"""Diff two live pipeline outputs (e.g. today's run vs last week's) using the
same tracked-field diff engine as run_refresh_replay.py, but without needing
to hand-build a snapshot-replay manifest. Both inputs must be profile/envelope
JSONL files covering the exact same set of organisation numbers.

Usage:
    uv run python scripts/diff_live_runs.py \
        --previous out/profiles-with-discovery-run1.jsonl \
        --current out/profiles-with-discovery-run2.jsonl \
        --output out/live-refresh-report.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from signal_scrape_core.refresh import diff_datasets  # noqa: E402


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Diff two live pipeline runs and report real changes, with no duplicates or false changes.")
    parser.add_argument("--previous", required=True)
    parser.add_argument("--current", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    previous = read_jsonl(Path(args.previous))
    current = read_jsonl(Path(args.current))
    previous_orgs = {row["organisation_number"] for row in previous}
    current_orgs = {row["organisation_number"] for row in current}
    if previous_orgs != current_orgs:
        only_previous = sorted(previous_orgs - current_orgs)
        only_current = sorted(current_orgs - previous_orgs)
        raise SystemExit(
            "Refresh datasets must cover identical organisation numbers. "
            f"Only in --previous: {only_previous[:5]}{'...' if len(only_previous) > 5 else ''}; "
            f"only in --current: {only_current[:5]}{'...' if len(only_current) > 5 else ''}"
        )

    changes = diff_datasets(previous, current)
    # idempotency check: diffing current against itself must yield nothing
    idempotent = diff_datasets(current, current) == []

    report = {
        "previous_file": str(args.previous),
        "current_file": str(args.current),
        "profiles_compared": len(current),
        "changes_found": len(changes),
        "idempotent_rerun": idempotent,
        "events": changes,
    }
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "events"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
