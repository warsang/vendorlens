# VendorLens risk brief: example.com

_Generated 2026-10-11T09:15:02.378934+00:00 by VendorLens (neatHack 2026, team solohackaton). Run 1de9e421._

## Verdict: MEDIUM (25/100)

| Signal | Weight | Detail | Sources |
| --- | --- | --- | --- |
| negative_reports | +25 | 7 negative report(s) found in web search. | [1], [2], [3], [4], [5] |

## Sources
[1] https://www.reddit.com/r/Scams/comments/1686a8o/if_examplecom_is_a_legit_website_does_that_mean/
[2] https://www.scam-detector.com/validator/example-com-review/
[3] https://www.scam-detector.com/validator/examples-com-review/
[4] https://www.scamadviser.com/
[5] https://www.scamadviser.com/check-website/example.com

## Tool results
- **whois_lookup**: ok
- **dns_lookup**: ok
- **tls_inspect**: ok
- **fetch_homepage**: ok
- **web_search_reports**: ok
- **crustdata_enrich**: FAILED
  - error: gave up after 3: CRUSTDATA_API_KEY not set

## Methodology

An AI agent planned an OSINT investigation, executed six tools step by step (company enrichment, DNS, WHOIS, TLS, homepage analysis, web search), retried failures with backoff, and combined the outputs into weighted risk signals. Every claim above cites the tool and source behind it. Scores are heuristic, not financial advice; verify before acting.
