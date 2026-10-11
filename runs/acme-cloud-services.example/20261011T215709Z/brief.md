# VendorLens risk brief: acme-cloud-services.example

_Generated 2026-10-11T21:57:09.631978+00:00 by VendorLens (neatHack 2026, team solohackaton). Run 21199f99._

## Verdict: MEDIUM (48/100)

| Signal | Weight | Detail | Sources |
| --- | --- | --- | --- |
| certificate_history | -6 | 14 certificate(s) in transparency logs covering 4 name(s). | [1] |
| certificate_history_long | -8 | Certificates publicly logged since 2022 (more than three years of continuity). | [1] |
| urlscan_malicious | +40 | urlscan.io holds 2 of 3 scan verdict(s) marked malicious (phishing). | [1] |
| scam_phrases | +10 | Homepage contains high-risk phrases: wire transfer, ends tonight, limited offer, telegram @, no company registration. (discounted: corroborating registry, certificate and firmographic evidence outweigh a keyword search hit) | [1] |
| negative_reports | +12 | 2 negative report(s) found in web search. (discounted: corroborating registry, certificate and firmographic evidence outweigh a keyword search hit) | [1], [2] |

## Sources
[1] demo: canned crt.sh response
[2] demo: canned homepage
[3] demo: canned urlscan response
[4] https://example-forum.example/t/12345
[5] https://example-reviews.example/acme

## Tool results
- **rdap_lookup**: ok
- **doh_dns**: ok
- **tls_inspect**: ok
- **ct_logs**: ok
- **urlscan_reputation**: ok
- **phishtank_check**: ok
- **fetch_homepage**: ok
- **web_search_reports**: ok
- **crustdata_enrich**: ok

## Methodology

An AI agent planned an OSINT investigation, executed six tools step by step (company enrichment, DNS, WHOIS, TLS, homepage analysis, web search), retried failures with backoff, and combined the outputs into weighted risk signals. Every claim above cites the tool and source behind it. Scores are heuristic, not financial advice; verify before acting.
