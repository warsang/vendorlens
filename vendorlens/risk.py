"""Risk scoring: combine tool outputs into weighted signals with citations.

Every claim in the final brief cites the tool + source that produced it.
Weights are heuristic and documented; the agent shows its work.
"""
from __future__ import annotations

SCAM_PHRASES = [
    "wire transfer", "western union", "crypto only", "no refund",
    "ends tonight", "act now", "limited offer", "guaranteed profit",
    "90% off", "double your money", "telegram @", "whatsapp only",
    "no company registration", "reviews coming soon",
]


def assess(domain: str, findings: dict) -> dict:
    signals: list[dict] = []
    sources: list[str] = []

    def add(name: str, weight: int, detail: str, srcs: list[str]):
        signals.append({"signal": name, "weight": weight,
                        "detail": detail, "sources": srcs})
        sources.extend(srcs)

    f = findings.get("whois_lookup", {})
    if f.get("ok"):
        age = (f.get("data") or {}).get("age_days")
        if age is not None and age < 90:
            add("very_young_domain", 30,
                f"Domain registered {age} days ago (< 90 days).",
                f.get("sources", []))
        elif age is not None and age < 365:
            add("young_domain", 10,
                f"Domain registered {age} days ago (< 1 year).",
                f.get("sources", []))

    f = findings.get("dns_lookup", {})
    if f.get("ok"):
        data = f.get("data") or {}
        if not data.get("MX"):
            add("no_mx_records", 10,
                "No MX records: domain cannot receive email; "
                "unusual for a real business.",
                f.get("sources", []))

    f = findings.get("tls_inspect", {})
    if f.get("ok"):
        data = f.get("data") or {}
        if data.get("self_signed"):
            add("self_signed_cert", 25,
                "TLS certificate is self-signed.", f.get("sources", []))
        elif data.get("days_left") is not None and data["days_left"] < 30:
            add("cert_expiring", 10,
                f"TLS certificate expires in {data['days_left']} days.",
                f.get("sources", []))

    f = findings.get("fetch_homepage", {})
    if f.get("ok"):
        text = ((f.get("data") or {}).get("text") or "").lower()
        hits = [p for p in SCAM_PHRASES if p in text]
        if hits:
            add("scam_phrases", 20,
                f"Homepage contains high-risk phrases: {', '.join(hits[:5])}.",
                f.get("sources", []))

    f = findings.get("web_search_reports", {})
    if f.get("ok"):
        results = (f.get("data") or {}).get("results") or []
        neg = [r for r in results
               if any(w in (r.get("snippet", "") + r.get("title", "")).lower()
                      for w in ("scam", "fraud", "avoid", "complaint",
                                "fake", "1.2/5", "1/5"))]
        if neg:
            add("negative_reports", 25,
                f"{len(neg)} negative report(s) found in web search.",
                [r["url"] for r in neg[:5]])

    f = findings.get("crustdata_enrich", {})
    if f.get("ok") and (f.get("data") or {}).get("found"):
        d = f["data"]
        add("established_company", -20,
            f"Company found in business data: {d.get('company_name')} "
            f"({d.get('location')}, {d.get('headcount')} employees).",
            f.get("sources", []))

    score = max(0, min(100, sum(s["weight"] for s in signals)))
    band = ("LOW" if score < 25 else "MEDIUM" if score < 50
            else "HIGH" if score < 75 else "CRITICAL")
    return {
        "domain": domain,
        "score": score,
        "band": band,
        "signals": signals,
        "sources": sorted(set(sources)),
    }
