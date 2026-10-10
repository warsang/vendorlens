"""DNS lookup: A, MX, TXT records via dnspython."""
from __future__ import annotations

import dns.resolver

NAME = "dns_lookup"
DESCRIPTION = ("Resolve A, MX and TXT records for a domain. "
               "Missing MX or suspicious TXT patterns feed risk signals.")

DEMO_DATA = {
    "A": ["93.184.216.34"],
    "MX": ["mail.acme-cloud-services.example"],
    "TXT": ["v=spf1 include:_spf.example ~all"],
    "_demo": True,
}


async def run(args: dict, ctx: dict) -> dict:
    domain = args["domain"]
    if ctx.get("demo"):
        return {"ok": True, "data": dict(DEMO_DATA),
                "sources": ["demo: canned DNS response"]}
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
