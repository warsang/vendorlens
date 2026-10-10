# Demo video script — VendorLens (≤ 3 minutes)

Target: 2:45. Every second must earn its place. The video MUST explicitly
cover neatlogs, Entire and cfo.ai (20% of the score is the demo).

## 0:00–0:20 — The problem (20s)
"Every week, companies wire money to vendors they've never verified. I built
VendorLens: give it a company domain, and an AI agent runs a full
due-diligence investigation — company data, DNS, domain age, TLS, homepage
analysis, scam-report search — then writes a cited risk brief."

## 0:20–1:10 — The agent live (50s)
- Terminal: `python -m vendorlens acme-cloud-services.example --demo`
- Narrate the plan: "The planner picks six tools, cheapest high-signal first."
- Show a tool failing and the retry: "A lookup fails; the agent backs off
  and retries instead of dying — that recovery is in the trace."
- The brief appears: risk score, band, every claim cited.

## 1:10–1:50 — neatlogs (40s)
- Dashboard: open the run's trace. "Every model call, every tool execution,
  inputs, outputs, latency, token cost — one trace per investigation."
- Show the before/after: "Here's the trace where the retry fired, and the
  fixed run after. That's our evidence the agent improved."

## 1:50–2:15 — Entire (25s)
- `entire checkpoint explain HEAD` in terminal. "Every commit links to the
  agent session behind it — the reasoning stays with the repo."
- Flash the checkpoint link that goes in the submission.

## 2:15–2:35 — cfo.ai (20s)
- The business plan: "VendorLens as a SaaS: pricing tiers, inference costs,
  revenue scenarios, runway — planned in cfo.ai, included in the submission."

## 2:35–2:45 — On-device verdict + close (10s)
- Demo page: paste homepage text, hit Assess, bars appear. "And the
  client-side verdict layer runs a typed-decision model entirely in the
  browser — your text never leaves the device."
- Close: "VendorLens — know your vendor. Repo and evidence linked below."

## B-roll / evidence to have ready
- neatlogs trace screenshots (before/after retry runs)
- Entire checkpoint link + ID
- cfo.ai business plan export
- trace.jsonl snippet showing the failure → retry → recovery
