"""Reliable DNS records over HTTPS via dns.google (no key).

dnspython needs raw UDP/53, which can be unreliable behind an outbound
firewall. DNS-over-HTTPS gives the same A/MX/NS/TXT picture over a single
HTTPS call, which is exactly what the Lambda deployment needs. It also fetches
the DMARC record at ``_dmarc.<domain>`` so the agent can score email
anti-spoofing posture without any extra tool.
"""
from __future__ import annotations

NAME = "doh_dns"
DESCRIPTION = ("Resolve A, MX, NS, TXT, CNAME and the _dmarc TXT record over "
               "HTTPS (DNS-over-HTTPS). A domain that does not resolve at "
               "all, or that has no MX records, is unusual for a real "
               "business. Missing SPF/DMARC weakens email posture. Keyless.")
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
        from . import demo_data
        data, src = demo_data.for_tool(ctx.get("scenario"), NAME)
        data["domain"] = domain
        return {"ok": True, "data": data, "sources": [src]}
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
            # DMARC lives one label below the apex: _dmarc.<domain>
            try:
                r = await c.get(
                    "https://dns.google/resolve",
                    params={"name": f"_dmarc.{domain}", "type": "TXT"},
                    headers={"User-Agent": "VendorLens/0.2"})
                r.raise_for_status()
                dmarc = _answers(r.json())
                statuses["DMARC"] = 0
            except Exception:
                dmarc, statuses["DMARC"] = [], -1
            records["DMARC"] = dmarc
        return {"ok": True,
                "data": dict(records, domain=domain, statuses=statuses,
                             _doh=True),
                "sources": [f"dns.google:{domain}"]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                "sources": []}
