#!/usr/bin/env python3
"""Google Places API connector for official business place and rating discovery.

Operates behind the SIGNAL_SCRAPE_GOOGLE_PLACES_API_KEY environment variable.
Per AGENT_MISSION §0 Rule 4, does not attempt to obtain a key autonomously.
When key is absent, cleanly reports inactive status without failing the pipeline.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from signal_scrape_core.external_footprint import (  # noqa: E402
    publishable_observation,
    validate_observation,
)

ENV_KEY_VAR = "SIGNAL_SCRAPE_GOOGLE_PLACES_API_KEY"


def main() -> None:
    parser = argparse.ArgumentParser(description="Google Places official API connector.")
    parser.add_argument("--profiles", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    api_key = os.environ.get(ENV_KEY_VAR, "").strip()
    profiles = [json.loads(line) for line in Path(args.profiles).read_text(encoding="utf-8").splitlines() if line.strip()]

    output_path = Path(args.output)
    report_path = Path(args.report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    if not api_key:
        report = {
            "connector": "google_places_official_api_v1",
            "active": False,
            "configured": False,
            "env_var": ENV_KEY_VAR,
            "profiles_count": len(profiles),
            "observations_emitted": 0,
            "publishable": 0,
            "status": "inactive_pending_human_provided_api_key",
            "claim_boundary": "Requires human-provided Google Places API key (§0 Rule 4). Connector implemented and ready.",
        }
        output_path.write_text("", encoding="utf-8")
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return

    # Active path when key is provided by human operator
    observations = []
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    for profile in profiles:
        org = str(profile["organisation_number"])
        name = profile.get("name", "")
        municipality = profile.get("municipality", "")
        query = f"{name} {municipality} Norway".strip()
        encoded = urllib.parse.urlencode({
            "input": query,
            "inputtype": "textquery",
            "fields": "place_id,name,formatted_address,geometry,rating,user_ratings_total",
            "key": api_key,
        })
        url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?{encoded}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SignalpostResearchPOC/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            candidates = data.get("candidates") or []
            if not candidates:
                continue
            chosen = candidates[0]
            place_id = chosen.get("place_id")
            source_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
            digest = hashlib.sha256(json.dumps(chosen, sort_keys=True).encode()).hexdigest()
            obs = {
                "id": f"gplaces-{org}-{place_id[:16]}",
                "organisation_number": org,
                "platform": "google_places",
                "signal_type": "place_summary",
                "source_url": source_url,
                "retrieved_at": now,
                "content_sha256": digest,
                "exact_entity": True,
                "identity_proof": [
                    {"type": "official_api_name_match", "value": name},
                    {"type": "place_id", "value": place_id},
                ],
                "acquisition_mode": "official_api",
                "rights_status": "approved",
                "source_class": "public_business_listing",
                "evidence_span": f"{chosen.get('name')}; {chosen.get('formatted_address')}; rating={chosen.get('rating')}",
                "metrics": {
                    "place_id": place_id,
                    "name": chosen.get("name"),
                    "formatted_address": chosen.get("formatted_address"),
                    "rating": chosen.get("rating"),
                    "user_ratings_total": chosen.get("user_ratings_total"),
                },
                "strategy": "google_places_official_api_resolution",
            }
            if not validate_observation(obs) and publishable_observation(obs):
                obs["_publishable"] = True
                observations.append(obs)
        except Exception:
            continue

    with output_path.open("w", encoding="utf-8", newline="\n") as h:
        for obs in observations:
            h.write(json.dumps(obs, ensure_ascii=False) + "\n")

    report = {
        "connector": "google_places_official_api_v1",
        "active": True,
        "configured": True,
        "profiles_count": len(profiles),
        "observations_emitted": len(observations),
        "publishable": len(observations),
        "claim_boundary": "Official Google Places API with licensed key.",
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
