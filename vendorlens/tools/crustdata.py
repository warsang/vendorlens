"""Crustdata company/people enrichment.

API: https://www.crustdata.com/api-documentation
Auth: Authorization: Token <CRUSTDATA_API_KEY>
Free tier for the hackathon: 5,000 credits with promo code NEATLOGS-OCT2026.

Endpoint paths follow Crustdata's screener API; every call is wrapped so any
failure degrades gracefully (the agent records the miss and continues with
the other tools). In --demo mode, canned data is returned instead.
"""
from __future__ import annotations

import os

import httpx

NAME = "crustdata_enrich"
DESCRIPTION = (
    "Look up a company by domain: legal name, location, headcount, "
    "founding year, LinkedIn, key people. Returns structured firmographics."
)
BASE = "https://api.crustdata.com"

DEMO_DATA = {
    "company_name": "Acme Cloud Services Ltd",
    "domain": "acme-cloud-services.example",
    "location": "Austin, TX, USA",
    "headcount": "11-50",
    "founded": 2024,
    "linkedin_url": "https://www.linkedin.com/company/acme-cloud-services",
    "description": "Cloud cost optimization platform for startups.",
    "key_people": [{"name": "Jane Doe", "title": "CEO"}],
    "found": False,
    "_demo": True,
}


async def run(args: dict, ctx: dict) -> dict:
    domain = args["domain"]
    if ctx.get("demo"):
        data = dict(DEMO_DATA)
        data["domain"] = domain
        return {"ok": True, "data": data,
                "sources": ["demo: canned Crustdata response"]}
    key = os.environ.get("CRUSTDATA_API_KEY", "").strip()
    if not key:
        return {"ok": False, "error": "CRUSTDATA_API_KEY not set",
                "sources": []}
    headers = {"Authorization": f"Token {key}",
               "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post(
                f"{BASE}/screener/company/search",
                headers=headers,
                json={"filters": {"company_website_domain": [domain]},
                      "page": 1},
            )
            r.raise_for_status()
            hits = r.json().get("companies") or r.json().get("results") or []
            if not hits:
                return {"ok": True, "data": {"found": False},
                        "sources": [f"{BASE}/screener/company/search"]}
            top = hits[0]
            return {"ok": True, "data": {
                "found": True,
                "company_name": top.get("company_name"),
                "location": top.get("company_location") or top.get("location"),
                "headcount": top.get("headcount") or top.get("company_size"),
                "founded": top.get("founded_year") or top.get("year_founded"),
                "linkedin_url": top.get("linkedin_company_url"),
                "description": (top.get("company_description") or "")[:500],
            }, "sources": [f"{BASE}/screener/company/search"]}
    except Exception as exc:  # noqa: BLE001 - degrade, never crash the agent
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                "sources": []}
