"""Risk scoring: combine tool outputs into weighted signals with citations.

Every claim in the final brief cites the tool + source that produced it and is
labelled with a due-diligence *layer*. Weights are heuristic and documented in
docs/scoring.md; the agent shows its work.

Three layers, so a procurement buyer can read the brief as answers to two
questions plus a disqualifier watch:

  real & established  "Is this domain a real, operating business?"
  security posture    "Is this vendor's hygiene mature?"
  threat & reputation  "Are there active abuse/disqualifier signals?"
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

LEGIT = "real & established"
SEC = "security posture"
REP = "threat & reputation"

SCAM_PHRASES = [
    "wire transfer", "western union", "crypto only", "no refund",
    "ends tonight", "act now", "limited offer", "guaranteed profit",
    "90% off", "double your money", "telegram @", "whatsapp only",
    "no company registration", "reviews coming soon",
]

_NEG_KEYWORDS = ("scam", "fraud", "avoid", "complaint", "fake", "swindle",
                 "do not use", "never delivered", "refund", "1.2/5", "1/5",
                 "stole")
_NAME_NOISE = ("ltd", "inc", "llc", "corp", "corporation", "limited",
               "gmbh", "company", "co", "group", "holdings", "technologies",
               "services", "solutions")


def _brand_tokens(domain: str, company_name: str | None) -> set[str]:
    tokens = {t for t in re.findall(r"[a-z0-9]{4,}", domain.lower())}
    if company_name:
        for t in re.findall(r"[a-z]{4,}", company_name.lower()):
            if t not in _NAME_NOISE:
                tokens.add(t)
    return tokens


def _host(url: str) -> str:
    try:
        h = (urlsplit(url).netloc or "").lower()
    except Exception:
        return ""
    return h[4:] if h.startswith("www.") else h


def assess(domain: str, findings: dict) -> dict:
    signals: list[dict] = []
    sources: list[str] = []

    def add(name, weight, detail, srcs, tool, layer):
        signals.append({"signal": name, "weight": weight, "detail": detail,
                        "sources": list(srcs), "tool": tool, "layer": layer})
        sources.extend(srcs)

    # ---- registration / legitimacy (real & established) ----
    f = findings.get("rdap_lookup", {})
    if f.get("ok"):
        data = f.get("data") or {}
        if data.get("found") is False:
            add("domain_unregistered", 40,
                "No RDAP registration record exists for this domain. It is "
                "not a registered domain at all.",
                f.get("sources", []), "rdap_lookup", LEGIT)
        else:
            age = data.get("age_days")
            if age is not None:
                if age < 30:
                    add("domain_registered_days_ago", 35,
                        f"Domain registered only {age} days ago.",
                        f.get("sources", []), "rdap_lookup", LEGIT)
                elif age < 90:
                    add("domain_very_young", 30,
                        f"Domain registered {age} days ago (< 90 days).",
                        f.get("sources", []), "rdap_lookup", LEGIT)
                elif age < 365:
                    add("domain_young", 12,
                        f"Domain registered {age} days ago (< 1 year).",
                        f.get("sources", []), "rdap_lookup", LEGIT)
                elif age > 1460:
                    add("domain_well_established", -12,
                        f"Domain registered {age} days ago (over 4 years of "
                        f"history).",
                        f.get("sources", []), "rdap_lookup", LEGIT)
            locked = [s for s in (data.get("status") or [])
                      if "prohibited" in str(s).lower()]
            if not locked and data.get("registrar"):
                add("domain_status_unlocked", 4,
                    f"Domain status "
                    f"({', '.join(data.get('status') or []) or 'none'}) does "
                    f"not include a client transfer lock at "
                    f"{data.get('registrar')}.",
                    f.get("sources", []), "rdap_lookup", LEGIT)

    # ---- DNS over HTTPS: resolution, mail, email-auth (SPF/DMARC) ----
    f = findings.get("doh_dns", {})
    if f.get("ok"):
        data = f.get("data") or {}
        statuses = data.get("statuses") or {}
        nxdomain = any(v == 3 for v in statuses.values())
        if nxdomain or statuses.get("A") == 3:
            add("domain_does_not_resolve", 30,
                "The domain does not resolve (NXDOMAIN). A vendor domain that "
                "does not exist cannot be a business you pay.",
                f.get("sources", []), "doh_dns", LEGIT)
        else:
            if not data.get("A"):
                add("no_a_records", 15,
                    "No A records: the domain does not point at a web server.",
                    f.get("sources", []), "doh_dns", LEGIT)
            if not data.get("MX"):
                add("no_mx_records", 10,
                    "No MX records: the domain cannot receive email; unusual "
                    "for a real business.",
                    f.get("sources", []), "doh_dns", LEGIT)
            if "TXT" in data:
                txt = " ".join(data.get("TXT") or []).lower()
                if txt and "v=spf1" not in txt:
                    add("no_spf_record", 6,
                        "No SPF record published for the domain.",
                        f.get("sources", []), "doh_dns", SEC)
                elif "v=spf1" in txt:
                    add("spf_record_present", -3,
                        "Domain publishes an SPF record authorising its mail "
                        "senders.",
                        f.get("sources", []), "doh_dns", SEC)
            if "DMARC" in data:
                dmarc = " ".join(data.get("DMARC") or []).lower()
                if "v=dmarc1" not in dmarc:
                    add("no_dmarc_record", 4,
                        "No DMARC policy published: the domain does not "
                        "declare how unauthenticated mail is handled.",
                        f.get("sources", []), "doh_dns", SEC)
                else:
                    m = re.search(r"p\s*=\s*([a-z]+)", dmarc)
                    policy = m.group(1) if m else "none"
                    if policy in ("reject", "quarantine"):
                        add("dmarc_enforced", -3,
                            f"DMARC enforcement is on (p={policy}).",
                            f.get("sources", []), "doh_dns", SEC)
                    else:
                        add("dmarc_policy_none", 2,
                            "DMARC is published but only monitors "
                            f"(p={policy}); a stricter policy is stronger.",
                            f.get("sources", []), "doh_dns", SEC)

    # ---- certificate transparency history (real & established) ----
    f = findings.get("ct_logs", {})
    if f.get("ok"):
        data = f.get("data") or {}
        certs = data.get("cert_count") or 0
        if certs == 0:
            add("no_certificate_history", 12,
                "No public certificate history. Real services leave a "
                "certificate-transparency trail; an absence is weak evidence "
                "of an operating business.",
                f.get("sources", []), "ct_logs", LEGIT)
        else:
            subs = data.get("subdomain_count") or 0
            add("certificate_history", -6,
                f"{certs} certificate(s) in transparency logs covering "
                f"{subs} name(s).",
                f.get("sources", []), "ct_logs", LEGIT)
            earliest = data.get("earliest_cert")
            if isinstance(earliest, str) and earliest[:4].isdigit():
                year = int(earliest[:4])
                from datetime import datetime, timezone
                if year <= datetime.now(timezone.utc).year - 3:
                    add("certificate_history_long", -8,
                        f"Certificates publicly logged since {year} (more "
                        f"than three years of continuity).",
                        f.get("sources", []), "ct_logs", LEGIT)
            if certs <= 1 and subs <= 1:
                add("single_certificate_only", 18,
                    "Only one certificate has ever been issued for the "
                    "domain, covering a single name: it looks like a scratch "
                    "or short-lived site, not an established service.",
                    f.get("sources", []), "ct_logs", LEGIT)

    # ---- web-scan reputation (threat & reputation) ----
    f = findings.get("urlscan_reputation", {})
    if f.get("ok"):
        data = f.get("data") or {}
        total = data.get("total_scans") or 0
        malicious = data.get("malicious_scans") or 0
        cats = data.get("categories") or []
        if malicious:
            add("urlscan_malicious", 40,
                f"urlscan.io holds {malicious} of {total} scan verdict(s) "
                f"marked malicious" + (f" ({', '.join(cats)})" if cats else "")
                + ".",
                f.get("sources", []), "urlscan_reputation", REP)
        elif cats:
            bad = [c for c in cats if c.lower() in
                   ("phishing", "malware", "malicious", "spam", "scam")]
            if bad:
                add("urlscan_flagged_categories", 25,
                    f"urlscan.io scans of the domain are categorised as "
                    f"{', '.join(bad)}.",
                    f.get("sources", []), "urlscan_reputation", REP)
        elif total >= 5:
            add("urlscan_scan_history_clean", -8,
                f"{total} urlscan.io scans on record with no malicious "
                f"verdicts.",
                f.get("sources", []), "urlscan_reputation", REP)

    # ---- PhishTank verified-phishing feed (threat & reputation) ----
    f = findings.get("phishtank_check", {})
    if f.get("ok") and (f.get("data") or {}).get("listed"):
        d = f.get("data") or {}
        n = d.get("matching_entries") or 0
        add("listed_in_phishtank", 55,
            f"The domain is listed in the PhishTank feed of verified "
            f"phishing sites ({n} entr{'y' if n == 1 else 'ies'}).",
            f.get("sources", []), "phishtank_check", REP)

    # ---- raw WHOIS corroboration (real & established) ----
    f = findings.get("whois_lookup", {})
    if f.get("ok"):
        age = (f.get("data") or {}).get("age_days")
        already = any(s["signal"].startswith("domain_")
                      and ("young" in s["signal"] or "days_ago" in s["signal"])
                      for s in signals)
        if not already and age is not None and age < 90:
            add("very_young_domain", 30,
                f"Domain registered {age} days ago (< 90 days).",
                f.get("sources", []), "whois_lookup", LEGIT)
        elif not already and age is not None and age < 365:
            add("young_domain", 10,
                f"Domain registered {age} days ago (< 1 year).",
                f.get("sources", []), "whois_lookup", LEGIT)

    # ---- raw DNS corroboration (real & established) ----
    f = findings.get("dns_lookup", {})
    if f.get("ok") and "doh_dns" not in findings:
        data = f.get("data") or {}
        if not data.get("MX"):
            add("no_mx_records", 10,
                "No MX records: domain cannot receive email; unusual for a "
                "real business.",
                f.get("sources", []), "dns_lookup", LEGIT)

    # ---- TLS hygiene (security posture) ----
    f = findings.get("tls_inspect", {})
    if f.get("ok"):
        data = f.get("data") or {}
        if data.get("self_signed"):
            add("self_signed_cert", 25,
                "TLS certificate is self-signed.",
                f.get("sources", []), "tls_inspect", SEC)
        elif data.get("days_left") is not None and data["days_left"] < 30:
            add("cert_expiring", 10,
                f"TLS certificate expires in {data['days_left']} days.",
                f.get("sources", []), "tls_inspect", SEC)

    # ---- homepage: scam copy + security posture + legal-entity cross-check ----
    home = findings.get("fetch_homepage", {})
    home_text = ((home.get("data") or {}).get("text") or "") if home.get("ok") else ""
    if home.get("ok"):
        f = home
        data = f.get("data") or {}
        text = data.get("text") or ""
        low = text.lower()
        hits = [p for p in SCAM_PHRASES if p in low]
        if hits:
            add("scam_phrases", 20,
                f"Homepage contains high-risk phrases: "
                f"{', '.join(hits[:5])}.",
                f.get("sources", []), "fetch_homepage", REP)
        headers = data.get("headers") or []
        if "strict-transport-security" in headers:
            add("hsts_enabled", -3,
                "Homepage sends HSTS, binding browsers to HTTPS.",
                f.get("sources", []), "fetch_homepage", SEC)
        else:
            add("no_hsts", 2,
                "No HSTS header on the homepage; traffic can be downgraded.",
                f.get("sources", []), "fetch_homepage", SEC)
        if "content-security-policy" in headers:
            add("csp_enabled", -2,
                "Homepage sends a Content-Security-Policy header.",
                f.get("sources", []), "fetch_homepage", SEC)
        pages = data.get("policy_pages") or []
        if "privacy" in pages and "terms" in pages:
            add("privacy_and_terms_pages", -3,
                "Homepage links to both a privacy policy and terms of "
                "service.",
                f.get("sources", []), "fetch_homepage", LEGIT)
        if "trust" in pages or "security" in pages:
            add("trust_page", -2,
                "Homepage links to a trust/security page.",
                f.get("sources", []), "fetch_homepage", SEC)
        sec = data.get("security_txt") or {}
        if isinstance(sec, dict) and sec.get("found"):
            contact = ", ".join(sec.get("contact") or [])[:120]
            add("security_txt_present", -4,
                "Publishes a security.txt contact"
                + (f" ({contact})" if contact else "") + ".",
                f.get("sources", []), "fetch_homepage", SEC)

    # ---- firmographic company record (real & established) ----
    f = findings.get("crustdata_enrich", {})
    company_name = None
    if f.get("ok") and (f.get("data") or {}).get("found"):
        d = f["data"]
        company_name = d.get("company_name")
        add("established_company", -20,
            f"Company found in business data: {company_name} "
            f"({d.get('location')}, {d.get('headcount')} employees).",
            f.get("sources", []), "crustdata_enrich", LEGIT)
        # Legal-entity cross-check: does the recorded company name appear on
        # the site we actually fetched? Corroborates the Crustdata record.
        if company_name and home_text:
            toks = [t for t in re.findall(r"[a-z]{4,}", company_name.lower())
                    if t not in _NAME_NOISE]
            if any(t in home_text.lower() for t in toks):
                add("company_name_on_site", -6,
                    "The registered company name appears on the fetched "
                    "homepage, cross-checking the business record.",
                    list(dict.fromkeys(
                        f.get("sources", []) + home.get("sources", []))),
                    "crustdata_enrich", LEGIT)

    # ---- web-search negative reports (threat & reputation), vendor-scoped ----
    f = findings.get("web_search_reports", {})
    if f.get("ok"):
        results = (f.get("data") or {}).get("results") or []
        brand = _brand_tokens(domain, company_name)
        neg = []
        for r in results:
            blob = (r.get("title", "") + " " + r.get("snippet", "")).lower()
            if not any(w in blob for w in _NEG_KEYWORDS):
                continue
            if not any(t in blob for t in brand):
                continue
            host = _host(r.get("url", ""))
            if host == domain or host.endswith("." + domain):
                continue  # the vendor talking about itself
            neg.append(r)
        if len(neg) >= 2:
            shown = []
            for r in neg[:3]:
                snip = re.sub(r"\s+", " ", r.get("snippet", "")).strip()
                snip = snip[:80] + ("..." if len(snip) > 80 else "")
                shown.append(f"{_host(r.get('url','')) or 'source'}: {snip}")
            add("negative_reports", 25,
                f"{len(neg)} independent negative report(s); e.g. " +
                "; ".join(shown) + ".",
                [r["url"] for r in neg[:5]], "web_search_reports", REP)

    # ---- cross-source corroboration discount (P0.2) ----
    # Only discount keyword-only risk (scam copy, search hits) when at least
    # two INDEPENDENT tools establish the business as real. The explanation
    # names only the evidence that actually fired, so it can never overclaim.
    _CREDIT = {
        "established_company": "the company record",
        "company_name_on_site": "the company record",
        "domain_well_established": "registration age",
        "certificate_history_long": "certificate history",
        "urlscan_scan_history_clean": "a clean scan history",
    }
    hit_signals = [s for s in signals if s["signal"] in _CREDIT]
    tools_behind = {s["tool"] for s in hit_signals}
    if len(tools_behind) >= 2:
        credit = ", ".join(dict.fromkeys(
            _CREDIT[s["signal"]] for s in hit_signals))
        for s in signals:
            if s["signal"] in ("negative_reports", "scam_phrases") \
                    and s["weight"] > 0:
                s["weight"] = max(1, int(round(s["weight"] * 0.5)))
                s["detail"] += (f" (discounted: {credit} corroborate a real "
                                f"business, outweigh a keyword search hit)")

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
