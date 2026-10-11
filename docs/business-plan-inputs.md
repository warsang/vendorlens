# VendorLens business plan — inputs for cfo.ai

Paste these into cfo.ai (https://cfo.ai/neathacks) to generate the formal
plan. Include the resulting plan in the hackathon submission.

## Product
VendorLens: AI vendor due-diligence. Input a company domain; an agent runs
OSINT (company data, DNS, WHOIS, TLS, homepage analysis, scam-report search)
and writes a cited risk brief with a 0–100 score. Plus an on-device browser
verdict layer (jev-web typed-decision model, no data leaves the browser).

## Customers
Procurement teams, finance controllers, and marketplace trust-and-safety
teams at SMBs doing 20–200 vendor onboardings a year.

## Pricing tiers (per month, annual billing)
- Starter: $49 — 50 investigations/mo, brief PDF export.
- Team: $199 — 500 investigations/mo, API access, Slack alerts.
- Enterprise: custom — SSO, audit log, custom risk weights, DPA.

## Unit economics (assumptions)
- Blended model cost per investigation: ~$0.04 (planner + observer calls on
  cheap models via LiteLLM; tools are mostly free APIs/DNS).
- Crustdata enrichment: ~$0.10 per enriched investigation (only on Team+).
- Gross margin at scale: ~85% on Starter, ~80% on Team.

## Revenue scenarios (year 1)
- Conservative: 200 paying teams avg $120/mo = $288k ARR.
- Base: 600 paying teams avg $140/mo = ~$1M ARR.
- Optimistic: 1,500 paying teams avg $150/mo = $2.7M ARR.

## Costs (monthly, base scenario at 12 months)
- Inference + data APIs: $4k. Infra (hosting, queues): $1.5k.
- Founder salary: $8k. Contractor (design): $2k. Total burn: ~$16k/mo.

## Runway
- Raise/grant: $250k pre-seed. Runway at base burn: ~15 months to
  profitability at ~450 paying teams.

## Moat
Cited-evidence briefs (every claim sourced), on-device private scoring
layer, and accumulated vendor-risk graph from investigations.
