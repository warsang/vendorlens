"""Centralized canned data for --demo runs.

Each scenario tells a coherent, self-consistent story so the scored signals,
the citations and the confidence tags agree with each other. Keeping every
tool's canned payload here (instead of scattered per-tool constants) is what
makes a whole run predictable and honest:

  - "suspicious"    young front, phishing listings, no corroboration  -> HIGH/CRITICAL
  - "legit"         established, clean, strong posture               -> LOW
  - "young_startup" young but real: the hard, borderline case        -> MEDIUM

The default scenario is "suspicious" so a plain `--demo` reproduces the
headline case used in the README and the demo page.
"""
from __future__ import annotations

SUSPICIOUS = {
    "rdap_lookup": {
        "found": True,
        "created": "2026-09-03T00:00:00+00:00",
        "last_changed": "2026-09-03T00:00:00+00:00",
        "expires": "2027-09-03T00:00:00+00:00",
        "age_days": 38,
        "registrar": "Cheap Registrar LLC",
        "status": [],
        "nameservers": ["ns1.cheapregistrar.example", "ns2.cheapregistrar.example"],
        "_demo": True,
    },
    "doh_dns": {
        "A": ["203.0.113.10"],
        "MX": [],
        "NS": ["ns1.cheapregistrar.example", "ns2.cheapregistrar.example"],
        "TXT": ["_verify=9f3c1a"],
        "CNAME": [],
        "DMARC": [],
        "domain": "",
        "statuses": {"A": 0, "MX": 0, "NS": 0, "TXT": 0, "CNAME": 0, "DMARC": 0},
        "_doh": True,
    },
    "tls_inspect": {
        "issuer": "Acme Self-Signed",
        "subject_cn": "acme-cloud-services.example",
        "not_after": "2026-11-01T00:00:00+00:00",
        "days_left": 21,
        "self_signed": True,
        "_demo": True,
    },
    "ct_logs": {
        "cert_count": 1,
        "earliest_cert": "2026-09-05T00:00:00+00:00",
        "latest_cert": "2026-09-05T00:00:00+00:00",
        "subdomain_count": 1,
        "issuers": ["Acme Self-Signed"],
        "_demo": True,
    },
    "urlscan_reputation": {
        "total_scans": 5,
        "malicious_scans": 3,
        "worst_score": 88,
        "categories": ["phishing"],
        "first_seen": "2026-09-20T00:00:00+00:00",
        "last_seen": "2026-10-06T00:00:00+00:00",
        "_demo": True,
    },
    "phishtank_check": {
        "listed": True,
        "matching_entries": 2,
        "sample_urls": [
            "acme-cloud-services.example (phishtank.com listing)",
            "login.acme-cloud-services.example (phishtank.com listing)",
        ],
        "feed_entries": 0,
        "_demo": True,
    },
    "fetch_homepage": {
        "url": "https://acme-cloud-services.example/",
        "final_url": "https://acme-cloud-services.example/",
        "title": "Acme Cloud Services - Cut your cloud bill by 90%",
        "text": ("Acme Cloud Services - Cut your cloud bill by 90% overnight! "
                 "Limited offer ends tonight. Wire transfer only. Contact us on "
                 "Telegram @acmeclouddeals. No company registration number listed."),
        "status_code": 200,
        "policy_pages": [],
        "security_txt": {"found": False, "contact": []},
        "headers": [],
        "_demo": True,
    },
    "web_search_reports": {
        "query": "",
        "results": [
            {"title": "Is acme-cloud-services.example a scam?",
             "url": "https://example-watch.example/acme-cloud-services",
             "snippet": "Acme-cloud-services.example took a wire transfer and "
                        "never delivered. Avoid."},
            {"title": "acme-cloud-services.example complaints",
             "url": "https://example-bureau.example/t/acme-cloud-services",
             "snippet": "Multiple complaints of fraud involving "
                        "acme-cloud-services.example."},
        ],
        "_demo": True,
    },
    "crustdata_enrich": {
        "found": False,
        "_demo": True,
    },
    # Raw-socket tools are not on the default plan but stay available.
    "dns_lookup": {
        "A": ["203.0.113.10"], "MX": [], "TXT": ["_verify=9f3c1a"],
        "_demo": True,
    },
    "whois_lookup": {
        "registrar": "Cheap Registrar LLC",
        "creation_date": "2026-09-03T00:00:00+00:00",
        "age_days": 38,
        "_demo": True,
    },
}

LEGIT = {
    "rdap_lookup": {
        "found": True,
        "created": "2011-03-08T00:00:00+00:00",
        "expires": "2031-03-08T00:00:00+00:00",
        "age_days": 5695,
        "registrar": "MarkMonitor Inc.",
        "status": ["client transfer prohibited", "client delete prohibited"],
        "nameservers": ["ns1.example-cloud-dns.com", "ns2.example-cloud-dns.com"],
        "_demo": True,
    },
    "doh_dns": {
        "A": ["93.184.216.34"],
        "MX": ["mail.acme-cloud-services.example"],
        "NS": ["ns1.example-cloud-dns.com", "ns2.example-cloud-dns.com"],
        "TXT": ["v=spf1 include:_spf.acme-cloud-services.example ~all",
                "google-site-verification=abcd"],
        "CNAME": [],
        "DMARC": ["v=DMARC1; p=reject; rua=mailto:dmarc@acme-cloud-services.example"],
        "domain": "",
        "statuses": {"A": 0, "MX": 0, "NS": 0, "TXT": 0, "CNAME": 0, "DMARC": 0},
        "_doh": True,
    },
    "tls_inspect": {
        "issuer": "Let's Encrypt",
        "subject_cn": "acme-cloud-services.example",
        "not_after": "2026-12-15T00:00:00+00:00",
        "days_left": 65,
        "self_signed": False,
        "_demo": True,
    },
    "ct_logs": {
        "cert_count": 62,
        "earliest_cert": "2015-06-01T00:00:00+00:00",
        "latest_cert": "2026-09-30T00:00:00+00:00",
        "subdomain_count": 14,
        "issuers": ["Let's Encrypt", "Amazon", "DigiCert"],
        "_demo": True,
    },
    "urlscan_reputation": {
        "total_scans": 92,
        "malicious_scans": 0,
        "worst_score": 0,
        "categories": [],
        "first_seen": "2019-02-01T00:00:00+00:00",
        "last_seen": "2026-10-05T00:00:00+00:00",
        "_demo": True,
    },
    "phishtank_check": {
        "listed": False,
        "matching_entries": 0,
        "sample_urls": [],
        "feed_entries": 48211,
        "_demo": True,
    },
    "fetch_homepage": {
        "url": "https://acme-cloud-services.example/",
        "final_url": "https://acme-cloud-services.example/",
        "title": "Acme Cloud Services - proven cloud cost optimization",
        "text": ("Acme Cloud Services Ltd is a cloud cost optimization platform "
                 "trusted by engineering teams worldwide. See our privacy policy "
                 "and security overview. Acme Cloud Services Ltd, Austin TX."),
        "status_code": 200,
        "policy_pages": ["privacy", "terms", "trust", "security"],
        "security_txt": {"found": True,
                         "contact": ["mailto:security@acme-cloud-services.example"]},
        "headers": ["strict-transport-security", "content-security-policy"],
        "_demo": True,
    },
    "web_search_reports": {
        "query": "",
        "results": [
            {"title": "Acme Cloud Services - how to cut cloud spend",
             "url": "https://example-tech-blog.example/acme-review",
             "snippet": "A practical review of Acme Cloud Services cost tooling."},
            {"title": "Acme Cloud Services pricing",
             "url": "https://example-directory.example/acme-cloud-services",
             "snippet": "Pricing tiers for Acme Cloud Services Ltd."},
        ],
        "_demo": True,
    },
    "crustdata_enrich": {
        "found": True,
        "company_name": "Acme Cloud Services Ltd",
        "domain": "acme-cloud-services.example",
        "location": "Austin, TX, USA",
        "headcount": "51-200",
        "founded": 2011,
        "linkedin_url": "https://www.linkedin.com/company/acme-cloud-services",
        "description": "Cloud cost optimization platform for engineering teams.",
        "confidence": 0.98,
        "_demo": True,
    },
    "dns_lookup": {
        "A": ["93.184.216.34"], "MX": ["mail.acme-cloud-services.example"],
        "TXT": ["v=spf1 include:_spf.acme-cloud-services.example ~all"],
        "_demo": True,
    },
    "whois_lookup": {
        "registrar": "MarkMonitor Inc.",
        "creation_date": "2011-03-08T00:00:00+00:00",
        "age_days": 5695,
        "_demo": True,
    },
}

YOUNG_STARTUP = {
    "rdap_lookup": {
        "found": True,
        "created": "2026-06-13T00:00:00+00:00",
        "expires": "2027-06-13T00:00:00+00:00",
        "age_days": 120,
        "registrar": "Name Silos LLC",
        "status": ["client transfer prohibited"],
        "nameservers": ["ns1.newly.example", "ns2.newly.example"],
        "_demo": True,
    },
    "doh_dns": {
        "A": ["198.51.100.7"],
        "MX": [],
        "NS": ["ns1.newly.example", "ns2.newly.example"],
        "TXT": ["v=spf1 include:_spf.newly.example ~all"],
        "CNAME": [],
        "DMARC": [],
        "domain": "",
        "statuses": {"A": 0, "MX": 0, "NS": 0, "TXT": 0, "CNAME": 0, "DMARC": 0},
        "_doh": True,
    },
    "tls_inspect": {
        "issuer": "Let's Encrypt",
        "subject_cn": "newly.example",
        "not_after": "2026-11-02T00:00:00+00:00",
        "days_left": 22,
        "self_signed": False,
        "_demo": True,
    },
    "ct_logs": {
        "cert_count": 6,
        "earliest_cert": "2026-06-15T00:00:00+00:00",
        "latest_cert": "2026-10-01T00:00:00+00:00",
        "subdomain_count": 3,
        "issuers": ["Let's Encrypt"],
        "_demo": True,
    },
    "urlscan_reputation": {
        "total_scans": 4,
        "malicious_scans": 0,
        "worst_score": 0,
        "categories": [],
        "first_seen": "2026-07-01T00:00:00+00:00",
        "last_seen": "2026-10-02T00:00:00+00:00",
        "_demo": True,
    },
    "phishtank_check": {
        "listed": False,
        "matching_entries": 0,
        "sample_urls": [],
        "feed_entries": 0,
        "_demo": True,
    },
    "fetch_homepage": {
        "url": "https://newly.example/",
        "final_url": "https://newly.example/",
        "title": "Newly - join the waitlist",
        "text": ("Newly is building developer tooling. Our privacy policy "
                 "explains what we collect. Newly, pre-launch. No public "
                 "compliance or trust page yet."),
        "status_code": 200,
        "policy_pages": ["privacy"],
        "security_txt": {"found": False, "contact": []},
        "headers": [],
        "_demo": True,
    },
    "web_search_reports": {
        "query": "",
        "results": [
            {"title": "Newly - new devtool startup",
             "url": "https://example-launch.example/newly",
             "snippet": "Newly launched on a product board this month."},
        ],
        "_demo": True,
    },
    "crustdata_enrich": {
        "found": False,
        "_demo": True,
    },
    "dns_lookup": {
        "A": ["198.51.100.7"], "MX": [],
        "TXT": ["v=spf1 include:_spf.newly.example ~all"],
        "_demo": True,
    },
    "whois_lookup": {
        "registrar": "Name Silos LLC",
        "creation_date": "2026-06-13T00:00:00+00:00",
        "age_days": 120,
        "_demo": True,
    },
}

SCENARIOS = {
    "suspicious": SUSPICIOUS,
    "legit": LEGIT,
    "young_startup": YOUNG_STARTUP,
}
DEFAULT = "suspicious"

_SOURCE_LABEL = {
    "rdap_lookup": "demo: canned RDAP response",
    "doh_dns": "demo: canned DoH response",
    "tls_inspect": "demo: canned TLS response",
    "ct_logs": "demo: canned crt.sh response",
    "urlscan_reputation": "demo: canned urlscan response",
    "phishtank_check": "demo: canned PhishTank",
    "fetch_homepage": "demo: canned homepage",
    "web_search_reports": "demo: canned search results",
    "crustdata_enrich": "demo: canned Crustdata response",
    "dns_lookup": "demo: canned DNS response",
    "whois_lookup": "demo: canned WHOIS response",
}


def for_tool(scenario, tool: str):
    """Return (data_dict, source_label) for a tool under a scenario."""
    name = scenario or DEFAULT
    table = SCENARIOS.get(name, SCENARIOS[DEFAULT])
    data = dict(table.get(tool) or {})
    return data, _SOURCE_LABEL.get(tool, f"demo: canned {tool}")
