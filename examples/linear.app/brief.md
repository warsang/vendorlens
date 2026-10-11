# VendorLens risk brief: linear.app

_Generated 2026-10-11T23:04:03.602544+00:00 by VendorLens (neatHack 2026, team solohackaton). Run a4e7044c._

## Verdict: LOW (0/100)

| Signal | Layer | Confidence | Weight | Detail | Sources |
| --- | --- | --- | --- | --- | --- |
| domain_well_established | real & established | single-source | -12 | Domain registered 3076 days ago (over 4 years of history). | [5] |
| spf_record_present | security posture | single-source | -3 | Domain publishes an SPF record authorising its mail senders. | [2] |
| dmarc_enforced | security posture | single-source | -3 | DMARC enforcement is on (p=reject). | [2] |
| no_certificate_history | real & established | single-source | +12 | No public certificate history. Real services leave a certificate-transparency trail; an absence is weak evidence of an operating business. | [1] |
| urlscan_scan_history_clean | threat & reputation | single-source | -8 | 25 urlscan.io scans on record with no malicious verdicts. | [6] |
| hsts_enabled | security posture | single-source | -3 | Homepage sends HSTS, binding browsers to HTTPS. | [4] |
| csp_enabled | security posture | single-source | -2 | Homepage sends a Content-Security-Policy header. | [4] |
| privacy_and_terms_pages | real & established | single-source | -3 | Homepage links to both a privacy policy and terms of service. | [4] |
| trust_page | security posture | single-source | -2 | Homepage links to a trust/security page. | [4] |
| security_txt_present | security posture | single-source | -4 | Publishes a security.txt contact (mailto:security@linear.app). | [4] |
| established_company | real & established | single-source | -20 | Company found in business data: Linear (San Francisco, California, United States, 51-200 employees). | [3] |
| company_name_on_site | real & established | single-source | -6 | The registered company name appears on the fetched homepage, cross-checking the business record. | [3], [4] |

## Sources
[1] crt.sh:linear.app
[2] dns.google:linear.app
[3] <https://api.crustdata.com/company/enrich>
[4] <https://linear.app/>
[5] rdap.org:linear.app
[6] urlscan.io:linear.app

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
