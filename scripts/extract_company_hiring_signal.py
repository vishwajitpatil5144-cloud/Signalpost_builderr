#!/usr/bin/env python3
"""Extract a bounded hiring signal from exact-entity company-site pages.

This reports only that a verified careers/jobs page exists and whether hiring
language appears in its captured text. It deliberately never asserts a job
count.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

CAREER_PATH = re.compile(
    r"/(?:jobb|jobs|karriere|careers|stilling(?:er)?|ledige|work-with-us|join-us|vacancies|rekruttering)(?:/|$)",
    re.I,
)
CAREER_TITLE = re.compile(
    r"\b(karriere|ledige\s+stillinger|jobb\s+hos\s+oss|careers|vacancies|work\s+with\s+us|join\s+our\s+team)\b",
    re.I,
)
HIRING_TERMS = re.compile(
    r"\b(vi\s+s(?:ø|o)ker|ledige\s+stilling|s(?:ø|o)k\s+n(?:å|a)|we(?:'|’)?re\s+hiring|"
    r"now\s+hiring|open\s+position|join\s+our\s+team|open\s+role)\b",
    re.I,
)


def observation(profile: dict) -> dict | None:
    website = (profile.get("evidence") or {}).get("website") or {}
    value = website.get("value") or {}
    identity = value.get("identity_assessment") or {}
    if website.get("status") != "available" or not identity.get("publishable"):
        return None
    career_pages = [
        page for page in (value.get("pages") or [])
        if CAREER_PATH.search(urlparse(str(page.get("url") or "")).path)
        or CAREER_TITLE.search(str(page.get("title") or ""))
    ]
    if not career_pages:
        return None
    page = career_pages[0]
    url = str(page.get("url") or "")
    digest = str(page.get("content_sha256") or "")
    if not url.startswith(("http://", "https://")) or len(digest) != 64:
        return None
    org = str(profile["organisation_number"])
    return {
        "id": "company-hiring-signal-" + hashlib.sha256(f"{org}|{url}".encode()).hexdigest()[:24],
        "organisation_number": org,
        "platform": "company_site",
        "signal_type": "hiring_page_present",
        "source_url": url,
        "retrieved_at": website.get("retrieved_at"),
        "content_sha256": digest,
        "exact_entity": True,
        "identity_proof": [{"type": "website_identity_gate", "score": identity.get("score"), "method": identity.get("method")}],
        "acquisition_mode": "permitted_public_page",
        "rights_status": "approved",
        "source_class": "company_site",
        "evidence_span": str(page.get("title") or "Careers/jobs page")[:1200],
        "metrics": {
            "career_page_found": True,
            "hiring_keyword_detected": bool(HIRING_TERMS.search(str(page.get("main_text_excerpt") or ""))),
            "interpretation": "Confirms a careers/jobs page exists and, if flagged, contains hiring language. Does not assert a job count.",
        },
        "strategy": "company_site_hiring_signal",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract a bounded hiring signal from exact-entity company sites.")
    parser.add_argument("--profiles", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    profiles = [json.loads(line) for line in Path(args.profiles).read_text(encoding="utf-8").splitlines() if line.strip()]
    rows = [item for profile in profiles if (item := observation(profile))]
    output = Path(args.output)
    report_path = Path(args.report)
    output.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    report = {
        "connector": "exact_company_site_hiring_signal_v1",
        "profiles": len(profiles),
        "companies_with_career_page": len(rows),
        "companies_with_hiring_keywords": sum(1 for row in rows if row["metrics"]["hiring_keyword_detected"]),
        "claim_boundary": "Page existence and keyword presence only; never an asserted job count.",
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
