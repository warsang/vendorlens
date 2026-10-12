"""Crustdata company/people enrichment.

API: https://docs.crustdata.com/company-docs/enrichment
Auth: Authorization: Bearer <CRUSTDATA_API_KEY> (+ x-api-version header).
Free tier for the hackathon: credits with promo code NEATLOGS-OCT2026.

Endpoint: POST /company/enrich with {"domains": [...]}. Every call is wrapped
so any failure degrades gracefully (the agent records the miss and continues
with the other tools). A 400/404 means Crustdata cannot match the domain
(e.g. a reserved TLD such as .example): that is a no-record answer, returned
as found=false, not a tool failure. In --demo mode, canned data is returned
instead.
"""
from __future__ import annotations

import os

import httpx

NAME = "crustdata_enrich"
DESCRIPTION = (
    "Look up a company by domain: legal name, location, headcount, "
    "founding year, LinkedIn, key people. Returns structured firmographics "
    "that corroborate a real, established business. Needs a key."
)
BASE = "https://api.crustdata.com"
API_VERSION = "2025-11-01"


def _pick(d: dict, *keys):
    for k in keys:
        if d.get(k) not in (None, "", []):
            return d[k]
    return None


async def run(args: dict, ctx: dict) -> dict:
    domain = args["domain"]
    if ctx.get("demo"):
        from . import demo_data
        data, src = demo_data.for_tool(ctx.get("scenario"), NAME)
        data["domain"] = domain
        return {"ok": True, "data": data, "sources": [src]}
    key = os.environ.get("CRUSTDATA_API_KEY", "").strip()
    if not key:
        return {"ok": False, "error": "CRUSTDATA_API_KEY not set",
                "sources": []}
    headers = {"Authorization": f"Bearer {key}",
               "Content-Type": "application/json",
               "x-api-version": API_VERSION}
    try:
        async with httpx.AsyncClient(timeout=25) as c:
            r = await c.post(
                f"{BASE}/company/enrich",
                headers=headers,
                json={"domains": [domain],
                      "fields": ["basic_info", "headcount", "funding",
                                 "locations", "social_profiles"],
                      "exact_match": True},
            )
            if r.status_code in (400, 404):
                # Crustdata rejects domains it cannot match (e.g. reserved
                # TLDs like .example) with 400: that is a no-record answer,
                # not an outage, so report it like rdap_lookup does. Auth,
                # rate-limit and server errors still surface below.
                return {"ok": True, "data": {"found": False},
                        "sources": [f"{BASE}/company/enrich"]}
            r.raise_for_status()
            payload = r.json()
            entries = payload if isinstance(payload, list) else \
                payload.get("results") or payload.get("data") or []
            match = None
            for entry in entries:
                matches = entry.get("matches") or []
                if matches:
                    match = max(matches,
                                key=lambda m: m.get("confidence_score") or 0)
                    break
            if not match:
                return {"ok": True, "data": {"found": False},
                        "sources": [f"{BASE}/company/enrich"]}
            cd = match.get("company_data") or {}
            basic = cd.get("basic_info") or {}
            loc = cd.get("locations") or {}
            if isinstance(loc, list):
                loc = loc[0] if loc else {}
            return {"ok": True, "data": {
                "found": True,
                "company_name": _pick(basic, "name", "company_name"),
                "location": _pick(loc, "headquarters", "city", "country"),
                "headcount": _pick(basic, "employee_count_range"),
                "founded": _pick(basic, "year_founded"),
                "linkedin_url": _pick(basic, "professional_network_url"),
                "description": str(_pick(basic, "description") or "")[:500],
                "confidence": match.get("confidence_score"),
            }, "sources": [f"{BASE}/company/enrich"]}
    except Exception as exc:  # noqa: BLE001 - degrade, never crash the agent
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                "sources": []}
