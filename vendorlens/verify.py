"""Verification layer (P1.4): tag each signal by how well it is corroborated.

Every signal produced by the risk model gets a confidence tag:

  corroborated   two independent tools agree on the underlying fact
  single_source only one tool backs it
  contradicted  two tools disagree (e.g. the registry says the domain is young
                but certificate logs hold years of history, which suggests the
                domain was re-registered: a real due-diligence insight)

It also computes the ``could_not_verify`` set: tools that failed or ran but
produced no signal, so the brief can tell the reader what it did NOT establish.
"""
from __future__ import annotations

from datetime import datetime, timezone

_AGE_SIGNALS = {
    "domain_registered_days_ago", "domain_very_young", "domain_young",
    "very_young_domain", "young_domain", "domain_well_established",
}
_YOUNG_SIGNALS = {
    "domain_registered_days_ago", "domain_very_young", "domain_young",
    "very_young_domain", "young_domain",
}


def _ok(findings, name):
    return bool(findings.get(name, {}).get("ok"))


def _data(findings, name):
    return findings.get(name, {}).get("data") or {}


def verify(assessment: dict, findings: dict) -> dict:
    signals = assessment.get("signals", [])

    rdap_age = _data(findings, "rdap_lookup").get("age_days") if _ok(findings, "rdap_lookup") else None
    whois_age = _data(findings, "whois_lookup").get("age_days") if _ok(findings, "whois_lookup") else None
    earliest = _data(findings, "ct_logs").get("earliest_cert") if _ok(findings, "ct_logs") else None
    cert_year = int(earliest[:4]) if isinstance(earliest, str) and earliest[:4].isdigit() else None

    now_year = datetime.now(timezone.utc).year
    registry_young = any(s["signal"] in _YOUNG_SIGNALS for s in signals)
    certs_old = cert_year is not None and cert_year <= now_year - 3
    re_registered = registry_young and certs_old

    for s in signals:
        name = s["signal"]
        own_tools = list(s.get("tools") or [s.get("tool")])
        tag = "single_source"
        if name in _AGE_SIGNALS:
            if rdap_age is not None and whois_age is not None \
                    and abs(int(rdap_age) - int(whois_age)) <= 45:
                tag, own_tools = "corroborated", ["rdap_lookup", "whois_lookup"]
        if len(set(own_tools)) >= 2:
            tag = "corroborated"
        if name in _AGE_SIGNALS and re_registered:
            tag = "contradicted"
        s["verification"] = tag
        s["tools"] = sorted(set(own_tools))

    signaled_tools = {s.get("tool") for s in signals}
    could_not = []
    for name, res in findings.items():
        if not res.get("ok"):
            could_not.append({"item": name,
                              "reason": f"tool failed: {res.get('error')}"})
        elif name not in signaled_tools:
            could_not.append({"item": name, "reason": "ran, no signal produced"})

    assessment["re_registered"] = re_registered
    assessment["could_not_verify"] = could_not
    notes = assessment.setdefault("notes", [])
    if re_registered and not any("re-registered" in n for n in notes):
        notes.append(
            "Registry age conflicts with certificate history: the domain may "
            "have been re-registered recently; treat the age signal with care.")
    return assessment
