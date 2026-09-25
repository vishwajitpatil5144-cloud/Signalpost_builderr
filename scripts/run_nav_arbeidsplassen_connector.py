#!/usr/bin/env python3
"""NAV Arbeidsplassen public job vacancy connector for Norwegian companies.

Queries the official NAV Job Vacancy Feed API (pam-stilling-feed.nav.no)
using Norway Labour and Welfare Administration's official public JWT token.
Matches vacancies to Norwegian companies via exact business name and
municipality verification.

Acquisition mode: official_api
Platform: job_board
Signal type: job_posting
Rights status: approved (public feed provided by NAV under open public terms)
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

USER_AGENT = "SignalpostResearchPOC/1.0 (+https://builderr.ai; contact: poc@builderr.ai)"
PUBLIC_TOKEN_URL = "https://pam-stilling-feed.nav.no/api/publicToken"
FEED_URL = "https://pam-stilling-feed.nav.no/api/v1/feed"


def _clean_name(name: str) -> str:
    """Normalize company or business name for exact token comparison."""
    tokens = re.findall(r"[a-z0-9æøå]+", str(name or "").casefold())
    legal_suffixes = {"as", "asa", "ba", "da", "ans", "enk", "nuf", "sa", "sti"}
    meaningful = [t for t in tokens if t not in legal_suffixes]
    return " ".join(meaningful if meaningful else tokens)


def _get_public_jwt(cache_path: Path | None = None) -> str | None:
    """Retrieve the public Bearer token from NAV, with optional disk cache."""
    if cache_path and cache_path.exists():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if cached.get("token") and (time.time() - cached.get("cached_at", 0)) < 86400:
                return cached["token"]
        except Exception:
            pass

    try:
        req = urllib.request.Request(PUBLIC_TOKEN_URL, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
            token = raw.strip().split("\n")[-1].strip()
            if token.startswith("ey"):
                if cache_path:
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    cache_path.write_text(
                        json.dumps({"token": token, "cached_at": time.time()}),
                        encoding="utf-8",
                    )
                return token
    except Exception as exc:
        print(f"Warning: Failed to fetch NAV public JWT: {exc}", file=sys.stderr)
    return None


def fetch_feed_items(
    jwt_token: str,
    max_pages: int = 2,
    cache_dir: Path | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """Stream pages from the NAV public vacancy feed."""
    items: list[dict[str, Any]] = []
    current_url = FEED_URL
    requests_made = 0

    for page_idx in range(max_pages):
        cache_file = cache_dir / f"page_{page_idx}.json" if cache_dir else None
        data = None

        if cache_file and cache_file.exists():
            try:
                data = json.loads(cache_file.read_text(encoding="utf-8"))
            except Exception:
                data = None

        if not data:
            try:
                req = urllib.request.Request(
                    current_url,
                    headers={
                        "User-Agent": USER_AGENT,
                        "Authorization": f"Bearer {jwt_token}",
                        "Accept": "application/json",
                    },
                )
                with urllib.request.urlopen(req, timeout=20) as resp:
                    raw = resp.read().decode("utf-8")
                    data = json.loads(raw)
                    requests_made += 1
                if cache_file:
                    cache_file.parent.mkdir(parents=True, exist_ok=True)
                    cache_file.write_text(raw, encoding="utf-8")
            except Exception as exc:
                print(f"Warning: NAV feed page {page_idx} error: {exc}", file=sys.stderr)
                break

        page_items = data.get("items", [])
        items.extend(page_items)

        next_url = data.get("next_url")
        if not next_url:
            break
        current_url = (
            next_url
            if next_url.startswith("http")
            else "https://pam-stilling-feed.nav.no" + next_url
        )

    return items, requests_made


def match_vacancies(
    profiles: list[dict[str, Any]],
    feed_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Match feed vacancy items to company profiles with exact identity gating."""
    observations: list[dict[str, Any]] = []

    # Index companies by normalized name and token sets
    by_norm_name: dict[str, list[dict[str, Any]]] = {}
    profile_tokens: list[tuple[set[str], dict[str, Any]]] = []
    for p in profiles:
        clean = _clean_name(p.get("name", ""))
        if clean:
            by_norm_name.setdefault(clean, []).append(p)
            toks = set(clean.split())
            if len(toks) >= 2:
                profile_tokens.append((toks, p))

    for item in feed_items:
        entry = item.get("_feed_entry", {})
        business_name = entry.get("businessName")
        if not business_name:
            continue

        clean_b = _clean_name(business_name)
        matched_profiles = list(by_norm_name.get(clean_b, []))

        # Substantive token subset matching (e.g. 'Orange Cyberdefense' vs 'Orange Cyberdefense Norway AS')
        b_tokens = set(clean_b.split())
        if not matched_profiles and len(b_tokens) >= 2:
            for p_toks, p in profile_tokens:
                if b_tokens.issubset(p_toks) or p_toks.issubset(b_tokens):
                    matched_profiles.append(p)

        if not matched_profiles:
            continue

        item_uuid = entry.get("uuid") or item.get("id")
        if not item_uuid:
            continue

        title = str(entry.get("title") or item.get("title") or "Stilling").strip()
        municipal = str(entry.get("municipal") or "").strip().upper()
        status = str(entry.get("status") or "ACTIVE")
        date_modified = str(entry.get("sistEndret") or item.get("date_modified") or "")

        for p in matched_profiles:
            org = str(p.get("organisation_number", ""))
            p_muni = str(p.get("municipality") or "").strip().upper()

            # Identity gate: if municipality is present on both, require match or substring
            muni_match = True
            if municipal and p_muni:
                muni_match = (municipal == p_muni) or (municipal in p_muni) or (p_muni in municipal)

            if not muni_match:
                continue

            raw_bytes = json.dumps(item, sort_keys=True).encode("utf-8")
            digest = hashlib.sha256(raw_bytes).hexdigest()
            obs_id = f"nav-job-{org}-{digest[:16]}"
            source_url = f"https://arbeidsplassen.nav.no/stillinger/stilling/{item_uuid}"
            retrieved_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

            obs: dict[str, Any] = {
                "id": obs_id,
                "organisation_number": org,
                "platform": "job_board",
                "signal_type": "job_posting",
                "source_url": source_url,
                "retrieved_at": retrieved_at,
                "content_sha256": digest,
                "exact_entity": True,
                "identity_proof": [
                    {"type": "exact_business_name_match", "value": business_name},
                    {"type": "municipality_match", "value": municipal or p_muni},
                ],
                "acquisition_mode": "official_api",
                "rights_status": "approved",
                "source_class": "public_job_board",
                "evidence_span": f"NAV vacancy '{title}' at {business_name} ({municipal or p_muni}), status {status}",
                "metrics": {
                    "job_title": title,
                    "status": status,
                    "date_modified": date_modified,
                    "municipal": municipal,
                },
            }

            validation_errors = validate_observation(obs)
            if not validation_errors:
                observations.append(obs)

    return observations


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract verified job postings from NAV Arbeidsplassen feed.")
    parser.add_argument("--profiles", required=True, help="Input profiles JSONL")
    parser.add_argument("--output", required=True, help="Output observations JSONL")
    parser.add_argument("--report", required=True, help="Output execution report JSON")
    parser.add_argument("--pages", type=int, default=4, help="Number of 1,000-item feed pages to scan (default 4)")
    parser.add_argument("--cache-dir", default="out/cache/nav_feed", help="Cache directory for feed items")
    args = parser.parse_args()

    profiles_path = Path(args.profiles)
    output_path = Path(args.output)
    report_path = Path(args.report)
    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    profiles = [
        json.loads(line)
        for line in profiles_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    profiles = [p.get("profile", p) for p in profiles]

    jwt_token = _get_public_jwt(cache_dir / "token.json")
    requests_made = 1  # For token (or 0 if cached)

    if not jwt_token:
        print("Warning: Unable to obtain NAV public token; writing empty observations.", file=sys.stderr)
        output_path.write_text("", encoding="utf-8")
        report = {
            "platform": "job_board",
            "items_scanned": 0,
            "observations_found": 0,
            "requests": requests_made,
            "error": "token_unavailable",
        }
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return

    feed_items, feed_reqs = fetch_feed_items(jwt_token, max_pages=args.pages, cache_dir=cache_dir)
    requests_made += feed_reqs

    observations = match_vacancies(profiles, feed_items)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for obs in observations:
            f.write(json.dumps(obs, ensure_ascii=False) + "\n")

    report = {
        "platform": "job_board",
        "feed_pages": args.pages,
        "items_scanned": len(feed_items),
        "observations_found": len(observations),
        "unique_companies_matched": len({o["organisation_number"] for o in observations}),
        "requests": requests_made,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"NAV connector done: {len(feed_items)} scanned, {len(observations)} observations, {requests_made} requests")


if __name__ == "__main__":
    main()
