"""Certificate transparency subdomains and cert history via crt.sh (no key).

A real, verifiable business tends to have a long certificate history and a
handful of stable subdomains (api, www, mail, app). A domain that only ever
had one certificate, issued last week, is weak evidence of an established
company.
"""
from __future__ import annotations

NAME = "ct_logs"
DESCRIPTION = ("Query certificate transparency logs for a domain: certificate "
               "count, earliest issuance date, and distinct subdomains. Long "
               "history and multiple subdomains indicate an established "
               "organisation. Keyless.")
_MAX_BYTES = 20_000_000


def _parse(entries: list) -> dict:
    certs = set()
    names = set()
    issuers = set()
    earliest = latest = None
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        cid = entry.get("id")
        if cid is not None:
            certs.add(cid)
        for raw in str(entry.get("name_value") or "").split("\n"):
            n = raw.strip().lower().lstrip("*.")
            if n:
                names.add(n)
        cn = str(entry.get("common_name") or "").strip().lower().lstrip("*.")
        if cn:
            names.add(cn)
        iss = str(entry.get("issuer_name") or "")
        for part in (p.strip() for p in iss.split(",")):
            if part.upper().startswith(("O=", "CN=")):
                issuers.add(part[2:])
        for key, store in (("not_before", "earliest"), ("not_after", "latest")):
            val = entry.get(key)
            if isinstance(val, str) and val:
                if store == "earliest":
                    earliest = val if earliest is None or val < earliest else earliest
                else:
                    latest = val if latest is None or val > latest else latest
    return {
        "cert_count": len(certs) or len(entries),
        "earliest_cert": earliest,
        "latest_cert": latest,
        "subdomain_count": len(names),
        "issuers": sorted(issuers)[:6],
    }


async def run(args: dict, ctx: dict) -> dict:
    domain = args["domain"]
    if ctx.get("demo"):
        from . import demo_data
        data, src = demo_data.for_tool(ctx.get("scenario"), NAME)
        data["domain"] = domain
        return {"ok": True, "data": data, "sources": [src]}
    import httpx
    from . import _http
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    try:
        async with httpx.AsyncClient(timeout=120, follow_redirects=True) as c:
            r = await _http.get_with_retry(c, url, timeout=120,
                                           headers={"User-Agent": "VendorLens/0.2"})
        if r.status_code == 404:
            return {"ok": True, "data": {"cert_count": 0, "subdomain_count": 0},
                    "sources": [f"crt.sh:{domain}"]}
        r.raise_for_status()
        if len(r.content) > _MAX_BYTES:
            return {"ok": False,
                    "error": f"crt.sh response too large ({len(r.content)} bytes)",
                    "sources": []}
        import json
        text = r.text.strip()
        entries = json.loads(text) if text else []
        if not isinstance(entries, list):
            entries = []
        return {"ok": True, "data": _parse(entries),
                "sources": [f"crt.sh:{domain}"]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                "sources": []}
