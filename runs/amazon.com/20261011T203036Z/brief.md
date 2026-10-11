# VendorLens risk brief: amazon.com

_Generated 2026-10-11T20:31:07.142711+00:00 by VendorLens (neatHack 2026, team solohackaton). Run e1693822._

## Verdict: LOW (0/100)

| Signal | Weight | Detail | Sources |
| --- | --- | --- | --- |
| domain_well_established | -12 | Domain registered 11667 days ago (over 4 years of history). | [1] |
| no_certificate_history | +12 | No public certificate history. Real services leave a certificate-transparency trail; an absence is weak evidence of an operating business. | [1] |
| urlscan_scan_history_clean | -8 | 100 urlscan.io scans on record with no malicious verdicts. | [1] |
| negative_reports | +25 | 6 negative report(s) found in web search. | [1], [2], [3], [4], [5] |
| established_company | -20 | Company found in business data: Amazon (None, 10001+ employees). | [1] |

## Sources
[1] crt.sh:amazon.com
[2] https://api.crustdata.com/company/enrich
[3] https://usacomplaints.com/company/amazon/
[4] https://www.amazon.com/gp/help/customer/display.html?nodeId=G4YFYCCNUSENA23B
[5] https://www.amazon.com/gp/help/customer/display.html?nodeId=TapjnwRvIRtlgyLPSl
[6] https://www.complaintsboard.com/amazon-b109438
[7] https://www.consumeraffairs.com/online/amazon.html
[8] rdap.org:amazon.com
[9] urlscan.io:amazon.com

## Tool results
- **rdap_lookup**: ok
- **doh_dns**: ok
- **tls_inspect**: ok
- **ct_logs**: ok
- **urlscan_reputation**: ok
- **phishtank_check**: FAILED
  - error: gave up after 3: HTTPStatusError: Client error '404 Not Found' for url 'https://cdn.phishtank.com/datadumps/verified_online.json?Expires=1791750652&Signature=QSZUIJpc3YKobBxt1LvwgDBEtjuYtkseOnpCOowuobKFsxGktcfTEhNPkBFKUQUFUa6FG9JO3jP9a5Wu~039MtSM3k-NnBwOuJy-YJ1T1b4lmEvIZ~rWCBt6o24mtgtx11aRM7LYTB-QqpCr7PBRQC~h5jMGkhkj1FdGjQpaEX8CxeNCS2cTuX7SIbeiArQKi0fzLb0sk9i0~OqX1nS60lwusKkFsXK2zwERbZttxxmHyQJu~5xxx83rHIu1AtNDVWYKNc8~w~yPQXGUYfmCeoHj5~ldSihliExFfj1EXVKyNziGiMUItBlaYRcVjkNw24A-J3KnltBPulXLXOAF5g__&Key-Pair-Id=APKAILB45UG3RB4CSOJA'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
- **fetch_homepage**: ok
- **web_search_reports**: ok
- **crustdata_enrich**: ok

## Methodology

An AI agent planned an OSINT investigation, executed six tools step by step (company enrichment, DNS, WHOIS, TLS, homepage analysis, web search), retried failures with backoff, and combined the outputs into weighted risk signals. Every claim above cites the tool and source behind it. Scores are heuristic, not financial advice; verify before acting.
