"""Domain registration data via RDAP (rdap.org, no key).

RDAP is the structured successor to WHOIS. It returns the registration event,
the last-changed event, the expiry, the registrar, the domain status and the
nameservers, all as JSON, which makes the registration-age signal far more
reliable than scraping port 43.
"""
from __future__ import annotations

NAME = "rdap_lookup"
DESCRIPTION = ("Look up registration data over RDAP: creation date, last "
               "update, expiry, registrar, status and nameservers. A domain "
               "registered days ago is a classic vendor-scam signal.")

DEMO_DATA = {
    "registered": "created 2024-03-15T00:00:00+00:00",
    "created": "2024-03-15T00:00:00+00:00",
    "age_days": 574,
    "registrar": "Example Registrar, Inc.",
    "expires": "2027-03-15T00:00:00+00:00",
    "status": ["client transfer prohibited"],
    "nameservers": ["ns1.example-registrar.net"],
    "found": True,
    "_demo": True,
}


def _event_date(events: list, action: str):
    for ev in events:
        if not isinstance(ev, dict):
            continue
        if str(ev.get("eventAction", "")).lower() == action:
            date = ev.get("eventDate")
            if isinstance(date, str):
                return date
    return None


def _registrar(entities: list):
    for ent in entities:
        if not isinstance(ent, dict):
            continue
        roles = ent.get("roles") or []
        if "registrar" in [str(r).lower() for r in roles]:
            vcard = ent.get("vcardArray") or []
            if isinstance(vcard, list) and len(vcard) > 1:
                for field in vcard[1]:
                    if isinstance(field, list) and field and field[0] == "fn":
                        return str(field[-1])
    return None


async def run(args: dict, ctx: dict) -> dict:
    domain = args["domain"]
    if ctx.get("demo"):
        data = dict(DEMO_DATA)
        data["domain"] = domain
        return {"ok": True, "data": data,
                "sources": ["demo: canned RDAP response"]}
    import httpx
    from datetime import datetime, timezone
    url = f"https://rdap.org/domain/{domain}"
    try:
        async with httpx.AsyncClient(timeout=25, follow_redirects=True) as c:
            r = await c.get(url, headers={"User-Agent": "VendorLens/0.2"})
        if r.status_code == 404:
            return {"ok": True, "data": {"found": False},
                    "sources": [f"rdap.org:{domain}"]}
        r.raise_for_status()
        payload = r.json()
        created = _event_date(payload.get("events") or [], "registration")
        expires = _event_date(payload.get("events") or [], "expiration")
        changed = _event_date(payload.get("events") or [], "last changed")
        age_days = None
        if created:
            try:
                when = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if when.tzinfo is None:
                    when = when.replace(tzinfo=timezone.utc)
                age_days = (datetime.now(timezone.utc) - when).days
            except Exception:
                age_days = None
        data = {
            "found": True,
            "created": created,
            "last_changed": changed,
            "expires": expires,
            "age_days": age_days,
            "registrar": _registrar(payload.get("entities") or []),
            "status": payload.get("status") or [],
            "nameservers": [
                (ns.get("ldhName") or "")
                for ns in (payload.get("nameservers") or [])
                if isinstance(ns, dict)],
        }
        return {"ok": True, "data": data, "sources": [f"rdap.org:{domain}"]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                "sources": []}
