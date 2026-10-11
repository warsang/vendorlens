# VendorLens risk brief: stripe.com

_Generated 2026-10-11T23:03:52.604181+00:00 by VendorLens (neatHack 2026, team solohackaton). Run 2cb9f362._

## Verdict: LOW (0/100)

| Signal | Layer | Confidence | Weight | Detail | Sources |
| --- | --- | --- | --- | --- | --- |
| domain_well_established | real & established | single-source | -12 | Domain registered 11352 days ago (over 4 years of history). | [10] |
| spf_record_present | security posture | single-source | -3 | Domain publishes an SPF record authorising its mail senders. | [2] |
| dmarc_enforced | security posture | single-source | -3 | DMARC enforcement is on (p=reject). | [2] |
| certificate_history | real & established | single-source | -6 | 2321 certificate(s) in transparency logs covering 213 name(s). | [1] |
| certificate_history_long | real & established | single-source | -8 | Certificates publicly logged since 2009 (more than three years of continuity). | [1] |
| urlscan_scan_history_clean | threat & reputation | single-source | -8 | 100 urlscan.io scans on record with no malicious verdicts. | [11] |
| hsts_enabled | security posture | single-source | -3 | Homepage sends HSTS, binding browsers to HTTPS. | [5] |
| csp_enabled | security posture | single-source | -2 | Homepage sends a Content-Security-Policy header. | [5] |
| security_txt_present | security posture | single-source | -4 | Publishes a security.txt contact (https://hackerone.com/stripe). | [5] |
| established_company | real & established | single-source | -20 | Company found in business data: Stripe (South San Francisco, California, United States, 5001-10000 employees). | [3] |
| company_name_on_site | real & established | single-source | -6 | The registered company name appears on the fetched homepage, cross-checking the business record. | [3], [5] |
| negative_reports | threat & reputation | single-source | +12 | 5 independent negative report(s); e.g. reddit.com: Stripe is taking advantage of a lack of regulation in this space to steal small ...; smartcustomer.com: 447 reviews for Stripe, 2.1 stars: 'After so many communications, emails, mails,...; thefinrate.com: Explore whether Stripe is a scam through our investigative report. We examine us.... (discounted: registration age, certificate history, a clean scan history, the company record corroborate a real business, outweigh a keyword search hit) | [7], [9], [6], [4], [8] |

## Sources
[1] crt.sh:stripe.com
[2] dns.google:stripe.com
[3] <https://api.crustdata.com/company/enrich>
[4] <https://socialcatfish.com/scamfish/how-to-identify-a-stripe-scam-before-it-costs-you-money-in-2026/>
[5] <https://stripe.com/es>
[6] <https://thefinrate.com/is-stripe-a-scam-an-investigative-report/>
[7] <https://www.reddit.com/r/ecommerce/comments/wa20e0/do_not_use_stripe_this_is_your_warning_learn_from/>
[8] <https://www.scamadviser.com/check-website/stripe.com>
[9] <https://www.smartcustomer.com/reviews/stripe.com>
[10] rdap.org:stripe.com
[11] urlscan.io:stripe.com

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
