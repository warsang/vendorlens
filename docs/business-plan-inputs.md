# VendorLens business plan — inputs for cfo.ai

Paste these into cfo.ai (https://cfo.ai/neathacks) to generate the formal
plan. Include the resulting plan in the hackathon submission. Numbers below
are internally consistent (revised Oct 11 2026: margins, breakeven and runway
were corrected); see the notes under each section.

## Product

VendorLens: AI vendor due-diligence. Input a company domain; an agent runs
OSINT (RDAP/WHOIS, DNS-over-HTTPS with SPF/DMARC, TLS, certificate-
transparency history, urlscan + PhishTank reputation, homepage security
posture + security.txt, company enrichment, web-search reports) and writes a
cited risk brief with a 0-100 score across two layers: "is this domain real
and established?" and "is this vendor's security posture mature?", plus a
threat/reputation watch. Plus an on-device browser verdict layer (jev-web
typed-decision model; no text leaves the device).

## Customers

Procurement teams, finance controllers, and marketplace trust-and-safety
teams at SMBs doing 20-200 vendor onboardings a year.

## Pricing tiers (per month, annual billing)

- Starter: $49 — 50 investigations/mo, brief PDF export.
- Team: $199 — 500 investigations/mo, API access, Slack alerts.
- Enterprise: custom — SSO, audit log, custom risk weights, DPA.

## Unit economics (assumptions)

- Blended model cost per investigation: ~$0.04 (planner + observer + analyst
  summary on cheap models via LiteLLM; most tools are free/keyless APIs).
- Company enrichment (Crustdata): ~$0.10 per investigation. **The agent calls
  it on every live run today**, so the blended data cost per live
  investigation is ~$0.14. (Roadmap cost lever: gate enrichment to Team+; that
  would lower Starter COGS to ~$0.04.)
- Gross margin, enrichment on every investigation:
  - Starter: 50 x $0.14 = $7 cost on $49 = ~86% margin.
  - Team: 500 x $0.14 = $70 cost on $199 = ~65% margin.
  - (If enrichment is gated to Team+, Starter rises to ~96%.)

## Revenue scenarios (year 1)

- Conservative: 200 paying teams avg $120/mo = $288k ARR.
- Base: 600 paying teams avg $140/mo = ~$1.0M ARR.
- Optimistic: 1,500 paying teams avg $150/mo = $2.7M ARR.

## Costs (monthly, base scenario at 12 months)

- Inference + data APIs: $4k. Infra (hosting, queues): $1.5k.
- Founder salary: $8k. Contractor (design): $2k. Total burn: ~$16k/mo.

## Runway and breakeven (corrected)

- Raise/grant: $250k pre-seed. Operating runway at $16k/mo burn: ~15.6 months
  of cash (not "runway to profitability").
- Contribution breakeven: at ~$140/mo average revenue per team, covering a
  $16k/mo burn needs ~$16k / $140 = ~115 paying teams. (Plan text no longer
  says ~450 teams; that figure was wrong.)

## Moat

- Cited-evidence briefs: every claim links to a public source and carries a
  confidence tag (corroborated / single-source / contradicted).
- A keyless, low-cost OSINT stack: cents per check, no enterprise contract.
- An on-device private verdict layer: verdict text never leaves the browser.
- Roadmap (NOT shipped): a cross-run cache of past investigations. The code
  does not retain a vendor-risk graph today, so it is not claimed as a moat.

## Plan correction notes (for a cfo.ai re-export)

The exported plan (`docs/business-plan.pdf`) already reconciles the runway
figures (15.6 months of cash, break-even ~115-135 teams, Team margin ~65% at
full use). Two wording items remain that the code does not support; correct
these when re-exporting:

1. **Moat.** Delete the "Accumulated vendor-risk graph" paragraph (the code
   does not retain a cross-run graph of domains/registrants/hosting). Replace
   with the shipped moat: cited-evidence briefs, a keyless low-cost OSINT
   stack, and the on-device private verdict layer. A cross-run cache is
   roadmap, not shipped.
2. **Crustdata.** Change "Crustdata enrichment per enriched investigation
   (Team+ only)" to per **live investigation** (the agent calls it on every
   live run today); note that gating it to Team+ is a roadmap cost lever.

Everything else (pricing, scenarios, burn, runway, break-even) is consistent
with the code and needs no change.



## Competitive landscape

- Security-ratings / TPRM vendors (e.g. BitSight, SecurityScorecard) and
  business-data providers (Crustdata, Clearbit): richer data, but annual
  enterprise contracts and costs of dollars-to-tens-of-dollars per lookup.
- KYB vendors (Veriff/Onfido KYB, Sumsub): document-based identity checks.
- URL/domain scanners (urlscan.io, VirusTotal, Google Safe Browsing): point
  tools that flag malicious pages but do not establish whether a company
  exists.

VendorLens differs by being cited and auditable (every claim links to a public
source), keyless and cheap per check (~cents), open-source, and privacy-
preserving (on-device verdict). It is the low-cost pre-contract check, not a
replacement for enterprise security ratings or formal KYB.
