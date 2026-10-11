"""Regression tests for citation mapping and methodology (P0.1, P0.3)."""
from vendorlens import brief


def _assessment():
    return {
        "domain": "x.example", "score": 50, "band": "MEDIUM",
        "signals": [
            {"signal": "certificate_history", "weight": -6, "detail": "certs",
             "layer": "real & established", "verification": "single_source",
             "sources": ["demo: canned crt.sh response", "shared src"]},
            {"signal": "urlscan_malicious", "weight": 40, "detail": "bad scans",
             "layer": "threat & reputation", "verification": "single_source",
             "sources": ["demo: canned urlscan response"]},
        ],
        "sources": sorted(["demo: canned urlscan response",
                           "demo: canned crt.sh response", "shared src"]),
        "could_not_verify": [], "notes": [], "re_registered": False,
    }


def test_every_citation_resolves_to_that_signals_own_source():
    md = brief.render(_assessment(), {}, {"run_id": "t", "retries": {}})
    idx = {s: i + 1 for i, s in enumerate(_assessment()["sources"])}
    crt, url, shared = (idx["demo: canned crt.sh response"],
                        idx["demo: canned urlscan response"],
                        idx["shared src"])
    cert_row = next(l for l in md.splitlines() if "certificate_history" in l)
    url_row = next(l for l in md.splitlines() if "urlscan_malicious" in l)
    assert f"[{crt}]" in cert_row and f"[{shared}]" in cert_row
    assert f"[{url}]" not in cert_row, "cert signal must not cite urlscan"
    assert f"[{url}]" in url_row
    assert f"[{crt}]" not in url_row, "urlscan signal must not cite crt.sh"


def test_sources_list_numbers_match_citations():
    a = _assessment()
    md = brief.render(a, {}, {"run_id": "t", "retries": {}})
    for n, src in enumerate(a["sources"], 1):
        assert f"[{n}]" in md
        # the source string appears in the rendered list
        assert src in md


def test_methodology_derived_from_findings():
    findings = {
        "rdap_lookup": {"ok": True, "data": {}, "sources": []},
        "ct_logs": {"ok": False, "error": "502 Bad Gateway", "sources": []},
    }
    md = brief.render(_assessment(), findings,
                      {"run_id": "t", "retries": {"s4": 2}})
    method = next(l for l in md.splitlines() if "step-by-step OSINT" in l)
    assert "2 tools" in method
    assert "rdap_lookup" in method and "ct_logs" in method
    assert "1 succeeded and 1 failed" in method
    assert "1 step(s) failed transiently and recovered" in method


def test_no_retry_clause_when_no_retries():
    md = brief.render(_assessment(), {}, {"run_id": "t", "retries": {"s1": 1}})
    method = next(l for l in md.splitlines() if "step-by-step OSINT" in l)
    assert "No step needed a retry" in method
