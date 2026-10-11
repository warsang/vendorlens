"""WHOIS / domain age via python-whois.

Kept for local corroboration; the keyless RDAP tool is preferred where
TCP/43 is blocked.
"""
from __future__ import annotations

from datetime import datetime, timezone

NAME = "whois_lookup"
DESCRIPTION = ("Get domain registration/creation date, registrar and age. "
               "Very young domains are a classic scam signal. Needs TCP/43.")


async def run(args: dict, ctx: dict) -> dict:
    domain = args["domain"]
    if ctx.get("demo"):
        from . import demo_data
        data, src = demo_data.for_tool(ctx.get("scenario"), NAME)
        data["domain"] = domain
        return {"ok": True, "data": data, "sources": [src]}
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
