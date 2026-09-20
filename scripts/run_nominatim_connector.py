#!/usr/bin/env python3
"""OpenStreetMap / Nominatim connector for Norwegian business location verification.

Cross-verifies official registered business addresses via OpenStreetMap's
official Nominatim API. Free, requires no API key, and adheres to the
Nominatim Usage Policy (custom User-Agent, max 1 req/sec, local caching).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from signal_scrape_core.external_footprint import (  # noqa: E402
    aggregate_footprint,
    publishable_observation,
    validate_observation,
)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "SignalpostResearchPOC/1.0 (+https://builderr.ai; contact: poc@builderr.ai)"
REQUEST_INTERVAL = 1.1  # seconds between requests to strictly respect 1 req/s policy


def _extract_address(profile: dict[str, Any]) -> dict[str, str] | None:
    evidence = profile.get("evidence") or {}
    reg_live = (evidence.get("registry_live") or {}).get("value") or {}
    b_addr = reg_live.get("business_address") or reg_live.get("postal_address") or {}
    lines = b_addr.get("adresse") or []
    street = lines[0].strip() if lines and lines[0] else ""
    postcode = str(b_addr.get("postnummer") or "").strip()
    city = str(b_addr.get("poststed") or "").strip()
    municipality = str(b_addr.get("kommune") or profile.get("municipality") or "").strip()

    if not street and not (postcode and city):
        return None

    return {
        "street": street,
        "postcode": postcode,
        "city": city,
        "municipality": municipality,
    }


def query_nominatim(
    address: dict[str, str],
    cache_path: Path | None = None,
    last_req_time: list[float] | None = None,
) -> tuple[dict[str, Any] | None, bool]:
    """Query Nominatim with rate-limiting and on-disk caching."""
    if cache_path and cache_path.exists():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            return cached, True
        except Exception:
            pass

    # Rate limiting
    if last_req_time is not None:
        elapsed = time.monotonic() - last_req_time[0]
        if elapsed < REQUEST_INTERVAL:
            time.sleep(REQUEST_INTERVAL - elapsed)
        last_req_time[0] = time.monotonic()

    parts = []
    if address.get("street"):
        parts.append(address["street"])
    if address.get("postcode"):
        parts.append(address["postcode"])
    if address.get("city"):
        parts.append(address["city"])
    parts.append("Norway")

    query_str = ", ".join(parts)
    params = urllib.parse.urlencode({
        "q": query_str,
        "format": "json",
        "countrycodes": "no",
        "limit": "1",
        "addressdetails": "1",
    })
    url = f"{NOMINATIM_URL}?{params}"

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            result = data[0] if data and isinstance(data, list) else None
            if cache_path:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
            return result, False
    except Exception:
        return None, False


def verify_and_build_observation(
    profile: dict[str, Any],
    address: dict[str, str],
    nom_result: dict[str, Any],
    retrieved_at: str,
) -> dict[str, Any] | None:
    org = str(profile["organisation_number"])
    osm_id = nom_result.get("osm_id")
    osm_type = nom_result.get("osm_type", "way")
    display_name = str(nom_result.get("display_name") or "")
    addr_details = nom_result.get("address") or {}

    # Verification: check postnummer or city/municipality match
    nom_postcode = str(addr_details.get("postcode") or "")
    nom_city = str(addr_details.get("city") or addr_details.get("town") or addr_details.get("village") or addr_details.get("municipality") or "")

    postcode_match = bool(address.get("postcode") and address["postcode"] == nom_postcode)
    city_match = bool(
        address.get("city")
        and (address["city"].casefold() in display_name.casefold() or address["city"].casefold() in nom_city.casefold())
    )
    muni_match = bool(
        address.get("municipality")
        and address["municipality"].casefold() in display_name.casefold()
    )

    if not (postcode_match or city_match or muni_match):
        return None

    osm_url = f"https://www.openstreetmap.org/{osm_type}/{osm_id}"
    digest = hashlib.sha256(json.dumps(nom_result, sort_keys=True).encode("utf-8")).hexdigest()
    proof = [
        {"type": "registered_business_address", "value": address.get("street") or ""},
        {"type": "registered_postcode_city", "value": f"{address.get('postcode', '')} {address.get('city', '')}".strip()},
        {"type": "osm_id", "value": str(osm_id)},
    ]
    if postcode_match:
        proof.append({"type": "postcode_match", "value": address["postcode"]})

    span = f"Registered address: {address.get('street', '')}, {address.get('postcode', '')} {address.get('city', '')}; OSM verified: {display_name[:200]}"
    observation = {
        "id": f"osm-place-{hashlib.sha256(f'{org}|{osm_id}'.encode()).hexdigest()[:24]}",
        "organisation_number": org,
        "platform": "openstreetmap",
        "signal_type": "place_summary",
        "source_url": osm_url,
        "retrieved_at": retrieved_at,
        "content_sha256": digest,
        "exact_entity": True,
        "identity_proof": proof,
        "acquisition_mode": "official_api",
        "rights_status": "approved",
        "source_class": "public_business_listing",
        "evidence_span": span,
        "metrics": {
            "latitude": float(nom_result.get("lat", 0.0)),
            "longitude": float(nom_result.get("lon", 0.0)),
            "osm_id": osm_id,
            "osm_type": osm_type,
            "display_name": display_name,
            "postcode": nom_postcode,
            "verified_against_registry": True,
        },
        "strategy": "registry_business_address_osm_cross_verification",
    }
    return observation


def main() -> None:
    parser = argparse.ArgumentParser(description="Cross-verify Norwegian company business locations via OpenStreetMap Nominatim.")
    parser.add_argument("--profiles", required=True, help="Input profiles JSONL")
    parser.add_argument("--output", required=True, help="Output observations JSONL")
    parser.add_argument("--report", required=True, help="Run report JSON")
    parser.add_argument("--cache-dir", default="out/cache/nominatim", help="Directory to cache Nominatim responses")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit on companies to process")
    args = parser.parse_args()

    profiles = [json.loads(line) for line in Path(args.profiles).read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.limit:
        profiles = profiles[:args.limit]

    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    observations = []
    last_req_time = [0.0]
    api_requests = 0
    cache_hits = 0
    verified_count = 0
    no_address_count = 0
    no_result_count = 0

    for profile in profiles:
        org = str(profile.get("organisation_number") or profile.get("org"))
        addr = _extract_address(profile)
        if not addr:
            no_address_count += 1
            continue

        cache_file = cache_dir / f"{org}.json"
        nom_result, was_cached = query_nominatim(addr, cache_path=cache_file, last_req_time=last_req_time)
        if was_cached:
            cache_hits += 1
        else:
            api_requests += 1

        if not nom_result:
            no_result_count += 1
            continue

        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        obs = verify_and_build_observation(profile, addr, nom_result, retrieved_at=now)
        if obs:
            err = validate_observation(obs)
            if not err and publishable_observation(obs):
                obs["_publishable"] = True
                observations.append(obs)
                verified_count += 1

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="\n") as h:
        for obs in observations:
            h.write(json.dumps(obs, ensure_ascii=False) + "\n")

    report = {
        "connector": "openstreetmap_nominatim_v1",
        "profiles_processed": len(profiles),
        "api_requests": api_requests,
        "cache_hits": cache_hits,
        "addresses_verified": verified_count,
        "no_address_in_profile": no_address_count,
        "no_nominatim_result": no_result_count,
        "publishable": len(observations),
        "claim_boundary": "Cross-verified official registered business address against OpenStreetMap; exact coordinates and OSM place ID. Official API, approved rights, no key required.",
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
