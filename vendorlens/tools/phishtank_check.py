"""Verify a domain against the public PhishTank feed (no key, no account).

PhishTank publishes valid phishing URLs as an open feed. A vendor domain that
appears there is an outright disqualify signal. Matching is on the exact
hostname, because the feed is mostly lookalike domains (amaz0n-style), and a
lookalike is a different (and worse) finding than the real domain.
"""
from __future__ import annotations

import re

NAME = "phishtank_check"
DESCRIPTION = ("Check whether the domain itself appears in the public "
               "PhishTank feed of verified phishing URLs. A listing is a "
               "disqualifying signal. Keyless.")
_FEED = "http://data.phishtank.com/data/online-valid.json"
_MAX_BYTES = 60_000_000
_HOST_RE = re.compile(r'https?://([A-Za-z0-9.\-]+)')


def _hosts_in_feed(text: str, domain: str) -> list[str]:
    """Match on hostnames, not URL substrings: the feed is mostly lookalike
    domains, and a lookalike is a different finding from the real domain."""
    matches = []
    seen = set()
    for host in _HOST_RE.findall(text):
        h = host.lower().rstrip(".")
        if h == domain or h.endswith("." + domain):
            if h not in seen:
                seen.add(h)
                if len(matches) < 5:
                    matches.append(f"{h} (phishtank.com listing)")
    return matches


async def run(args: dict, ctx: dict) -> dict:
    domain = args["domain"]
    if ctx.get("demo"):
        from . import demo_data
        data, src = demo_data.for_tool(ctx.get("scenario"), NAME)
        data["domain"] = domain
        return {"ok": True, "data": data, "sources": [src]}
    import httpx
    from . import _http
    try:
        async with httpx.AsyncClient(timeout=180, follow_redirects=True) as c:
            r = await _http.get_with_retry(
                c, _FEED, timeout=180,
                headers={"User-Agent": "VendorLens/0.2 (due-diligence research)"})
        if r.status_code == 403:
            return {"ok": False,
                    "error": "PhishTank feed refused the anonymous request",
                    "sources": []}
        r.raise_for_status()
        if len(r.content) > _MAX_BYTES:
            return {"ok": False,
                    "error": f"PhishTank feed too large ({len(r.content)} bytes)",
                    "sources": []}
        text = r.text
        matches = _hosts_in_feed(text, domain)
        total = text.count('"phish_id"')
        src = f"phishtank.com (feed of {total})" if total else "phishtank.com"
        if not matches:
            return {"ok": True,
                    "data": {"listed": False, "matching_entries": 0,
                             "sample_urls": [], "feed_entries": total},
                    "sources": [src]}
        return {"ok": True,
                "data": {"listed": True, "matching_entries": len(matches),
                         "sample_urls": matches, "feed_entries": total},
                "sources": [src]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                "sources": []}
