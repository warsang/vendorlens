"""Web search for scam reports / reviews via DuckDuckGo (no key needed).

Returns raw results; the keyword filtering that decides whether a hit is a
genuine negative report (vendor name present, vendor's own site excluded)
lives in the risk model, which also knows the company name from Crustdata.
"""
from __future__ import annotations

import re
from html import unescape

import httpx

NAME = "web_search_reports"
DESCRIPTION = ("Search the web for scam reports, reviews or complaints about "
               "the vendor. Negative findings feed risk signals with URLs. "
               "Keyless.")


async def run(args: dict, ctx: dict) -> dict:
    domain = args["domain"]
    query = f"{domain} scam reviews complaints"
    if ctx.get("demo"):
        from . import demo_data
        data, src = demo_data.for_tool(ctx.get("scenario"), NAME)
        data["domain"] = domain
        data["query"] = query
        return {"ok": True, "data": data, "sources": [src]}
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post("https://html.duckduckgo.com/html/",
                             data={"q": query},
                             headers={"User-Agent": "VendorLens/0.3"})
            r.raise_for_status()
        results = []
        for m in re.finditer(
                r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>'
                r'.*?<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
                r.text, re.DOTALL):
            url, title, snippet = m.groups()
            results.append({
                "title": unescape(re.sub(r"<.*?>", "", title)).strip(),
                "url": unescape(url),
                "snippet": unescape(re.sub(r"<.*?>", "", snippet)).strip()[:300],
            })
            if len(results) >= 8:
                break
        return {"ok": True, "data": {"query": query, "results": results},
                "sources": [x["url"] for x in results]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                "sources": []}
