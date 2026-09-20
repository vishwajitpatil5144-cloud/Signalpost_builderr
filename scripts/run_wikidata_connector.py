#!/usr/bin/env python3
"""Wikidata connector for Norwegian companies via SPARQL.

Queries Wikidata for companies matching Norwegian organisation numbers
(P2333). This is free, requires no API key, and uses Wikidata's official
SPARQL endpoint (query.wikidata.org). Identity matching is based exclusively
on the exact organisation number stored as a Wikidata property — never on
name similarity alone.

Acquisition mode: official_api (Wikidata SPARQL Service is the official
query interface for Wikidata, operated by the Wikimedia Foundation).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from signal_scrape_core.external_footprint import validate_observation  # noqa: E402

UA = "SignalpostResearchPOC/1.0 (https://builderr.ai; bounded qualification run)"
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

# Maximum org numbers per SPARQL query (Wikidata has query size limits).
# 100 is well within safe limits for a VALUES clause.
BATCH_SIZE = 100


def _sparql_query(org_numbers: list[str]) -> tuple[list[dict], str]:
    """Run a SPARQL query for the given org numbers. Returns (bindings, raw_response)."""
    values = " ".join(f"'{o}'" for o in org_numbers)
    query = f"""
SELECT ?item ?itemLabel ?org ?description ?website ?inception ?industry ?industryLabel WHERE {{
  ?item wdt:P2333 ?org .
  VALUES ?org {{ {values} }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "nb,nn,en". }}
  OPTIONAL {{ ?item schema:description ?description . FILTER(LANG(?description) = "nb") }}
  OPTIONAL {{ ?item wdt:P856 ?website }}
  OPTIONAL {{ ?item wdt:P571 ?inception }}
  OPTIONAL {{ ?item wdt:P452 ?industry . ?industry rdfs:label ?industryLabel . FILTER(LANG(?industryLabel) = "nb") }}
}}
"""
    url = SPARQL_ENDPOINT + "?" + urllib.parse.urlencode({"query": query, "format": "json"})
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        raw = resp.read()
    data = json.loads(raw)
    return data["results"]["bindings"], raw.decode("utf-8", errors="replace")


def _build_observations(bindings: list[dict], raw_response: str) -> list[dict]:
    """Convert SPARQL result bindings into external-footprint observations."""
    retrieved_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    content_hash = hashlib.sha256(raw_response.encode("utf-8")).hexdigest()

    # Group by org number to deduplicate (Wikidata can return multiple rows
    # per entity when it has multiple websites/industries).
    by_org: dict[str, dict] = {}
    for row in bindings:
        org = row["org"]["value"]
        if org not in by_org:
            by_org[org] = {
                "org": org,
                "entity": row["item"]["value"],
                "label": row["itemLabel"]["value"],
                "description": row.get("description", {}).get("value", ""),
                "websites": set(),
                "inception": row.get("inception", {}).get("value"),
                "industries": set(),
            }
        website = row.get("website", {}).get("value")
        if website:
            by_org[org]["websites"].add(website)
        industry = row.get("industryLabel", {}).get("value")
        if industry:
            by_org[org]["industries"].add(industry)

    observations = []
    for org, info in by_org.items():
        wikidata_url = info["entity"]
        evidence_parts = [
            f"Wikidata entity: {wikidata_url}",
            f"Label: {info['label']}",
        ]
        if info["description"]:
            evidence_parts.append(f"Description: {info['description']}")
        if info["websites"]:
            evidence_parts.append(f"Websites: {', '.join(sorted(info['websites']))}")
        if info["industries"]:
            evidence_parts.append(f"Industries: {', '.join(sorted(info['industries']))}")
        if info["inception"]:
            evidence_parts.append(f"Inception: {info['inception'][:10]}")

        obs = {
            "id": "wikidata-profile-" + hashlib.sha256(f"{org}|{wikidata_url}".encode()).hexdigest()[:24],
            "organisation_number": org,
            "platform": "wikidata",
            "signal_type": "company_profile",
            "source_url": wikidata_url,
            "retrieved_at": retrieved_at,
            "content_sha256": content_hash,
            "exact_entity": True,
            "identity_proof": [
                {"type": "wikidata_P2333_exact_match", "value": org},
            ],
            "acquisition_mode": "official_api",
            "rights_status": "approved",
            "source_class": "wikidata",
            "evidence_span": "; ".join(evidence_parts)[:1200],
            "wikidata_entity": wikidata_url,
            "wikidata_label": info["label"],
            "wikidata_description": info["description"],
            "wikidata_websites": sorted(info["websites"]),
            "wikidata_industries": sorted(info["industries"]),
            "wikidata_inception": info["inception"],
            "strategy": "wikidata_org_number_exact_match",
        }
        # Validate against the external-footprint schema
        issues = validate_observation(obs)
        if issues:
            obs["_validation_issues"] = issues
            obs["_publishable"] = False
        else:
            obs["_publishable"] = True
        observations.append(obs)

    return observations


def main() -> None:
    parser = argparse.ArgumentParser(description="Query Wikidata for Norwegian company profiles by organisation number.")
    parser.add_argument("--profiles", required=True, help="profiles.jsonl or profiles-with-discovery.jsonl")
    parser.add_argument("--output", required=True, help="Output observations JSONL")
    parser.add_argument("--report", required=True, help="Output report JSON")
    args = parser.parse_args()

    profiles = [json.loads(line) for line in Path(args.profiles).read_text(encoding="utf-8").splitlines() if line.strip()]
    org_numbers = [str(p["organisation_number"]) for p in profiles]

    all_observations: list[dict] = []
    total_bindings = 0
    errors = 0

    # Process in batches
    for i in range(0, len(org_numbers), BATCH_SIZE):
        batch = org_numbers[i : i + BATCH_SIZE]
        try:
            bindings, raw = _sparql_query(batch)
            total_bindings += len(bindings)
            observations = _build_observations(bindings, raw)
            all_observations.extend(observations)
        except Exception as exc:
            errors += 1
            print(f"Error querying Wikidata for batch {i // BATCH_SIZE + 1}: {type(exc).__name__}: {exc}", file=sys.stderr)
        # Respect Wikidata rate limits (polite delay between batches)
        if i + BATCH_SIZE < len(org_numbers):
            time.sleep(2)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "".join(json.dumps(obs, ensure_ascii=False) + "\n" for obs in all_observations),
        encoding="utf-8",
    )

    publishable = [obs for obs in all_observations if obs.get("_publishable")]
    report = {
        "connector": "wikidata_org_number_v1",
        "profiles_queried": len(org_numbers),
        "sparql_requests": (len(org_numbers) + BATCH_SIZE - 1) // BATCH_SIZE,
        "bindings_returned": total_bindings,
        "observations": len(all_observations),
        "publishable": len(publishable),
        "companies_found": len(set(obs["organisation_number"] for obs in all_observations)),
        "errors": errors,
        "claim_boundary": "Company profile from Wikidata matched by exact P2333 (Norwegian org number). Free, official API, no key required.",
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
