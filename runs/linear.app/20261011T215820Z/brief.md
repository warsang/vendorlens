# VendorLens risk brief: linear.app

_Generated 2026-10-11T21:58:59.439823+00:00 by VendorLens (neatHack 2026, team solohackaton). Run c9af086a._

## Verdict: LOW (2/100)

| Signal | Weight | Detail | Sources |
| --- | --- | --- | --- |
| no_mx_records | +10 | No MX records: domain cannot receive email; unusual for a real business. | [1], [2], [3] |
| negative_reports | +12 | 3 negative report(s) found in web search. (discounted: corroborating registry, certificate and firmographic evidence outweigh a keyword search hit) | [1], [2], [3] |
| established_company | -20 | Company found in business data: Linear (San Francisco, California, United States, 51-200 employees). | [1] |

## Sources
[1] dns:A linear.app
[2] dns:MX linear.app
[3] dns:TXT linear.app
[4] https://api.crustdata.com/company/enrich
[5] https://justuseapp.com/en/app/1645587184/linear-mobile/reviews
[6] https://www.scamadviser.com/
[7] https://www.scamadviser.com/check-website/linear.app

## Tool results
- **whois_lookup**: ok
- **dns_lookup**: ok
- **tls_inspect**: ok
- **fetch_homepage**: ok
- **crustdata_enrich**: ok
- **web_search_reports**: ok

## Methodology

An AI agent planned an OSINT investigation, executed six tools step by step (company enrichment, DNS, WHOIS, TLS, homepage analysis, web search), retried failures with backoff, and combined the outputs into weighted risk signals. Every claim above cites the tool and source behind it. Scores are heuristic, not financial advice; verify before acting.
