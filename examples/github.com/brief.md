# VendorLens risk brief: github.com

_Generated 2026-10-11T23:03:19.970466+00:00 by VendorLens (neatHack 2026, team solohackaton). Run 88a3682b._

## Verdict: LOW (0/100)

| Signal | Layer | Confidence | Weight | Detail | Sources |
| --- | --- | --- | --- | --- | --- |
| domain_well_established | real & established | single-source | -12 | Domain registered 6942 days ago (over 4 years of history). | [7] |
| spf_record_present | security posture | single-source | -3 | Domain publishes an SPF record authorising its mail senders. | [2] |
| dmarc_enforced | security posture | single-source | -3 | DMARC enforcement is on (p=quarantine). | [2] |
| certificate_history | real & established | single-source | -6 | 1223 certificate(s) in transparency logs covering 128 name(s). | [1] |
| certificate_history_long | real & established | single-source | -8 | Certificates publicly logged since 2008 (more than three years of continuity). | [1] |
| urlscan_scan_history_clean | threat & reputation | single-source | -8 | 100 urlscan.io scans on record with no malicious verdicts. | [8] |
| hsts_enabled | security posture | single-source | -3 | Homepage sends HSTS, binding browsers to HTTPS. | [5] |
| csp_enabled | security posture | single-source | -2 | Homepage sends a Content-Security-Policy header. | [5] |
| privacy_and_terms_pages | real & established | single-source | -3 | Homepage links to both a privacy policy and terms of service. | [5] |
| trust_page | security posture | single-source | -2 | Homepage links to a trust/security page. | [5] |
| security_txt_present | security posture | single-source | -4 | Publishes a security.txt contact (https://hackerone.com/github). | [5] |
| established_company | real & established | single-source | -20 | Company found in business data: GitHub (San Francisco, California, United States, 501-1000 employees). | [3] |
| company_name_on_site | real & established | single-source | -6 | The registered company name appears on the fetched homepage, cross-checking the business record. | [3], [5] |
| negative_reports | threat & reputation | single-source | +12 | 2 independent negative report(s); e.g. scamadviser.com: Check github.com with our free review tool and find out if github.com is legit a...; fraudreviews.net: This GitHub review uncovers how its platform is used by crypto projects, potenti.... (discounted: registration age, certificate history, a clean scan history, the company record corroborate a real business, outweigh a keyword search hit) | [6], [4] |

## Sources
[1] crt.sh:github.com
[2] dns.google:github.com
[3] <https://api.crustdata.com/company/enrich>
[4] <https://fraudreviews.net/crypto-scam-reviews/github-scam-review/>
[5] <https://github.com/>
[6] <https://www.scamadviser.com/check-website/github.com>
[7] rdap.org:github.com
[8] urlscan.io:github.com

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

## Methodology

An AI agent planned and executed a step-by-step OSINT investigation using 8 tools (crustdata_enrich, ct_logs, doh_dns, fetch_homepage, rdap_lookup, tls_inspect, urlscan_reputation, web_search_reports). 8 succeeded and 0 failed; failures are recorded, never fatal. No step needed a retry. Outputs were combined into weighted risk signals across three layers (is it real and established, is its security posture mature, are there active abuse signals). Every claim cites the tool and source behind it and is tagged corroborated, single-source or contradicted. Scores are heuristic, not financial advice; verify before acting.
