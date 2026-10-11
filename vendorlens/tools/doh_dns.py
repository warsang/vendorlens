"""Reliable DNS records over HTTPS via dns.google (no key).

dnspython needs raw UDP/53, which can be unreliable behind an outbound
firewall. DNS-over-HTTPS gives the same A/MX/NS/TXT picture over a single
HTTPS call, which is exactly what the Lambda deployment needs.
"""
from __future__ import annotations

NAME = "doh_dns"
DESCRIPTION = ("Resolve A, MX, NS, TXT and CNAME records over HTTPS "
               "(DNS-over-HTTPS). A domain that does not resolve at all, or "
               "that has no MX records, is unusual for a real business.")

DEMO_DATA = {
    "A": ["93.184.216.34"],
    "MX": ["mail.acme-cloud-services.example"],
    "NS": ["ns1.example-registrar.net", "ns2.example-registrar.net"],
    "TXT": ["v=spf1 include:_spf.example ~all"],
    "CNAME": [],
    "_demo": True,
}
_TYPES = ("A", "MX", "NS", "TXT", "CNAME")


def _answers(payload: dict) -> list[str]:
    out = []
    for ans in (payload.get("Answer") or []):
        data = ans.get("data")
        if isinstance(data, str):
            out.append(data.strip().strip('"'))
    return out


async def run(args: dict, ctx: dict) -> dict:
    domain = args["domain"]
    if ctx.get("demo"):
        data = dict(DEMO_DATA)
        data["domain"] = domain
        return {"ok": True, "data": data,
                "sources": ["demo: canned DoH response"]}
    import httpx
    records: dict[str, list[str]] = {}
    statuses: dict[str, int] = {}
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as c:
            for rtype in _TYPES:
                try:
                    r = await c.get(
                        "https://dns.google/resolve",
                        params={"name": domain, "type": rtype},
                        headers={"User-Agent": "VendorLens/0.2"})
                    r.raise_for_status()
                    payload = r.json()
                    statuses[rtype] = int(payload.get("Status", 0))
                    records[rtype] = _answers(payload)
                except Exception:
                    statuses[rtype] = -1
                    records[rtype] = []
        return {"ok": True,
                "data": dict(records, domain=domain, statuses=statuses,
                             _doh=True),
                "sources": [f"dns.google:{domain}"]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                "sources": []}
