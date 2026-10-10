"""WHOIS / domain age via python-whois."""
from __future__ import annotations

from datetime import datetime, timezone

NAME = "whois_lookup"
DESCRIPTION = ("Get domain registration/creation date, registrar and age. "
               "Very young domains are a classic scam signal.")

DEMO_DATA = {
    "registrar": "Example Registrar, Inc.",
    "creation_date": "2024-03-15T00:00:00+00:00",
    "age_days": 574,
    "_demo": True,
}


async def run(args: dict, ctx: dict) -> dict:
    domain = args["domain"]
    if ctx.get("demo"):
        return {"ok": True, "data": dict(DEMO_DATA),
                "sources": ["demo: canned WHOIS response"]}
    try:
        import whois
        w = whois.whois(domain)
        created = w.creation_date
        if isinstance(created, list):
            created = created[0]
        age_days = None
        if created:
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - created).days
        return {"ok": True, "data": {
            "registrar": w.registrar,
            "creation_date": created.isoformat() if created else None,
            "age_days": age_days,
        }, "sources": [f"whois:{domain}"]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                "sources": []}
