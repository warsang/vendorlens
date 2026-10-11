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

    f = findings.get("rdap_lookup", {})
    if f.get("ok"):
        data = f.get("data") or {}
        if data.get("found") is False:
            add("domain_unregistered", 40,
                "No RDAP registration record exists for this domain. "
                "It is not a registered domain at all.",
                f.get("sources", []))
        else:
            age = data.get("age_days")
            if age is not None:
                if age < 30:
                    add("domain_registered_days_ago", 35,
                        f"Domain registered only {age} days ago.",
                        f.get("sources", []))
                elif age < 90:
                    add("domain_very_young", 30,
                        f"Domain registered {age} days ago (< 90 days).",
                        f.get("sources", []))
                elif age < 365:
                    add("domain_young", 12,
                        f"Domain registered {age} days ago (< 1 year).",
                        f.get("sources", []))
                elif age > 1460:
                    add("domain_well_established", -12,
                        f"Domain registered {age} days ago "
                        f"(over 4 years of history).",
                        f.get("sources", []))
            locked = [s for s in (data.get("status") or [])
                      if "prohibited" in str(s).lower()]
            if not locked and data.get("registrar"):
                add("domain_status_unlocked", 4,
                    f"Domain status "
                    f"({', '.join(data.get('status') or []) or 'none'}) does not "
                    f"include a client transfer lock at {data.get('registrar')}.",
                    f.get("sources", []))

    f = findings.get("doh_dns", {})
    if f.get("ok"):
        data = f.get("data") or {}
        statuses = data.get("statuses") or {}
        nxdomain = any(v == 3 for v in statuses.values())
        if nxdomain or statuses.get("A") == 3:
            add("domain_does_not_resolve", 30,
                "The domain does not resolve (NXDOMAIN). A vendor domain "
                "that does not exist cannot be a business you pay.",
                f.get("sources", []))
        else:
            if not data.get("A"):
                add("no_a_records", 15,
                    "No A records: the domain does not point at a web server.",
                    f.get("sources", []))
            if not data.get("MX"):
                add("no_mx_records", 10,
                    "No MX records: the domain cannot receive email; unusual "
                    "for a real business.",
                    f.get("sources", []))
            if "TXT" in data:
                txt = " ".join(data.get("TXT") or []).lower()
                if txt and "v=spf1" not in txt:
                    add("no_spf_record", 6,
                        "No SPF record published for the domain.",
                        f.get("sources", []))

    f = findings.get("ct_logs", {})
    if f.get("ok"):
        data = f.get("data") or {}
        certs = data.get("cert_count") or 0
        if certs == 0:
            add("no_certificate_history", 12,
                "No public certificate history. Real services leave a "
                "certificate-transparency trail; an absence is weak evidence "
                "of an operating business.",
                f.get("sources", []))
        else:
            subs = data.get("subdomain_count") or 0
            add("certificate_history", -6,
                f"{certs} certificate(s) in transparency logs covering "
                f"{subs} name(s).",
                f.get("sources", []))
            earliest = data.get("earliest_cert")
            if isinstance(earliest, str) and earliest[:4].isdigit():
                year = int(earliest[:4])
                from datetime import datetime, timezone
                if year <= datetime.now(timezone.utc).year - 3:
                    add("certificate_history_long", -8,
                        f"Certificates publicly logged since {year} "
                        f"(more than three years of continuity).",
                        f.get("sources", []))
            if certs <= 1 and subs <= 1:
                add("single_certificate_only", 18,
                    "Only one certificate has ever been issued for the domain, "
                    "covering a single name: it looks like a scratch or "
                    "short-lived site, not an established service.",
                    f.get("sources", []))

    f = findings.get("urlscan_reputation", {})
    if f.get("ok"):
        data = f.get("data") or {}
        total = data.get("total_scans") or 0
        malicious = data.get("malicious_scans") or 0
        cats = data.get("categories") or []
        if malicious:
            add("urlscan_malicious", 40,
                f"urlscan.io holds {malicious} of {total} scan verdict(s) "
                f"marked malicious"
                + (f" ({', '.join(cats)})" if cats else "") + ".",
                f.get("sources", []))
        elif cats:
            bad = [c for c in cats if c.lower() in
                   ("phishing", "malware", "malicious", "spam", "scam")]
            if bad:
                add("urlscan_flagged_categories", 25,
                    f"urlscan.io scans of the domain are categorised as "
                    f"{', '.join(bad)}.",
                    f.get("sources", []))
        elif total >= 5:
            add("urlscan_scan_history_clean", -8,
                f"{total} urlscan.io scans on record with no malicious "
                f"verdicts.",
                f.get("sources", []))

    f = findings.get("phishtank_check", {})
    if f.get("ok") and (f.get("data") or {}).get("listed"):
        d = f.get("data") or {}
        n = d.get("matching_entries") or 0
        add("listed_in_phishtank", 55,
            f"The domain is listed in the PhishTank feed of verified "
            f"phishing sites ({n} entr{'y' if n == 1 else 'ies'}).",
            f.get("sources", []))

    f = findings.get("whois_lookup", {})
    if f.get("ok"):
        age = (f.get("data") or {}).get("age_days")
        already = any(s["signal"].startswith("domain_")
                      and ("young" in s["signal"] or "days_ago" in s["signal"])
                      for s in signals)
        if not already and age is not None and age < 90:
            add("very_young_domain", 30,
                f"Domain registered {age} days ago (< 90 days).",
                f.get("sources", []))
        elif not already and age is not None and age < 365:
            add("young_domain", 10,
                f"Domain registered {age} days ago (< 1 year).",
                f.get("sources", []))

    f = findings.get("dns_lookup", {})
    if f.get("ok") and "doh_dns" not in findings:
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

    # Cross-signal reasoning: when independent sources corroborate that the
    # domain is an established, real business, evidence that only comes from a
    # keyword search is discounted. This is the part a phishing detector
    # cannot do, because it looks at one page rather than the whole record.
    corroborated = any(
        s["signal"] in ("established_company", "certificate_history_long",
                        "domain_well_established", "urlscan_scan_history_clean")
        for s in signals)
    if corroborated:
        for s in signals:
            if s["signal"] in ("negative_reports", "scam_phrases") \
                    and s["weight"] > 0:
                s["weight"] = max(1, int(round(s["weight"] * 0.5)))
                s["detail"] += (" (discounted: corroborating registry, "
                                "certificate and firmographic evidence "
                                "outweigh a keyword search hit)")

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
