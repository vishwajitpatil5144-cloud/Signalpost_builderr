#!/usr/bin/env python3
"""Free website-discovery connector: no API key, no paid search provider.

This is a $0 replacement for scripts/run_brave_discovery.py. Instead of paying
for a search API, it generates candidate domains directly from the company's
legal name (deterministic slugging + common Norwegian/company TLD and suffix
patterns), issues a direct HTTP(S) request to each candidate, and reuses the
project's existing exact-entity identity gate to decide whether a candidate is
publishable. No search engine, directory, or social platform is queried or
scraped -- every request is a direct fetch of a guessed company domain, so
this connector has no dependency on any third party's terms of service beyond
the target site itself (which the crawler already respects via robots.txt in
fetch_website / the Scrapy crawler).

Because there is no search ranking to trust, every candidate is only ever a
*candidate*: publication still requires the same independent fetched-page
exact-entity verification (apply_website_identity_gate) used everywhere else
in this project. A candidate that fails the gate is discarded, never
published, and the profile's website_discovery evidence is marked
not_found/not_applicable rather than silently guessed at.

Usage:
    uv run python scripts/run_free_domain_discovery.py \
        --input out/profiles.jsonl \
        --output out/profiles-with-discovery.jsonl \
        --report out/free-discovery-report.json \
        --limit 1000 \
        --promote-verified
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from signal_scrape_core.evidence import evidence, utc_now  # noqa: E402
from signal_scrape_core.identity import apply_website_identity_gate  # noqa: E402
from signal_scrape_core.website import fetch_website  # noqa: E402

# Legal-form and generic suffixes stripped before slugging, mirroring the
# tokens the project already treats as non-distinctive in identity.py.
LEGAL_AND_GENERIC = {
    "as", "asa", "ans", "da", "enk", "iks", "sa", "sam", "sti", "stiftelsen",
    "nuf", "ab", "b", "v", "limited", "ltd", "inc", "plc", "the", "og", "and",
    "norge", "norway", "group", "gruppen", "holding",
}

# Ordered by how likely a Norwegian SMB is to actually register it.
CANDIDATE_TLDS = (".no", ".com", ".net")


def _ascii_fold(value: str) -> str:
    value = value.translate(str.maketrans({"ø": "o", "Ø": "O", "å": "a", "Å": "A", "æ": "ae", "Æ": "AE"}))
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()


def _name_tokens(name: str) -> list[str]:
    folded = _ascii_fold(name).casefold()
    tokens = re.findall(r"[a-z0-9]+", folded)
    return [token for token in tokens if token not in LEGAL_AND_GENERIC and len(token) > 1]


def candidate_domains(name: str, *, municipality: str = "", max_candidates: int = 8) -> list[str]:
    """Generate plausible bare domains (no scheme, no TLD) from a legal name."""
    tokens = _name_tokens(name)
    if not tokens:
        return []
    variants: list[str] = []
    joined = "".join(tokens)
    hyphenated = "-".join(tokens)
    variants.append(joined)
    if hyphenated != joined:
        variants.append(hyphenated)

    # If municipality or location token is part of the name, try stripped variant (e.g. Haagensen Enebakk -> Haagensen)
    if municipality:
        muni_tokens = set(_name_tokens(municipality))
        stripped_tokens = [t for t in tokens if t not in muni_tokens]
        if stripped_tokens and len(stripped_tokens) < len(tokens):
            s_joined = "".join(stripped_tokens)
            variants.append(s_joined)
            if "-".join(stripped_tokens) != s_joined:
                variants.append("-".join(stripped_tokens))

    # Many small companies register under just the first distinctive word.
    if len(tokens) > 1:
        variants.append(tokens[0])

    # De-duplicate while preserving priority order, drop anything too short
    # or too generic to be worth a network request.
    seen: set[str] = set()
    ordered: list[str] = []
    for variant in variants:
        if len(variant) < 3 or variant in seen:
            continue
        seen.add(variant)
        ordered.append(variant)
    return ordered[:max_candidates]


def build_candidate_urls(name: str, *, municipality: str = "") -> list[str]:
    urls: list[str] = []
    for bare in candidate_domains(name, municipality=municipality):
        for tld in CANDIDATE_TLDS:
            urls.append(f"https://{bare}{tld}")
    return urls


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Free, key-less domain-guess website discovery with exact-entity verification.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--limit", type=int, default=1000, help="Maximum missing-website profiles to attempt")
    parser.add_argument("--max-candidates-per-company", type=int, default=6)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--min-interval", type=float, default=0.2, help="Seconds to sleep between outbound requests (politeness)")
    parser.add_argument("--promote-verified", action="store_true", help="Copy exact-entity verified sites into canonical website evidence")
    parser.add_argument("--max-requests", type=int, default=1800, help="Hard stop on total outbound requests this connector may issue")
    args = parser.parse_args()

    rows = read_jsonl(Path(args.input))
    counts: Counter[str] = Counter()
    started_at = utc_now()
    attempted = 0
    requests_used = 0

    for row in rows:
        if attempted >= args.limit or requests_used >= args.max_requests:
            counts["stopped_on_budget"] = 1
            break
        existing_website = (row.get("evidence", {}).get("website") or {}).get("status")
        if existing_website == "available" or row.get("website"):
            counts["registry_or_existing_website_skipped"] += 1
            continue

        name = row.get("name") or ""
        municipality = row.get("municipality") or ""
        candidates = build_candidate_urls(name, municipality=municipality)[: args.max_candidates_per_company]
        if not candidates:
            counts["no_candidates_generated"] += 1
            row.setdefault("evidence", {})["website_discovery"] = evidence(
                "website_discovery",
                "not_applicable",
                "free_domain_guess",
                "n/a",
                value={"provider": "free_domain_guess", "reason": "legal name produced no usable slug"},
                note="No candidate domain could be generated from the legal name; no request was sent.",
            )
            continue

        attempted += 1
        selected_website: dict[str, Any] | None = None
        tried: list[dict[str, Any]] = []
        for url in candidates:
            if requests_used >= args.max_requests:
                break
            website, web_ops = fetch_website(url, timeout=args.timeout)
            requests_used += web_ops.get("requests", 1)
            time.sleep(args.min_interval)
            tried.append({"url": url, "status": website.get("status")})
            if website.get("status") != "available":
                continue
            gated = apply_website_identity_gate(row, website)
            assessment = gated["assessment"]
            if assessment and assessment.get("publishable"):
                selected_website = gated["website"]
                selected_website["source_type"] = "domain_guess_discovered_company_website"
                counts["verified_sites"] += 1
                break
            counts["candidate_failed_identity_gate"] += 1

        discovery_summary = {
            "provider": "free_domain_guess",
            "candidates_generated": len(candidates),
            "candidates_tried": tried,
            "selected": bool(selected_website),
        }
        if selected_website:
            row["evidence"]["website_discovery"] = evidence(
                "website_discovery",
                "available",
                "domain_guess_then_independent_fetch",
                selected_website.get("source_url", ""),
                value=discovery_summary,
                note="Domain was guessed from the legal name; publication depended only on the independently fetched page passing the exact-entity identity gate.",
            )
            row["evidence"]["website_discovered"] = selected_website
            if args.promote_verified:
                row["evidence"]["website"] = selected_website
                counts["promoted_sites"] += 1
        else:
            counts["abstained_no_match"] += 1
            row["evidence"]["website_discovery"] = evidence(
                "website_discovery",
                "not_found",
                "domain_guess_then_independent_fetch",
                "n/a",
                value=discovery_summary,
                note="No guessed domain resolved to a page that passed the exact-entity identity gate. Reported not_found rather than guessed.",
            )

    write_jsonl(Path(args.output), rows)
    report = {
        "generated_at": utc_now(),
        "started_at": started_at,
        "provider": "free_domain_guess (no API key, no search engine, no paid provider)",
        "input_profiles": len(rows),
        "attempted_profiles": attempted,
        "outbound_requests_used": requests_used,
        "counts": dict(counts),
        "promote_verified_enabled": args.promote_verified,
        "note": "Every published site passed the same apply_website_identity_gate used by the registry-website path. This connector never treats a reachable domain as evidence by itself.",
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
