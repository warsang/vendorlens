"""Homepage fetch + clean text extraction, with SSRF safeguards (P0.4).

Fetches https://<domain>/ with redirects followed manually so every hop's host
is re-validated (a public page cannot redirect us onto a private address), a
capped response size, and collection of the security-posture evidence the risk
model needs: status, HSTS/CSP headers, privacy/terms/trust/security page links
and the .well-known/security.txt file.
"""
from __future__ import annotations

import httpx
import trafilatura

from ._netguard import normalize_domain, host_is_public, host_from_url

NAME = "fetch_homepage"
DESCRIPTION = ("Fetch the vendor homepage and extract readable text plus "
               "security posture (HSTS/CSP headers, privacy/terms/trust page "
               "links, security.txt) for scam and maturity analysis.")
_MAX_BYTES = 2_000_000
_MAX_REDIRECTS = 5
_SEC_HEADERS = ("strict-transport-security", "content-security-policy",
                "x-content-type-options", "referrer-policy",
                "permissions-policy")
_POLICY_KEYWORDS = {
    "privacy": "privacy",
    "terms": "terms",
    "trust": "trust",
    "security": "security",
}
_UA = {"User-Agent": "VendorLens/0.3 (vendor due-diligence)"}


def _policy_pages(html_text: str) -> list[str]:
    import re
    found: set[str] = set()
    hay = html_text.lower()
    for label in _POLICY_KEYWORDS:
        if re.search(rf'href="[^"]*{label}', hay):
            found.add(label)
    return sorted(found)


def _headers_present(resp) -> list[str]:
    return [h for h in _SEC_HEADERS
            if h in {k.lower() for k in resp.headers.keys()}]


async def _fetch_security_txt(client: httpx.AsyncClient, base_host: str):
    url = f"https://{base_host}/.well-known/security.txt"
    r = await client.get(url, headers=_UA)
    text = r.text or ""
    if r.status_code >= 400 or "contact:" not in text.lower():
        return {"found": False, "contact": []}
    import re
    contacts = [c.strip() for c in
                re.findall(r"(?im)^\s*contact:\s*(.+)$", text)][:4]
    return {"found": True, "contact": contacts or [text.strip()[:120]]}


async def run(args: dict, ctx: dict) -> dict:
    domain = args["domain"]
    if ctx.get("demo"):
        from . import demo_data
        data, src = demo_data.for_tool(ctx.get("scenario"), NAME)
        data["domain"] = domain
        return {"ok": True, "data": data, "sources": [src]}

    host = normalize_domain(domain)
    if not host:
        return {"ok": False, "error": f"invalid domain: {domain!r}",
                "sources": []}
    if not host_is_public(host):
        return {"ok": False,
                "error": f"refusing to fetch a non-public host: {host}",
                "sources": []}

    url = f"https://{host}/"
    try:
        async with httpx.AsyncClient(timeout=20,
                                     follow_redirects=False) as c:
            for _ in range(_MAX_REDIRECTS + 1):
                r = await c.get(url, headers=_UA)
                if r.is_redirect and r.headers.get("location"):
                    nxt = r.headers["location"]
                    joined = str(httpx.URL(url).join(nxt))
                    new_host = host_from_url(joined)
                    if not new_host:
                        return {"ok": False,
                                "error": f"redirect to invalid host: {nxt}",
                                "sources": []}
                    if not host_is_public(new_host):
                        return {"ok": False,
                                "error": f"redirect to non-public host: "
                                         f"{new_host}",
                                "sources": []}
                    path = httpx.URL(joined).path or "/"
                    if httpx.URL(joined).query:
                        path += "?" + str(httpx.URL(joined).query)
                    url = f"https://{new_host}{path}"
                    continue
                break
            r.raise_for_status()
            if len(r.content) > _MAX_BYTES:
                return {"ok": False,
                        "error": f"homepage too large "
                                 f"({len(r.content)} bytes)",
                        "sources": []}
            final_host = host_from_url(str(r.url)) or host
            body = r.text
            text = trafilatura.extract(body) or ""
            title = ""
            try:
                from html import unescape
                import re
                m = re.search(r"<title>(.*?)</title>", body,
                              re.IGNORECASE | re.DOTALL)
                title = unescape(m.group(1)).strip() if m else ""
            except Exception:
                pass
            sec_txt = {"found": False, "contact": []}
            try:
                sec_txt = await _fetch_security_txt(c, final_host)
            except Exception:
                pass
            return {"ok": True, "data": {
                "url": url,
                "final_url": str(r.url),
                "title": title[:200],
                "text": text[:6000],
                "status_code": r.status_code,
                "headers": _headers_present(r),
                "policy_pages": _policy_pages(body),
                "security_txt": sec_txt,
            }, "sources": [str(r.url)]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                "sources": []}
