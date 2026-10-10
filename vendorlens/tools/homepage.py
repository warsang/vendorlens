"""Homepage fetch + clean text extraction (httpx + trafilatura)."""
from __future__ import annotations

import httpx
import trafilatura

NAME = "fetch_homepage"
DESCRIPTION = ("Fetch the vendor homepage and extract clean readable text "
               "for scam-signal analysis (pressure tactics, vague identity, "
               "too-good-to-be-true pricing).")

DEMO_TEXT = """Acme Cloud Services - Cut your cloud bill by 90% overnight!
Limited offer ends tonight. No company registration number listed.
Contact us on Telegram @acmeclouddeals. Wire transfer only.
Our revolutionary AI does everything, trusted by thousands (reviews coming soon)."""

DEMO_DATA = {
    "url": "https://acme-cloud-services.example/",
    "title": "Acme Cloud Services - Cut your cloud bill by 90%",
    "text": DEMO_TEXT,
    "_demo": True,
}


async def run(args: dict, ctx: dict) -> dict:
    domain = args["domain"]
    if ctx.get("demo"):
        return {"ok": True, "data": dict(DEMO_DATA),
                "sources": ["demo: canned homepage"]}
    url = f"https://{domain}/"
    try:
        async with httpx.AsyncClient(timeout=20,
                                     follow_redirects=True) as c:
            r = await c.get(url, headers={"User-Agent": "VendorLens/0.1"})
            r.raise_for_status()
        text = trafilatura.extract(r.text) or ""
        title = ""
        try:
            from html import unescape
            import re
            m = re.search(r"<title>(.*?)</title>", r.text,
                          re.IGNORECASE | re.DOTALL)
            title = unescape(m.group(1)).strip() if m else ""
        except Exception:
            pass
        return {"ok": True, "data": {
            "url": str(r.url),
            "title": title[:200],
            "text": text[:6000],
        }, "sources": [str(r.url)]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                "sources": []}
