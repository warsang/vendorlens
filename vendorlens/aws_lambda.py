"""AWS Lambda entry point for a live VendorLens investigation.

Served publicly via an API Gateway. Because the endpoint is public by design,
the browser "x-api-key" header is a *public client token* (rate/billing
attribution), NOT authentication. The real protections are external:

  - per-IP request throttling + usage plan on API Gateway
  - a hard daily budget alarm (CloudWatch billing alarm)
  - reserved concurrency on the function (caps blast radius / spend)
  - ALLOWED_ORIGIN pinned to the real demo origin (never "*" in production)

Input is validated to a strict bare public hostname before any tool runs, so a
domain string can never steer a fetch at an internal address (SSRF).

Query: ?<domain|q=><domain or company name>&mode=demo|nollm|live
Returns structured JSON (no raw markdown in the UI path):
  ok, input, domain, mode, run_id,
  verdict {score, band, headline, summary},
  signals[{signal, layer, confidence, weight, detail, sources}],
  sources[], tools[{name, ok, error}],
  homepage_text  (fed to the on-device jev-web verdict model),
  brief_md       (kept for the CLI / archival only)
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import tempfile
import uuid
from pathlib import Path

from . import agent, tracing
from .tools import _netguard

# A company name (not yet a domain) is anything with no dotted TLD; a bare
# domain roughly looks like a dotted hostname. The strict check below
# (_netguard.normalize_domain) is the authoritative gate before any fetch.
_TLD_RE = re.compile(r"\.[a-z]{2,}$")
_STOP_DOMAINS = {
    "facebook.com", "twitter.com", "x.com", "linkedin.com", "instagram.com",
    "youtube.com", "wikipedia.org", "reddit.com", "tiktok.com", "crunchbase.com",
    "github.com", "medium.com", "glassdoor.com", "indeed.com",
}


def _headers(event) -> dict:
    h = event.get("headers") or {}
    return {str(k).lower(): v for k, v in h.items()}


def _authorized(event) -> bool:
    """Public client-token check (defense in depth, NOT auth). If a token is
    configured it must match; origin/referrer, if pinned, must match. When
    neither is configured the endpoint is intentionally open and its real
    protection is external rate limiting + a spend budget."""
    want = os.environ.get("VENDORLENS_API_KEY", "").strip()
    got = str(_headers(event).get("x-api-key", "")).strip()
    if want and got != want:
        return False
    allow = os.environ.get("ALLOWED_ORIGIN", "").strip().rstrip("/")
    if allow:
        src = _headers(event).get("origin") or _headers(event).get("referer") or ""
        if src and not src.startswith(allow):
            return False
    return True


def _resp(code: int, payload: dict) -> dict:
    allow = os.environ.get("ALLOWED_ORIGIN", "").strip().rstrip("/")
    headers = {
        "content-type": "application/json",
        "access-control-allow-headers": "content-type,x-api-key",
        "access-control-allow-methods": "GET,OPTIONS",
    }
    # Never default to a wildcard: echo the configured origin only.
    if allow:
        headers["access-control-allow-origin"] = allow
    return {"statusCode": code, "headers": headers,
            "body": json.dumps(payload)}


def _looks_like_domain(value: str) -> bool:
    return "." in value and bool(_TLD_RE.search(value.lower()))


def _hosts_from_html(html_text: str) -> list[str]:
    import re as _re
    from urllib.parse import unquote, urlsplit
    hosts: list[str] = []
    # ddg wraps outbound links as /l/?uddg=<encoded>, but also emits raw hrefs.
    for m in _re.finditer(r'uddg=([^&"\'>]+)', html_text):
        try:
            u = urlsplit(unquote(m.group(1)))
            if u.netloc:
                hosts.append(u.netloc.lower())
        except Exception:
            pass
    if not hosts:
        for m in _re.finditer(r'href="(https?://[^"]+)"', html_text):
            try:
                u = urlsplit(m.group(1))
                if u.netloc:
                    hosts.append(u.netloc.lower())
            except Exception:
                pass
    cleaned = []
    for h in hosts:
        h = h.split(":")[0]
        if h.startswith("www."):
            h = h[4:]
        if h and h not in cleaned:
            cleaned.append(h)
    return cleaned


def _pick_domain(hosts: list[str], name: str) -> str | None:
    tokens = [t for t in re.findall(r"[a-z0-9]+", name.lower()) if len(t) > 2]
    pool = [h for h in hosts
            if h not in _STOP_DOMAINS
            and "duckduckgo" not in h
            and _looks_like_domain(h)]
    if not pool:
        return None
    key = re.sub(r"[^a-z0-9]", "", name.lower())
    tld_bonus = {"com": 5, "org": 4, "net": 3, "io": 3, "co": 2, "ai": 2}
    # "aboutamazon.com" and "dashboard.stripe.com" are real but they are not
    # where you would verify a counterparty, so prefer the brand apex domain.
    prefixes = ("about", "dashboard", "login", "accounts", "account",
                "support", "help", "careers", "jobs", "www", "app")

    def score(h):
        labels = h.split(".")
        first = labels[0].replace("-", "")
        s = 0.0
        if key and first == key:
            s += 100
        elif key and len(first) >= 3 and key.startswith(first):
            s += 60
        elif key and len(key) >= 6 and first.startswith(key[:6]):
            s += 40
        elif any(t in h for t in tokens):
            s += 20
        s += tld_bonus.get(labels[-1], 0)
        s -= (len(labels) - 2) * 6      # penalty per extra subdomain label
        s -= len(first) * 0.2
        if first in prefixes or any(first.startswith(p) for p in prefixes):
            s -= 8
        return s

    pool.sort(key=score, reverse=True)
    return pool[0]


async def _resolve_company_to_domain(name: str) -> str | None:
    """Best-effort company name -> official domain, without any API key.

    Ranks candidate hosts by how much of the company name they contain, so
    "Acme Cloud" prefers acmecloud.com over the first result on the page.
    """
    import httpx
    for url, data in (
        ("https://lite.duckduckgo.com/lite/", {"q": f"{name} official website"}),
        ("https://html.duckduckgo.com/html/", {"q": f"{name} official website"}),
    ):
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as c:
                r = await c.post(url, data=data,
                                 headers={"User-Agent": "VendorLens/0.3"})
                r.raise_for_status()
            picked = _pick_domain(_hosts_from_html(r.text), name)
            if picked:
                return picked
        except Exception:
            continue
    return None


def _structured(state: dict, domain: str, mode: str, run_id: str,
                user_input: str, resolved_from: str | None) -> dict:
    a = state.get("assessment", {})
    findings = state.get("findings", {})
    signals = [{"signal": s["signal"], "weight": s["weight"],
                "detail": s["detail"], "sources": s.get("sources", []),
                "layer": s.get("layer", ""),
                "confidence": s.get("verification", "")}
               for s in a.get("signals", [])]
    tools = [{"name": name, "ok": bool(res.get("ok")),
              "error": res.get("error")}
             for name, res in findings.items()]
    homepage_text = ""
    try:
        homepage_text = (findings.get("fetch_homepage", {})
                         .get("data", {}).get("text") or "")
    except Exception:
        pass
    retries = state.get("retries", {})
    weighted = sorted(signals, key=lambda s: abs(s["weight"]), reverse=True)
    headline = (f"{a.get('band','?')} risk" if weighted and weighted[0]["weight"] > 0
                else "No strong risk signals found")
    summary = "; ".join(s["detail"] for s in signals[:3]) or \
        "No significant risk signals were detected across the sources checked."
    return {
        "ok": True,
        "input": user_input,
        "domain": domain,
        "resolved_from": resolved_from,
        "mode": mode,
        "run_id": run_id,
        "verdict": {
            "score": a.get("score"),
            "band": a.get("band"),
            "headline": headline,
            "summary": summary,
            "retries": retries,
            "signals_count": len(signals),
            "could_not_verify": a.get("could_not_verify", []),
            "re_registered": a.get("re_registered", False),
        },
        "signals": signals,
        "sources": a.get("sources", []),
        "tools": tools,
        "homepage_text": homepage_text,
        "brief_md": state.get("brief_md", ""),
    }


def lambda_handler(event, context=None):
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    if method == "OPTIONS":
        return _resp(200, {"ok": True})
    if not _authorized(event):
        return _resp(401, {"ok": False, "error": "unauthorized"})

    q = event.get("queryStringParameters") or {}
    raw = (q.get("domain") or q.get("q") or q.get("company") or "").strip()
    mode = (q.get("mode") or "nollm").strip().lower()
    if not raw:
        return _resp(400, {"ok": False, "error": "missing domain or company name"})

    run_id = uuid.uuid4().hex[:8]
    resolved_from = None

    if _looks_like_domain(raw.lower()):
        domain = raw.lower()
    else:
        domain = raw.lower().replace(" ", "")
        if not _looks_like_domain(domain) and "." not in domain:
            # resolve name -> domain in a fresh loop (Lambda has none running)
            guessed = asyncio.run(_resolve_company_to_domain(raw))
            if guessed:
                resolved_from = domain
                domain = guessed
            else:
                return _resp(422, {"ok": False,
                                   "error": f"could not resolve a domain for "
                                            f"'{raw}'. Try the exact domain."})

    # Authoritative SSRF gate: only a strict, public bare hostname is allowed.
    safe = _netguard.normalize_domain(domain)
    if not safe:
        return _resp(422, {"ok": False,
                           "error": f"'{domain}' is not a valid public domain."})
    domain = safe

    try:
        tracing.init_tracing("vendorlens-investigation")
        tracing.set_trace_file(
            Path(tempfile.gettempdir()) / f"trace_{run_id}.jsonl", run_id)
    except Exception:
        pass
    try:
        with tracing.workflow("vendorlens-investigation", domain=domain, mode=mode):
            state = asyncio.run(agent.run_investigation(
                domain, run_id=run_id,
                demo=(mode == "demo"), no_llm=(mode != "live")))
        return _resp(200, _structured(state, domain, mode, run_id,
                                      raw, resolved_from))
    except Exception as exc:  # noqa: BLE001
        return _resp(500, {"ok": False, "error": f"{type(exc).__name__}: {exc}"})
    finally:
        try:
            tracing.flush()
            tracing.shutdown()
        except Exception:
            pass
