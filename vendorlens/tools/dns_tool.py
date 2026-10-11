"""DNS lookup: A, MX, TXT records via dnspython.

Prefer the keyless ``doh_dns`` tool on serverless/restricted networks; this
raw UDP/53 resolver is kept for local runs and corroboration.
"""
from __future__ import annotations

import dns.resolver

NAME = "dns_lookup"
DESCRIPTION = ("Resolve A, MX and TXT records for a domain. Missing MX or "
               "suspicious TXT patterns feed risk signals. Needs UDP/53.")


async def run(args: dict, ctx: dict) -> dict:
    domain = args["domain"]
    if ctx.get("demo"):
        from . import demo_data
        data, src = demo_data.for_tool(ctx.get("scenario"), NAME)
        data["domain"] = domain
        return {"ok": True, "data": data, "sources": [src]}
    out: dict = {}
    try:
        res = dns.resolver.Resolver()
        res.lifetime = 8
        for rtype in ("A", "MX", "TXT"):
            try:
                ans = res.resolve(domain, rtype)
                vals = sorted({str(r).strip('"') for r in ans})
                out[rtype] = vals
            except Exception:
                out[rtype] = []
        return {"ok": True, "data": out,
                "sources": [f"dns:{rtype} {domain}" for rtype in out]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                "sources": []}
