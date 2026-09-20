#!/usr/bin/env python3
"""Lightweight internal audit helper for published claims.

Samples N company envelopes from terminal-envelopes.jsonl and prints each claim
alongside its exact evidence source URL, source class, and evidence span so a
human reviewer can quickly verify accuracy against the source of truth.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit published claims against their underlying evidence spans.")
    parser.add_argument("--input", required=True, help="terminal-envelopes.jsonl")
    parser.add_argument("--sample", type=int, default=20, help="Number of companies to sample (default: 20)")
    parser.add_argument("--field", help="Optional specific field to filter audit on (e.g. place_summary, company_profile)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible sampling")
    args = parser.parse_args()

    envelopes = [json.loads(line) for line in Path(args.input).read_text(encoding="utf-8").splitlines() if line.strip()]
    rng = random.Random(args.seed)
    sampled = rng.sample(envelopes, min(args.sample, len(envelopes)))

    print("=" * 80)
    print(f"SIGNAL_SCRAPE PUBLISHED CLAIMS AUDIT — {len(sampled)} Companies Sampled")
    print("=" * 80)

    total_audited = 0
    available_audited = 0

    for idx, env in enumerate(sampled, 1):
        org = env.get("organisation_number")
        claims = env.get("claims") or []
        evidence_map = {e["id"]: e for e in env.get("evidence") or []}

        legal_name_claim = next((c for c in claims if c["field"] == "legal_name"), None)
        company_name = legal_name_claim["value"] if legal_name_claim else "Unknown"

        print(f"\n[{idx}/{len(sampled)}] Company: {company_name} (Org: {org})")
        print("-" * 80)

        for c in claims:
            field = c["field"]
            if args.field and field != args.field:
                continue

            avail = c.get("availability")
            val = c.get("value")
            conf = c.get("confidence")
            note = c.get("note")
            ev_ids = c.get("evidence_ids") or []

            total_audited += 1
            if avail == "available":
                available_audited += 1

            status_indicator = f"[{avail.upper():13s}]"
            print(f"  {status_indicator} {field:22s} (conf: {conf:.2f})")
            if val is not None:
                val_str = str(val) if len(str(val)) < 120 else f"{str(val)[:115]}..."
                print(f"    Value: {val_str}")
            if note:
                print(f"    Note : {note}")

            for ev_id in ev_ids:
                ev = evidence_map.get(ev_id)
                if ev:
                    print(f"    Evidence [{ev_id}]:")
                    print(f"      Source URL   : {ev.get('source_url')}")
                    print(f"      Source Class : {ev.get('source_class')}")
                    print(f"      Retrieved At : {ev.get('retrieved_at')}")
                    span = ev.get("claim_span") or ""
                    if span:
                        print(f"      Claim Span   : {span[:160]}")

    print("\n" + "=" * 80)
    print(f"AUDIT SUMMARY: {len(sampled)} companies, {total_audited} claims ({available_audited} available)")
    print("=" * 80)


if __name__ == "__main__":
    main()
