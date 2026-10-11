# Scoring: signals, weights and rationale

The score is `clamp(0, 100, sum(signal weights))`. Bands: `LOW < 25`,
`MEDIUM 25-49`, `HIGH 50-74`, `CRITICAL >= 75`. Weights are heuristic and
demonstrably opinionated; they are documented here so a reader can audit and
tune them (`vendorlens/risk.py`). Negative weights offset positives; the total
never leaves 0-100.

Each signal also carries a **layer** and a **confidence** tag.

- Layers: `real & established` (is it a real, operating business),
  `security posture` (is its hygiene mature), `threat & reputation`
  (active abuse / disqualifier). See the two headline questions in the README.
- Confidence (`vendorlens/verify.py`): `corroborated` (>= 2 independent tools
  agree), `single_source`, or `contradicted` (two tools disagree, e.g. registry
  age vs certificate history, which suggests a re-registered domain).

## Real & established (legitimacy)

| Signal | Weight | Rationale |
|---|---:|---|
| `domain_unregistered` | +40 | No RDAP record: the domain does not exist. |
| `domain_registered_days_ago` (<30d) | +35 | Days-old domains are a classic vendor-scam tell. |
| `domain_very_young` (30-89d) | +30 | Under 90 days: little history. |
| `domain_young` (90-364d) | +12 | Under a year. |
| `domain_well_established` (>4y) | -12 | Long history is evidence of a real business. |
| `domain_status_unlocked` | +4 | No transfer lock invites hijacking. |
| `domain_does_not_resolve` (NXDOMAIN) | +30 | A vendor domain that resolves to nothing cannot be paid. |
| `no_a_records` | +15 | Nothing points at a web server. |
| `no_mx_records` | +10 | Cannot receive mail; unusual for a real business. |
| `no_certificate_history` | +12 | No transparency trail: weak evidence of operation. |
| `certificate_history` (>=1 cert) | -6 | A public cert trail is a positive. |
| `certificate_history_long` (>=3y) | -8 | Years of continuity. |
| `single_certificate_only` | +18 | One cert for one name looks temporary. |
| `privacy_and_terms_pages` | -3 | Basic legal surface present. |
| `established_company` | -20 | A real company record (Crustdata). |
| `company_name_on_site` | -6 | Company record cross-checks against the homepage. |

## Security posture (maturity)

| Signal | Weight | Rationale |
|---|---:|---|
| `self_signed_cert` | +25 | Self-signed TLS is a strong negative. |
| `cert_expiring` (<30d) | +10 | Lapses are operational risk. |
| `no_spf_record` | +6 | Email can be spoofed as the domain. |
| `spf_record_present` | -3 | SPF authorises legitimate senders. |
| `no_dmarc_record` | +4 | No declared policy for unauthenticated mail. |
| `dmarc_policy_none` (p=none) | +2 | Monitors only; weak. |
| `dmarc_enforced` (p=reject/quarantine) | -3 | Strong anti-spoofing posture. |
| `no_hsts` | +2 | Traffic can be downgraded. |
| `hsts_enabled` | -3 | Binds browsers to HTTPS. |
| `csp_enabled` | -2 | Content-Security-Policy present. |
| `trust_page` | -2 | Links a trust/security page. |
| `security_txt_present` | -4 | Publishes a security contact. |

## Threat & reputation (abuse / disqualifier)

| Signal | Weight | Rationale |
|---|---:|---|
| `listed_in_phishtank` | +55 | Verified-phishing listing is a near-disqualifier. |
| `urlscan_malicious` | +40 | Independent scanners flag it malicious. |
| `urlscan_flagged_categories` | +25 | Categorised phishing/malware/etc. |
| `urlscan_scan_history_clean` (>=5, 0 malicious) | -8 | A real scanned history with no bad verdict. |
| `scam_phrases` | +20 | Pressure/payment red flags in the copy. |
| `negative_reports` | +25 | >=2 independent third-party hits naming the vendor, own-domain excluded, snippets shown. |

## Cross-source corroboration discount

If at least **two independent tools** establish the business as real
(`company record`, `registration age`, `certificate history`, `clean scan
history`), the keyword-only signals `scam_phrases` and `negative_reports` are
halved, and the explanation names only the evidence that actually fired. This
is deliberately conservative: a single corroborating source does not discount
anything, and it never claims evidence that did not run.

## Known limitations

- Weights are expert-guessed, not learned; the offline eval
  (`python -m vendorlens.eval`) reports accuracy on 7 labelled cached runs
  only.
- `negative_reports` can still match a legitimate vendor that is widely
  discussed in anti-scam content; the discount and shown snippets exist so a
  human can judge quickly.
- Absence of evidence (a tool that fails) is reported under "What we could not
  verify", not silently scored.
