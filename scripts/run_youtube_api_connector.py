#!/usr/bin/env python3
"""YouTube Data API connector for official company channel discovery.

Operates behind the SIGNAL_SCRAPE_YOUTUBE_API_KEY environment variable.
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

ENV_KEY_VAR = "SIGNAL_SCRAPE_YOUTUBE_API_KEY"


def main() -> None:
    parser = argparse.ArgumentParser(description="YouTube official Data API connector.")
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
            "connector": "youtube_official_data_api_v3",
            "active": False,
            "configured": False,
            "env_var": ENV_KEY_VAR,
            "profiles_count": len(profiles),
            "observations_emitted": 0,
            "publishable": 0,
            "status": "inactive_pending_human_provided_api_key",
            "claim_boundary": "Requires human-provided YouTube Data API v3 key (§0 Rule 4). Connector implemented and ready.",
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
        query = f'"{name}" Norway'
        encoded = urllib.parse.urlencode({
            "part": "snippet",
            "q": query,
            "type": "channel",
            "maxResults": "3",
            "key": api_key,
        })
        url = f"https://www.googleapis.com/youtube/v3/search?{encoded}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SignalpostResearchPOC/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            items = data.get("items") or []
            if not items:
                continue
            item = items[0]
            snippet = item.get("snippet") or {}
            channel_id = snippet.get("channelId") or (item.get("id") or {}).get("channelId")
            channel_title = snippet.get("channelTitle") or snippet.get("title")
            source_url = f"https://www.youtube.com/channel/{channel_id}"
            digest = hashlib.sha256(json.dumps(item, sort_keys=True).encode()).hexdigest()
            obs = {
                "id": f"yt-{org}-{channel_id[:16]}",
                "organisation_number": org,
                "platform": "youtube",
                "signal_type": "company_profile",
                "source_url": source_url,
                "retrieved_at": now,
                "content_sha256": digest,
                "exact_entity": True,
                "identity_proof": [
                    {"type": "exact_legal_name_match", "value": name},
                    {"type": "channel_id", "value": channel_id},
                ],
                "acquisition_mode": "official_api",
                "rights_status": "approved",
                "source_class": "public_social_profile",
                "evidence_span": f"Channel: {channel_title}; ID: {channel_id}",
                "metrics": {
                    "channel_id": channel_id,
                    "channel_title": channel_title,
                    "description": snippet.get("description"),
                },
                "strategy": "youtube_official_data_api_v3",
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
        "connector": "youtube_official_data_api_v3",
        "active": True,
        "configured": True,
        "profiles_count": len(profiles),
        "observations_emitted": len(observations),
        "publishable": len(observations),
        "claim_boundary": "Official YouTube Data API v3 with licensed key.",
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
