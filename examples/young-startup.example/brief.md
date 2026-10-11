# VendorLens risk brief: acme-cloud-services.example

_Generated 2026-10-11T23:04:03.664874+00:00 by VendorLens (neatHack 2026, team solohackaton). Run f265b6e1._

## Verdict: MEDIUM (29/100)

| Signal | Layer | Confidence | Weight | Detail | Sources |
| --- | --- | --- | --- | --- | --- |
| domain_young | real & established | single-source | +12 | Domain registered 120 days ago (< 1 year). | [2] |
| no_mx_records | real & established | single-source | +10 | No MX records: the domain cannot receive email; unusual for a real business. | [1] |
| spf_record_present | security posture | single-source | -3 | Domain publishes an SPF record authorising its mail senders. | [1] |
| no_dmarc_record | security posture | single-source | +4 | No DMARC policy published: the domain does not declare how unauthenticated mail is handled. | [1] |
| certificate_history | real & established | single-source | -6 | 6 certificate(s) in transparency logs covering 3 name(s). | [4] |
| cert_expiring | security posture | single-source | +10 | TLS certificate expires in 22 days. | [3] |
| no_hsts | security posture | single-source | +2 | No HSTS header on the homepage; traffic can be downgraded. | [5] |

## Sources
[1] demo: canned DoH response
[2] demo: canned RDAP response
[3] demo: canned TLS response
[4] demo: canned crt.sh response
[5] demo: canned homepage

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
- **urlscan_reputation**: ran, no signal produced
- **web_search_reports**: ran, no signal produced
- **crustdata_enrich**: ran, no signal produced
- **phishtank_check**: ran, no signal produced

## Methodology

An AI agent planned and executed a step-by-step OSINT investigation using 9 tools (crustdata_enrich, ct_logs, doh_dns, fetch_homepage, phishtank_check, rdap_lookup, tls_inspect, urlscan_reputation, web_search_reports). 9 succeeded and 0 failed; failures are recorded, never fatal. No step needed a retry. Outputs were combined into weighted risk signals across three layers (is it real and established, is its security posture mature, are there active abuse signals). Every claim cites the tool and source behind it and is tagged corroborated, single-source or contradicted. Scores are heuristic, not financial advice; verify before acting.
