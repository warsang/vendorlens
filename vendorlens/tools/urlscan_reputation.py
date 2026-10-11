"""Web-scan reputation via the urlscan.io public search API (no key).

Whether a domain has been scanned before, and what verdicts independent
scanners returned, is a reputation signal a phishing detector never produces:
urlscan reports on the whole history of a domain, including verdicts from many
scanners and categories such as "phishing" or "malware".
"""
from __future__ import annotations

NAME = "urlscan_reputation"
DESCRIPTION = ("Search urlscan.io for public scans of a domain: how often it "
               "has been scanned, how many were judged malicious, the worst "
               "verdict score, and the categories seen. Keyless.")


def _summarise(results: list) -> dict:
    total = len(results)
    malicious = 0
    worst = 0
    categories: set[str] = set()
    times = []
    for res in results:
        if not isinstance(res, dict):
            continue
        verdicts = (res.get("verdicts") or {}).get("overall") or {}
        if verdicts.get("malicious"):
            malicious += 1
        score = verdicts.get("score")
        if isinstance(score, (int, float)):
            worst = max(worst, int(score))
        for cat in (res.get("verdicts") or {}).get("engines") or []:
            if isinstance(cat, dict):
                for name in cat.get("categories") or []:
                    categories.add(str(name))
        t = (res.get("task") or {}).get("time")
        if isinstance(t, str):
            times.append(t)
    return {
        "total_scans": total,
        "malicious_scans": malicious,
        "worst_score": worst,
        "categories": sorted(categories)[:8],
        "first_seen": min(times) if times else None,
        "last_seen": max(times) if times else None,
    }


async def run(args: dict, ctx: dict) -> dict:
    domain = args["domain"]
    if ctx.get("demo"):
        from . import demo_data
        data, src = demo_data.for_tool(ctx.get("scenario"), NAME)
        data["domain"] = domain
        return {"ok": True, "data": data, "sources": [src]}
    import httpx
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as c:
            r = await c.get("https://urlscan.io/api/v1/search/",
                            params={"q": f"domain:{domain}"},
                            headers={"User-Agent": "VendorLens/0.2"})
        if r.status_code == 429:
            return {"ok": False, "error": "urlscan rate limit (anonymous tier)",
                    "sources": []}
        r.raise_for_status()
        payload = r.json()
        results = payload.get("results")
        if not isinstance(results, list):
            results = []
        return {"ok": True, "data": _summarise(results),
                "sources": [f"urlscan.io:{domain}"]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                "sources": []}
