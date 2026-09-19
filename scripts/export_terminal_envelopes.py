#!/usr/bin/env python3
"""Export internal profiles into Builderr's required terminal-envelope shape.

The internal pipeline uses statuses such as ``not_found`` and ``source_error``.
The submission contract uses six availability states, so this script is the
explicit translation boundary before a run is submitted.

A fetched website that fails the exact-entity identity gate is exported as
``ambiguous`` rather than ``available``. That preserves the distinction
between finding a page and proving that it belongs to the legal entity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from signal_scrape_core.evidence import utc_now  # noqa: E402
from signal_scrape_core.refresh import diff_datasets  # noqa: E402

_STATUS_MAP = {
    "available": "available",
    "not_found": "not_available",
    "not_applicable": "not_applicable",
    "not_fetched": "not_applicable",
    "source_error": "failed",
    "blocked": "blocked",
}
_VALID_STATES = {"available", "not_available", "blocked", "not_applicable", "ambiguous", "failed"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _hash(*parts: Any) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(str(part).encode("utf-8"))
    return digest.hexdigest()


def _map_status(raw_status: str | None) -> str:
    mapped = _STATUS_MAP.get(raw_status or "not_applicable", "not_applicable")
    assert mapped in _VALID_STATES, f"internal mapping produced an invalid state: {mapped!r}"
    return mapped


def _canonical_record(record: dict[str, Any] | None) -> dict[str, Any]:
    record = record or {}
    value = record.get("value") or {}
    return {
        **record,
        "value": value,
        "source": record.get("source") or record.get("source_url"),
        "retrievedAt": record.get("retrievedAt") or record.get("retrieved_at"),
        "hash": record.get("hash") or record.get("content_sha256"),
    }


def _add_evidence(
    evidence_list: list[dict[str, Any]],
    evidence_by_id: dict[tuple[str | None, str | None], str],
    source_url: str | None,
    source_class: str | None,
    retrieved_at: str | None,
    content_hash: str | None,
    claim_span: str,
) -> list[str]:
    if not source_url:
        return []
    key = (source_url, retrieved_at)
    if key not in evidence_by_id:
        evidence_id = f"ev-{len(evidence_list) + 1}"
        evidence_list.append(
            {
                "id": evidence_id,
                "source_url": source_url,
                "source_class": source_class or "unknown",
                "retrieved_at": retrieved_at,
                "content_sha256": content_hash or _hash(source_url, retrieved_at or ""),
                "claim_span": claim_span[:280],
            }
        )
        evidence_by_id[key] = evidence_id
    return [evidence_by_id[key]]


def build_envelope(
    row: dict[str, Any],
    run_id: str,
    per_company_ops: dict[str, Any] | None = None,
    changes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    org = row.get("org") or row.get("organisation_number")
    claims: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    evidence_by_id: dict[tuple[str | None, str | None], str] = {}

    def claim(
        field: str,
        value: Any,
        availability: str,
        confidence: float,
        source_url: str | None,
        source_class: str | None,
        retrieved_at: str | None,
        content_hash: str | None,
        note: str | None = None,
    ) -> None:
        evidence_ids = _add_evidence(
            evidence,
            evidence_by_id,
            source_url,
            source_class,
            retrieved_at,
            content_hash,
            note or f"{field}: {value}",
        )
        entry = {
            "field": field,
            "value": value,
            "availability": availability,
            "confidence": confidence,
            "evidence_ids": evidence_ids,
        }
        if note:
            entry["note"] = note
        claims.append(entry)

    # Registry identity is the highest-confidence source in the output.
    records = row.get("evidence") or {}
    registry = _canonical_record(row.get("registry") or records.get("registry_live") or records.get("registry"))
    registry_source = registry.get("source") or row.get("registrySource")
    registry_retrieved = registry.get("retrievedAt")
    if row.get("name"):
        claim("legal_name", row["name"], "available", 1.0, registry_source, "official_identity", registry_retrieved, registry.get("hash"))
    legal_form = row.get("form") or row.get("legal_form")
    industry_code = row.get("industryCode") or row.get("industry_code")
    claim("legal_form", legal_form, "available" if legal_form else "not_available", 1.0 if legal_form else 0.0, registry_source, "official_identity", registry_retrieved, registry.get("hash"))
    claim("municipality", row.get("municipality"), "available" if row.get("municipality") else "not_available", 1.0 if row.get("municipality") else 0.0, registry_source, "official_identity", registry_retrieved, registry.get("hash"))
    claim("industry_code", industry_code, "available" if industry_code else "not_available", 1.0 if industry_code else 0.0, registry_source, "official_identity", registry_retrieved, registry.get("hash"))
    if row.get("employees") is not None:
        claim("employees", row["employees"], "available", 0.8, registry_source, "official_identity", registry_retrieved, registry.get("hash"))
    else:
        claim("employees", None, "not_available", 0.0, registry_source, "official_identity", registry_retrieved, registry.get("hash"), note="Not reported by the registry; not interpreted as zero.")

    # A successful fetch is not enough to publish a company-site match.
    web = _canonical_record(row.get("web") or records.get("website"))
    web_status = web.get("status")
    web_value = web.get("value") or {}
    identity_assessment = web_value.get("identity_assessment") or {}
    title = web_value.get("title") or ""
    looks_unverified = "identity not verified" in title.lower() or (
        identity_assessment and not identity_assessment.get("publishable", True)
    )
    if web_status == "available" and looks_unverified:
        claim(
            "official_website",
            web_value.get("final_url") or web_value.get("requested_url"),
            "ambiguous",
            0.3,
            web.get("source") or web_value.get("final_url"),
            "unverified_candidate_site",
            web.get("retrievedAt"),
            web.get("hash"),
            note="Fetched successfully but exact-entity identity verification did not pass.",
        )
    elif web_status == "available":
        claim(
            "official_website",
            web_value.get("final_url") or web_value.get("requested_url"),
            "available",
            0.95,
            web.get("source") or web_value.get("final_url"),
            "registry_linked_company_website",
            web.get("retrievedAt"),
            web.get("hash"),
        )
    else:
        mapped = _map_status(web_status)
        claim("official_website", None, mapped, 0.0, web.get("source"), "registry_linked_company_website", web.get("retrievedAt"), web.get("hash"))
        if mapped == "failed":
            errors.append({"field": "official_website", "message": web.get("note") or "website fetch failed", "source_url": web.get("source")})

    financial = _canonical_record(row.get("financial") or records.get("financials"))
    financial_records = financial.get("records") or financial["value"].get("records") or []
    if financial_records:
        latest = financial_records[0]
        for field_name, key in (("revenue", "revenue"), ("operating_result", "operating_result"), ("annual_result", "annual_result"), ("assets", "assets"), ("debt", "debt")):
            value = latest.get(key)
            claim(field_name, value, "available" if value is not None else "not_available", 0.9 if value is not None else 0.0, financial.get("source"), "official_annual_accounts", financial.get("retrievedAt"), financial.get("hash"), note=f"period {latest.get('period', {}).get('fraDato')} to {latest.get('period', {}).get('tilDato')}")
    else:
        mapped = _map_status(financial.get("status"))
        claim("revenue", None, mapped, 0.0, financial.get("source"), "official_annual_accounts", financial.get("retrievedAt"), financial.get("hash"), note="No filed account record returned. Missing is not interpreted as zero.")
        if mapped == "failed":
            errors.append({"field": "financial_accounts", "message": financial.get("note") or "financial lookup failed", "source_url": financial.get("source")})

    roles = _canonical_record(row.get("roles") or records.get("roles"))
    role_items = [item for item in (roles.get("items") or roles["value"].get("roles") or []) if not item.get("inactive")]
    if role_items:
        names = [item.get("name") for item in role_items if item.get("name")]
        claim("leadership", names, "available", 0.9, roles.get("source"), "official_roles", roles.get("retrievedAt"), roles.get("hash"))
    else:
        mapped = _map_status(roles.get("status"))
        claim("leadership", [], mapped if roles.get("status") != "available" else "not_available", 0.0, roles.get("source"), "official_roles", roles.get("retrievedAt"), roles.get("hash"), note="No active role holder returned.")

    locations = _canonical_record(row.get("locations") or records.get("locations"))
    location_items = locations.get("items") or locations["value"].get("locations") or []
    if location_items:
        claim("operating_locations", [item.get("name") for item in location_items], "available", 0.9, locations.get("source"), "official_subunits", locations.get("retrievedAt"), locations.get("hash"))
    else:
        mapped = _map_status(locations.get("status"))
        claim("operating_locations", [], mapped if locations.get("status") != "available" else "not_available", 0.0, locations.get("source"), "official_subunits", locations.get("retrievedAt"), locations.get("hash"))

    metrics = row.get("run_metrics") or {}
    ops = per_company_ops or {
        "requests": metrics.get("requests", 0),
        "runtime_ms": round(sum(metrics.get("latencies_ms") or []), 3),
    }
    return {
        "organisation_number": org,
        "run": {
            "run_id": run_id,
            "started_at": ops.get("started_at") or registry_retrieved or utc_now(),
            "completed_at": ops.get("completed_at") or utc_now(),
            "terminal_status": "completed" if not errors else "completed_with_errors",
        },
        "claims": claims,
        "evidence": evidence,
        "changes": changes if changes is not None else row.get("changes") or [],
        "errors": errors,
        "operations": {
            "requests": ops.get("requests", 0),
            "runtime_ms": ops.get("runtime_ms", 0),
            "third_party_cost_usd": 0,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export profiles into the terminal-envelope output contract.")
    parser.add_argument("--input", required=True, help="profiles.jsonl or profiles-with-discovery.jsonl")
    parser.add_argument("--output", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--previous", help="previous profile JSONL used to populate changes[]")
    args = parser.parse_args()

    rows = read_jsonl(Path(args.input))
    changes_by_org: dict[str, list[dict[str, Any]]] = {}
    if args.previous:
        previous = read_jsonl(Path(args.previous))
        changes_by_org = {}
        for change in diff_datasets(previous, rows):
            changes_by_org.setdefault(change["organisation_number"], []).append(change)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    invalid = 0
    ambiguous_count = 0
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            envelope = build_envelope(row, args.run_id, changes=changes_by_org.get(row.get("organisation_number")))
            for item in envelope["claims"]:
                if item["availability"] not in _VALID_STATES:
                    invalid += 1
                ambiguous_count += item["availability"] == "ambiguous"
            handle.write(json.dumps(envelope, ensure_ascii=False, separators=(",", ":")) + "\n")

    print(f"Wrote {len(rows)} terminal envelopes to {output}")
    print(f"Ambiguous claims (fetched but not identity-verified): {ambiguous_count}")
    if invalid:
        raise SystemExit(f"FAIL: {invalid} claims used an invalid availability state")


if __name__ == "__main__":
    main()
