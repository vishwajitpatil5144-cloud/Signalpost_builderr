from __future__ import annotations

import re
import unicodedata
import urllib.parse
from typing import Any


LEGAL_AND_GENERIC = {
    "as", "asa", "ans", "da", "enk", "iks", "sa", "sam", "sti", "stiftelsen",
    "nuf", "ab", "b", "v", "limited", "ltd", "inc", "plc", "the", "og", "and",
}


def _tokens(value: Any) -> list[str]:
    text = str(value or "").translate(str.maketrans({"ø": "o", "Ø": "O", "å": "a", "Å": "A", "æ": "ae", "Æ": "AE"}))
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().casefold()
    return [token for token in re.findall(r"[a-z0-9]+", text) if token not in LEGAL_AND_GENERIC and len(token) > 1]


def _structured_names(value: Any) -> list[str]:
    names: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"name", "legalName", "alternateName"} and isinstance(child, str):
                names.append(child)
            else:
                names.extend(_structured_names(child))
    elif isinstance(value, list):
        for child in value:
            names.extend(_structured_names(child))
    return names


PARKED_OR_INACTIVE_PATTERNS = [
    # Explicit parking / registrar holding
    r"is parked",
    r"parked free",
    r"parked courtesy",
    r"parked at",
    r"parked with",
    r"this domain is parked",
    r"domain has been registered",
    r"domain is registered",
    r"domenet er parkert",
    r"er parkert hos",
    r"domeneshop",
    r"domainnameshop",
    r"hugedomains",
    r"sedo",
    r"dan\.com",
    r"afternic",
    r"godaddy",
    r"namecheap",
    r"domain parking",
    r"parking-lander",
    r"eieren har forel.pig ikke noe aktivt nettsted",
    r"does not have an active website",
    r"her flytter snart en ny gjest",
    r"siden er under opprettelse",
    r"parkert-su",
    r"webit\.no",
    r"find the best information and most relevant links",
    r"has been informing visitors",
    # Domain for sale / rent
    r"domain is for sale",
    r"domain for sale",
    r"this domain may be for sale",
    r"inquire about this domain",
    r"buy this domain",
    r"for rent/sell",
    r"for rent",
    r"for sale",
    r"til salgs",
    r"dette domenet er til salgs",
    r"til leie",
    r"dette domenet er til leie",
    r"domain for rent",
    r"kj.p dette domenet",
    # Under construction / maintenance
    r"under construction",
    r"website under construction",
    r"coming soon",
    r"kommer snart",
    r"under oppbygging",
    r"under utvikling",
    r"under konstruksjon",
    r"arbeid p.g.r",
    r"maintenance mode",
    r"we\'ll be back soon",
    r"your browser does not support frames",
    # Domain reserved / holding / hosters
    r"domain reserved",
    r"domain is reserved",
    r"domain is now reserved",
    r"strato",
    r"no content has been uploaded",
    r"keine inhalte hinterlegt",
    r"inget inneh.ll",
    # Technical fatal error / crash dumps
    r"fatal error",
    r"uncaught valueerror",
    r"uncaught exception",
    r"uncaught error",
    r"parse error",
    r"syntax error",
    r"database error",
    r"error establishing a database connection",
]
PARKED_REGEX = re.compile("|".join(f"(?:{p})" for p in PARKED_OR_INACTIVE_PATTERNS), re.IGNORECASE)


def classify_site_liveness(
    title: str,
    desc: str,
    text: str,
    url: str,
    frame_urls: list[str] | None = None,
) -> tuple[str, str | None]:
    combined = f"{title or ''} {desc or ''} {text or ''} {url or ''}"
    m = PARKED_REGEX.search(combined)
    if m:
        return "inactive_domain", f"Detected parked/inactive/for-sale marker: '{m.group(0)}'"

    for f_url in (frame_urls or []):
        f_m = PARKED_REGEX.search(f_url)
        if f_m:
            return "inactive_domain", f"Frame target matches parking/for-sale marker: '{f_m.group(0)}'"

    parsed = urllib.parse.urlparse(url or "")
    hostname = (parsed.hostname or "").lower()
    clean_host = hostname.removeprefix("www.")
    clean_title = (title or "").lower().strip().removeprefix("www.")
    is_title_just_domain = clean_title in (clean_host, clean_host + "/", f"http://{clean_host}", f"https://{clean_host}")

    if (not title or is_title_just_domain) and len((text or "").strip()) < 50:
        return "inactive_domain", f"Empty stub or title is merely domain hostname ({len((text or '').strip())} chars text)"

    return "active", None


def assess_website_identity(profile: dict[str, Any]) -> dict[str, Any]:
    website = profile.get("evidence", {}).get("website", {})
    value = website.get("value") or {}
    core = _tokens(profile.get("name"))
    url = value.get("final_url") or website.get("source_url") or profile.get("website") or ""
    parsed_url = urllib.parse.urlparse(url)
    hostname = (parsed_url.hostname or "").lower()
    is_dot_no = not hostname or hostname.endswith(".no") or ".no/" in url
    path = parsed_url.path or ""

    structured_names = _structured_names(value.get("structured_organisations") or [])
    rendered = value.get("js_fallback") or {}
    homepage_identity_parts = [
        value.get("title"), value.get("description"), value.get("identity_text_excerpt"), hostname, *structured_names,
        rendered.get("title"),
    ]
    candidate_parts = [
        *homepage_identity_parts, value.get("main_text_excerpt"),
        *[page.get("title") for page in value.get("pages", [])],
        *[page.get("main_text_excerpt") for page in value.get("pages", [])],
        *[page.get("identity_text_excerpt") for page in value.get("pages", [])],
    ]
    candidate_parts.append(rendered.get("main_text_excerpt"))
    candidate_text = " ".join(str(part or "") for part in candidate_parts)
    homepage_candidate_text = " ".join(str(part or "") for part in [*homepage_identity_parts, value.get("main_text_excerpt"), rendered.get("main_text_excerpt")])
    normalized_candidate_text = " ".join(_tokens(candidate_text))
    candidate_tokens = set(_tokens(candidate_text))
    org_digits = re.sub(r"\D", "", str(profile.get("organisation_number") or ""))
    compact_candidate = re.sub(r"\D", "", candidate_text)
    compact_homepage_candidate = re.sub(r"\D", "", homepage_candidate_text)
    overlap = sorted(set(core) & candidate_tokens)
    ratio = len(overlap) / len(set(core)) if core else 0.0

    # 1. Liveness check: catch parked, under-construction, for-sale, and empty stubs
    frame_urls = value.get("frame_urls") or []
    liveness_status, liveness_reason = classify_site_liveness(
        value.get("title") or "",
        value.get("description") or "",
        value.get("main_text_excerpt") or "",
        url,
        frame_urls,
    )
    if liveness_status != "active":
        return {
            "status": "inactive_domain",
            "score": 0.1,
            "publishable": False,
            "liveness_status": "inactive_domain",
            "legal_name_tokens": core,
            "matched_tokens": overlap,
            "reasons": [liveness_reason or "Captured page is a parked, for-sale, or under-construction placeholder"],
            "method": "deterministic_name_org_evidence_v3",
        }

    normalized_raw = unicodedata.normalize("NFKD", candidate_text).encode("ascii", "ignore").decode().casefold()
    core_phrase = " ".join(core)
    text_phrase = " ".join(_tokens(homepage_candidate_text))
    contiguous_name_match = bool(core_phrase and core_phrase in text_phrase)
    homepage_token_sets = [set(_tokens(part)) for part in homepage_identity_parts if part]
    exact_homepage_name = bool(core and any(set(core).issubset(tokens) for tokens in homepage_token_sets))
    substantive_homepage = len(str(value.get("main_text_excerpt") or "").strip()) >= 100
    is_business_sports_club = bool(re.search(r"(?:^|\s)B\.?\s*I\.?\s*L\.?(?:\s|$)", str(profile.get("name") or ""), re.I))

    host_clean = hostname.removeprefix("www.")
    host_slug = host_clean.split(".")[0].replace("-", "")
    core_compact = "".join(core)
    exact_domain_slug = bool(core_compact and len(core_compact) >= 4 and host_slug == core_compact)

    # 2. Norwegian Grounding check for non-.no domains
    has_org_nr = bool(org_digits and org_digits in compact_homepage_candidate)
    municipality = (profile.get("municipality") or "").strip().lower()
    has_municipality = bool(municipality and len(municipality) >= 4 and municipality in normalized_raw)
    norwegian_markers = ("norge", "norway", "+47", "organisasjonsnummer", "org.nr", "kontakt oss", "om oss", "apningstider", "tlf:", "kulturkafe")
    has_norwegian_text = any(nm in normalized_raw for nm in norwegian_markers) or any(c in candidate_text for c in "æøåÆØÅ")
    has_norwegian_path = path.startswith("/no") or "/no/" in path or path.endswith("/no")

    if not is_dot_no:
        if not (has_org_nr or has_municipality or has_norwegian_text or has_norwegian_path):
            return {
                "status": "unverified_foreign_domain",
                "score": 0.2,
                "publishable": False,
                "liveness_status": "unverified_foreign_domain",
                "legal_name_tokens": core,
                "matched_tokens": overlap,
                "reasons": [f"Generic TLD '{hostname}' lacks verifiable Norwegian company anchor (no org nr, municipality, or Norwegian presence)"],
                "method": "deterministic_name_org_evidence_v3",
            }

    # 3. Acronym collision guard (e.g. 2-3 letter names like VTO AS vs vto.no)
    if len(core) == 1 and len(core[0]) <= 3:
        if not (has_org_nr or (has_municipality and contiguous_name_match)):
            return {
                "status": "ambiguous_acronym",
                "score": 0.3,
                "publishable": False,
                "liveness_status": "ambiguous_acronym",
                "legal_name_tokens": core,
                "matched_tokens": overlap,
                "reasons": [f"Short acronym domain '{hostname}' lacks org nr or municipality match (risk of unrelated company collision)"],
                "method": "deterministic_name_org_evidence_v3",
            }

    reasons = []
    if is_business_sports_club and "bedriftsidrett" not in normalized_candidate_text and "b i l" not in normalized_candidate_text:
        score = 0.3
        reasons.append("business sports-club entity points to the operating company's site without club evidence")
    elif has_org_nr:
        score = 1.0
        reasons.append("exact organisation number appears in homepage identity evidence")
    elif len(core) >= 2 and exact_homepage_name and (is_dot_no or has_norwegian_text or has_norwegian_path):
        score = 0.95
        reasons.append("all normalized legal-name tokens appear together in homepage identity evidence")
    elif contiguous_name_match and (exact_domain_slug or exact_homepage_name) and (is_dot_no or has_norwegian_text or has_norwegian_path):
        score = 0.95
        reasons.append("contiguous legal name appears in homepage text with matching brand domain")
    elif exact_domain_slug and is_dot_no and (has_norwegian_text or has_municipality or substantive_homepage):
        score = 0.95
        reasons.append("exact .no domain slug matches legal name with Norwegian context")
    elif len(core) == 1 and exact_homepage_name and substantive_homepage and is_dot_no:
        score = 0.95
        reasons.append("single distinctive legal-name token appears in homepage identity evidence with substantive content")
    elif ratio >= 0.75 and len(overlap) >= 2 and is_dot_no:
        score = 0.85
        reasons.append("most legal-name tokens appear, but exact identity is incomplete")
    elif ratio >= 0.5 and len(overlap) >= 2:
        score = 0.65
        reasons.append("partial legal-name overlap only")
    else:
        score = 0.3
        reasons.append("registry-linked URL lacks strong exact-entity identity evidence")

    status = "exact" if score >= 0.9 else "review" if score >= 0.8 else "related_or_uncertain"
    return {
        "status": status,
        "score": score,
        "publishable": status == "exact",
        "liveness_status": "active",
        "legal_name_tokens": core,
        "matched_tokens": overlap,
        "reasons": reasons,
        "method": "deterministic_name_org_evidence_v3",
    }


def assess_social_identity(profile: dict[str, Any], link: dict[str, str]) -> dict[str, Any]:
    core = _tokens(profile.get("name"))
    parsed = urllib.parse.urlparse(link.get("url") or "")
    handle_text = urllib.parse.unquote(parsed.path)
    handle_compact = "".join(_tokens(handle_text))
    matched = [token for token in core if token in handle_compact]
    core_compact = "".join(core)
    ratio = len(set(matched)) / len(set(core)) if core else 0.0
    if core_compact and core_compact in handle_compact:
        score = 0.98
        reason = "normalized legal-name sequence appears in the social handle"
    elif len(core) == 1 and matched:
        score = 0.95
        reason = "single distinctive legal-name token appears in the social handle"
    elif ratio >= 0.75 and len(set(matched)) >= 2:
        score = 0.9
        reason = "most legal-name tokens appear in the social handle"
    else:
        score = 0.3
        reason = "social handle lacks strong exact-entity name evidence"
    return {
        **link,
        "identity_score": score,
        "publishable": score >= 0.9,
        "matched_tokens": matched,
        "reason": reason,
        "method": "deterministic_social_handle_identity_v1",
    }


def apply_website_identity_gate(profile: dict[str, Any], website: dict[str, Any]) -> dict[str, Any]:
    if website.get("status") != "available":
        return {"website": website, "assessment": None, "quarantined_social_links": 0}
    temporary_profile = {**profile, "evidence": {**profile.get("evidence", {}), "website": website}}
    value = website.get("value") or {}
    assessment = assess_website_identity(temporary_profile)
    value["identity_assessment"] = assessment
    original = list(value.get("discovered_social_links") or value.get("social_links") or [])
    value["discovered_social_links"] = original
    social_assessments = [assess_social_identity(profile, link) for link in original]
    value["social_link_assessments"] = social_assessments
    value["social_links"] = [
        {"platform": item["platform"], "url": item["url"]}
        for item in social_assessments
        if assessment["publishable"] and item["publishable"]
    ]
    website["value"] = value
    return {
        "website": website,
        "assessment": assessment,
        "quarantined_social_links": len(original) - len(value["social_links"]),
    }
