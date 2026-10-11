# VendorLens risk brief: acme-cloud-services.example

_Generated 2026-10-11T23:04:03.698573+00:00 by VendorLens (neatHack 2026, team solohackaton). Run 18f2ba13._

## Verdict: LOW (0/100)

| Signal | Layer | Confidence | Weight | Detail | Sources |
| --- | --- | --- | --- | --- | --- |
| domain_well_established | real & established | single-source | -12 | Domain registered 5695 days ago (over 4 years of history). | [3] |
| spf_record_present | security posture | single-source | -3 | Domain publishes an SPF record authorising its mail senders. | [2] |
| dmarc_enforced | security posture | single-source | -3 | DMARC enforcement is on (p=reject). | [2] |
| certificate_history | real & established | single-source | -6 | 62 certificate(s) in transparency logs covering 14 name(s). | [4] |
| certificate_history_long | real & established | single-source | -8 | Certificates publicly logged since 2015 (more than three years of continuity). | [4] |
| urlscan_scan_history_clean | threat & reputation | single-source | -8 | 92 urlscan.io scans on record with no malicious verdicts. | [6] |
| hsts_enabled | security posture | single-source | -3 | Homepage sends HSTS, binding browsers to HTTPS. | [5] |
| csp_enabled | security posture | single-source | -2 | Homepage sends a Content-Security-Policy header. | [5] |
| privacy_and_terms_pages | real & established | single-source | -3 | Homepage links to both a privacy policy and terms of service. | [5] |
| trust_page | security posture | single-source | -2 | Homepage links to a trust/security page. | [5] |
| security_txt_present | security posture | single-source | -4 | Publishes a security.txt contact (mailto:security@acme-cloud-services.example). | [5] |
| established_company | real & established | single-source | -20 | Company found in business data: Acme Cloud Services Ltd (Austin, TX, USA, 51-200 employees). | [1] |
| company_name_on_site | real & established | single-source | -6 | The registered company name appears on the fetched homepage, cross-checking the business record. | [1], [5] |

## Sources
[1] demo: canned Crustdata response
[2] demo: canned DoH response
[3] demo: canned RDAP response
[4] demo: canned crt.sh response
[5] demo: canned homepage
[6] demo: canned urlscan response

## Tool results
- **rdap_lookup**: ok
- **doh_dns**: ok
- **tls_inspect**: ok
- **ct_logs**: ok
- **urlscan_reputation**: ok
- **fetch_homepage**: ok
- **web_search_reports**: ok
- **crustdata_enrich**: ok

## What we could not verify
- **tls_inspect**: ran, no signal produced
- **web_search_reports**: ran, no signal produced

## Methodology

An AI agent planned and executed a step-by-step OSINT investigation using 8 tools (crustdata_enrich, ct_logs, doh_dns, fetch_homepage, rdap_lookup, tls_inspect, urlscan_reputation, web_search_reports). 8 succeeded and 0 failed; failures are recorded, never fatal. No step needed a retry. Outputs were combined into weighted risk signals across three layers (is it real and established, is its security posture mature, are there active abuse signals). Every claim cites the tool and source behind it and is tagged corroborated, single-source or contradicted. Scores are heuristic, not financial advice; verify before acting.
