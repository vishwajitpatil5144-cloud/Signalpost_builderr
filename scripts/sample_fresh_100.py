#!/usr/bin/env python3
"""Sample 100 completely fresh companies from the universe with zero overlap to previous runs."""

from __future__ import annotations

import csv
import gzip
import json
import random
from pathlib import Path

def main():
    root = Path(__file__).resolve().parents[1]
    
    # 1. Collect all previously used organisation numbers
    prev_orgs = set()
    for path in (root / "out").glob("**/companies.jsonl"):
        for line in open(path, encoding="utf-8"):
            if line.strip():
                prev_orgs.add(str(json.loads(line).get("organisation_number")))
    print(f"Loaded {len(prev_orgs)} previous organisation numbers to exclude.")

    # 2. Check which orgs exist in brreg-enheter.csv (for 100% guarantee)
    print("Reading available orgs in brreg-enheter.csv...")
    bulk_path = root / "brreg-enheter.csv"
    bulk_orgs = set()
    with bulk_path.open(encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f, delimiter=";")
        header = next(reader, None)
        # Find column index for organisasjonsnummer
        org_idx = 0
        for idx, col in enumerate(header or []):
            if "organisasjonsnummer" in col.lower():
                org_idx = idx
                break
        for row in reader:
            if row:
                bulk_orgs.add(row[org_idx].strip())
    print(f"Found {len(bulk_orgs):,} entities in bulk snapshot.")

    # 3. Read candidates from universe that are NOT in prev_orgs and ARE in bulk snapshot
    candidates = []
    universe_path = root / "data" / "signalpost-company-universe-2025.jsonl.gz"
    with gzip.open(universe_path, "rt", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            org = str(row.get("organisation_number"))
            if org in prev_orgs:
                continue
            if org in bulk_orgs:
                candidates.append(row)

    print(f"Eligible fresh candidates: {len(candidates):,}")

    # 4. Deterministically sample 100 companies with seed 20260921
    rng = random.Random(20260921)
    sampled = rng.sample(candidates, 100)

    out_dir = root / "out" / "fresh-100-run-20260921"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "companies.jsonl"
    
    with out_file.open("w", encoding="utf-8") as f:
        for item in sampled:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Wrote {len(sampled)} fresh companies to {out_file}")
    
    # Verify zero overlap
    sampled_orgs = {str(item["organisation_number"]) for item in sampled}
    assert len(sampled_orgs.intersection(prev_orgs)) == 0, "Overlap detected!"
    print("Verification passed: 0 overlap with previous companies.")

    # Print summary of sampled companies
    legal_forms = {}
    with_website = sum(1 for item in sampled if item.get("website"))
    for item in sampled:
        form = item.get("legal_form", "OTHER")
        legal_forms[form] = legal_forms.get(form, 0) + 1
    print(f"Sample breakdown: {len(sampled)} companies, {with_website} with registry website, forms: {legal_forms}")

if __name__ == "__main__":
    main()
