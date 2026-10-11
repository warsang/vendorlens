"""Verification layer (P1.4): corroboration tags and re-registration insight."""
from vendorlens import risk, verify


def _base_signals(*pairs):
    return {"signals": [], "sources": []}


def test_single_source_by_default():
    findings = {"rdap_lookup": {"ok": True, "data": {"found": True,
                "age_days": 40, "status": []},
                "sources": ["rdap"]}}
    a = verify.verify(risk.assess("x.example", findings), findings)
    age = next(s for s in a["signals"] if s["signal"] == "domain_very_young")
    assert age["verification"] == "single_source"


def test_age_corroborated_when_rdap_and_whois_agree():
    findings = {
        "rdap_lookup": {"ok": True, "data": {"found": True, "age_days": 120,
                        "status": []}, "sources": ["rdap"]},
        "whois_lookup": {"ok": True, "data": {"age_days": 130},
                         "sources": ["whois"]},
    }
    a = verify.verify(risk.assess("x.example", findings), findings)
    # a young signal should be corroborated by two tools agreeing
    age = next(s for s in a["signals"] if "young" in s["signal"])
    assert age["verification"] == "corroborated"
    assert set(age["tools"]) >= {"rdap_lookup", "whois_lookup"}


def test_re_registration_contradiction():
    # Registry says the domain is young, but certs go back years: re-registered.
    findings = {
        "rdap_lookup": {"ok": True, "data": {"found": True, "age_days": 60,
                        "status": []}, "sources": ["rdap"]},
        "ct_logs": {"ok": True, "data": {"cert_count": 5, "subdomain_count": 4,
                    "earliest_cert": "2001-01-01"}, "sources": ["crt"]},
    }
    a = verify.verify(risk.assess("x.example", findings), findings)
    assert a["re_registered"] is True
    age = next(s for s in a["signals"] if "young" in s["signal"])
    assert age["verification"] == "contradicted"
    assert any("re-registered" in n for n in a["notes"])


def test_could_not_verify_lists_failed_and_empty():
    findings = {
        "rdap_lookup": {"ok": True, "data": {"found": True, "age_days": 40,
                        "status": []}, "sources": ["rdap"]},
        "crustdata_enrich": {"ok": True, "data": {"found": False},
                             "sources": ["crust"]},
        "ct_logs": {"ok": False, "error": "502 Bad Gateway",
                    "sources": []},
    }
    a = verify.verify(risk.assess("x.example", findings), findings)
    items = {c["item"] for c in a["could_not_verify"]}
    assert "ct_logs" in items          # failed tool
    assert "crustdata_enrich" in items  # ran, produced no signal
    assert "rdap_lookup" not in items   # produced a signal
