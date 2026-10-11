# VendorLens risk brief: acme-cloud-services.example

_Generated 2026-10-11T23:04:03.631693+00:00 by VendorLens (neatHack 2026, team solohackaton). Run ca405a38._

## Verdict: CRITICAL (100/100)

| Signal | Layer | Confidence | Weight | Detail | Sources |
| --- | --- | --- | --- | --- | --- |
| domain_very_young | real & established | single-source | +30 | Domain registered 38 days ago (< 90 days). | [3] |
| domain_status_unlocked | real & established | single-source | +4 | Domain status (none) does not include a client transfer lock at Cheap Registrar LLC. | [3] |
| no_mx_records | real & established | single-source | +10 | No MX records: the domain cannot receive email; unusual for a real business. | [1] |
| no_spf_record | security posture | single-source | +6 | No SPF record published for the domain. | [1] |
| no_dmarc_record | security posture | single-source | +4 | No DMARC policy published: the domain does not declare how unauthenticated mail is handled. | [1] |
| certificate_history | real & established | single-source | -6 | 1 certificate(s) in transparency logs covering 1 name(s). | [5] |
| single_certificate_only | real & established | single-source | +18 | Only one certificate has ever been issued for the domain, covering a single name: it looks like a scratch or short-lived site, not an established service. | [5] |
| urlscan_malicious | threat & reputation | single-source | +40 | urlscan.io holds 3 of 5 scan verdict(s) marked malicious (phishing). | [7] |
| listed_in_phishtank | threat & reputation | single-source | +55 | The domain is listed in the PhishTank feed of verified phishing sites (2 entries). | [2] |
| self_signed_cert | security posture | single-source | +25 | TLS certificate is self-signed. | [4] |
| scam_phrases | threat & reputation | single-source | +20 | Homepage contains high-risk phrases: wire transfer, ends tonight, limited offer, telegram @, no company registration. | [6] |
| no_hsts | security posture | single-source | +2 | No HSTS header on the homepage; traffic can be downgraded. | [6] |
| negative_reports | threat & reputation | single-source | +25 | 2 independent negative report(s); e.g. example-watch.example: Acme-cloud-services.example took a wire transfer and never delivered. Avoid.; example-bureau.example: Multiple complaints of fraud involving acme-cloud-services.example.. | [9], [8] |

## Sources
[1] demo: canned DoH response
[2] demo: canned PhishTank
[3] demo: canned RDAP response
[4] demo: canned TLS response
[5] demo: canned crt.sh response
[6] demo: canned homepage
[7] demo: canned urlscan response
[8] <https://example-bureau.example/t/acme-cloud-services>
[9] <https://example-watch.example/acme-cloud-services>

## Tool results
- **rdap_lookup**: ok
- **doh_dns**: ok
- **tls_inspect**: ok
- **ct_logs**: ok
- **urlscan_reputation**: ok
- **fetch_homepage**: ok
- **web_search_reports**: ok
- **crustdata_enrich**: ok
- **phishtank_check**: ok

## What we could not verify
- **crustdata_enrich**: ran, no signal produced

## Methodology

An AI agent planned and executed a step-by-step OSINT investigation using 9 tools (crustdata_enrich, ct_logs, doh_dns, fetch_homepage, phishtank_check, rdap_lookup, tls_inspect, urlscan_reputation, web_search_reports). 9 succeeded and 0 failed; failures are recorded, never fatal. No step needed a retry. Outputs were combined into weighted risk signals across three layers (is it real and established, is its security posture mature, are there active abuse signals). Every claim cites the tool and source behind it and is tagged corroborated, single-source or contradicted. Scores are heuristic, not financial advice; verify before acting.
