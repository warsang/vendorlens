"""Risk scoring: bands, clamping, corroboration, scoping (P0.2, P1.5, P1.6)."""
from vendorlens import risk


def _rdap(age, found=True, status=("client transfer prohibited",),
          src="rdap.org:x"):
    return {"ok": True, "data": {"found": found, "age_days": age,
                                 "status": list(status),
                                 "registrar": "R"}, "sources": [src]}


def _crustdata(found=True, name="Acme Cloud Services Ltd", src="crustdata:x"):
    if found:
        return {"ok": True, "data": {"found": True, "company_name": name,
                                     "location": "Austin", "headcount": "5"},
                "sources": [src]}
    return {"ok": True, "data": {"found": False}, "sources": [src]}


def _ct(certs=6, subs=3, earliest="2015-01-01", src="crt.sh:x"):
    return {"ok": True, "data": {"cert_count": certs,
                                 "subdomain_count": subs,
                                 "earliest_cert": earliest}, "sources": [src]}


def _search(results):
    return {"ok": True, "data": {"results": results},
            "sources": [r["url"] for r in results]}


def _sig(signals, name):
    return next((s for s in signals if s["signal"] == name), None)


def test_clamp_to_100_and_0():
    many_bad = {"phishtank_check": {"ok": True, "data": {"listed": True,
                "matching_entries": 3}, "sources": ["pt"]},
                "urlscan_reputation": {"ok": True, "data": {"total_scans": 9,
                "malicious_scans": 9, "categories": ["phishing"]},
                "sources": ["us"]}}
    a = risk.assess("evil.example", many_bad)
    assert a["score"] <= 100 and a["score"] == max(0, min(100, a["score"]))

    all_good = {"rdap_lookup": _rdap(6000), "crustdata_enrich": _crustdata(),
                "ct_logs": _ct()}
    a2 = risk.assess("good.example", all_good)
    assert a2["score"] >= 0  # negatives offset, floor at 0


def test_band_boundaries():
    assert risk.assess("x", {})["band"] == "LOW"  # 0


def test_negative_weights_offset_positive():
    findings = {"rdap_lookup": _rdap(6000),  # well-established -12
                "crustdata_enrich": _crustdata(),  # -20
                "ct_logs": _ct()}  # -6
    a = risk.assess("good.example", findings)
    assert all(s["weight"] <= 0 for s in a["signals"])
    assert a["score"] == 0 and a["band"] == "LOW"


def test_discount_requires_two_independent_tools():
    # Only ONE corroborating source (cert history). No discount.
    f = {"ct_logs": _ct(certs=20, subs=8, earliest="2012-01-01"),
         "fetch_homepage": {"ok": True, "data": {"text": "wire transfer only",
                            "headers": [], "policy_pages": [],
                            "security_txt": {"found": False}},
                            "sources": ["home"]}}
    a = risk.assess("x.example", f)
    scam = _sig(a["signals"], "scam_phrases")
    assert scam["weight"] == 20
    assert "discounted" not in scam["detail"]


def test_discount_fires_only_names_actual_triggers():
    # Two corroborating tools: rdap age + crustdata company. NOT certificates.
    f = {"rdap_lookup": _rdap(6000),
         "crustdata_enrich": _crustdata(),
         "fetch_homepage": {"ok": True, "data": {"text": "wire transfer only",
                            "headers": [], "policy_pages": [],
                            "security_txt": {"found": False}},
                            "sources": ["home"]}}
    a = risk.assess("x.example", f)
    scam = _sig(a["signals"], "scam_phrases")
    assert scam["weight"] == 10
    assert "discounted" in scam["detail"]
    assert "registration age" in scam["detail"]
    assert "company record" in scam["detail"]
    assert "certificate history" not in scam["detail"]  # never overclaims


def test_negative_reports_requires_vendor_name_and_two_hits():
    # One hit mentions a negative word but NOT the vendor -> ignored.
    one = _search([{"title": "some other company scam",
                    "url": "https://a.example/x", "snippet": "avoid"}])
    a = risk.assess("acme.example", {"web_search_reports": one})
    assert _sig(a["signals"], "negative_reports") is None

    # Two independent hits mention the vendor name -> fires, own domain excluded.
    good = _search([
        {"title": "acme scam", "url": "https://a.example/acme",
         "snippet": "avoid acme"},
        {"title": "acme fraud", "url": "https://b.example/acme",
         "snippet": "acme never delivered"},
        {"title": "acme complaints", "url": "https://acme.example/complaints",
         "snippet": "acme official page"},  # vendor's own site -> excluded
    ])
    a2 = risk.assess("acme.example", {"web_search_reports": good})
    neg = _sig(a2["signals"], "negative_reports")
    assert neg is not None and neg["weight"] == 25
    # snippets are shown
    assert "a.example" in neg["detail"] and "b.example" in neg["detail"]
    # own domain not among cited sources
    assert not any("acme.example/complaints" in s for s in neg["sources"])


def test_company_name_on_site_cross_check():
    home = {"ok": True, "data": {"text": "Acme Cloud Services Ltd build tools",
            "headers": ["strict-transport-security"], "policy_pages": ["privacy",
            "terms"], "security_txt": {"found": True, "contact": ["mailto:s"]}},
            "sources": ["home"]}
    a = risk.assess("x.example", {"crustdata_enrich": _crustdata(),
                                  "fetch_homepage": home})
    assert _sig(a["signals"], "company_name_on_site") is not None
    assert _sig(a["signals"], "established_company") is not None
    # security posture credits
    assert _sig(a["signals"], "hsts_enabled") is not None
    assert _sig(a["signals"], "security_txt_present") is not None
    assert _sig(a["signals"], "privacy_and_terms_pages") is not None


def test_signals_carry_layer_and_tool():
    a = risk.assess("x.example", {"rdap_lookup": _rdap(40)})
    s = _sig(a["signals"], "domain_very_young")
    assert s["layer"] == "real & established"
    assert s["tool"] == "rdap_lookup"
